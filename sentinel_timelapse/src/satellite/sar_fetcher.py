"""
Sentinel-1 SAR (Radar) Image Fetcher
Downloads GRD (Ground Range Detected) imagery via COG windowed reads.

SAR sees through clouds, works at night, and is the gold standard
for rapid damage assessment. Detects structural damage via backscatter changes.

Key bands:
  - VV polarization: vertical transmit, vertical receive (best for urban)
  - VH polarization: vertical transmit, horizontal receive (vegetation)
"""

import os
import json
import requests
import numpy as np
from pathlib import Path
from datetime import datetime

import rasterio
from rasterio.windows import from_bounds
from rasterio.warp import transform_bounds

from src.core.config import AOI_CONFIG, OUTPUT_WIDTH, OUTPUT_HEIGHT, TIMELAPSE_OUTPUT

GDAL_ENV = {
    'GDAL_HTTP_MERGE_CONSECUTIVE_RANGES': 'YES',
    'GDAL_DISABLE_READDIR_ON_OPEN': 'EMPTY_DIR',
    'VSI_CACHE': 'TRUE',
    'VSI_CACHE_SIZE': '5000000',
    'GDAL_HTTP_TIMEOUT': '120',
    'GDAL_HTTP_CONNECTTIMEOUT': '30',
}

STAC_SEARCH_URL = "https://earth-search.aws.element84.com/v1/search"
SAR_FOLDER = os.path.join('archive', 'sar')


