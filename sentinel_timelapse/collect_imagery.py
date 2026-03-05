"""
Sentinel Hub Time-Lapse Collection
Download imagery from CDSE Sentinel Hub for date range and create time-lapse
"""

import os
import json
import base64
import requests
from datetime import datetime, timedelta
from pathlib import Path
import sys

from config import (
    CDSE_CLIENT_ID, CDSE_CLIENT_SECRET, CDSE_TOKEN_URL, CDSE_CATALOG_URL,
    CDSE_PROCESS_URL, AOI_CONFIG, START_DATE, END_DATE, MAX_CLOUD_COVERAGE,
    OUTPUT_WIDTH, OUTPUT_HEIGHT, MCP_THRESHOLD, ARCHIVE_DIR, VISUALIZATION
)

# ============================================================================
# EvalScripts for different visualizations
# ============================================================================

EVALSCRIPT_TRUE_COLOR = """//VERSION=3
var MCP = 40;

function setup() {
  return {
    input: ["B02", "B03", "B04", "SCL", "CLD", "dataMask"],
    output: { bands: 4 }
  };
}

function isCloud(sample) {
  var sclCloud = [3, 8, 9, 10].includes(sample.SCL);
  var probCloud = sample.CLD > MCP;
  return sclCloud || probCloud;
}

function evaluatePixel(sample) {
  if (sample.dataMask === 0) return [0, 0, 0, 0];
  if (isCloud(sample)) return [0, 0, 0, 0];
  return [2.5 * sample.B04, 2.5 * sample.B03, 2.5 * sample.B02, 1];
}
"""

EVALSCRIPT_SWIR = """//VERSION=3
var MCP = 40;

function setup() {
  return {
    input: ["B04", "B11", "B12", "SCL", "CLD", "dataMask"],
    output: { bands: 4 }
  };
}

function isCloud(sample) {
  return (sample.CLD > MCP) || [3, 8, 9, 10].includes(sample.SCL);
}

function evaluatePixel(sample) {
  if (sample.dataMask === 0) return [0, 0, 0, 0];
  if (isCloud(sample)) return [0, 0, 0, 0];
  return [2.5 * sample.B12, 2.5 * sample.B11, 2.5 * sample.B04, 1];
}
"""

# ============================================================================
# OAuth2 Token Management
# ============================================================================

class CDSEAuth:
    def __init__(self):
        self.token = None
        self.token_expiry = None
    
    def get_token(self):
        """Get or refresh OAuth2 token"""
        if self.token and self.token_expiry and datetime.utcnow() < self.token_expiry:
            print(f"✓ Using cached token (expires: {self.token_expiry})")
            return self.token
        
        print("🔐 Requesting new OAuth2 token...")
        
        payload = {
            "grant_type": "client_credentials",
            "client_id": CDSE_CLIENT_ID,
            "client_secret": CDSE_CLIENT_SECRET,
        }
        
        response = requests.post(CDSE_TOKEN_URL, data=payload)
        
        if response.status_code != 200:
            print(f"❌ Token request failed: {response.status_code}")
            print(response.text)
            sys.exit(1)
        
        data = response.json()
        self.token = data["access_token"]
        
        # Token typically expires in ~3600 seconds (1 hour)
        self.token_expiry = datetime.utcnow() + timedelta(seconds=data.get("expires_in", 3600) - 60)
        
        print(f"✓ Token acquired (expires: {self.token_expiry})")
        return self.token


# ============================================================================
# Catalog Search
# ============================================================================

def catalog_search(auth, bbox, from_date, to_date, aoi_name):
    """Search Catalog/STAC for available scenes"""
    
    print(f"\n📡 Searching for scenes ({aoi_name}): {from_date[:10]} to {to_date[:10]}")
    
    headers = {
        "Authorization": f"Bearer {auth.get_token()}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "bbox": bbox,
        "datetime": f"{from_date}/{to_date}",
        "collections": ["sentinel-2-l2a"],
        "limit": 100,
        "filter": f"eo:cloud_cover <= {MAX_CLOUD_COVERAGE}",
        "filter-lang": "cql2-text"
    }
    
    response = requests.post(CDSE_CATALOG_URL, json=payload, headers=headers)
    
    if response.status_code != 200:
        print(f"⚠️  Catalog search returned {response.status_code}")
        print(response.text[:500])
        return []
    
    data = response.json()
    features = data.get("features", [])
    
    print(f"✓ Found {len(features)} scenes with cloud cover ≤ {MAX_CLOUD_COVERAGE}%")
    
    # Extract sensing dates
    scenes = []
    for feature in features:
        properties = feature.get("properties", {})
        sensing_date = properties.get("datetime", "unknown")
        cloud_cover = properties.get("eo:cloud_cover", "N/A")
        
        scenes.append({
            "id": feature.get("id"),
            "sensing_date": sensing_date,
            "cloud_cover": cloud_cover,
            "feature": feature
        })
    
    # Sort by date
    scenes.sort(key=lambda x: x["sensing_date"])
    
    for scene in scenes:
        print(f"  • {scene['sensing_date'][:10]} | Cloud: {scene['cloud_cover']}%")
    
    return scenes


