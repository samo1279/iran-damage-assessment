"""
Planet Labs PlanetScope Fetcher — ~3m Resolution Imagery

From deep-research-report:
  - PlanetScope (PSScene) delivers ortho products at 3.0m pixel size
  - "finalized" data typically available ~12-24 hours after standard
  - Subscriptions API recommended for continuous delivery
  - UDM2/UDM2.1 provides per-pixel cloud classification

This module uses the Planet Data API (quick-search + asset activation + download).
Requires PL_API_KEY environment variable.
"""

import os
import time
import json
import requests
import numpy as np
from pathlib import Path
from datetime import datetime

try:
    import rasterio
    from rasterio.windows import from_bounds
    from rasterio.warp import transform_bounds
    HAS_RASTERIO = True
except ImportError:
    HAS_RASTERIO = False

from config import AOI_CONFIG, OUTPUT_WIDTH, OUTPUT_HEIGHT, TIMELAPSE_OUTPUT

# Planet API endpoints
PLANET_DATA_API = "https://api.planet.com/data/v1"
PLANET_SEARCH_URL = f"{PLANET_DATA_API}/quick-search"
PLANET_ORDERS_API = "https://api.planet.com/compute/ops/orders/v2"

PLANET_FOLDER = os.path.join('archive', 'planet')

# GDAL environment for COG reads
GDAL_ENV = {
    'GDAL_HTTP_MERGE_CONSECUTIVE_RANGES': 'YES',
    'GDAL_DISABLE_READDIR_ON_OPEN': 'EMPTY_DIR',
    'VSI_CACHE': 'TRUE',
    'VSI_CACHE_SIZE': '5000000',
    'GDAL_HTTP_TIMEOUT': '120',
    'GDAL_HTTP_CONNECTTIMEOUT': '30',
}


def get_planet_key():
    """Get Planet API key from environment."""
    return os.environ.get('PL_API_KEY', '').strip()


def planet_available():
    """Check if Planet API key is configured."""
    return bool(get_planet_key())


