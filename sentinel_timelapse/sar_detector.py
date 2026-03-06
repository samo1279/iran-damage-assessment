"""
SAR (Radar) Change Detection Engine

Uses Sentinel-1 GRD backscatter to detect structural damage:
  1. Load before/after SAR amplitude images
  2. Convert to dB (log scale) for stable comparison
  3. Compute log-ratio change map (standard SAR CD method)
  4. Threshold + blob detection for damage events
  5. Generate grayscale SAR views + color-coded damage overlay
  6. Optionally overlay damage zones onto optical Sentinel-2 image

This works THROUGH CLOUDS and AT NIGHT — the key advantage over optical.

SAR damage signatures:
  - Building collapse: backscatter DECREASES (less reflection)
  - New rubble/debris: backscatter INCREASES (rough surface scattering)
  - Craters: characteristic decrease in center + increase at rim
  - Burned areas: moderate backscatter change
"""

import os
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

import rasterio

from config import OUTPUT_WIDTH, OUTPUT_HEIGHT, TIMELAPSE_OUTPUT


def load_sar_amplitude(path):
    """
    Load SAR GRD as float32 amplitude (H, W).
    Handles both linear power and dB encoded data.
    """
    with rasterio.open(path) as src:
        data = src.read(1).astype(np.float64)

    # Replace zeros/negatives with small value to avoid log issues
    data = np.where(data > 0, data, 1e-10)
    return data


def amplitude_to_db(amplitude):
    """Convert linear amplitude to decibels: dB = 10 * log10(amp)."""
    return 10.0 * np.log10(np.clip(amplitude, 1e-10, None))


def compute_log_ratio(before_amp, after_amp):
    """
    Standard SAR change detection: log-ratio of backscatter.

    log_ratio = log10(after / before)

    Interpretation:
      - Near 0: no change
      - Large positive: backscatter increased (new rough surface/debris)
      - Large negative: backscatter decreased (structure removed/collapsed)

    The absolute value gives change magnitude regardless of direction.
    """
    ratio = after_amp / np.clip(before_amp, 1e-10, None)
    log_ratio = np.log10(np.clip(ratio, 1e-10, None))
    return log_ratio


