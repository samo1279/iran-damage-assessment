# Sentinel Hub Configuration
# Replace these with your CDSE credentials from https://dataspace.copernicus.eu

CDSE_CLIENT_ID = "sh-0a34fef5-b4e5-44ed-88ae-96c032e64cf8"
CDSE_CLIENT_SECRET = "Mtl9tNIAN5AJqaFgpnrSNXCIU6Cdxkxq"

# Choose your AOI
AOI_CONFIG = {
    "tehran": {
        "name": "Tehran 5km Box",
        "bbox": [51.362049329675, 35.666442220625, 51.417350670325, 35.711357779375],
    },
    "isfahan": {
        "name": "Isfahan 5km Box",
        "bbox": [51.643602920397, 32.642822220625, 51.696957079603, 32.687737779375],
    }
}

# Sentinel Hub API endpoints
CDSE_TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
CDSE_CATALOG_URL = "https://sh.dataspace.copernicus.eu/api/v1/catalog/1.0.0/search"
CDSE_PROCESS_URL = "https://sh.dataspace.copernicus.eu/api/v1/process"

# Sentinel Hub Configuration Instance ID
INSTANCE_ID = "b17a2514-69c8-4d4b-93db-dd151221750f"

# Time range for time-lapse
START_DATE = "2026-02-20T00:00:00Z"  # Earlier to capture more data
END_DATE = "2026-03-05T23:59:59Z"    # Through March 5

# Cloud coverage threshold (percent)
MAX_CLOUD_COVERAGE = 80  # Very relaxed to get any available data

# Processing parameters
OUTPUT_WIDTH = 1024   # Increased for better quality
OUTPUT_HEIGHT = 1024
MCP_THRESHOLD = 40  # Cloud probability threshold: 20/40/60

# Export settings
EXPORT_FORMAT = "geotiff"  # "geotiff" or "png"
ARCHIVE_DIR = "archive"
OUTPUT_DIR = "timelapse_output"

# Visualization type
VISUALIZATION = "true_color"  # "true_color" or "swir"
