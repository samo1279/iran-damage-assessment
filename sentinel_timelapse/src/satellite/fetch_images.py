"""
Sentinel-2 Satellite Image Fetcher
Downloads real imagery via COG windowed reads from AWS S3
Supports RGB (visual) + individual bands (B04 Red, B08 NIR) for NDVI
"""

import os
import json
import requests
import numpy as np
from pathlib import Path
from datetime import datetime

import rasterio
from rasterio.windows import from_bounds
from rasterio.transform import array_bounds
from rasterio.warp import transform_bounds

from src.core.config import (
    AOI_CONFIG, OUTPUT_WIDTH, OUTPUT_HEIGHT,
    MCP_CLOUD_THRESHOLD, API_TIMEOUT
)

# GDAL environment for COG reads
GDAL_ENV = {
    'GDAL_HTTP_MERGE_CONSECUTIVE_RANGES': 'YES',
    'GDAL_DISABLE_READDIR_ON_OPEN': 'EMPTY_DIR',
    'VSI_CACHE': 'TRUE',
    'VSI_CACHE_SIZE': '5000000',
    'GDAL_HTTP_TIMEOUT': '60',
    'GDAL_HTTP_CONNECTTIMEOUT': '15',
}

# Element84 STAC endpoint (free, no auth)
STAC_SEARCH_URL = "https://earth-search.aws.element84.com/v1/search"


