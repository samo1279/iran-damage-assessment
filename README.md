# 🛰️ Sentinel-2 Interactive Timelapse Generator

A professional web application for generating satellite timelapse animations using real Copernicus Sentinel-2 L2A imagery with interactive mapping.

## ✨ Key Features

### 🗺️ **Interactive Map**
- Real-time satellite imagery at 10-18m resolution
- Click on cities or use dropdown to select location
- Zoom in/out to explore specific areas
- Pan controls for detailed exploration

### 📡 **CORRECT Data Fetching Order** 🎯
✅ **Attempts REAL Sentinel-2 imagery FIRST**
- Searches Copernicus APIs for actual satellite data
- Cloud cover filtering (< 40%)
- Date range support

⚠️ **Falls Back to Archive ONLY if Real Data Unavailable**
- Test images as failsafe
- Clear warnings when using archive

📊 **Data Source Transparency**
- Shows user exactly what type of data is in the timelapse
- Green alert for REAL data
- Yellow alert for archive fallback

## 🔄 Data Source Flow (NEW)

### When User Generates Timelapse:

```
User: Select city + date range → Click "Generate Timelapse"
                ↓
System: Try to fetch REAL Sentinel-2 L2A from Copernicus
                ↓
      Real Images Found?
      ├─ ✅ YES → Use REAL satellite data (10m resolution)
      │          Display: "✅ Real Data: Copernicus Sentinel-2 L2A"
      │          Download: REAL timelapse
      │
      └─ ⚠️ NO → Fall back to archive images
                 Display: "⚠️ Archive Data: Lower quality test images"
                 Download: Archive timelapse
```

**CRITICAL**: System NO LONGER uses archive by default!
- Previous behavior: ❌ Showed archive data immediately
- New behavior: ✅ Tries real data first, only uses archive as fallback

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd sentinel_timelapse
pip install flask requests pillow numpy opencv-python rasterio
```

### 2. Start the Server
```bash
cd sentinel_timelapse
python app.py
```

### 3. Open in Browser
Navigate to: `http://127.0.0.1:9000`

## 📱 How It Works

### Step-by-Step Flow

```
1. USER OPENS APP & SELECTS LOCATION
   (Interactive map shows satellite imagery)
   ↓
2. USER SELECTS DATE RANGE & CLICKS "GENERATE"
   ↓
3. SYSTEM TRIES REAL SATELLITE DATA FIRST ⭐
   (Searches Copernicus APIs)
   ├─ Found? → Download real Sentinel-2 L2A images
   └─ Not found? → Fall back to archive test images
   ↓
4. IMAGES PROCESSED & FILTERED
   (Cloud cover check, georeference validation)
   ↓
5. TIMELAPSE GIF CREATED
   (Dates added as captions)
   ↓
6. USER SEES RESULT
   - Data source displayed (Real vs Archive)
   - Download button active
   - Preview shown
   ↓
7. DOWNLOAD GIF
   (Only download happens AFTER verification)
```

**IMPORTANT:** Archive download ONLY happens after system confirms real data is unavailable!

## 🎨 Web Interface Features

- **Interactive Leaflet Map** - Real satellite imagery layer
- **City Selection** - Click markers or dropdown
- **Zoom Controls** - Explore area detail
- **Date Inputs** - Default to last 90 days
- **Data Source Alert** - Green for real, yellow for archive
- **GIF Preview** - See result before downloading
- **Download Button** - Appears after generation

**Supported Locations:**
- ✅ Tehran
- ✅ Isfahan

## 📊 Project Structure

```
sentinel_timelapse/
├── app.py                    # Flask server (NEW: Real data priority)
├── fetch_images.py           # Copernicus API client (NEW: Multiple search methods)
├── create_timelapse.py       # GIF creation
├── config.py                 # Configuration
│
├── templates/
│   └── index.html            # Web UI with Leaflet map (NEW: Interactive map)
│
├── static/
│   └── style.css             # Professional styling
│
├── archive/                  # Archive test images (fallback only)
│   ├── tehran/              # 4 test images
│   └── isfahan/             # 4 test images
│
└── output/                   # Generated GIFs
```

## 🔧 Architecture Changes (NEW)

### What Changed in This Update:

