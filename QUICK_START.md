# Quick Start: Satellite Damage Assessment

## 🎯 What This Tool Does

Tracks destruction in Iran by comparing **REAL satellite imagery** from before and after conflict events.

## ⚡ 60-Second Start

1. **Open:** http://127.0.0.1:9000
2. **Click:** Tehran or Isfahan on map
3. **Set dates:** BEFORE event → AFTER event
4. **Click:** "Analyze & Compare"
5. **Watch:** Timelapse to see damage

## 📊 Data You Get

- ✅ **10-meter resolution** satellite imagery
- ✅ **REAL satellite data** (not test images)
- ✅ **Before/After comparison** for damage assessment
- ❌ **NO archive fallback** - requires actual satellite data

## ⚠️ Critical: No Real Data = System Fails

If Sentinel-2 hasn't captured imagery for your date range, the system will **clearly tell you** instead of showing fake test data.

## 🔍 What You Can Detect

- Building destruction
- Craters and blast zones
- Burned areas
- Infrastructure damage
- Military facility damage
- Roads/bridges destroyed

## 📍 Supported Areas

- **Tehran** - Capital city
- **Isfahan** - Major city

## ⏰ Date Tips

- **Sentinel-2 revisits every ~5 days**
- **Cloud cover** can block imagery
- **Use wider date ranges** (±3 days) for better results
- **Winter = more clouds**, Summer = clearer

## 🌐 Real-Time Satellite Source

All data from **Copernicus Sentinel-2 L2A** satellite:
- Free, open-access
- 10m per pixel resolution
- Global coverage including Iran
- Updated every 5 days (weather dependent)

## 🚀 Setup (One-Time)

```bash
cd /Users/sepehrmortazavi/Desktop/map_api/sentinel_timelapse
pip install flask requests pillow numpy opencv-python rasterio
python app.py
```

Then open: **http://127.0.0.1:9000**

## 💾 Output

Downloads GIF showing satellite timelapse of area changes

---

**Remember:** This is for damage assessment using REAL satellite data only.
