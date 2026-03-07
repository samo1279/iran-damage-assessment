# Multi-stage build for Iran Damage Assessment Map API

# Stage 1: Build Frontend
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend

# Copy frontend package files
COPY sentinel_timelapse/frontend/package*.json ./
RUN npm ci

# Copy frontend source
COPY sentinel_timelapse/frontend ./
RUN npm run build

# Stage 2: Python Backend with Frontend
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set GDAL environment variables
ENV GDAL_CONFIG=/usr/bin/gdal-config
ENV LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH

# Copy Python requirements
COPY sentinel_timelapse/requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY sentinel_timelapse/ ./

# Copy built frontend from stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Create required directories
RUN mkdir -p timelapse_output/strikes

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:9000/api/quick-stats || exit 1

# Expose ports
EXPOSE 9000

# Set environment
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Run the app
CMD ["python", "app.py"]
