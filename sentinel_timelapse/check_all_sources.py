"""
Check MULTIPLE satellite data sources for the most recent Tehran imagery.
Checks: Element84 STAC, Copernicus ODATA, and Sentinel-1 SAR availability.
"""
import requests
import json
from datetime import datetime, timedelta

bbox = [51.362049, 35.666442, 51.417351, 35.711358]
TODAY = "2026-03-06"

print("=" * 70)
print("  MULTI-SOURCE SATELLITE AVAILABILITY CHECK — TEHRAN")
print(f"  Date: {TODAY}  |  War started: 2026-03-01")
print("=" * 70)

# ── 1. Element84 STAC (what we currently use) ──
print("\n[SOURCE 1] Element84 AWS STAC — Sentinel-2 L2A")
print("-" * 50)
try:
    resp = requests.post(
        "https://earth-search.aws.element84.com/v1/search",
        json={
            "collections": ["sentinel-2-l2a"],
            "bbox": bbox,
            "datetime": f"2026-02-20T00:00:00Z/{TODAY}T23:59:59Z",
            "limit": 10
        },
        timeout=15
    )
    data = resp.json()
    features = sorted(data.get("features", []),
                      key=lambda f: f["properties"].get("datetime", ""),
                      reverse=True)
    if features:
        for f in features[:5]:
            p = f["properties"]
            print(f"  {p.get('datetime','?')[:10]}  |  Cloud: {p.get('eo:cloud_cover',0):.1f}%")
        print(f"  >> Latest: {features[0]['properties']['datetime'][:10]}")
    else:
        print("  No images found in this range.")
except Exception as e:
    print(f"  ERROR: {e}")


# ── 2. Copernicus ODATA (ESA direct — usually fresher) ──
print("\n[SOURCE 2] Copernicus Data Space ODATA — Sentinel-2")
print("-" * 50)
try:
    # OData catalog search (free, no auth needed for searching)
    odata_url = (
        "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
        "?$filter=Collection/Name eq 'SENTINEL-2'"
        f" and OData.CSC.Intersects(area=geography'SRID=4326;POLYGON(("
        f"{bbox[0]} {bbox[1]},{bbox[2]} {bbox[1]},{bbox[2]} {bbox[3]},{bbox[0]} {bbox[3]},{bbox[0]} {bbox[1]}))')"
        f" and ContentDate/Start gt 2026-02-25T00:00:00.000Z"
        f" and ContentDate/Start lt {TODAY}T23:59:59.000Z"
        "&$orderby=ContentDate/Start desc"
        "&$top=10"
    )
    resp2 = requests.get(odata_url, timeout=20)
    if resp2.status_code == 200:
        items = resp2.json().get("value", [])
        if items:
            for item in items[:5]:
                name = item.get("Name", "?")
                date = item.get("ContentDate", {}).get("Start", "?")[:10]
                cc = item.get("CloudCover", "?")
                print(f"  {date}  |  Cloud: {cc}%  |  {name[:50]}")
            print(f"  >> Latest: {items[0].get('ContentDate',{}).get('Start','?')[:10]}")
        else:
            print("  No images found. Archive may not have post-Mar-1 data yet.")
    else:
        print(f"  HTTP {resp2.status_code}: {resp2.text[:200]}")
except Exception as e:
    print(f"  ERROR: {e}")


# ── 3. Sentinel-1 SAR (radar — works through clouds!) ──
print("\n[SOURCE 3] Element84 STAC — Sentinel-1 SAR (radar, cloud-proof)")
print("-" * 50)
try:
    resp3 = requests.post(
        "https://earth-search.aws.element84.com/v1/search",
        json={
            "collections": ["sentinel-1-grd"],
            "bbox": bbox,
            "datetime": f"2026-02-25T00:00:00Z/{TODAY}T23:59:59Z",
            "limit": 10
        },
        timeout=15
    )
    data3 = resp3.json()
    features3 = sorted(data3.get("features", []),
                       key=lambda f: f["properties"].get("datetime", ""),
                       reverse=True)
    if features3:
        for f in features3[:5]:
            p = f["properties"]
            print(f"  {p.get('datetime','?')[:10]}  |  Mode: {p.get('sar:instrument_mode','?')}")
        print(f"  >> Latest: {features3[0]['properties']['datetime'][:10]}")
    else:
        print("  No S1 data found in this range either.")
        # Try broader search
        resp3b = requests.post(
            "https://earth-search.aws.element84.com/v1/search",
            json={
                "collections": ["sentinel-1-grd"],
                "bbox": bbox,
                "datetime": f"2025-01-01T00:00:00Z/{TODAY}T23:59:59Z",
                "limit": 5
            },
            timeout=15
        )
        d3b = resp3b.json()
        f3b = d3b.get("features", [])
        if f3b:
            f3b.sort(key=lambda f: f["properties"].get("datetime", ""), reverse=True)
            print(f"  (Wider search found {len(f3b)} images, latest: {f3b[0]['properties']['datetime'][:10]})")
        else:
            print("  S1 collection may not be indexed on Element84.")
except Exception as e:
    print(f"  ERROR: {e}")


# ── 4. Check Copernicus for Sentinel-1 too ──
print("\n[SOURCE 4] Copernicus ODATA — Sentinel-1 SAR")
print("-" * 50)
try:
    s1_url = (
        "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
        "?$filter=Collection/Name eq 'SENTINEL-1'"
        f" and OData.CSC.Intersects(area=geography'SRID=4326;POLYGON(("
        f"{bbox[0]} {bbox[1]},{bbox[2]} {bbox[1]},{bbox[2]} {bbox[3]},{bbox[0]} {bbox[3]},{bbox[0]} {bbox[1]}))')"
        f" and ContentDate/Start gt 2026-02-28T00:00:00.000Z"
        f" and ContentDate/Start lt {TODAY}T23:59:59.000Z"
        "&$orderby=ContentDate/Start desc"
        "&$top=10"
    )
    resp4 = requests.get(s1_url, timeout=20)
    if resp4.status_code == 200:
        items4 = resp4.json().get("value", [])
        if items4:
            for item in items4[:5]:
                name = item.get("Name", "?")
                date = item.get("ContentDate", {}).get("Start", "?")[:10]
                print(f"  {date}  |  {name[:60]}")
            print(f"  >> Latest: {items4[0].get('ContentDate',{}).get('Start','?')[:10]}")
        else:
            print("  No S1 data found post-Feb-28.")
    else:
        print(f"  HTTP {resp4.status_code}")
except Exception as e:
    print(f"  ERROR: {e}")


print("\n" + "=" * 70)
print("BOTTOM LINE:")
print("  - Sentinel-2 archive lag is 1-3 days. Feb 25 is the latest optical.")
print("  - Next S2 pass over Tehran: ~Mar 2 or Mar 7 (5-day cycle from Feb 25)")
print("  - That image should appear in archive by Mar 4-5 or Mar 9-10.")
print("  - Sentinel-1 SAR can see through clouds and processes faster.")
print("  - For REAL near-real-time, need commercial providers (Planet, Maxar)")
print("    which offer images within hours, not days.")
print("=" * 70)
