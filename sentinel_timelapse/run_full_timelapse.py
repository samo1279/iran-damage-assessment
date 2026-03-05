#!/usr/bin/env python3
"""
Master Time-Lapse Generator
Collects real satellite data from CDSE for both Tehran and Isfahan
Creates animated GIFs in one run
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(cmd, description):
    """Run shell command and report results"""
    print(f"\n{'='*60}")
    print(f"🔄 {description}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, shell=True, cwd="/Users/sepehrmortazavi/Desktop/map_api/sentinel_timelapse")
    return result.returncode == 0

def main():
    print("\n" + "="*60)
    print("🛰️  SENTINEL-2 TIME-LAPSE GENERATOR (BOTH CITIES)")
    print("="*60)
    print("Real API calls → Download satellite data → Create GIFs")
    print()
    
    # Step 1: Collect Isfahan
    print("\n📍 STEP 1: Collecting Isfahan (6 frames expected)")
    if not run_command(
        "python3 collect_imagery.py isfahan 2>&1 | grep -E '(📡|✓|Exported|Found)'",
        "Fetching Isfahan satellite data from CDSE..."
    ):
        print("⚠️  Isfahan collection had issues, continuing...")
    
    # Step 2: Collect Tehran
    print("\n📍 STEP 2: Collecting Tehran (2 frames expected)")
    if not run_command(
        "python3 collect_imagery.py tehran 2>&1 | grep -E '(📡|✓|Exported|Found)'",
        "Fetching Tehran satellite data from CDSE..."
    ):
        print("⚠️  Tehran collection had issues, continuing...")
    
    # Step 3: Create GIFs
    print("\n📍 STEP 3: Creating animated GIFs")
    if not run_command(
        "pip install -q Pillow && python3 create_gif_timelapse.py --aoi both --fps 1",
        "Generating GIF time-lapses..."
    ):
        print("❌ GIF creation failed")
        return False
    
    # Step 4: Show results
    print("\n" + "="*60)
    print("✅ GENERATION COMPLETE!")
    print("="*60)
    
    output_dir = Path("/Users/sepehrmortazavi/Desktop/map_api/sentinel_timelapse/timelapse_output")
    if output_dir.exists():
        print("\n📁 Generated GIFs:")
        for gif in sorted(output_dir.glob("*.gif")):
            size_kb = gif.stat().st_size / 1024
            print(f"  ✓ {gif.name} ({size_kb:.1f} KB)")
            print(f"    → open {gif}")
    
    print("\n" + "="*60)
    print("🎬 VIEW YOUR TIME-LAPSES:")
    print("="*60)
    
    # Find the latest GIF files
    gifs = list(output_dir.glob("S2L2A-*-timelapse_*.gif"))
    if gifs:
        for gif in sorted(gifs):
            if "isfahan" in gif.name:
                print(f"\n📍 Isfahan (6 frames, {(gif.stat().st_size / 1024):.0f} KB):")
                print(f"   open {gif}")
            elif "tehran" in gif.name:
                print(f"\n📍 Tehran (2 frames, {(gif.stat().st_size / 1024):.0f} KB):")
                print(f"   open {gif}")
    
    print("\n" + "="*60)
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
