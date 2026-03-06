"""
Change Detection Engine
Implements multi-method change detection for satellite imagery.

Architecture (adapted from deep-research-report):
  1. Pixel differencing on normalized RGB bands
  2. NDVI differencing (Red + NIR bands)
  3. Combined change magnitude heatmap
  4. Connected-component blob vectorization
  5. Confidence scoring per detected change event
  6. SQLite persistence for change events

References:
  - Ulmas & Liiv (2020): U-Net for Sentinel-2 land cover segmentation
  - Research report: pixel diff + NDVI/NBR + optional U-Net/Siamese
"""

import os
import json
import uuid
import sqlite3
from pathlib import Path
from datetime import datetime

import numpy as np
from PIL import Image

try:
    import rasterio
except ImportError:
    rasterio = None

from src.core.config import AOI_CONFIG, OUTPUT_WIDTH, OUTPUT_HEIGHT, TIMELAPSE_OUTPUT


# ── Change Detection Configuration ──────────────────────────────────

# Pixel differencing threshold (0-1 normalized)
PIXEL_DIFF_THRESHOLD = 0.12

# NDVI difference threshold
NDVI_DIFF_THRESHOLD = 0.15

# Minimum blob area (pixels) to be considered a real change event
MIN_BLOB_PIXELS = 50

# Combined weight: how much NDVI contributes vs RGB diff
NDVI_WEIGHT = 0.4
RGB_WEIGHT = 0.6

# Cloud detection thresholds
CLOUD_BRIGHTNESS_THRESHOLD = 0.65  # Pixels brighter than this may be clouds
CLOUD_BLUE_RATIO_THRESHOLD = 0.25  # Blue/(R+G+B) ratio - clouds are whitish
CLOUD_WHITE_TOLERANCE = 0.15       # Max difference between RGB channels (clouds are gray/white)

# Database
DB_PATH = os.path.join(TIMELAPSE_OUTPUT, 'change_events.db')


# ── Database Layer (lightweight PostGIS alternative) ────────────────

