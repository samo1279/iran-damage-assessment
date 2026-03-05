"""
Create GIF time-lapse from collected GeoTIFF imagery
Requires: rasterio, Pillow, opencv-python (pip install rasterio Pillow opencv-python)
"""

import os
import sys
from pathlib import Path
from PIL import Image
import numpy as np
import rasterio
from datetime import datetime

def create_gif_timelapse(archive_dir, output_file, aoi_name, fps=1):
    """
    Create animated GIF from GeoTIFF files
    
    Args:
        archive_dir: Directory containing .tif files
        output_file: Output GIF path
        aoi_name: AOI name (tehran or isfahan)
        fps: Frames per second (controls duration)
    """
    
    archive_path = Path(archive_dir) / aoi_name
    
    if not archive_path.exists():
        print(f"❌ Archive directory not found: {archive_path}")
        return False
    
    # Find all GeoTIFF files
    tif_files = sorted(archive_path.glob("*.tif"))
    
    if not tif_files:
        print(f"❌ No .tif files found in {archive_path}")
        return False
    
    print(f"\n🎬 Creating GIF: {aoi_name.upper()}")
    print(f"   Frames: {len(tif_files)}")
    print(f"   FPS: {fps}")
    
    frames = []
    
    # Process each GeoTIFF
    for i, tif_file in enumerate(tif_files, 1):
        try:
            with rasterio.open(tif_file) as src:
                # Read RGBA (4 bands)
                data = src.read([1, 2, 3, 4])  # B, G, R, A
                
                # Convert to uint8 (0-255)
                if data.dtype != np.uint8:
                    if data.max() <= 1.0:
                        data = (data * 255).astype(np.uint8)
                    else:
                        data = np.clip(data, 0, 255).astype(np.uint8)
                
                # Transpose to HWC format and convert RGB
                frame_rgb = np.transpose(data[:3], (1, 2, 0))  # Only RGB, no alpha
                
                # Convert to PIL Image
                img = Image.fromarray(frame_rgb, mode='RGB')
                frames.append(img)
                
                print(f"   [{i}/{len(tif_files)}] {tif_file.name}")
        
        except Exception as e:
            print(f"   ⚠️  Skipped {tif_file.name}: {e}")
            continue
    
    if not frames:
        print(f"❌ No valid frames to create GIF")
        return False
    
    # Create GIF
    duration = int(1000 / fps)  # Duration per frame in milliseconds
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    frames[0].save(
        output_file,
        save_all=True,
        append_images=frames[1:] if len(frames) > 1 else [],
        duration=duration,
        loop=0,
        optimize=False
    )
    
    file_size_kb = os.path.getsize(output_file) / 1024
    print(f"✓ GIF created: {output_file} ({file_size_kb:.1f} KB)")
    
    return True


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Create GIF time-lapse from GeoTIFF archive")
    parser.add_argument("--archive-dir", default="archive", help="Archive directory")
    parser.add_argument("--output-dir", default="timelapse_output", help="Output directory")
    parser.add_argument("--fps", type=int, default=1, help="Frames per second")
    parser.add_argument("--aoi", default="both", help="AOI name (tehran, isfahan, or both)")
    
    args = parser.parse_args()
    
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Get timestamp for naming
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    
    aois_to_process = []
    if args.aoi in ["both", "tehran"]:
        aois_to_process.append("tehran")
    if args.aoi in ["both", "isfahan"]:
        aois_to_process.append("isfahan")
    
    for aoi in aois_to_process:
        output_file = Path(args.output_dir) / f"S2L2A-{timestamp}-timelapse_{aoi}.gif"
        create_gif_timelapse(args.archive_dir, str(output_file), aoi, args.fps)