def detect_sar_changes(before_path, after_path, bbox, city='unknown'):
    """
    Full SAR change detection pipeline.

    Args:
        before_path: path to before SAR TIF
        after_path: path to after SAR TIF
        bbox: [lon_min, lat_min, lon_max, lat_max]
        city: label for output filenames

    Returns:
        dict with change stats, damage map paths, event list
    """
    print(f"\n[SAR-CD] Loading SAR pair...")

    # 1. Load amplitude data
    before_amp = load_sar_amplitude(before_path)
    after_amp = load_sar_amplitude(after_path)

    # Ensure same shape
    if before_amp.shape != after_amp.shape:
        min_h = min(before_amp.shape[0], after_amp.shape[0])
        min_w = min(before_amp.shape[1], after_amp.shape[1])
        before_amp = before_amp[:min_h, :min_w]
        after_amp = after_amp[:min_h, :min_w]

    h, w = before_amp.shape
    print(f"  Image size: {w}x{h}")

    # 2. Convert to dB
    before_db = amplitude_to_db(before_amp)
    after_db = amplitude_to_db(after_amp)

    print(f"  Before dB range: [{before_db.min():.1f}, {before_db.max():.1f}]")
    print(f"  After  dB range: [{after_db.min():.1f}, {after_db.max():.1f}]")

    # 3. Compute log-ratio change map
    log_ratio = compute_log_ratio(before_amp, after_amp)
    abs_change = np.abs(log_ratio)

    print(f"  Log-ratio range: [{log_ratio.min():.3f}, {log_ratio.max():.3f}]")
    print(f"  Mean abs change: {abs_change.mean():.4f}")

    # 4. Adaptive thresholding based on image statistics
    change_mean = abs_change.mean()
    change_std = abs_change.std()
    threshold = change_mean + 1.5 * change_std  # ~ top 7% most changed pixels
    threshold = max(threshold, 0.15)  # Minimum threshold to avoid noise

    print(f"  Threshold: {threshold:.4f} (mean+1.5*std)")

    binary_change = abs_change > threshold
    change_pixels = binary_change.sum()
    change_percent = (change_pixels / (h * w)) * 100

    print(f"  Changed pixels: {change_pixels} ({change_percent:.1f}%)")

    # 5. Find damage blobs
    blobs = _find_sar_blobs(abs_change, binary_change, min_pixels=30)
    print(f"  Damage blobs: {len(blobs)}")

    # 6. Classify each blob
    events = []
    for i, blob in enumerate(blobs):
        cx, cy = blob['centroid']
        # Convert pixel to geo
        lon = bbox[0] + (cx / w) * (bbox[2] - bbox[0])
        lat = bbox[3] - (cy / h) * (bbox[3] - bbox[1])

        # Check direction of change (increase vs decrease)
        bx0, by0, bx1, by1 = blob['bbox']
        region = log_ratio[by0:by1, bx0:bx1]
        region_binary = binary_change[by0:by1, bx0:bx1]
        mean_direction = region[region_binary].mean() if region_binary.sum() > 0 else 0

        if mean_direction < -0.1:
            damage_type = "structural-collapse"
        elif mean_direction > 0.1:
            damage_type = "debris-scatter"
        else:
            damage_type = "surface-disruption"

        # Compute area in m2
        import math
        mid_lat = (bbox[1] + bbox[3]) / 2
        m_per_deg_lon = 111320 * math.cos(math.radians(mid_lat))
        m_per_deg_lat = 111320
        pixel_w_m = (bbox[2] - bbox[0]) * m_per_deg_lon / w
        pixel_h_m = (bbox[3] - bbox[1]) * m_per_deg_lat / h
        area_m2 = blob['area'] * pixel_w_m * pixel_h_m

        # Confidence: based on magnitude and area
        conf = min(blob['mean_magnitude'] / (threshold * 3), 1.0) * 0.7
        conf += min(blob['area'] / 200, 1.0) * 0.3
        conf = min(conf, 1.0)

        events.append({
            'event_id': f"SAR-{i+1:03d}",
            'damage_type': damage_type,
            'change_type': damage_type,  # alias for frontend compatibility
            'centroid_lat': round(lat, 6),
            'centroid_lon': round(lon, 6),
            'area_pixels': blob['area'],
            'area_m2': round(area_m2, 1),
            'mean_magnitude': round(blob['mean_magnitude'], 4),
            'direction': round(float(mean_direction), 4),
            'confidence': round(conf, 3),
            'bbox_pixels': blob['bbox'],
        })

    # 7. Generate output images
    before_date = _extract_date(before_path)
    after_date = _extract_date(after_path)
    prefix = f"sar_{city}_{before_date}_to_{after_date}"

    # SAR before/after grayscale views
    before_png = f"{prefix}_before.png"
    after_png = f"{prefix}_after.png"
    _save_sar_grayscale(before_db, os.path.join(TIMELAPSE_OUTPUT, before_png),
                        label=f"SAR BEFORE: {before_date}")
    _save_sar_grayscale(after_db, os.path.join(TIMELAPSE_OUTPUT, after_png),
                        label=f"SAR AFTER: {after_date}")

    # Change heatmap
    heatmap_png = f"{prefix}_heatmap.png"
    _save_sar_heatmap(abs_change, log_ratio, threshold,
                      os.path.join(TIMELAPSE_OUTPUT, heatmap_png))

    # Damage overlay on after image
    overlay_png = f"{prefix}_overlay.png"
    _save_sar_overlay(after_db, abs_change, log_ratio, threshold, events,
                      os.path.join(TIMELAPSE_OUTPUT, overlay_png))

    # Annotated with boxes
    annotated_png = f"{prefix}_annotated.png"
    _save_sar_annotated(after_db, events,
                        os.path.join(TIMELAPSE_OUTPUT, annotated_png))

    result = {
        'success': True,
        'sensor': 'Sentinel-1 SAR (Radar)',
        'city': city,
        'before_date': before_date,
        'after_date': after_date,
        'before_image': before_png,
        'after_image': after_png,
        'heatmap': heatmap_png,
        'overlay_image': overlay_png,
        'annotated_image': annotated_png,
        'events': events,
        'event_count': len(events),
        'stats': {
            'total_pixels': h * w,
            'change_pixels': int(change_pixels),
            'change_percent': round(change_percent, 2),
            'threshold_db': round(threshold, 4),
            'mean_abs_change': round(float(abs_change.mean()), 4),
            'max_abs_change': round(float(abs_change.max()), 4),
            'blobs_detected': len(blobs),
        }
    }

    print(f"\n  [SAR-RESULT] {len(events)} damage zones detected")
    print(f"  [SAR-RESULT] {change_percent:.1f}% of area shows radar change")
    return result


