#!/usr/bin/env python3
"""
Sub-AOI Time-Lapse Creator
Focus on specific regions within cities for detailed monitoring
"""

import subprocess
import sys
from pathlib import Path

# Sub-AOI definitions
SUBAOIS = {
    "isfahan_city_center": {
        "name": "Isfahan City Center",
        "bbox": [51.655, 32.665, 51.680, 32.680],
        "description": "Naqsh-e Jahan Square, Historic Bazaar"
    },
    "isfahan_south_industrial": {
        "name": "Isfahan South Industrial",
        "bbox": [51.630, 32.630, 51.670, 32.655],
        "description": "Manufacturing, Refineries, Factories"
    },
    "isfahan_zayanderud_river": {
        "name": "Isfahan Zayanderud River",
        "bbox": [51.640, 32.655, 51.695, 32.675],
        "description": "Water Body, Riparian Vegetation"
    },
    "tehran_city_center": {
        "name": "Tehran City Center",
        "bbox": [51.390, 35.675, 51.410, 35.690],
        "description": "Azadi Square, CBD Activity"
    },
    "tehran_south_industrial": {
        "name": "Tehran South Industrial",
        "bbox": [51.360, 35.650, 51.410, 35.670],
        "description": "Factories, Warehouses, Pollution"
    },
    "tehran_north_wealthy": {
        "name": "Tehran North Wealthy Districts",
        "bbox": [51.400, 35.700, 51.420, 35.715],
        "description": "Upscale Residential, Construction"
    },
}

def create_subaoi_timelapse(subaoi_key):
    """Create time-lapse for a specific sub-AOI"""
    
    if subaoi_key not in SUBAOIS:
        print(f"❌ Unknown sub-AOI: {subaoi_key}")
        print(f"Available: {list(SUBAOIS.keys())}")
        return False
    
    aoi = SUBAOIS[subaoi_key]
    
    print("\n" + "="*70)
    print(f"🎯 Creating Sub-AOI Time-Lapse: {aoi['name']}")
    print("="*70)
    print(f"Description: {aoi['description']}")
    print(f"Bbox: {aoi['bbox']}")
    print()
    
    # Read current config
    config_path = Path("config.py")
    config_content = config_path.read_text()
    
    # Save original
    config_backup = config_content
    
    # Update AOI_CONFIG in config
    old_aoi_config = """AOI_CONFIG = {
    "tehran": {
        "name": "Tehran 5km Box",
        "bbox": [51.362049329675, 35.666442220625, 51.417350670325, 35.711357779375],
    },
    "isfahan": {
        "name": "Isfahan 5km Box",
        "bbox": [51.643602920397, 32.642822220625, 51.696957079603, 32.687737779375],
    }
}"""
    
    new_aoi_config = f"""AOI_CONFIG = {{
    "{subaoi_key}": {{
        "name": "{aoi['name']}",
        "bbox": {aoi['bbox']},
    }}
}}"""
    
    config_content = config_content.replace(old_aoi_config, new_aoi_config)
    config_path.write_text(config_content)
    
    print("📝 Updated config.py with sub-AOI boundaries")
    print()
    
    # Run collection
    print("🔄 Collecting satellite data for sub-AOI...")
    result = subprocess.run(
        f"python3 collect_imagery.py {subaoi_key} 2>&1 | grep -E '(📡|✓|Found|Exported)'",
        shell=True
    )
    
    if result.returncode != 0:
        print("⚠️  Collection had issues")
    
    # Create GIF
    print("\n🎬 Creating GIF time-lapse...")
    result = subprocess.run(
        f"python3 create_gif_timelapse.py --aoi {subaoi_key} --fps 1",
        shell=True
    )
    
    # Restore config
    config_path.write_text(config_backup)
    print("\n✓ Restored original config.py")
    
    # Show results
    gif_files = list(Path("timelapse_output").glob(f"*{subaoi_key}*.gif"))
    if gif_files:
        print("\n" + "="*70)
        print(f"✅ Sub-AOI Time-Lapse Created!")
        print("="*70)
        for gif in gif_files:
            size_mb = gif.stat().st_size / (1024 * 1024)
            print(f"\n📁 {gif.name}")
            print(f"   Size: {size_mb:.2f} MB")
            print(f"   Location: {gif.absolute()}")
            print(f"\n   Open with: open {gif}")
    
    return True


def list_subaois():
    """Display all available sub-AOIs"""
    
    print("\n" + "="*70)
    print("📍 AVAILABLE SUB-AOIs")
    print("="*70)
    
    print("\n🏙️  ISFAHAN AREAS:")
    for key, aoi in SUBAOIS.items():
        if key.startswith("isfahan"):
            print(f"\n  {aoi['name']}")
            print(f"  ID: {key}")
            print(f"  Description: {aoi['description']}")
            print(f"  Command: python3 create_subaoi_timelapse.py {key}")
    
    print("\n\n🏙️  TEHRAN AREAS:")
    for key, aoi in SUBAOIS.items():
        if key.startswith("tehran"):
            print(f"\n  {aoi['name']}")
            print(f"  ID: {key}")
            print(f"  Description: {aoi['description']}")
            print(f"  Command: python3 create_subaoi_timelapse.py {key}")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\nUsage: python3 create_subaoi_timelapse.py [subaoi_id]")
        print("       python3 create_subaoi_timelapse.py --list")
        list_subaois()
        sys.exit(1)
    
    if sys.argv[1] == "--list":
        list_subaois()
    else:
        create_subaoi_timelapse(sys.argv[1])
