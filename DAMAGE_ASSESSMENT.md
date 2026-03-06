# 🛰️ Satellite Damage Assessment Tool for Iran

**Purpose:** Track destruction and assess damage using real Copernicus Sentinel-2 satellite imagery for before/after analysis during conflict periods.

## 🎯 Mission

This platform enables **independent satellite-based damage assessment** by:

1. **Fetching REAL satellite imagery** - Not simulated, not archive test data
2. **Before/After comparison** - Select dates before and after significant events
3. **Detecting changes** - Visual damage, destruction, infrastructure damage, craters, etc.
4. **NO archive fallback** - This tool requires actual satellite data to function

## ⚠️ CRITICAL REQUIREMENT: NO ARCHIVE FALLBACK

**This tool is designed specifically for war damage assessment.** Unlike previous versions:

- ❌ **NO fallback to archive/test data** - If no real satellite imagery exists, the system fails
- ✅ **REAL satellite data ONLY** - Copernicus Sentinel-2 L2A current/recent imagery
- 📊 **Before/After analysis** - Requires two time periods for comparison
- 🎯 **Transparency** - System is honest about data availability

### Why No Archive Fallback?

Using old test images for damage assessment is **useless and misleading**. If Sentinel-2 hasn't captured imagery for the location/date you selected, the system tells you clearly rather than show fake "test data."

## 🛰️ How It Works

### Step 1: Select Location
- Click on Tehran or Isfahan on the interactive map
- Zoom in to see the specific area of interest
- System shows exact satellite imagery (not Google Maps)

### Step 2: Select BEFORE Date
- Choose a date **before** the major event/conflict
- Date when area was unaffected (peacetime)
- Example: "2024-12-15" (before bombing campaign)

### Step 3: Select AFTER Date
- Choose a date **after** the event
- When you want to see the damage/changes
- Example: "2025-01-15" (after bombing campaign)

### Step 4: Generate Analysis
- System searches Copernicus APIs for REAL Sentinel-2 L2A imagery
- Attempts to find satellite data for BOTH dates
- Creates timelapse showing changes over time

### Step 5: Review Damage Assessment
- Watch timelapse frame-by-frame
- Compare before/after satellite imagery
- Look for visible destruction, damage patterns, new impacts

## 📡 Data Source: Copernicus Sentinel-2 L2A

### Specifications
- **Resolution:** 10 meters per pixel
- **Satellite:** Sentinel-2 A & B (ESA)
- **Revisit Time:** ~5 days (weather dependent)
- **Spectral Bands:** 11 bands (RGB + infrared + others)
- **Coverage:** Global, including Iran
- **Cost:** Free and open access
- **License:** Creative Commons Attribution 4.0
- **Processing Level:** L2A (atmosphere corrected)

### What You Can See at 10m Resolution
- ✅ Buildings (individual houses visible)
- ✅ Roads and highways
- ✅ Craters and blast zones
- ✅ Destroyed structures (collapsed roofs)
- ✅ Infrastructure damage
- ✅ Military installations
- ✅ Burned areas
- ✅ Construction sites
- ✅ Vegetation changes
- ✅ Vehicle convoys (if large)

### What You CANNOT See
- ❌ Individual people
- ❌ Small vehicles
- ❌ Text/signs
- ❌ Fine details < 10m

## 🎯 Example Use Cases

### Use Case 1: Missile Strike Damage
1. Select Tehran city center
2. BEFORE: "2025-01-14" (day before missile strike)
3. AFTER: "2025-01-16" (day after strike)
4. Generate timelapse
5. Compare satellite imagery to see impact zones, damaged buildings

### Use Case 2: Bombing Campaign Impact
1. Select Isfahan region
2. BEFORE: "2024-11-01" (before campaign)
3. AFTER: "2024-12-15" (after campaign)
4. Watch timelapse showing progression
5. Identify destroyed military facilities, damaged infrastructure

### Use Case 3: City-Wide Assessment
1. Select entire Tehran region
2. BEFORE: "2024-06-01" (baseline)
3. AFTER: "2025-03-01" (after multiple events)
4. See overall changes across city
5. Identify reconstruction efforts

## ⚡ Critical Data Limitations

### Availability Issues

**Real Sentinel-2 imagery depends on:**

1. **Cloud cover** - Iran often has 40%+ cloud cover
   - Overcast days = no usable imagery
   - Solution: Try different dates

2. **Satellite revisit time** - ~5 days between passes
   - You might not get data for exact dates you want
   - Solution: Use wider date ranges (±3 days)

3. **API access** - Requires internet connection
   - Copernicus servers sometimes unavailable
   - Solution: Retry later

### What If No Data Is Available?

The system will **FAIL with clear message:**
```
❌ NO REAL SATELLITE DATA AVAILABLE
   Reasons could be:
   - No Sentinel-2 acquisitions for this date/location
   - Area completely cloud-covered
   - API unreachable
   - Credentials needed for access
```

**This is CORRECT behavior.** We don't want fake archive data for damage assessment.

## 🔧 Configuration for Maximum Coverage

### Maximize Chances of Getting Real Data

1. **Use wider date ranges** (±5 days from target)
   - BEFORE: "2025-01-10" to "2025-01-14"
   - AFTER: "2025-01-16" to "2025-01-20"

2. **Try multiple date combinations**
   - If 2025-01-14 shows 90% clouds, try 2025-01-13