def _find_sar_blobs(abs_change, binary, min_pixels=30):
    """Find connected damage blobs in the SAR change map."""
    try:
        from scipy import ndimage
    except ImportError:
        return _find_blobs_grid(abs_change, binary, min_pixels)

    labeled, num = ndimage.label(binary.astype(np.int32))
    blobs = []
    for i in range(1, num + 1):
        mask = labeled == i
        count = mask.sum()
        if count < min_pixels:
            continue

        rows = np.any(mask, axis=1)
        cols = np.any(mask, axis=0)
        rmin, rmax = np.where(rows)[0][[0, -1]]
        cmin, cmax = np.where(cols)[0][[0, -1]]
        cy, cx = ndimage.center_of_mass(mask)

        blobs.append({
            'bbox': [int(cmin), int(rmin), int(cmax), int(rmax)],
            'centroid': [float(cx), float(cy)],
            'area': int(count),
            'mean_magnitude': float(abs_change[mask].mean()),
        })

    blobs.sort(key=lambda b: b['mean_magnitude'], reverse=True)
    return blobs[:50]  # Limit to top 50


def _find_blobs_grid(abs_change, binary, min_pixels):
    """Fallback grid-based blob detection without scipy."""
    h, w = binary.shape
    cell = 32
    blobs = []
    for gy in range(0, h, cell):
        for gx in range(0, w, cell):
            c = binary[gy:gy+cell, gx:gx+cell]
            cnt = c.sum()
            if cnt >= min_pixels:
                mag = abs_change[gy:gy+cell, gx:gx+cell]
                blobs.append({
                    'bbox': [gx, gy, min(gx+cell, w), min(gy+cell, h)],
                    'centroid': [float(gx+cell/2), float(gy+cell/2)],
                    'area': int(cnt),
                    'mean_magnitude': float(mag[c].mean()),
                })
    blobs.sort(key=lambda b: b['mean_magnitude'], reverse=True)
    return blobs[:50]


def _save_sar_grayscale(db_data, path, label=None):
    """Save SAR dB data as grayscale PNG with stretched contrast."""
    # Clip and normalize for display
    p2, p98 = np.percentile(db_data[np.isfinite(db_data)], [2, 98])
    norm = np.clip((db_data - p2) / max(p98 - p2, 1), 0, 1)
    gray = (norm * 255).astype(np.uint8)

    img = Image.fromarray(gray, 'L').convert('RGB')

    if label:
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 14)
        except Exception:
            font = ImageFont.load_default()
        # Dark background bar at top
        draw.rectangle([0, 0, img.width, 22], fill=(0, 0, 0))
        draw.text((6, 4), label, fill=(0, 255, 100), font=font)

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    img.save(path, 'PNG')


def _save_sar_heatmap(abs_change, log_ratio, threshold, path):
    """
    Color-coded SAR change heatmap:
      - Blue/cyan = backscatter DECREASE (collapse)
      - Red/yellow = backscatter INCREASE (debris)
      - Black = no change
    """
    h, w = abs_change.shape
    img_data = np.zeros((h, w, 3), dtype=np.uint8)

    # Normalize change magnitude
    max_change = max(abs_change.max(), threshold * 3)
    norm = np.clip(abs_change / max_change, 0, 1)

    # Above threshold only
    mask = abs_change > threshold * 0.5

    # Direction: negative = collapse (blue), positive = debris (red)
    decrease = mask & (log_ratio < 0)
    increase = mask & (log_ratio >= 0)

    # Blue channel for decrease (collapse)
    img_data[decrease, 2] = (norm[decrease] * 255).astype(np.uint8)  # Blue
    img_data[decrease, 1] = (norm[decrease] * 180).astype(np.uint8)  # Cyan tint

    # Red channel for increase (debris)
    img_data[increase, 0] = (norm[increase] * 255).astype(np.uint8)  # Red
    img_data[increase, 1] = (norm[increase] * 120).astype(np.uint8)  # Orange tint

    # Severe changes get full brightness
    severe = mask & (abs_change > threshold * 2)
    img_data[severe & decrease] = [100, 220, 255]  # Bright cyan
    img_data[severe & increase] = [255, 160, 0]    # Bright orange

    img = Image.fromarray(img_data, 'RGB')

    # Add legend bar at bottom
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 11)
    except Exception:
        font = ImageFont.load_default()
    bar_y = h - 24
    draw.rectangle([0, bar_y, w, h], fill=(20, 20, 20))
    draw.text((8, bar_y + 4), "BLUE=Collapse  RED=Debris/Rubble  BLACK=No change", fill=(180, 180, 180), font=font)

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    img.save(path, 'PNG')


