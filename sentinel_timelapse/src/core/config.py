"""
Sentinel-2 Timelapse Configuration
Based on Copernicus Data Space Ecosystem (CDSE) requirements
and deep-research-report recommendations for multi-source architecture.
"""

import os

# ── Provider API Keys (read from environment) ──────────────────────

# Planet Labs (PlanetScope ~3m) — commercial, daily revisit
# Get key: https://www.planet.com/account/ → API Key
PL_API_KEY = os.environ.get('PL_API_KEY', '').strip()

# Copernicus Data Space Ecosystem (CDSE) — free Sentinel Hub access
# Register: https://dataspace.copernicus.eu → OAuth2 credentials
CDSE_CLIENT_ID = os.environ.get('CDSE_CLIENT_ID', '').strip() or None
CDSE_CLIENT_SECRET = os.environ.get('CDSE_CLIENT_SECRET', '').strip() or None

# AOI Configuration from research document (exact CRS84 bboxes)
# Format: [lon_min, lat_min, lon_max, lat_max]
AOI_CONFIG = {
    'tehran': {
        'name': 'Tehran',
        'bbox': [51.362049329675, 35.666442220625, 51.417350670325, 35.711357779375],
        'folder': 'archive/tehran',
        'city_center': (35.6889, 51.3897)
    },
    'isfahan': {
        'name': 'Isfahan',
        'bbox': [51.643602920397, 32.642822220625, 51.696957079603, 32.687737779375],
        'folder': 'archive/isfahan',
        'city_center': (32.66528, 51.67028)
    },
    'isfahan_center': {
        'name': 'Isfahan City Center',
        'bbox': [51.643602920397, 32.642822220625, 51.696957079603, 32.687737779375],
        'folder': 'archive/isfahan_center',
        'city_center': (32.66528, 51.67028)
    }
}

# Sentinel-2 L2A Configuration
SENTINEL_COLLECTION = 'sentinel-2-l2a'

# Cloud Filtering Configuration (MCP - Mosaicking Cloud Probability)
# Options: 20, 40, 60 (percent)
# 20: only very clear pixels (more gaps)
# 40: balanced (recommended)
# 60: highest retention but tolerates thin clouds
MCP_CLOUD_THRESHOLD = 40  # Cloud cover percentage threshold

# Image Processing
OUTPUT_WIDTH = 512
OUTPUT_HEIGHT = 512
GIF_FRAME_DURATION = 500  # milliseconds
GIF_LOOP = 0  # infinite loop

# Output directories
TIMELAPSE_OUTPUT = 'timelapse_output'
ARCHIVE_BASE = 'archive'

# API Timeouts and Retries
API_TIMEOUT = 30  # seconds for API calls
DOWNLOAD_TIMEOUT = 300  # seconds for image downloads
MAX_RETRIES = 3

# ── Change Detection Configuration ──────────────────────────────────

# Pixel differencing threshold (0-1 normalized RGB difference)
CHANGE_PIXEL_DIFF_THRESHOLD = 0.12

# NDVI difference threshold
CHANGE_NDVI_DIFF_THRESHOLD = 0.15

# Minimum blob area (pixels) to count as real change
CHANGE_MIN_BLOB_PIXELS = 50

# Weight balance for combined signal
CHANGE_NDVI_WEIGHT = 0.4
CHANGE_RGB_WEIGHT = 0.6

# Change event database (SQLite)
CHANGE_DB_PATH = 'timelapse_output/change_events.db'

# Legacy compatibility (deprecated - use CDSE_* instead)
MAX_CLOUD_COVERAGE = 80
TIMELAPSE_FPS = 2
