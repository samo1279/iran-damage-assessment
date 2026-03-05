#!/bin/bash
# Quick setup and execution script for sentinel timelapse

set -e

echo "🚀 Sentinel Hub Time-Lapse Setup"
echo "================================="

# Check Python
python3 --version

# Install dependencies
echo ""
echo "📦 Installing Python dependencies..."
pip install -q requests rasterio opencv-python

# Prompt for credentials if not set
if grep -q "YOUR_CLIENT_ID" config.py; then
    echo ""
    echo "⚠️  IMPORTANT: You need Sentinel Hub credentials"
    echo ""
    echo "1. Go to: https://dataspace.copernicus.eu"
    echo "2. Create account or login"
    echo "3. Generate OAuth credentials (API keys)"
    echo "4. Edit config.py and replace:"
    echo "   - CDSE_CLIENT_ID"
    echo "   - CDSE_CLIENT_SECRET"
    echo ""
    echo "Then run: python3 collect_imagery.py [tehran|isfahan]"
else
    echo ""
    echo "✓ Credentials found in config.py"
    echo ""
    echo "Choose an AOI and run:"
    echo "  python3 collect_imagery.py tehran"
    echo "  python3 collect_imagery.py isfahan"
    echo ""
    echo "Then create time-lapse:"
    echo "  python3 create_timelapse.py --aoi tehran"
fi
