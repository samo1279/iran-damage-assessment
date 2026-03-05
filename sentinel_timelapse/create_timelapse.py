"""
Create time-lapse video from collected GeoTIFF imagery
Requires: rasterio, opencv-python (pip install rasterio opencv-python)
"""

import os
import sys
from pathlib import Path
import cv2
import numpy as np
from rasterio.io import MemoryFile
import rasterio

def create_timelapse(archive_dir, output_file, fps=2, aoi_name="tehran"):
    """
    Create time-lapse MP4 from GeoTIFF files
    
    Args:
        archive_dir: Directory containing .tif files
        output_file: Output MP4 path
        fps: Frames per second (default 2)
        aoi_name: AOI name for organizing archive
    """
    
    archive_path = Path(archive_dir) / aoi_name
    
    if not archive_path.exists():
        print(f"❌ Archive directory not found: {archive_path}")
        sys.exit(1)
    
    # Find all GeoTIFF files
    tif_files = sorted(archive_path.glob("*.tif"))
    
    if not tif_files:
        print(f"❌ No .tif files found in {archive_path}")
        sys.exit(1)
    
    print(f"🎬 Creating time-lapse from {len(tif_files)} frames")
    print(f"   FPS: {fps}")
    
    # Read first image to get dimensions
    with rasterio.open(tif_files[0]) as src:
        height, width = src.height, src.width
        print(f"   Resolution: {width} × {height}")
    
    # Initialize video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_file, fourcc, fps, (width, height))
    
    # Process each GeoTIFF
    for i, tif_file in enumerate(tif_files, 1):
        try:
            with rasterio.open(tif_file) as src:
                # Read RGBA (4 bands)
                data = src.read([1, 2, 3, 4])  # B, G, R, A
                
                # Convert to uint8 (0-255)
                if data.dtype != np.uint8:
                    # If float, scale to 0-255
                    if data.max() <= 1.0:
                        data = (data * 255).astype(np.uint8)
                    else:
                        # Clip and normalize
                        data = np.clip(data, 0, 255).astype(np.uint8)
                
                # Rearrange to BGR for OpenCV
                frame = cv2.cvtColor(np.transpose(data, (1, 2, 0)), cv2.COLOR_RGBA2BGR)
                
                out.write(frame)
                
                print(f"   [{i}/{len(tif_files)}] {tif_file.name}")
        
        except Exception as e:
            print(f"   ⚠️  Skipped {tif_file.name}: {e}")
            continue
    
    out.release()
    
    file_size_mb = os.path.getsize(output_file) / (1024 * 1024)
    print(f"\n✓ Time-lapse created: {output_file} ({file_size_mb:.1f} MB)")
    print(f"   Play with: open {output_file}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Create time-lapse from GeoTIFF archive")
    parser.add_argument("--archive-dir", default="archive", help="Archive directory")
    parser.add_argument("--output", default="timelapse_output/timelapse.mp4", help="Output MP4 file")
    parser.add_argument("--fps", type=int, default=2, help="Frames per second")
    parser.add_argument("--aoi", default="tehran", help="AOI name (tehran or isfahan)")
    
    args = parser.parse_args()
    
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    create_timelapse(args.archive_dir, args.output, args.fps, args.aoi)
