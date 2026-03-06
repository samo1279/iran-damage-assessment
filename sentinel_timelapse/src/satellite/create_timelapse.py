"""
Timelapse Creator
Loads satellite TIF crops, creates animated GIF with date captions,
and saves individual before/after frames.
"""

import os
import glob
from pathlib import Path
from datetime import datetime

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from src.core.config import OUTPUT_WIDTH, OUTPUT_HEIGHT, GIF_FRAME_DURATION, GIF_LOOP


class TimelapseCreator:
    """Load satellite image crops and produce GIF timelapses."""

    def __init__(self):
        self.images = []   # list of PIL.Image
        self.dates = []    # list of date strings
        self.paths = []    # list of file paths

    def load_images(self, folder, start_date=None, end_date=None):
        """
        Load all TIF files from folder, sorted by date.
        Filters to only visual (RGB) files (excludes _red.tif, _nir.tif band files).
        Returns count of successfully loaded images.
        """
        self.images = []
        self.dates = []
        self.paths = []

        pattern = os.path.join(folder, "S2_*.tif")
        files = sorted(glob.glob(pattern))

        # Exclude band files (e.g., _red.tif, _nir.tif)
        files = [f for f in files if not any(
            f.endswith(f"_{b}.tif") for b in ['red', 'nir', 'blue', 'green', 'swir']
        )]

        for fpath in files:
            try:
                # Extract date from filename: S2_YYYY-MM-DD_...
                basename = os.path.basename(fpath)
                parts = basename.split('_')
                if len(parts) >= 2:
                    date_str = parts[1]  # YYYY-MM-DD
                else:
                    continue

                # Filter by date range if specified
                if start_date and date_str < start_date:
                    continue
                if end_date and date_str > end_date:
                    continue

                # Load TIF as PIL Image
                img = self._load_tif_as_pil(fpath)
                if img is not None:
                    self.images.append(img)
                    self.dates.append(date_str)
                    self.paths.append(fpath)

            except Exception as e:
                print(f"  [LOAD-WARN] {fpath}: {e}")
                continue

        print(f"[TIMELAPSE] Loaded {len(self.images)} images from {folder}")
        return len(self.images)

    def _load_tif_as_pil(self, tif_path):
        """Load a GeoTIFF as a PIL RGB Image."""
        try:
            import rasterio
            with rasterio.open(tif_path) as src:
                # Read bands
                if src.count >= 3:
                    data = src.read([1, 2, 3])  # RGB
                elif src.count == 1:
                    band = src.read(1)
                    data = np.stack([band, band, band])
                else:
                    data = src.read()
                    while data.shape[0] < 3:
                        data = np.vstack([data, data[-1:]])
                    data = data[:3]

                # Normalize to uint8 if needed
                if data.dtype != np.uint8:
                    # Handle typical Sentinel-2 reflectance values (0-10000)
                    if data.max() > 255:
                        data = np.clip(data / 10000.0 * 255, 0, 255).astype(np.uint8)
                    else:
                        data = data.astype(np.uint8)

                # Transpose from (C, H, W) to (H, W, C)
                rgb = np.transpose(data, (1, 2, 0))
                return Image.fromarray(rgb, 'RGB')

        except Exception as e:
            print(f"  [TIF-LOAD ERROR] {tif_path}: {e}")
            return None

    def create_gif(self, output_path, add_captions=True):
        """Create animated GIF from loaded images."""
        if not self.images:
            print("[GIF] No images to create GIF from")
            return False

        try:
            frames = []
            for i, (img, date) in enumerate(zip(self.images, self.dates)):
                frame = img.copy()
                if add_captions:
                    frame = self._add_caption(frame, date, frame_num=i + 1)
                frames.append(frame)

            # Save GIF
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            frames[0].save(
                output_path,
                save_all=True,
                append_images=frames[1:],
                duration=GIF_FRAME_DURATION,
                loop=GIF_LOOP,
                optimize=True
            )

            size_kb = os.path.getsize(output_path) / 1024
            print(f"[GIF] Created: {output_path} ({size_kb:.0f} KB, {len(frames)} frames)")
            return True

        except Exception as e:
            print(f"[GIF ERROR] {e}")
            return False

    def save_frame(self, img, output_path, caption=None):
        """Save a single frame as PNG with optional caption."""
        try:
            frame = img.copy()
            if caption:
                frame = self._add_caption(frame, caption)
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            frame.save(str(output_path), 'PNG')
            return True
        except Exception as e:
            print(f"[FRAME ERROR] {e}")
            return False

    def _add_caption(self, img, text, frame_num=None):
        """Add date/text caption overlay to image."""
        draw = ImageDraw.Draw(img)
        w, h = img.size

        # Build caption text
        if frame_num is not None:
            caption = f"{text}  [{frame_num}/{len(self.images)}]"
        else:
            caption = text

        # Use default font (no external font file needed)
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", 14)
        except Exception:
            font = ImageFont.load_default()

        # Measure text
        bbox_text = draw.textbbox((0, 0), caption, font=font)
        tw = bbox_text[2] - bbox_text[0]
        th = bbox_text[3] - bbox_text[1]

        # Draw background rectangle
        padding = 6
        x = 10
        y = h - th - padding * 2 - 10
        draw.rectangle(
            [x, y, x + tw + padding * 2, y + th + padding * 2],
            fill=(0, 0, 0, 180)
        )

        # Draw text
        draw.text((x + padding, y + padding), caption, fill=(0, 255, 0), font=font)

        return img