class SARFetcher:
    """Search and download Sentinel-1 GRD SAR imagery."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
        Path(SAR_FOLDER).mkdir(parents=True, exist_ok=True)

    def search_sar(self, bbox, start_date, end_date, max_items=10):
        """
        Search Element84 STAC for Sentinel-1 GRD scenes.
        Returns list of STAC items sorted by date ascending.
        """
        payload = {
            "collections": ["sentinel-1-grd"],
            "bbox": bbox,
            "datetime": f"{start_date}T00:00:00Z/{end_date}T23:59:59Z",
            "limit": max_items,
        }

        try:
            resp = self.session.post(STAC_SEARCH_URL, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            features = data.get('features', [])
            # Sort by datetime ascending
            features.sort(key=lambda f: f['properties'].get('datetime', ''))
            print(f"[SAR-STAC] Found {len(features)} Sentinel-1 GRD scenes")
            for f in features:
                dt = f['properties'].get('datetime', '?')[:19]
                mode = f['properties'].get('sar:instrument_mode', '?')
                print(f"  {dt}  |  Mode: {mode}  |  ID: {f['id'][:40]}")
            return features
        except Exception as e:
            print(f"[SAR-STAC ERROR] {e}")
            return []

    def download_sar_pair(self, city, start_date, end_date):
        """
        Download before + after SAR images for a city.
        Returns (before_path, after_path, before_date, after_date) or None.
        """
        if city not in AOI_CONFIG:
            raise ValueError(f"Unknown city: {city}")
        bbox = AOI_CONFIG[city]['bbox']
        return self.download_sar_pair_bbox(bbox, city, start_date, end_date)

    def download_sar_pair_bbox(self, bbox, label, start_date, end_date):
        """
        Download before + after SAR for a bbox.
        Searches the full date range and picks the earliest + latest.
        Returns dict with paths and dates or None.
        """
        items = self.search_sar(bbox, start_date, end_date, max_items=20)
        if len(items) < 2:
            # Need at least 2 scenes for before/after
            print(f"[SAR] Only {len(items)} scenes found, need at least 2.")
            if len(items) == 0:
                return None
            # If only 1, we can't do change detection
            return None

        before_item = items[0]   # earliest
        after_item = items[-1]   # latest

        before_date = before_item['properties']['datetime'][:10]
        after_date = after_item['properties']['datetime'][:10]

        if before_date == after_date:
            print(f"[SAR] Before and after are same date ({before_date}), trying harder...")
            # Try to find different dates
            dates_seen = {}
            for item in items:
                d = item['properties']['datetime'][:10]
                if d not in dates_seen:
                    dates_seen[d] = item
            if len(dates_seen) < 2:
                print("[SAR] All scenes are from same date. Cannot compare.")
                return None
            sorted_dates = sorted(dates_seen.keys())
            before_item = dates_seen[sorted_dates[0]]
            after_item = dates_seen[sorted_dates[-1]]
            before_date = sorted_dates[0]
            after_date = sorted_dates[-1]

        print(f"\n[SAR] Downloading pair: {before_date} -> {after_date}")

        # Download both VV polarization images
        before_path = self._download_sar_image(before_item, bbox, label, 'before')
        after_path = self._download_sar_image(after_item, bbox, label, 'after')

        if not before_path or not after_path:
            return None

        return {
            'before_path': before_path,
            'after_path': after_path,
            'before_date': before_date,
            'after_date': after_date,
            'before_item_id': before_item['id'],
            'after_item_id': after_item['id'],
        }

    def _download_sar_image(self, item, bbox, label, tag):
        """
        Download a SAR GRD COG crop. Tries VV first, falls back to VH.
        Returns path to saved TIF or None.
        """
        item_id = item.get('id', 'unknown')
        acquired = item['properties'].get('datetime', '')[:10]
        assets = item.get('assets', {})

        # Find the VV polarization band (best for urban damage detection)
        vv_url = None
        for key in ['vv', 'VV']:
            if key in assets:
                vv_url = assets[key].get('href', '')
                break

        if not vv_url:
            # Some items have different asset naming
            for key, asset in assets.items():
                if 'vv' in key.lower():
                    vv_url = asset.get('href', '')
                    break

        if not vv_url:
            print(f"  [SAR-WARN] No VV band found in {item_id}. Available: {list(assets.keys())}")
            # Fall back to any available band
            for key in ['vh', 'VH']:
                if key in assets:
                    vv_url = assets[key].get('href', '')
                    print(f"  [SAR] Using VH band instead")
                    break

        if not vv_url:
            print(f"  [SAR-FAIL] No usable SAR band in {item_id}")
            return None

        out_path = os.path.join(SAR_FOLDER, f"S1_{acquired}_{label}_{tag}.tif")
        if os.path.exists(out_path):
            print(f"  [SAR-CACHED] {out_path}")
            return out_path

        print(f"  [SAR-DL] {tag} {acquired} - {item_id[:30]}...")
        success = self._download_cog_crop(vv_url, bbox, out_path)
        if success:
            print(f"  [SAR-OK] {out_path}")
            return out_path
        return None

    def _download_cog_crop(self, url, bbox, output_path, target_size=512):
        """
        Download a windowed crop from a SAR COG.
        SAR data is typically float32 backscatter values (dB or linear power).
        """
        vsicurl_url = f"/vsicurl/{url}"

        with rasterio.Env(**GDAL_ENV):
            try:
                with rasterio.open(vsicurl_url) as src:
                    src_bbox = transform_bounds('EPSG:4326', src.crs, *bbox)
                    window = from_bounds(*src_bbox, transform=src.transform)

                    data = src.read(
                        [1],  # Single band (VV or VH)
                        window=window,
                        out_shape=(1, target_size, target_size),
                        resampling=rasterio.enums.Resampling.bilinear
                    )

                    out_transform = rasterio.transform.from_bounds(
                        *src_bbox, target_size, target_size
                    )
                    profile = {
                        'driver': 'GTiff',
                        'dtype': data.dtype,
                        'width': target_size,
                        'height': target_size,
                        'count': 1,
                        'crs': src.crs,
                        'transform': out_transform,
                        'compress': 'deflate',
                    }

                    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                    with rasterio.open(output_path, 'w', **profile) as dst:
                        dst.write(data)

                    return True

            except Exception as e:
                print(f"  [SAR-COG ERROR] {e}")
                return False

    def check_availability(self, city, start_date, end_date):
        """
        Check SAR availability without downloading.
        Returns list of available dates and metadata.
        """
        if city not in AOI_CONFIG:
            return []
        bbox = AOI_CONFIG[city]['bbox']
        items = self.search_sar(bbox, start_date, end_date, max_items=20)
        results = []
        for item in items:
            results.append({
                'id': item.get('id', ''),
                'datetime': item['properties'].get('datetime', ''),
                'mode': item['properties'].get('sar:instrument_mode', ''),
                'orbit': item['properties'].get('sat:orbit_state', ''),
                'assets': list(item.get('assets', {}).keys()),
            })
        return results