3. **Start with larger areas**
   - Zoom to city level first, narrow down later
   - Larger areas = more cloud-free pixels

4. **Check weather patterns**
   - Winter (Dec-Feb): More clouds
   - Summer (Jun-Aug): Clearer skies
   - Plan assessments during clear seasons

5. **Use API credentials** (optional)
   ```bash
   export CDSE_CLIENT_ID='your_id'
   export CDSE_CLIENT_SECRET='your_secret'
   ```
   - Registered users get priority access
   - Better rate limits
   - More reliable downloads

## 📊 Interpreting Results

### What Changes to Look For

When comparing before/after timelapse:

**Destruction Indicators:**
- ❌ Buildings/structures disappear
- 💥 Blast zones (lighter colored circular areas)
- 🔥 Burned/blackened areas
- 🕳️ Craters or holes
- 🏚️ Collapsed roofs (shadow changes)
- 🌊 Flooding or secondary damage

**Infrastructure Damage:**
- Roads blocked or destroyed
- Bridges collapsed
- Power lines down
- Water/sewage disruption

**Military Changes:**
- Aircraft/vehicles destroyed
- Fortifications damaged
- Supply depots damaged
- Command centers hit

### Confidence in Assessments

**High confidence:**
- Large structures destroyed
- Widespread damage zones
- Obvious craters/impacts
- 10m+ diameter changes

**Medium confidence:**
- Partial destruction
- Damaged infrastructure
- Changed vegetation
- New construction

**Low confidence:**
- Small changes
- Camouflaged damage
- Underground facilities
- Individual vehicle damage

## 🌐 Data Sources & APIs

### Primary Source: Copernicus Data Space Ecosystem

```
Endpoint: https://catalogue.dataspace.copernicus.eu/api/v1/search
Method: OpenSearch + STAC API
Authentication: OAuth2 (optional - public access available)
Rate Limit: ~100 requests/day (free tier)
```

### Fallback Sources

1. **OpenAerialMap STAC** - Community satellite data
2. **USGS Earth Explorer** - Alternative satellite sources
3. **ESA Scihub** - Raw Sentinel data (requires registration)

## ⚙️ Setup & Running

### Prerequisites
```bash
Python 3.13+
flask, requests, pillow, numpy, opencv-python, rasterio
```

### Installation
```bash
cd /Users/sepehrmortazavi/Desktop/map_api/sentinel_timelapse
pip install flask requests pillow numpy opencv-python rasterio
```

### Start Server
```bash
python app.py
# Opens: http://127.0.0.1:9000
```

### Optional: Configure CDSE Credentials
```bash
# Get credentials from https://account.dataspace.copernicus.eu/
export CDSE_CLIENT_ID='your_client_id'
export CDSE_CLIENT_SECRET='your_client_secret'

python app.py  # Now with better API access
```

## 📁 Project Structure

```
sentinel_timelapse/
├── app.py                    # Flask server - damage assessment mode
├── fetch_images.py           # Copernicus API client - REAL data ONLY
├── create_timelapse.py       # GIF creation from satellite images
├── config.py                 # Settings, bounding boxes, API endpoints
│
├── templates/
│   └── index.html            # Web UI - damage assessment interface
│
├── static/
│   └── style.css             # Professional styling
│
└── output/
    └── [generated GIFs]      # Output timelapse files
```

## 🚨 Important Notes

### Data Accuracy
- Satellite imagery is an **objective recording** of what happened
- Free from editorializing or interpretation
- Timestamps are accurate to pixel
- Cloud cover is clearly visible (not hidden)

### Limitations
- Cannot see underground damage
- Cannot see through thick smoke/dust clouds
- Small damage (< 10m) not detectable
- Temporal resolution limited to 5-day intervals

### Ethical Use
This tool is designed for:
- ✅ Humanitarian damage assessment
- ✅ Conflict documentation
- ✅ Rebuilding verification
- ✅ NGO/UN monitoring
- ✅ Civilian casualty investigation

This tool should NOT be used for:
- ❌ Military targeting
- ❌ Real-time warfare support
- ❌ Commercial surveillance
- ❌ Privacy invasion

## 🔗 Resources

- **Copernicus:** https://www.copernicus.eu/
- **Sentinel-2:** https://sentinel.esa.int/web/sentinel/missions/sentinel-2
- **Data Space Hub:** https://dataspace.copernicus.eu/
- **Documentation:** https://documentation.dataspace.copernicus.eu/

## 📞 Support

### No Real Data Available?

1. **Check cloud cover** - Look at satellite imagery on Google Maps for visual confirmation
2. **Try different dates** - Sentinel-2 revisits every ~5 days
3. **Use wider date range** - ±3-5 days from target date
4. **Check API status** - Copernicus servers sometimes down

### Server Issues?

```bash
# Check if port 9000 is in use
lsof -i :9000

# Kill existing process
pkill -f "python app.py"

# Restart
python app.py
```

### Need Better API Access?

Register for free CDSE account:
- https://account.dataspace.copernicus.eu/
- Get OAuth2 credentials
- Set environment variables

---

**Last Updated:** March 5, 2026

**Purpose:** War Damage Assessment via Satellite Imagery

**Data Source:** REAL Copernicus Sentinel-2 L2A ONLY (No Archive Fallback)

**Resolution:** 10 meters per pixel

**Status:** Ready for deployment
