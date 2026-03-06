import requests, json

STAC_URL = 'https://earth-search.aws.element84.com/v1'
# Isfahan center coords: [51.6680, 32.6546]
search_params = {
    'collections': ['sentinel-2-l2a'],
    'bbox': [51.6, 32.6, 51.7, 32.7],
    'datetime': '2024-01-01/2024-02-01',
    'limit': 1
}

try:
    print("Searching for Sentinel-2 L2A in Isfahan sector...")
    response = requests.post(f'{STAC_URL}/search', json=search_params)
    data = response.json()
    if data['features']:
        feature = data['features'][0]
        print(f"### ID: {feature['id']}")
        
        # Determine the tile (MGRS)
        props = feature['properties']
        tile = f"{props.get('mgrs:utm_zone')}{props.get('mgrs:latitude_band')}{props.get('mgrs:grid_square')}"
        print(f"### MGRS TILE: {tile}")
        
        print("\n### ASSET KEYS AVAILABLE:")
        print(list(feature['assets'].keys()))
        
        print("\n### VISUAL ASSET (TCI) INFO:")
        print(json.dumps(feature['assets'].get('visual', {}), indent=2))
        
        print("\n### BAND 4 (RED) INFO:")
        print(json.dumps(feature['assets'].get('red', {}), indent=2))
        
        print("\n### BAND 8 (NIR) INFO:")
        print(json.dumps(feature['assets'].get('nir', {}), indent=2))
        
        # Test if the visual asset href is accessible directly via GET
        viz_href = feature['assets'].get('visual', {}).get('href')
        if viz_href:
            print(f"\n### TESTING ACCESS TO: {viz_href}")
            res_head = requests.head(viz_href)
            print(f"HTTP Status: {res_head.status_code}")
    else:
        print("No features found.")
except Exception as e:
    print(f"Error: {e}")
