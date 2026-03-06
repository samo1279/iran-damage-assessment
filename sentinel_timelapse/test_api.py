#!/usr/bin/env python3
"""Quick API test"""
import urllib.request, json, sys

def test(endpoint, body):
    print(f"\n--- POST {endpoint} ---")
    try:
        req = urllib.request.Request(
            f'http://127.0.0.1:9000{endpoint}',
            data=json.dumps(body).encode(),
            headers={'Content-Type': 'application/json'}
        )
        resp = urllib.request.urlopen(req, timeout=30)
        data = json.loads(resp.read())
        return data
    except Exception as e:
        print(f"ERROR: {e}")
        return None

# Test 1: Data Availability
data = test('/api/data-availability', {
    'city': 'tehran',
    'start_date': '2026-02-01',
    'end_date': '2026-03-05'
})
if data:
    print(f"Success: {data.get('success')}")
    print(f"Total scenes: {data.get('total_scenes')}")
    print(f"Summary: {(data.get('summary',''))[:200]}")
    for k, v in data.get('sources', {}).items():
        print(f"  {k}: {v.get('count',0)} scenes ({v.get('provider','')})")
    for r in data.get('recommendations', []):
        print(f"  [{r.get('priority','')}] {r.get('message','')}")

# Test 2: Settings GET
print("\n--- GET /api/settings ---")
try:
    req = urllib.request.Request('http://127.0.0.1:9000/api/settings')
    resp = urllib.request.urlopen(req, timeout=10)
    data = json.loads(resp.read())
    print(f"Success: {data.get('success')}")
    for k, v in data.get('providers', {}).items():
        print(f"  {k}: configured={v.get('configured')}, free={v.get('free')}")
except Exception as e:
    print(f"ERROR: {e}")

print("\n✅ Tests complete")
