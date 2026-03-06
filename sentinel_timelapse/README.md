# Iran Damage Assessment Platform

Real-time OSINT intelligence platform for monitoring strategic targets.

## Features

- 🎯 **217+ Strategic Targets** - Dynamic database, auto-discovers new sites
- 🔍 **Auto-Discovery** - Finds new targets from GDELT news every 5 hours
- 🛰️ **Satellite Analysis** - Sentinel-2 imagery and change detection
- 📰 **Live OSINT** - Real-time news monitoring
- 🗺️ **Interactive Map** - React frontend with Leaflet

## Structure

```
├── app.py              # Flask server
├── Dockerfile          # Production deploy
├── requirements.txt    # Dependencies
├── frontend/           # React UI
└── src/
    ├── core/          # Config
    ├── osint/         # OSINT engine, targets
    └── satellite/     # Imagery processing
```

## Quick Start

```bash
pip install -r requirements.txt
cd frontend && npm install && npm run build && cd ..
gunicorn app:app --bind 0.0.0.0:8080
```

## API

- `GET /api/known-targets` - List targets
- `POST /api/targets` - Add target
- `POST /api/trigger-discovery` - Run discovery
- `GET /api/full-assessment` - Strike data

## Deploy

```bash
railway up
```