# ============================================================================
# Process API Export
# ============================================================================

def export_geotiff(auth, bbox, from_date, to_date, output_path, aoi_name):
    """Export imagery using Process API"""
    
    print(f"\n📤 Exporting GeoTIFF for {aoi_name}...")
    
    # Choose evalscript
    evalscript = EVALSCRIPT_SWIR if VISUALIZATION == "swir" else EVALSCRIPT_TRUE_COLOR
    
    headers = {
        "Authorization": f"Bearer {auth.get_token()}",
        "Content-Type": "application/json",
        "Accept": "image/tiff",
    }
    
    payload = {
        "input": {
            "bounds": {
                "properties": {"crs": "http://www.opengis.net/def/crs/OGC/1.3/CRS84"},
                "bbox": bbox,
            },
            "data": [
                {
                    "type": "sentinel-2-l2a",
                    "dataFilter": {
                        "timeRange": {
                            "from": from_date,
                            "to": to_date,
                        },
                        "maxCloudCoverage": MAX_CLOUD_COVERAGE,
                        "mosaickingOrder": "mostRecent"
                    }
                }
            ]
        },
        "output": {
            "width": OUTPUT_WIDTH,
            "height": OUTPUT_HEIGHT,
        },
        "evalscript": evalscript,
    }
    
    response = requests.post(CDSE_PROCESS_URL, json=payload, headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Process API failed: {response.status_code}")
        print(response.text[:500])
        return False
    
    # Write GeoTIFF
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(response.content)
    
    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"✓ Exported: {output_path} ({file_size_mb:.1f} MB)")
    
    return True


# ============================================================================
# Main Collection Loop
# ============================================================================

def collect_timelapse(aoi_choice="tehran"):
    """Main function to collect imagery for time-lapse"""
    
    if aoi_choice not in AOI_CONFIG:
        print(f"❌ Unknown AOI: {aoi_choice}")
        print(f"Available: {list(AOI_CONFIG.keys())}")
        sys.exit(1)
    
    aoi = AOI_CONFIG[aoi_choice]
    print(f"🎯 Target AOI: {aoi['name']}")
    print(f"📅 Period: {START_DATE[:10]} to {END_DATE[:10]}")
    
    # Verify credentials
    if CDSE_CLIENT_ID == "YOUR_CLIENT_ID":
        print("❌ ERROR: Update CDSE_CLIENT_ID and CDSE_CLIENT_SECRET in config.py")
        print("   Get credentials at: https://dataspace.copernicus.eu")
        sys.exit(1)
    
    # Initialize auth
    auth = CDSEAuth()
    
    # Search for scenes
    scenes = catalog_search(auth, aoi["bbox"], START_DATE, END_DATE, aoi["name"])
    
    if not scenes:
        print("\n⚠️  No scenes found. Possible reasons:")
        print("  • Cloud cover threshold too strict (try MAX_CLOUD_COVERAGE = 50)")
        print("  • Check CDSE status: https://dataspace.copernicus.eu")
        print("  • Try broader date range or different AOI")
        return
    
    # Create daily exports (one per day if available)
    archive_path = Path(ARCHIVE_DIR) / aoi_choice
    archive_path.mkdir(parents=True, exist_ok=True)
    
    exported_count = 0
    
    # Group scenes by day
    from collections import defaultdict
    by_date = defaultdict(list)
    for scene in scenes:
        day = scene["sensing_date"][:10]
        by_date[day].append(scene)
    
    print(f"\n📦 Exporting by date ({len(by_date)} unique days)...")
    
    for day in sorted(by_date.keys()):
        day_scenes = by_date[day]
        best_scene = min(day_scenes, key=lambda x: x["cloud_cover"])
        
        # Export one GeoTIFF per day (most recent/clearest)
        output_file = archive_path / f"{day}_sentinel2_l2a.tif"
        
        # Extract date part and construct proper ISO 8601 range
        sensing_day = best_scene["sensing_date"][:10]
        from_date_str = f"{sensing_day}T00:00:00Z"
        to_date_str = f"{sensing_day}T23:59:59Z"
        
        if export_geotiff(auth, aoi["bbox"], 
                          from_date_str,
                          to_date_str,
                          str(output_file), aoi["name"]):
            exported_count += 1
    
    print(f"\n✓ Exported {exported_count} GeoTIFF files")
    print(f"   Location: {archive_path.absolute()}")
    
    return archive_path


if __name__ == "__main__":
    aoi = sys.argv[1] if len(sys.argv) > 1 else "tehran"
    collect_timelapse(aoi)
