# Iran Damage Assessment - Docker & Railway Deployment

## Prerequisites
- Docker installed locally
- Railway account (https://railway.app)
- GitHub repository (for Railway to pull from)

## Local Docker Testing

Build and run locally:
```bash
cd /Users/sepehrmortazavi/Desktop/map_api

# Build Docker image
docker build -t map-api:latest .

# Run with docker-compose
docker-compose up -d

# Check logs
docker-compose logs -f map-api

# Test API
curl http://localhost:9000/api/quick-stats

# Stop
docker-compose down
```

Visit: http://localhost:9000 (API) or access via frontend proxy

---

## Railway Deployment

### Step 1: Initialize Git Repository
```bash
cd /Users/sepehrmortazavi/Desktop/map_api
git init
git add .
git commit -m "Initial commit with Docker setup"
git remote add origin https://github.com/YOUR_USERNAME/map_api.git
git push -u origin main
```

### Step 2: Connect to Railway
1. Go to https://railway.app
2. Click **"New Project"**
3. Select **"Deploy from GitHub"**
4. Authorize and select your `map_api` repository
5. Railway auto-detects the `Dockerfile` and `railway.json`

### Step 3: Configure Environment
In Railway Dashboard → Project Settings:
- **Port**: 9000 (auto-detected)
- **Build Command**: (leave empty - uses Dockerfile)
- **Start Command**: (leave empty - uses CMD from Dockerfile)

### Step 4: Add Domain
1. In Railway → Your Service
2. Click **"Networking"** → **"Generate Domain"**
3. Railway assigns: `map-api-production-xxxx.railway.app`
4. (Optional) Add custom domain in Railway settings

### Step 5: Deploy
Railway auto-deploys on git push:
```bash
git add .
git commit -m "Update code"
git push origin main
# Railway detects push and auto-deploys!
```

---

## Final URLs

### API Endpoint (Backend)
```
https://map-api-production-xxxx.railway.app/api/quick-stats
https://map-api-production-xxxx.railway.app/api/assess-strike
```

### Frontend Access
```
https://map-api-production-xxxx.railway.app/
```

### Health Check
```
https://map-api-production-xxxx.railway.app/api/quick-stats
```

---

## Railway Environment Variables (if needed)
Set in Railway Dashboard → Variables:
```
FLASK_ENV=production
PYTHONUNBUFFERED=1
```

---

## Troubleshooting

Check logs in Railway:
```
View Logs → map-api service
```

SSH into container (Railway supports this):
- Railway → Service → Remote Development

Redeploy:
- Push to GitHub or click Deploy button in Railway

---

## Next: Custom Domain (Optional)

After deployment, add your custom domain:
1. Railway → Service → Networking
2. Add custom domain: `api.yourdomain.com`
3. Update DNS CNAME to Railway's nameserver

---

## Quick Summary

| Item | Value |
|------|-------|
| **Image** | Dockerfile (multi-stage) |
| **Backend Port** | 9000 |
| **Frontend** | Built & served at root |
| **Database** | SQLite (persisted in volume) |
| **Health Check** | /api/quick-stats endpoint |
| **Final URL** | `https://map-api-production-xxxx.railway.app` |

After Railway deployment completes, your **final production URL** will be displayed in the Railway Dashboard Deployments tab.