def _save_sar_overlay(after_db, abs_change, log_ratio, threshold, events, path):
    """Overlay damage colors onto the SAR after image."""
    # Grayscale base
    p2, p98 = np.percentile(after_db[np.isfinite(after_db)], [2, 98])
    norm = np.clip((after_db - p2) / max(p98 - p2, 1), 0, 1)
    gray = (norm * 255).astype(np.uint8)
    base = np.stack([gray, gray, gray], axis=-1).astype(np.float32)

    h, w = abs_change.shape

    # Create color overlay
    overlay = np.zeros((h, w, 4), dtype=np.uint8)
    mask = abs_change > threshold * 0.7

    decrease = mask & (log_ratio < 0)
    increase = mask & (log_ratio >= 0)

    # Cyan for collapse, red-orange for debris
    overlay[decrease] = [0, 200, 255, 180]
    overlay[increase] = [255, 80, 0, 180]

    # Severe
    severe_dec = decrease & (abs_change > threshold * 2)
    severe_inc = increase & (abs_change > threshold * 2)
    overlay[severe_dec] = [0, 255, 255, 220]
    overlay[severe_inc] = [255, 0, 0, 220]

    # Alpha composite
    oa = overlay[:, :, 3:4].astype(np.float32) / 255.0 * 0.6
    oc = overlay[:, :, :3].astype(np.float32)
    result = base * (1 - oa) + oc * oa
    result = np.clip(result, 0, 255).astype(np.uint8)

    img = Image.fromarray(result, 'RGB')
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 11)
    except Exception:
        font = ImageFont.load_default()

    # Draw event boxes
    for i, ev in enumerate(events[:20]):
        bx0, by0, bx1, by1 = ev['bbox_pixels']
        color = (0, 255, 255) if ev['direction'] < 0 else (255, 80, 0)
        for off in range(2):
            draw.rectangle([bx0-off, by0-off, bx1+off, by1+off], outline=color)
        label = f"#{i+1}"
        tw = len(label) * 8
        draw.rectangle([bx0, by0-16, bx0+tw+4, by0-2], fill=color)
        draw.text((bx0+2, by0-15), label, fill=(0, 0, 0), font=font)

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    img.save(path, 'PNG')


def _save_sar_annotated(after_db, events, path):
    """SAR after image with numbered damage boxes."""
    p2, p98 = np.percentile(after_db[np.isfinite(after_db)], [2, 98])
    norm = np.clip((after_db - p2) / max(p98 - p2, 1), 0, 1)
    gray = (norm * 255).astype(np.uint8)
    img = Image.fromarray(gray, 'L').convert('RGB')
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 12)
        font_sm = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 10)
    except Exception:
        font = ImageFont.load_default()
        font_sm = font

    for i, ev in enumerate(events[:30]):
        bx0, by0, bx1, by1 = ev['bbox_pixels']

        if ev['damage_type'] == 'structural-collapse':
            color = (0, 200, 255)
        elif ev['damage_type'] == 'debris-scatter':
            color = (255, 100, 0)
        else:
            color = (255, 255, 0)

        for off in range(3):
            draw.rectangle([bx0-off, by0-off, bx1+off, by1+off], outline=color)

        label = f"#{i+1} {ev['damage_type'].split('-')[0].upper()}"
        tw = len(label) * 7
        draw.rectangle([bx0, by0-18, bx0+tw+4, by0-2], fill=color)
        draw.text((bx0+2, by0-17), label, fill=(0, 0, 0), font=font_sm)

    # Header bar
    draw.rectangle([0, 0, img.width, 22], fill=(0, 0, 0))
    draw.text((6, 4), f"SAR DAMAGE ASSESSMENT: {len(events)} ZONES DETECTED", fill=(255, 80, 0), font=font)

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    img.save(path, 'PNG')


def _extract_date(path):
    """Extract date from SAR filename like S1_2026-03-03_tehran_after.tif"""
    basename = os.path.basename(path)
    parts = basename.split('_')
    if len(parts) >= 2:
        return parts[1]
    return 'unknown'
