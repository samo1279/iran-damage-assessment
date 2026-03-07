# Stage 1: Build Frontend
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend
COPY sentinel_timelapse/frontend/package*.json ./
RUN npm install
COPY sentinel_timelapse/frontend/ ./
RUN npm run build

# Stage 2: Python Backend
FROM python:3.11-slim

# Install system dependencies for rasterio/GDAL
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libgdal-dev \
    gdal-bin \
    libffi-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
COPY sentinel_timelapse/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir setuptools wheel && \
    pip install --no-cache-dir rasterio && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY sentinel_timelapse/ .

# Copy built frontend from stage 1
COPY --from=frontend-builder /app/frontend/dist ./static/dist

# Set environment variables
ENV PORT=8000
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT:-80}/ || exit 1

# Run with gunicorn for production (4 workers, increased timeout)
CMD gunicorn --bind 0.0.0.0:${PORT:-80} --workers 4 --timeout 120 --preload app:app