class PlanetFetcher:
    """
    Search and download PlanetScope ~3m imagery via Planet Data API.

    From research report:
      - Quick-search endpoint for discovery
      - Asset activation + download for retrieval
      - PSScene item_type for ~3m data
      - UDM2 cloud mask available globally from Aug 2018+
    """

    def __init__(self):
        self.api_key = get_planet_key()
        self.session = requests.Session()
        if self.api_key:
            self.session.auth = (self.api_key, '')
        self.session.headers.update({'Content-Type': 'application/json'})
        Path(PLANET_FOLDER).mkdir(parents=True, exist_ok=True)

    def is_configured(self):
        """Check if Planet API key is set."""
        return bool(self.api_key)

    def validate_key(self):
        """Test if the API key is valid by hitting the API."""
        if not self.api_key:
            return False, "No PL_API_KEY set"
        try:
            resp = self.session.get(
                f"{PLANET_DATA_API}/item-types",
                timeout=10
            )
            if resp.status_code == 200:
                return True, "Valid"
            elif resp.status_code == 401:
                return False, "Invalid API key (401 Unauthorized)"
            else:
                return False, f"API returned {resp.status_code}"
        except Exception as e:
            return False, str(e)

    def search(self, bbox, start_date, end_date, max_items=20, cloud_cover=40):
        """
        Quick-search for PlanetScope scenes (PSScene) over a bbox.

        From research report:
          - Data API Item Search: POST /data/v1/quick-search
          - Supports sorting by acquired or published
          - Filter by geometry, date range, cloud cover
          - PSScene for ~3m ortho products

        Returns list of scene metadata dicts.
        """
        if not self.api_key:
            print("[PLANET] No API key configured")
            return []

        # Build Planet-style filter
        search_filter = {
            "type": "AndFilter",
            "config": [
                {
                    "type": "GeometryFilter",
                    "field_name": "geometry",
                    "config": {
                        "type": "Polygon",
                        "coordinates": [[
                            [bbox[0], bbox[1]],
                            [bbox[2], bbox[1]],
                            [bbox[2], bbox[3]],
                            [bbox[0], bbox[3]],
                            [bbox[0], bbox[1]]
                        ]]
                    }
                },
                {
                    "type": "DateRangeFilter",
                    "field_name": "acquired",
                    "config": {
                        "gte": f"{start_date}T00:00:00Z",
                        "lte": f"{end_date}T23:59:59Z"
                    }
                },
                {
                    "type": "RangeFilter",
                    "field_name": "cloud_cover",
                    "config": {
                        "lte": cloud_cover / 100.0
                    }
                },
                {
                    "type": "StringInFilter",
                    "field_name": "publishing_stage",
                    "config": ["standard", "finalized"]
                }
            ]
        }

        payload = {
            "item_types": ["PSScene"],
            "filter": search_filter,
        }

        try:
            resp = self.session.post(
                f"{PLANET_SEARCH_URL}?_sort=acquired%20desc&_page_size={max_items}",
                json=payload,
                timeout=30
            )

            if resp.status_code == 401:
                print("[PLANET] Authentication failed — check PL_API_KEY")
                return []

            resp.raise_for_status()
            data = resp.json()
            features = data.get('features', [])

            print(f"[PLANET] Found {len(features)} PlanetScope scenes")
            for f in features:
                props = f.get('properties', {})
                dt = props.get('acquired', '?')[:19]
                cc = props.get('cloud_cover', -1)
                gsd = props.get('gsd', -1)
                stage = props.get('publishing_stage', '?')
                print(f"  {dt} | Cloud:{cc*100:.0f}% | GSD:{gsd:.1f}m | {stage}")

            return features

        except requests.exceptions.HTTPError as e:
            print(f"[PLANET HTTP ERROR] {e}")
            return []
        except Exception as e:
            print(f"[PLANET ERROR] {e}")
            return []

    def search_city(self, city, start_date, end_date, **kwargs):
        """Search using a configured city AOI."""
        if city not in AOI_CONFIG:
            raise ValueError(f"Unknown city: {city}")
        bbox = AOI_CONFIG[city]['bbox']
        return self.search(bbox, start_date, end_date, **kwargs)

    def get_asset_url(self, item, asset_type='ortho_visual'):
        """
        Activate an asset and get its download URL.

        From research report:
          - Assets require activation before download
          - Once active, they contain a 'location' URL
          - Activation takes minutes
          - Downloading consumes quota

        Common asset types for PSScene:
          - ortho_visual: RGB visual (no auth needed after activation)
          - ortho_analytic_4b_sr: Surface reflectance 4-band (R,G,B,NIR)
          - ortho_analytic_4b: TOA reflectance 4-band
          - ortho_udm2: Usable Data Mask (cloud/shadow classification)
        """
        if not self.api_key:
            return None

        item_id = item.get('id', '')
        assets_url = item.get('_links', {}).get('assets', '')

        if not assets_url:
            assets_url = f"{PLANET_DATA_API}/item-types/PSScene/items/{item_id}/assets"

        try:
            resp = self.session.get(assets_url, timeout=15)
            resp.raise_for_status()
            assets = resp.json()

            # Try requested asset type, then fallbacks
            asset_types_priority = [
                asset_type,
                'ortho_visual',
                'ortho_analytic_4b_sr',
                'ortho_analytic_4b',
                'ortho_analytic_sr',
            ]

            asset = None
            for at in asset_types_priority:
                if at in assets:
                    asset = assets[at]
                    break

            if not asset:
                print(f"  [PLANET] No suitable asset in {item_id}. Available: {list(assets.keys())}")
                return None

            # Check if already active
            status = asset.get('status', '')
            if status == 'active':
                return asset.get('location', '')

            # Activate the asset
            activate_url = asset.get('_links', {}).get('activate', '')
            if activate_url:
                print(f"  [PLANET] Activating asset for {item_id}...")
                self.session.get(activate_url, timeout=15)

                # Poll for activation (up to 2 minutes)
                for attempt in range(24):
                    time.sleep(5)
                    resp2 = self.session.get(assets_url, timeout=15)
                    resp2.raise_for_status()
                    updated_assets = resp2.json()

                    for at in asset_types_priority:
                        if at in updated_assets:
                            if updated_assets[at].get('status') == 'active':
                                print(f"  [PLANET] Asset activated ({attempt*5}s)")
                                return updated_assets[at].get('location', '')

                print(f"  [PLANET] Asset activation timeout for {item_id}")
                return None

            return None

        except Exception as e:
            print(f"  [PLANET ASSET ERROR] {e}")
            return None

    def download_pair(self, bbox, label, start_date, end_date, cloud_cover=40):
        """
        Download before + after PlanetScope pair for change detection.
        Returns dict with paths and dates or None.
        """
        if not self.api_key:
            print("[PLANET] No API key — skipping PlanetScope")
            return None

        items = self.search(bbox, start_date, end_date, cloud_cover=cloud_cover)
        if len(items) < 2:
            print(f"[PLANET] Only {len(items)} scenes — need at least 2")
            return None

        before_item = items[-1]   # Oldest (list is sorted desc)
        after_item = items[0]     # Newest

        before_date = before_item['properties']['acquired'][:10]
        after_date = after_item['properties']['acquired'][:10]

        if before_date == after_date:
            # All scenes same date
            dates = {}
            for it in items:
                d = it['properties']['acquired'][:10]
                if d not in dates:
                    dates[d] = it
            if len(dates) < 2:
                print(f"[PLANET] All scenes from {before_date}, need different dates")
                return None
            sorted_dates = sorted(dates.keys())
            before_item = dates[sorted_dates[0]]
            after_item = dates[sorted_dates[-1]]
            before_date = sorted_dates[0]
            after_date = sorted_dates[-1]

        print(f"\n[PLANET] Downloading pair: {before_date} -> {after_date} (3m PlanetScope)")

        before_path = self._download_scene(before_item, bbox, label, 'before')
        after_path = self._download_scene(after_item, bbox, label, 'after')

        if not before_path or not after_path:
            return None

        return {
            'before_path': before_path,
            'after_path': after_path,
            'before_date': before_date,
            'after_date': after_date,
            'resolution': '3m',
            'source': 'PlanetScope',
            'before_item_id': before_item['id'],
            'after_item_id': after_item['id'],
        }

    def _download_scene(self, item, bbox, label, tag):
        """Download a single PlanetScope scene crop."""
        item_id = item.get('id', 'unknown')
        acquired = item['properties'].get('acquired', '')[:10]

        out_path = os.path.join(PLANET_FOLDER, f"PS_{acquired}_{label}_{tag}.tif")
        if os.path.exists(out_path):
            print(f"  [PLANET-CACHED] {out_path}")
            return out_path

        # Get download URL
        url = self.get_asset_url(item, 'ortho_visual')
        if not url:
            url = self.get_asset_url(item, 'ortho_analytic_4b_sr')
        if not url:
            print(f"  [PLANET-FAIL] Could not activate asset for {item_id}")
            return None

        # Download COG crop
        print(f"  [PLANET-DL] {tag} {acquired} — {item_id[:30]}...")
        success = self._download_cog_crop(url, bbox, out_path)
        if success:
            print(f"  [PLANET-OK] Saved: {out_path}")
            return out_path
        return None

    def _download_cog_crop(self, url, bbox, output_path):
        """Download windowed crop from PlanetScope COG."""
        if not HAS_RASTERIO:
            print("  [PLANET] rasterio not available")
            return False

        vsicurl_url = f"/vsicurl/{url}"

        with rasterio.Env(**GDAL_ENV):
            try:
                with rasterio.open(vsicurl_url) as src:
                    src_bbox = transform_bounds('EPSG:4326', src.crs, *bbox)
                    window = from_bounds(*src_bbox, transform=src.transform)

                    read_bands = list(range(1, min(src.count + 1, 4)))  # RGB
                    data = src.read(
                        read_bands,
                        window=window,
                        out_shape=(len(read_bands), OUTPUT_HEIGHT, OUTPUT_WIDTH),
                        resampling=rasterio.enums.Resampling.bilinear
                    )

                    out_transform = rasterio.transform.from_bounds(
                        *src_bbox, OUTPUT_WIDTH, OUTPUT_HEIGHT
                    )
                    profile = {
                        'driver': 'GTiff',
                        'dtype': data.dtype,
                        'width': OUTPUT_WIDTH,
                        'height': OUTPUT_HEIGHT,
                        'count': len(read_bands),
                        'crs': src.crs,
                        'transform': out_transform,
                        'compress': 'deflate',
                    }

                    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                    with rasterio.open(output_path, 'w', **profile) as dst:
                        dst.write(data)
                    return True

            except Exception as e:
                print(f"  [PLANET-COG ERROR] {e}")
                return False

    def check_availability(self, bbox, start_date, end_date, cloud_cover=50):
        """
        Check what PlanetScope scenes exist without downloading.
        Returns list of metadata dicts.
        """
        items = self.search(bbox, start_date, end_date, cloud_cover=cloud_cover)
        results = []
        for item in items:
            props = item.get('properties', {})
            results.append({
                'id': item.get('id', ''),
                'datetime': props.get('acquired', ''),
                'cloud_cover': round(props.get('cloud_cover', -1) * 100, 1),
                'gsd': round(props.get('gsd', -1), 2),
                'sun_elevation': props.get('sun_elevation', -1),
                'publishing_stage': props.get('publishing_stage', ''),
                'source': 'PlanetScope',
                'resolution': '~3m',
            })
        return results