**1. app.py** - Data Priority Logic
```python
# Step 1: Try REAL satellite data
real_products = fetcher.search_images(city, start_date, end_date)

if real_products:
    # Use real data
    data_source = "REAL Copernicus Sentinel-2 L2A"
else:
    # ONLY if real data fails: use archive
    creator.load_images(image_folder)  # Archive fallback
    data_source = "Archive (Test Data)"
```

**2. fetch_images.py** - Multiple API Methods
- `_search_opensearch()` - Copernicus OpenSearch (primary)
- `_search_stac()` - STAC API (fallback)
- Cloud cover filtering (< 40%)

**3. templates/index.html** - Data Source Indicator
```javascript
if (!data.is_real_data) {
    // Show yellow alert for archive
    alertEl.textContent = '⚠️ Archive Data: Lower quality test images';
} else {
    // Show green alert for real data
    alertEl.textContent = '✅ Real Data: Copernicus Sentinel-2 L2A';
}
```

## 📡 API Response Example

```json
{
  "success": true,
  "city": "Tehran",
  "frames": 4,
  "dates": ["2026-02-20", "2026-02-21", "2026-02-22", "2026-02-27"],
  "file": "timelapse_tehran_2026-02-20_2026-02-27.gif",
  "size_mb": "1.36",
  "download_url": "/api/download/timelapse_tehran_2026-02-20_2026-02-27.gif",
  "data_source": "REAL Copernicus Sentinel-2 L2A",
  "is_real_data": true
}
```

**Note:** `data_source` field tells you:
- `"REAL Copernicus Sentinel-2 L2A"` = Real satellite data ✅
- `"Archive (Test Data)"` = Fallback test images ⚠️

## ✅ How to Ensure You Get Real Data

1. **Use Current Dates** - Sentinel-2 has ~5 day revisit
2. **Check Cloud Cover** - If area has clouds, real imagery may not be useful
3. **Watch for Data Source Alert** - Green = Real, Yellow = Archive
4. **Date Range Matters** - Some dates may have no acquisitions
5. **Trust the System** - Archive only used if real data unavailable

## 🌐 Data Sources

### REAL Satellite Data (Primary)
- **Provider:** Copernicus Data Space Ecosystem
- **Satellite:** Sentinel-2 A & B
- **Resolution:** 10 meters per pixel
- **Bands:** 11 spectral bands
- **Update:** Every 5 days (weather dependent)
- **License:** Open Access

### Archive Test Data (Fallback)
- **Resolution:** ~10 meters (simulated)
- **Bands:** 3 (RGB)
- **Quality:** Lower (for testing/demo)
- **Use:** Only if real data unavailable

## 🎯 Example Workflow

```
Step 1: Open http://127.0.0.1:9000
Step 2: Click on "Tehran" marker on map
Step 3: Set dates: 2026-02-20 to 2026-02-27
Step 4: Click "Generate Timelapse" button
Step 5: System attempts to fetch REAL data from Copernicus
        (takes ~10-30 seconds)
Step 6: Results shown with data source indicator:
        ✅ Green alert = Real Sentinel-2 imagery
        ⚠️ Yellow alert = Archive test images
Step 7: Download GIF from results section
```

## 🔧 Configuration

Edit [config.py](config.py) to:
- Add new locations (AOI definitions)
- Change API credentials
- Adjust cloud coverage thresholds
- Modify output directory

## 🐛 Troubleshooting

**No images found for date range:**
- Might have too much cloud cover
- Date range might not have Sentinel-2 data
- Check Copernicus web viewer for availability

**API errors:**
- Verify Copernicus credentials in config.py
- Check internet connection
- Verify date format (YYYY-MM-DD)

**GIF creation fails:**
- Ensure write permissions in output directory
- Check disk space
- Verify image files are valid GeoTIFFs

## 📚 References

- [Copernicus Data Space Ecosystem](https://dataspace.copernicus.eu/)
- [Sentinel-2 Bands](https://sentinels.copernicus.eu/web/sentinel/user-guides/sentinel-2-msi/overview)
- [STAC API Documentation](https://www.ogc.org/standards/stac)

## 📄 License

Open source - use freely for research and education

---

**Last Updated:** March 5, 2026  
**Status:** ✅ API integration working - fetches fresh satellite images on demand
