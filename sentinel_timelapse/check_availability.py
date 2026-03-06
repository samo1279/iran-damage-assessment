"""Check what Sentinel-2 images are actually available for Tehran right now."""
import requests
import json

STAC_URL = "https://earth-search.aws.element84.com/v1/search"
bbox = [51.362049, 35.666442, 51.417351, 35.711358]

print("=" * 60)
print("CHECKING SENTINEL-2 AVAILABILITY FOR TEHRAN")
print("=" * 60)

# 1. Search Feb 15 - Mar 6, 2026
print("\n[1] Searching Feb 15 - Mar 6, 2026 (cloud < 80%)...")
payload = {
    "collections": ["sentinel-2-l2a"],
    "bbox": bbox,
    "datetime": "2026-02-15T00:00:00Z/2026-03-06T23:59:59Z",
    "limit": 30,
    "query": {"eo:cloud_cover": {"lt": 80}}
}

resp = requests.post(STAC_URL, json=payload, timeout=30)
print(f"  HTTP Status: {resp.status_code}")
data = resp.json()
features = data.get("features", [])
features.sort(key=lambda f: f["properties"].get("datetime", ""), reverse=True)

print(f"  Images found: {len(features)}")
for f in features:
    p = f["properties"]
    dt = p.get("datetime", "?")[:19]
    cc = p.get("eo:cloud_cover", -1)
    tile = p.get("s2:mgrs_tile", "?")
    print(f"    {dt}  |  Cloud: {cc:.1f}%  |  Tile: {tile}")

# 2. If nothing found, check what the LATEST available image is
if not features:
    print("\n[2] No images in that range. Checking latest available image...")
    payload2 = {
        "collections": ["sentinel-2-l2a"],
        "bbox": bbox,
        "datetime": "2024-01-01T00:00:00Z/2026-03-06T23:59:59Z",
        "limit": 10
    }
    resp2 = requests.post(STAC_URL, json=payload2, timeout=30)
    data2 = resp2.json()
    features2 = data2.get("features", [])
    features2.sort(key=lambda f: f["properties"].get("datetime", ""), reverse=True)
    
    print(f"  Total images (2024-2026): {len(features2)}")
    for f in features2[:10]:
        p = f["properties"]
        dt = p.get("datetime", "?")[:19]
        cc = p.get("eo:cloud_cover", -1)
        tile = p.get("s2:mgrs_tile", "?")
        print(f"    {dt}  |  Cloud: {cc:.1f}%  |  Tile: {tile}")

    if not features2:
        print("\n[3] Still nothing. Checking if the STAC catalog has ANY data...")
        payload3 = {
            "collections": ["sentinel-2-l2a"],
            "bbox": bbox,
            "limit": 5
        }
        resp3 = requests.post(STAC_URL, json=payload3, timeout=30)
        data3 = resp3.json()
        features3 = data3.get("features", [])
        print(f"  Any images at all: {len(features3)}")
        for f in features3:
            p = f["properties"]
            dt = p.get("datetime", "?")[:19]
            cc = p.get("eo:cloud_cover", -1)
            print(f"    {dt}  |  Cloud: {cc:.1f}%")
        if not features3:
            print("\n  RAW RESPONSE:")
            print(json.dumps(data3, indent=2)[:2000])

print("\n" + "=" * 60)
print("EXPLANATION:")
print("  Sentinel-2 has TWO satellites (2A + 2B) passing every 5 days combined.")
print("  But images take 24-48 hours to process and appear in the archive.")
print("  So the NEWEST possible image is typically from 1-2 days ago.")
print("  If the war started March 1, the first post-war image should be")
print("  around March 1-3 (if clear sky) or March 4-6 (next pass).")
print("=" * 60)