class SatelliteFetcher:
    """Search STAC catalog and download Sentinel-2 COG crops."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})

    def search_and_download(self, city, start_date, end_date, max_images=10):
        """
        Full pipeline: search STAC → download COG crops → return list of saved paths.
        Downloads both visual (RGB) and band files (B04, B08) for change detection.
        """
        if city not in AOI_CONFIG:
            raise ValueError(f"Unknown city: {city}")

        bbox = AOI_CONFIG[city]['bbox']
        folder = str(Path(AOI_CONFIG[city]['folder']).absolute())
        Path(folder).mkdir(parents=True, exist_ok=True)

        # Search STAC
        items = self._search_stac(bbox, start_date, end_date, max_items=max_images)
        if not items:
            print(f"[STAC] No items found for {city} between {start_date} and {end_date}")
            return []

        print(f"[STAC] Found {len(items)} scenes for {city}")

        downloaded = []
        for item in items:
            try:
                # Extract date from item
                acquired = item['properties'].get('datetime', '')[:10]
                item_id = item.get('id', 'unknown')

                # Download visual (RGB) crop
                visual_url = self._get_asset_url(item, 'visual')
                if not visual_url:
                    print(f"  [SKIP] No visual asset for {item_id}")
                    continue

                out_path = os.path.join(folder, f"S2_{acquired}_{item_id[:20]}.tif")
                if os.path.exists(out_path):
                    print(f"  [CACHED] {out_path}")
                    downloaded.append(out_path)

                    # Also download bands if not cached
                    self._download_bands(item, folder, acquired, item_id, bbox)
                    continue

                print(f"  [DL] {acquired} — {item_id[:30]}...")
                success = self._download_cog_crop(visual_url, bbox, out_path)
                if success:
                    downloaded.append(out_path)
                    print(f"  [OK] Saved: {out_path}")

                    # Download individual bands for change detection (B04, B08)
                    self._download_bands(item, folder, acquired, item_id, bbox)
                else:
                    print(f"  [FAIL] Could not crop {item_id}")

            except Exception as e:
                print(f"  [ERROR] {e}")
                continue

        return downloaded

    def search_and_download_bbox(self, bbox, folder, start_date, end_date, max_images=10, bands_only=None):
        """
        Download COG crops for a custom bounding box (user-drawn area).
        Same pipeline as search_and_download but accepts raw bbox and folder.
        """
        Path(folder).mkdir(parents=True, exist_ok=True)
        items = self._search_stac(bbox, start_date, end_date, max_items=max_images)
        if not items:
            print(f"[STAC] No items for custom bbox {start_date}..{end_date}")
            return []

        print(f"[STAC] Found {len(items)} scenes for custom area")
        downloaded = []
        for item in items:
            try:
                acquired = item['properties'].get('datetime', '')[:10]
                item_id = item.get('id', 'unknown')
                
                # Check visual first
                visual_url = self._get_asset_url(item, 'visual')
                if not visual_url:
                    continue

                out_path = os.path.join(folder, f"S2_{acquired}_{item_id[:20]}.tif")
                
                if bands_only:
                    # Quick Mode: only download specific bands (e.g. visual)
                    if 'visual' in bands_only:
                        if os.path.exists(out_path):
                            downloaded.append(out_path)
                        else:
                            print(f"  [DL-QUICK] {acquired} (visual)...")
                            if self._download_cog_crop(visual_url, bbox, out_path):
                                downloaded.append(out_path)
                    
                    # Download other bands if requested specifically
                    for b in [b for b in bands_only if b != 'visual']:
                         self._download_specific_band(item, folder, acquired, item_id, bbox, b)
                    continue

                # Standard Mode
                if os.path.exists(out_path):
                    downloaded.append(out_path)
                    self._download_bands(item, folder, acquired, item_id, bbox)
                    continue

                print(f"  [DL] {acquired} — {item_id[:30]}...")
                success = self._download_cog_crop(visual_url, bbox, out_path)
                if success:
                    downloaded.append(out_path)
                    self._download_bands(item, folder, acquired, item_id, bbox)
            except Exception as e:
                print(f"  [ERROR] {e}")
                continue
        return downloaded

    def _download_specific_band(self, item, folder, acquired, item_id, bbox, band_name):
        """Helper to download a single band."""
        band_url = self._get_asset_url(item, band_name)
        if not band_url:
            alt_names = {'red': ['B04', 'b04'], 'nir': ['B08', 'b08', 'nir08']}
            for alt in alt_names.get(band_name, []):
                band_url = self._get_asset_url(item, alt)
                if band_url: break
        
        if not band_url: return False
        
        band_path = os.path.join(folder, f"S2_{acquired}_{item_id[:20]}_{band_name}.tif")
        if os.path.exists(band_path): return True
        
        try:
            return self._download_cog_crop(band_url, bbox, band_path, bands=1)
        except:
            return False

    def _download_bands(self, item, folder, acquired, item_id, bbox):
        """Download Red (B04) and NIR (B08) bands for NDVI computation."""
        for band_name in ['red', 'nir']:
            band_url = self._get_asset_url(item, band_name)
            if not band_url:
                # Try alternative names
                alt_names = {'red': ['B04', 'b04'], 'nir': ['B08', 'b08', 'nir08']}
                for alt in alt_names.get(band_name, []):
                    band_url = self._get_asset_url(item, alt)
                    if band_url:
                        break

            if not band_url:
                continue

            band_path = os.path.join(folder, f"S2_{acquired}_{item_id[:20]}_{band_name}.tif")
            if os.path.exists(band_path):
                continue

            try:
                self._download_cog_crop(band_url, bbox, band_path, bands=1)
            except Exception as e:
                print(f"  [BAND-WARN] {band_name}: {e}")

    def _search_stac(self, bbox, start_date, end_date, max_items=10):
        """Search Element84 STAC for Sentinel-2 L2A scenes."""
        payload = {
            "collections": ["sentinel-2-l2a"],
            "bbox": bbox,
            "datetime": f"{start_date}T00:00:00Z/{end_date}T23:59:59Z",
            "query": {
                "eo:cloud_cover": {"lt": MCP_CLOUD_THRESHOLD}
            },
            "sortby": [{"field": "properties.datetime", "direction": "asc"}],
            "limit": max_items,
        }

        try:
            resp = self.session.post(STAC_SEARCH_URL, json=payload, timeout=API_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            features = data.get('features', [])
            return features
        except Exception as e:
            print(f"[STAC ERROR] {e}")
            return []

    def _get_asset_url(self, item, asset_key):
        """Extract href from STAC item assets."""
        assets = item.get('assets', {})
        asset = assets.get(asset_key)
        if asset:
            return asset.get('href', '')
        return ''

    def _download_cog_crop(self, url, bbox, output_path, bands=None):
        """
        Download a windowed crop from a COG via /vsicurl/.
        This reads only the bytes needed for our AOI — no full scene download.
        """
        vsicurl_url = f"/vsicurl/{url}"

        with rasterio.Env(**GDAL_ENV):
            try:
                with rasterio.open(vsicurl_url) as src:
                    # Transform bbox from EPSG:4326 to the raster's CRS
                    src_bbox = transform_bounds('EPSG:4326', src.crs, *bbox)

                    # Compute pixel window
                    window = from_bounds(*src_bbox, transform=src.transform)

                    # Determine bands to read
                    if bands is None:
                        read_bands = list(range(1, min(src.count + 1, 4)))  # RGB (up to 3)
                    elif isinstance(bands, int):
                        read_bands = [1]  # single band
                    else:
                        read_bands = bands

                    # Read with resampling to target size
                    out_height = OUTPUT_HEIGHT
                    out_width = OUTPUT_WIDTH

                    data = src.read(
                        read_bands,
                        window=window,
                        out_shape=(len(read_bands), out_height, out_width),
                        resampling=rasterio.enums.Resampling.bilinear
                    )

                    # Build output profile
                    out_transform = rasterio.transform.from_bounds(
                        *src_bbox, out_width, out_height
                    )
                    profile = {
                        'driver': 'GTiff',
                        'dtype': data.dtype,
                        'width': out_width,
                        'height': out_height,
                        'count': len(read_bands),
                        'crs': src.crs,
                        'transform': out_transform,
                        'compress': 'deflate',
                    }

                    with rasterio.open(output_path, 'w', **profile) as dst:
                        dst.write(data)

                    return True

            except Exception as e:
                print(f"  [COG ERROR] {e}")
                return False

    def search_only(self, city, start_date, end_date, max_items=10):
        """Search STAC without downloading — returns metadata only."""
        if city not in AOI_CONFIG:
            return []
        bbox = AOI_CONFIG[city]['bbox']
        items = self._search_stac(bbox, start_date, end_date, max_items=max_items)
        results = []
        for item in items:
            results.append({
                'id': item.get('id', ''),
                'datetime': item['properties'].get('datetime', ''),
                'cloud_cover': item['properties'].get('eo:cloud_cover', -1),
                'visual_url': self._get_asset_url(item, 'visual'),
                'red_url': self._get_asset_url(item, 'red'),
                'nir_url': self._get_asset_url(item, 'nir'),
            })
        return results