def init_db():
    """Initialize SQLite database with change event schema."""
    Path(TIMELAPSE_OUTPUT).mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''CREATE TABLE IF NOT EXISTS change_event (
        event_id TEXT PRIMARY KEY,
        aoi_id TEXT NOT NULL,
        before_date TEXT NOT NULL,
        after_date TEXT NOT NULL,
        detected_at TEXT NOT NULL,
        bbox_json TEXT,
        centroid_lat REAL,
        centroid_lon REAL,
        area_pixels INTEGER,
        area_m2 REAL,
        confidence REAL,
        change_type TEXT,
        rgb_magnitude REAL,
        ndvi_magnitude REAL,
        heatmap_path TEXT,
        before_path TEXT,
        after_path TEXT,
        diff_path TEXT
    )''')
    conn.commit()
    conn.close()


def save_event(event):
    """Save a change event to the database."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''INSERT OR REPLACE INTO change_event
        (event_id, aoi_id, before_date, after_date, detected_at,
         bbox_json, centroid_lat, centroid_lon, area_pixels, area_m2,
         confidence, change_type, rgb_magnitude, ndvi_magnitude,
         heatmap_path, before_path, after_path, diff_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (event['event_id'], event['aoi_id'], event['before_date'],
         event['after_date'], event['detected_at'],
         json.dumps(event.get('bbox', [])),
         event.get('centroid_lat', 0), event.get('centroid_lon', 0),
         event.get('area_pixels', 0), event.get('area_m2', 0),
         event.get('confidence', 0), event.get('change_type', 'unknown'),
         event.get('rgb_magnitude', 0), event.get('ndvi_magnitude', 0),
         event.get('heatmap_path', ''), event.get('before_path', ''),
         event.get('after_path', ''), event.get('diff_path', '')))
    conn.commit()
    conn.close()


def get_events(aoi_id=None, limit=50):
    """Retrieve change events from database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    if aoi_id:
        rows = conn.execute(
            'SELECT * FROM change_event WHERE aoi_id = ? ORDER BY detected_at DESC LIMIT ?',
            (aoi_id, limit)).fetchall()
    else:
        rows = conn.execute(
            'SELECT * FROM change_event ORDER BY detected_at DESC LIMIT ?',
            (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Image Loading Helpers ───────────────────────────────────────────

def load_tif_as_array(path):
    """Load a GeoTIFF as float32 numpy array (C, H, W), normalized 0-1."""
    if rasterio is None:
        raise ImportError("rasterio required")
    with rasterio.open(path) as src:
        data = src.read().astype(np.float32)
        # Normalize based on data range
        if data.max() > 255:
            data = data / 10000.0  # Sentinel-2 reflectance
        elif data.max() > 1:
            data = data / 255.0
        return np.clip(data, 0, 1)


def load_single_band(path):
    """Load a single-band TIF as float32 (H, W), normalized 0-1."""
    if rasterio is None:
        raise ImportError("rasterio required")
    with rasterio.open(path) as src:
        data = src.read(1).astype(np.float32)
        if data.max() > 255:
            data = data / 10000.0
        elif data.max() > 1:
            data = data / 255.0
        return np.clip(data, 0, 1)


# ── Cloud Detection & Masking ──────────────────────────────────────

def detect_clouds_rgb(rgb_array):
    """
    Detect clouds in an RGB image using brightness and color uniformity.
    
    Clouds are characterized by:
    1. High brightness (white/light gray)
    2. Similar values across R, G, B channels (grayish/white)
    3. High blue channel relative to vegetation
    
    Input: (C, H, W) or (H, W, C) float32 RGB array normalized 0-1
    Output: (H, W) boolean mask where True = cloud pixel
    """
    # Handle both (C, H, W) and (H, W, C) formats
    if rgb_array.ndim == 3:
        if rgb_array.shape[0] in [3, 4]:  # (C, H, W)
            r, g, b = rgb_array[0], rgb_array[1], rgb_array[2]
        else:  # (H, W, C)
            r, g, b = rgb_array[:, :, 0], rgb_array[:, :, 1], rgb_array[:, :, 2]
    else:
        # Grayscale - can't detect clouds reliably
        return np.zeros(rgb_array.shape, dtype=bool)
    
    # Method 1: High brightness (mean of RGB)
    brightness = (r + g + b) / 3.0
    bright_mask = brightness > CLOUD_BRIGHTNESS_THRESHOLD
    
    # Method 2: Low color variance (clouds are grayish/white, not colorful)
    # Compute max difference between any two channels
    max_rgb = np.maximum(np.maximum(r, g), b)
    min_rgb = np.minimum(np.minimum(r, g), b)
    color_range = max_rgb - min_rgb
    gray_mask = color_range < CLOUD_WHITE_TOLERANCE
    
    # Method 3: High blue ratio (helps distinguish from sand/desert)
    # Clouds have relatively high blue compared to ground
    total = r + g + b + 0.001  # avoid division by zero
    blue_ratio = b / total
    # Clouds typically have blue_ratio > 0.3 (balanced RGB)
    # Vegetation/soil has lower blue ratio
    blue_mask = blue_ratio > CLOUD_BLUE_RATIO_THRESHOLD
    
    # Combine: bright AND (grayish OR high blue)
    cloud_mask = bright_mask & (gray_mask | blue_mask)
    
    # Morphological cleanup to remove isolated pixels and fill holes
    try:
        from scipy import ndimage
        # Dilate slightly to catch cloud edges
        cloud_mask = ndimage.binary_dilation(cloud_mask, iterations=2)
        # Remove small isolated "cloud" pixels (likely just bright objects)
        cloud_mask = ndimage.binary_opening(cloud_mask, iterations=1)
    except ImportError:
        pass  # Use mask as-is without morphological operations
    
    return cloud_mask


def detect_cloud_shadows(rgb_array, cloud_mask):
    """
    Detect cloud shadows (dark areas near clouds).
    Shadows appear as darker regions, often with slight blue tint.
    
    Input: (C, H, W) float32 RGB array, (H, W) cloud mask
    Output: (H, W) boolean shadow mask
    """
    if rgb_array.shape[0] in [3, 4]:
        r, g, b = rgb_array[0], rgb_array[1], rgb_array[2]
    else:
        r, g, b = rgb_array[:, :, 0], rgb_array[:, :, 1], rgb_array[:, :, 2]
    
    brightness = (r + g + b) / 3.0
    
    # Shadows are dark (brightness < 0.15) and slightly blue-shifted
    dark_mask = brightness < 0.15
    
    # Must be near clouds (within 50 pixels)
    try:
        from scipy import ndimage
        # Dilate cloud mask to find areas "near" clouds
        near_clouds = ndimage.binary_dilation(cloud_mask, iterations=50)
        shadow_mask = dark_mask & near_clouds & ~cloud_mask
    except ImportError:
        shadow_mask = dark_mask  # Less accurate without spatial relation
    
    return shadow_mask


def create_cloud_mask_combined(before_rgb, after_rgb):
    """
    Create a combined cloud mask from both before and after images.
    If EITHER image has clouds at a pixel, mask that pixel.
    
    This prevents:
    - Clouds appearing = false positive damage
    - Clouds disappearing = false positive recovery
    
    Input: Two (C, H, W) float32 RGB arrays
    Output: (H, W) boolean mask where True = should be excluded
    """
    before_clouds = detect_clouds_rgb(before_rgb)
    after_clouds = detect_clouds_rgb(after_rgb)
    
    # Also detect shadows
    before_shadows = detect_cloud_shadows(before_rgb, before_clouds)
    after_shadows = detect_cloud_shadows(after_rgb, after_clouds)
    
    # Combined mask: exclude any pixel with clouds/shadows in either image
    combined_mask = before_clouds | after_clouds | before_shadows | after_shadows
    
    return combined_mask


def get_cloud_coverage_percent(cloud_mask):
    """Calculate percentage of image covered by clouds."""
    total_pixels = cloud_mask.size
    cloud_pixels = cloud_mask.sum()
    return (cloud_pixels / total_pixels) * 100


# ── Change Detection Methods ───────────────────────────────────────

def compute_rgb_difference(before_rgb, after_rgb):
    """
    Compute per-pixel mean absolute difference across RGB bands.
    Input: (C, H, W) float32 arrays normalized 0-1
    Output: (H, W) float32 difference magnitude 0-1
    """
    diff = np.abs(after_rgb - before_rgb)
    magnitude = diff.mean(axis=0)  # Mean across channels
    return magnitude


def compute_ndvi(red_band, nir_band):
    """
    Compute NDVI = (NIR - Red) / (NIR + Red)
    Input: (H, W) float32 arrays
    Output: (H, W) float32 NDVI values in [-1, 1]
    """
    denominator = nir_band + red_band
    # Avoid division by zero
    ndvi = np.where(denominator > 0.001,
                    (nir_band - red_band) / denominator,
                    0.0)
    return ndvi.astype(np.float32)


def compute_ndvi_difference(ndvi_before, ndvi_after):
    """
    Compute absolute NDVI difference.
    Large negative ΔNDVI = vegetation loss (potential damage)
    Large positive ΔNDVI = vegetation growth
    """
    return ndvi_after - ndvi_before


def combine_change_signals(rgb_diff, ndvi_diff=None):
    """
    Combine RGB pixel differencing with NDVI differencing into
    a single change magnitude map.
    """
    if ndvi_diff is not None:
        # Use absolute NDVI diff
        abs_ndvi = np.abs(ndvi_diff)
        # Normalize to 0-1
        abs_ndvi = np.clip(abs_ndvi / 0.5, 0, 1)  # 0.5 NDVI diff = max
        combined = RGB_WEIGHT * rgb_diff + NDVI_WEIGHT * abs_ndvi
    else:
        combined = rgb_diff

    return np.clip(combined, 0, 1)


# ── Blob Vectorization ─────────────────────────────────────────────

def find_change_blobs(change_map, threshold=PIXEL_DIFF_THRESHOLD, min_pixels=MIN_BLOB_PIXELS):
    """
    Threshold the change magnitude map and find connected components.
    Returns list of blob dictionaries with bbox, area, centroid, mean magnitude.

    Uses scipy.ndimage for connected component labeling.
    """
    try:
        from scipy import ndimage
    except ImportError:
        # Fallback: simple grid-based approach without scipy
        return _find_blobs_simple(change_map, threshold, min_pixels)

    # Threshold
    binary = (change_map > threshold).astype(np.int32)

    # Label connected components
    labeled, num_features = ndimage.label(binary)

    blobs = []
    for i in range(1, num_features + 1):
        mask = labeled == i
        pixel_count = mask.sum()

        if pixel_count < min_pixels:
            continue

        # Bounding box (row_min, row_max, col_min, col_max)
        rows = np.any(mask, axis=1)
        cols = np.any(mask, axis=0)
        rmin, rmax = np.where(rows)[0][[0, -1]]
        cmin, cmax = np.where(cols)[0][[0, -1]]

        # Centroid
        cy, cx = ndimage.center_of_mass(mask)

        # Mean change magnitude within blob
        mean_mag = change_map[mask].mean()

        blobs.append({
            'bbox_pixels': [int(cmin), int(rmin), int(cmax), int(rmax)],
            'centroid_pixels': [float(cx), float(cy)],
            'area_pixels': int(pixel_count),
            'mean_magnitude': float(mean_mag),
        })

    # Sort by magnitude (most significant changes first)
    blobs.sort(key=lambda b: b['mean_magnitude'], reverse=True)
    return blobs


def _find_blobs_simple(change_map, threshold, min_pixels):
    """Simple grid-based blob detection without scipy."""
    binary = (change_map > threshold).astype(np.uint8)
    h, w = binary.shape

    # Divide into grid cells
    cell_size = 32
    blobs = []

    for gy in range(0, h, cell_size):
        for gx in range(0, w, cell_size):
            cell = binary[gy:gy + cell_size, gx:gx + cell_size]
            count = cell.sum()
            if count >= min(min_pixels, cell_size * cell_size // 4):
                mag = change_map[gy:gy + cell_size, gx:gx + cell_size]
                mean_mag = mag[cell > 0].mean() if cell.sum() > 0 else 0

                blobs.append({
                    'bbox_pixels': [gx, gy, min(gx + cell_size, w), min(gy + cell_size, h)],
                    'centroid_pixels': [float(gx + cell_size / 2), float(gy + cell_size / 2)],
                    'area_pixels': int(count),
                    'mean_magnitude': float(mean_mag),
                })

    blobs.sort(key=lambda b: b['mean_magnitude'], reverse=True)
    return blobs


# ── Pixel → Geo Coordinate Mapping ─────────────────────────────────

def pixel_to_geo(px, py, bbox, img_width=OUTPUT_WIDTH, img_height=OUTPUT_HEIGHT):
    """Convert pixel coordinates to geographic (lon, lat)."""
    lon_min, lat_min, lon_max, lat_max = bbox
    lon = lon_min + (px / img_width) * (lon_max - lon_min)
    lat = lat_max - (py / img_height) * (lat_max - lat_min)  # Y is flipped
    return lon, lat


def pixels_to_area_m2(pixel_count, bbox, img_width=OUTPUT_WIDTH, img_height=OUTPUT_HEIGHT):
    """Estimate area in m² from pixel count using bbox dimensions."""
    import math
    lon_min, lat_min, lon_max, lat_max = bbox
    # Approximate meters per degree at this latitude
    mid_lat = (lat_min + lat_max) / 2
    m_per_deg_lat = 111320  # roughly constant
    m_per_deg_lon = 111320 * math.cos(math.radians(mid_lat))

    width_m = (lon_max - lon_min) * m_per_deg_lon
    height_m = (lat_max - lat_min) * m_per_deg_lat

    pixel_area_m2 = (width_m / img_width) * (height_m / img_height)
    return pixel_count * pixel_area_m2


# ── Confidence Scoring ──────────────────────────────────────────────

def score_confidence(blob, rgb_magnitude, ndvi_magnitude=None, persistence=1):
    """
    Compute confidence score (0-1) per change event.
    Factors:
      - Change magnitude (stronger = more confident)
      - NDVI support (if NDVI also changed = more confident)
      - Persistence (observed in multiple passes = more confident)
    """
    # Base confidence from RGB magnitude
    mag_score = min(blob['mean_magnitude'] / 0.3, 1.0)  # 0.3 = very strong change

    # NDVI bonus
    ndvi_bonus = 0
    if ndvi_magnitude is not None and ndvi_magnitude > NDVI_DIFF_THRESHOLD:
        ndvi_bonus = min(ndvi_magnitude / 0.4, 1.0) * 0.2

    # Persistence bonus
    persist_bonus = min((persistence - 1) * 0.1, 0.2)

    # Area factor (larger blobs more reliable)
    area_factor = min(blob['area_pixels'] / 200, 1.0) * 0.1

    confidence = min(mag_score * 0.7 + ndvi_bonus + persist_bonus + area_factor, 1.0)
    return round(confidence, 3)


# ── Heatmap Generation ──────────────────────────────────────────────

def generate_heatmap(change_map, output_path):
    """
    Generate a color-coded change heatmap image.
    Blue = no change, Yellow = moderate, Red = severe
    Also generates a transparent overlay version.
    """
    h, w = change_map.shape

    # Create RGB heatmap
    heatmap = np.zeros((h, w, 4), dtype=np.uint8)

    # Threshold levels
    for y in range(h):
        for x in range(w):
            val = change_map[y, x]
            if val < 0.05:
                # Transparent (no change)
                heatmap[y, x] = [0, 0, 0, 0]
            elif val < 0.1:
                # Blue (minor)
                heatmap[y, x] = [0, 100, 255, 80]
            elif val < 0.2:
                # Yellow (moderate)
                heatmap[y, x] = [255, 255, 0, 140]
            elif val < 0.35:
                # Orange (significant)
                heatmap[y, x] = [255, 140, 0, 180]
            else:
                # Red (severe)
                heatmap[y, x] = [255, 0, 0, 220]

    img = Image.fromarray(heatmap, 'RGBA')
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output_path), 'PNG')
    return True


def generate_heatmap_fast(change_map, output_path):
    """Vectorized heatmap generation (much faster than per-pixel loop)."""
    h, w = change_map.shape
    heatmap = np.zeros((h, w, 4), dtype=np.uint8)

    # Vectorized thresholding
    mask_minor = (change_map >= 0.05) & (change_map < 0.1)
    mask_moderate = (change_map >= 0.1) & (change_map < 0.2)
    mask_significant = (change_map >= 0.2) & (change_map < 0.35)
    mask_severe = change_map >= 0.35

    heatmap[mask_minor] = [0, 100, 255, 80]
    heatmap[mask_moderate] = [255, 255, 0, 140]
    heatmap[mask_significant] = [255, 140, 0, 180]
    heatmap[mask_severe] = [255, 0, 0, 220]

    img = Image.fromarray(heatmap, 'RGBA')
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output_path), 'PNG')
    return True


def generate_cloud_mask_image(cloud_mask, output_path):
    """
    Generate a visualization of detected clouds/shadows.
    Blue = cloud, Purple = shadow-like, Transparent = clear
    """
    h, w = cloud_mask.shape
    img_data = np.zeros((h, w, 4), dtype=np.uint8)
    
    # Clouds shown in semi-transparent cyan/blue
    img_data[cloud_mask] = [0, 200, 255, 150]
    
    img = Image.fromarray(img_data, 'RGBA')
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output_path), 'PNG')
    return True


def generate_diff_image(before_rgb, after_rgb, output_path):
    """
    Generate a visual difference image using a hot colormap.
    Black = no change, Yellow = moderate, Bright Red/White = severe.
    Much more visible than raw enhanced diff.
    """
    diff = np.abs(after_rgb - before_rgb)
    magnitude = diff.mean(axis=0)  # (H, W)

    # Apply a hot-style colormap for maximum visibility
    h, w = magnitude.shape
    img_data = np.zeros((h, w, 3), dtype=np.uint8)

    # Normalize magnitude for coloring (stretch contrast)
    mag_max = max(magnitude.max(), 0.05)
    norm = np.clip(magnitude / mag_max, 0, 1)

    # Hot colormap: black -> red -> yellow -> white
    # R channel rises first
    img_data[:, :, 0] = np.clip(norm * 3.0, 0, 1) * 255
    # G channel rises second
    img_data[:, :, 1] = np.clip((norm - 0.33) * 3.0, 0, 1) * 255
    # B channel rises last
    img_data[:, :, 2] = np.clip((norm - 0.66) * 3.0, 0, 1) * 255

    img = Image.fromarray(img_data, 'RGB')
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output_path), 'PNG')
    return True


def generate_overlay_composite(after_rgb, change_map, output_path, alpha=0.55):
    """
    Overlay the color-coded heatmap ONTO the actual satellite image.
    This makes it visually obvious WHERE changes occurred on the real terrain.
    """
    h, w = change_map.shape
    c = after_rgb.shape[0]

    # Convert satellite image to RGB uint8 (H, W, C)
    sat = (np.clip(after_rgb[:3], 0, 1) * 255).astype(np.uint8)
    sat = np.transpose(sat, (1, 2, 0))  # (C,H,W) -> (H,W,C)
    if sat.shape[2] == 1:
        sat = np.repeat(sat, 3, axis=2)

    # Build RGBA heatmap overlay
    overlay = np.zeros((h, w, 4), dtype=np.uint8)
    mask_minor = (change_map >= 0.05) & (change_map < 0.1)
    mask_moderate = (change_map >= 0.1) & (change_map < 0.2)
    mask_significant = (change_map >= 0.2) & (change_map < 0.35)
    mask_severe = change_map >= 0.35

    overlay[mask_minor] = [0, 150, 255, 100]
    overlay[mask_moderate] = [255, 255, 0, 160]
    overlay[mask_significant] = [255, 140, 0, 200]
    overlay[mask_severe] = [255, 0, 0, 240]

    # Alpha-composite onto satellite
    result = sat.copy().astype(np.float32)
    oa = overlay[:, :, 3:4].astype(np.float32) / 255.0 * alpha
    oc = overlay[:, :, :3].astype(np.float32)
    result = result * (1 - oa) + oc * oa
    result = np.clip(result, 0, 255).astype(np.uint8)

    img = Image.fromarray(result, 'RGB')
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output_path), 'PNG')
    return True


def generate_annotated_image(after_rgb, blobs, bbox, output_path):
    """
    Draw red bounding boxes and numbered labels around each detected
    change blob on the actual satellite image.
    Makes it crystal clear where changes were detected.
    """
    from PIL import ImageDraw, ImageFont

    # Convert to PIL
    sat = (np.clip(after_rgb[:3], 0, 1) * 255).astype(np.uint8)
    sat = np.transpose(sat, (1, 2, 0))
    img = Image.fromarray(sat, 'RGB')
    draw = ImageDraw.Draw(img)

    # Try to get a font; fall back to default
    try:
        font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 14)
        font_sm = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 11)
    except Exception:
        font = ImageFont.load_default()
        font_sm = font

    for i, blob in enumerate(blobs):
        cmin, rmin, cmax, rmax = blob['bbox_pixels']
        mag = blob['mean_magnitude']

        # Color by severity
        if mag >= 0.35:
            color = (255, 0, 0)
        elif mag >= 0.2:
            color = (255, 140, 0)
        elif mag >= 0.1:
            color = (255, 255, 0)
        else:
            color = (0, 150, 255)

        # Draw rectangle (3px wide for visibility)
        for offset in range(3):
            draw.rectangle(
                [cmin - offset, rmin - offset, cmax + offset, rmax + offset],
                outline=color
            )

        # Label with event number and confidence
        label = f"#{i+1}"
        # Background for text
        tw = len(label) * 9
        draw.rectangle([cmin, rmin - 18, cmin + tw + 6, rmin - 2], fill=color)
        draw.text((cmin + 3, rmin - 17), label, fill=(0, 0, 0), font=font_sm)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output_path), 'PNG')
    return True


# ── Main Detection Pipeline ────────────────────────────────────────

class ChangeDetector:
    """
    Full change detection pipeline.

    Usage:
        detector = ChangeDetector()
        result = detector.detect(city, before_path, after_path)
    """

    def __init__(self):
        init_db()

    def detect(self, city, before_path, after_path,
               before_red_path=None, before_nir_path=None,
               after_red_path=None, after_nir_path=None,
               bbox=None):
        """
        Run change detection between two satellite images.

        Args:
            city: city key from AOI_CONFIG, or 'custom' for user-drawn areas
            before_path: path to before RGB TIF
            after_path: path to after RGB TIF
            before_red_path/before_nir_path: optional band files for NDVI
            after_red_path/after_nir_path: optional band files for NDVI
            bbox: optional [lon_min, lat_min, lon_max, lat_max] for custom areas

        Returns:
            dict with events, heatmap_path, stats
        """
        if bbox is not None:
            # Custom drawn area — use provided bbox directly
            pass
        elif city in AOI_CONFIG:
            bbox = AOI_CONFIG[city]['bbox']
        else:
            raise ValueError(f"Unknown city: {city}. Provide a bbox for custom areas.")
        before_date = self._extract_date(before_path)
        after_date = self._extract_date(after_path)

        print(f"\n[CHANGE-DETECT] {city.upper()}: {before_date} → {after_date}")

        # Load RGB images
        before_rgb = load_tif_as_array(before_path)
        after_rgb = load_tif_as_array(after_path)

        # Ensure same shape
        if before_rgb.shape != after_rgb.shape:
            # Resize to match
            min_c = min(before_rgb.shape[0], after_rgb.shape[0])
            min_h = min(before_rgb.shape[1], after_rgb.shape[1])
            min_w = min(before_rgb.shape[2], after_rgb.shape[2])
            before_rgb = before_rgb[:min_c, :min_h, :min_w]
            after_rgb = after_rgb[:min_c, :min_h, :min_w]

        # ─── NEW: Cloud Detection & Masking ─────────────────────────────
        print("  [1/5] Detecting clouds and shadows...")
        cloud_mask = create_cloud_mask_combined(before_rgb, after_rgb)
        cloud_coverage = get_cloud_coverage_percent(cloud_mask)
        print(f"    Cloud/shadow coverage: {cloud_coverage:.1f}%")
        
        if cloud_coverage > 70:
            print(f"  [WARN] High cloud coverage ({cloud_coverage:.0f}%) - results may be unreliable")

        # 2. RGB Pixel Differencing
        print("  [2/5] Computing RGB difference...")
        rgb_diff = compute_rgb_difference(before_rgb, after_rgb)
        
        # Apply cloud mask - set masked pixels to 0 (no change)
        rgb_diff_masked = rgb_diff.copy()
        rgb_diff_masked[cloud_mask] = 0

        # 3. NDVI Differencing (if bands available)
        ndvi_diff = None
        if (before_red_path and before_nir_path and
                after_red_path and after_nir_path and
                os.path.exists(before_red_path) and os.path.exists(before_nir_path) and
                os.path.exists(after_red_path) and os.path.exists(after_nir_path)):
            print("  [3/5] Computing NDVI difference...")
            try:
                before_red = load_single_band(before_red_path)
                before_nir = load_single_band(before_nir_path)
                after_red = load_single_band(after_red_path)
                after_nir = load_single_band(after_nir_path)

                ndvi_before = compute_ndvi(before_red, before_nir)
                ndvi_after = compute_ndvi(after_red, after_nir)
                ndvi_diff = compute_ndvi_difference(ndvi_before, ndvi_after)
                
                # Apply cloud mask to NDVI diff too
                ndvi_diff[cloud_mask] = 0
                
                print(f"    NDVI range: before [{ndvi_before.min():.2f}, {ndvi_before.max():.2f}]"
                      f" → after [{ndvi_after.min():.2f}, {ndvi_after.max():.2f}]")
            except Exception as e:
                print(f"  [NDVI-WARN] {e}")
                ndvi_diff = None
        else:
            print("  [3/5] NDVI skipped (band files not available)")

        # 4. Combine signals (using cloud-masked RGB diff)
        print("  [4/5] Combining change signals...")
        change_map = combine_change_signals(rgb_diff_masked, ndvi_diff)

        # 5. Find change blobs + generate all output images
        # (blob finding and image generation happen together below)

        # Generate output files
        output_prefix = f"change_{city}_{before_date}_to_{after_date}"
        heatmap_filename = f"{output_prefix}_heatmap.png"
        diff_filename = f"{output_prefix}_diff.png"
        overlay_filename = f"{output_prefix}_overlay.png"
        annotated_filename = f"{output_prefix}_annotated.png"
        cloud_mask_filename = f"{output_prefix}_cloudmask.png"
        heatmap_path = os.path.join(TIMELAPSE_OUTPUT, heatmap_filename)
        diff_path = os.path.join(TIMELAPSE_OUTPUT, diff_filename)
        overlay_path = os.path.join(TIMELAPSE_OUTPUT, overlay_filename)
        annotated_path = os.path.join(TIMELAPSE_OUTPUT, annotated_filename)
        cloud_mask_path = os.path.join(TIMELAPSE_OUTPUT, cloud_mask_filename)

        generate_heatmap_fast(change_map, heatmap_path)
        generate_diff_image(before_rgb, after_rgb, diff_path)
        generate_overlay_composite(after_rgb, change_map, overlay_path)
        
        # Generate cloud mask visualization
        generate_cloud_mask_image(cloud_mask, cloud_mask_path)

        # 5b. Find blobs first (need them for annotation)
        print("  [5/5] Vectorizing change regions...")
        blobs = find_change_blobs(change_map)
        generate_annotated_image(after_rgb, blobs, bbox, annotated_path)

        # Create events from blobs
        events = []
        for blob in blobs:
            # Convert pixel coords to geo coords
            cx, cy = blob['centroid_pixels']
            clon, clat = pixel_to_geo(cx, cy, bbox)

            # Compute bounding box in geo coords
            bx0, by0, bx1, by1 = blob['bbox_pixels']
            geo_min = pixel_to_geo(bx0, by1, bbox)
            geo_max = pixel_to_geo(bx1, by0, bbox)

            # Compute area
            area_m2 = pixels_to_area_m2(blob['area_pixels'], bbox)

            # Classify change type based on NDVI
            change_type = self._classify_change(blob, ndvi_diff, bbox)

            # Mean NDVI magnitude for this blob
            ndvi_mag = 0
            if ndvi_diff is not None:
                by0p, bx0p = blob['bbox_pixels'][1], blob['bbox_pixels'][0]
                by1p, bx1p = blob['bbox_pixels'][3], blob['bbox_pixels'][2]
                ndvi_region = np.abs(ndvi_diff[by0p:by1p, bx0p:bx1p])
                ndvi_mag = float(ndvi_region.mean()) if ndvi_region.size > 0 else 0

            # Confidence score
            confidence = score_confidence(blob, blob['mean_magnitude'], ndvi_mag)

            event = {
                'event_id': str(uuid.uuid4()),
                'aoi_id': city,
                'before_date': before_date,
                'after_date': after_date,
                'detected_at': datetime.utcnow().isoformat() + 'Z',
                'bbox': [geo_min[0], geo_min[1], geo_max[0], geo_max[1]],
                'centroid_lat': clat,
                'centroid_lon': clon,
                'area_pixels': blob['area_pixels'],
                'area_m2': round(area_m2, 1),
                'confidence': confidence,
                'change_type': change_type,
                'rgb_magnitude': round(blob['mean_magnitude'], 4),
                'ndvi_magnitude': round(ndvi_mag, 4),
                'heatmap_path': heatmap_filename,
                'before_path': os.path.basename(before_path),
                'after_path': os.path.basename(after_path),
                'diff_path': diff_filename,
            }

            # Save to DB
            save_event(event)
            events.append(event)

        # Summary stats
        total_change_pixels = sum(b['area_pixels'] for b in blobs)
        total_pixels = change_map.shape[0] * change_map.shape[1]
        change_percent = (total_change_pixels / total_pixels) * 100

        city_display = AOI_CONFIG[city]['name'] if city in AOI_CONFIG else 'Custom Area'

        result = {
            'success': True,
            'city': city_display,
            'before_date': before_date,
            'after_date': after_date,
            'events': events,
            'event_count': len(events),
            'heatmap': heatmap_filename,
            'diff_image': diff_filename,
            'overlay_image': overlay_filename,
            'annotated_image': annotated_filename,
            'cloud_mask_image': cloud_mask_filename,
            'stats': {
                'total_change_pixels': total_change_pixels,
                'total_pixels': total_pixels,
                'change_percent': round(change_percent, 2),
                'cloud_coverage_percent': round(cloud_coverage, 2),
                'cloud_masked': True,
                'mean_rgb_diff': round(float(rgb_diff.mean()), 4),
                'max_rgb_diff': round(float(rgb_diff.max()), 4),
                'has_ndvi': ndvi_diff is not None,
                'mean_ndvi_diff': round(float(np.abs(ndvi_diff).mean()), 4) if ndvi_diff is not None else None,
                'blobs_detected': len(blobs),
                'blobs_above_threshold': len(events),
            }
        }

        print(f"\n  [RESULT] {len(events)} change events detected")
        print(f"  [RESULT] {change_percent:.1f}% of area changed (clouds masked: {cloud_coverage:.1f}%)")
        print(f"  [RESULT] Heatmap: {heatmap_path}")

        return result

    def _extract_date(self, path):
        """Extract date from filename like S2_2024-01-15_xxx.tif"""
        basename = os.path.basename(path)
        parts = basename.split('_')
        if len(parts) >= 2:
            return parts[1]
        return 'unknown'

    def _classify_change(self, blob, ndvi_diff, bbox):
        """Classify the type of change based on available signals."""
        if ndvi_diff is None:
            mag = blob['mean_magnitude']
            if mag > 0.35:
                return 'severe-change'
            elif mag > 0.2:
                return 'significant-change'
            else:
                return 'moderate-change'

        # Use NDVI to classify
        by0, bx0 = blob['bbox_pixels'][1], blob['bbox_pixels'][0]
        by1, bx1 = blob['bbox_pixels'][3], blob['bbox_pixels'][2]
        ndvi_region = ndvi_diff[by0:by1, bx0:bx1]

        if ndvi_region.size == 0:
            return 'unknown'

        mean_ndvi_change = ndvi_region.mean()

        if mean_ndvi_change < -0.2:
            return 'vegetation-loss'  # Possible damage/destruction
        elif mean_ndvi_change > 0.2:
            return 'vegetation-growth'
        elif blob['mean_magnitude'] > 0.3:
            return 'structural-change'  # Non-vegetation change (buildings, roads)
        else:
            return 'surface-change'


def find_band_files(folder, date_str):
    """Find red and NIR band files for a given date in a folder."""
    import glob
    red_files = glob.glob(os.path.join(folder, f"S2_{date_str}_*_red.tif"))
    nir_files = glob.glob(os.path.join(folder, f"S2_{date_str}_*_nir.tif"))
    return (red_files[0] if red_files else None,
            nir_files[0] if nir_files else None)
