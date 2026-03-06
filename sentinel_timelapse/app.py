"""
Iran Damage Assessment Platform
==============================
Production-ready Flask server with:
  - OSINT intelligence from GDELT
  - Dynamic target discovery
  - Satellite imagery analysis
  - React frontend
"""

from flask import Flask, request, jsonify, send_file, send_from_directory, Response
from pathlib import Path
import os, glob, traceback, json
import threading
import time
from datetime import datetime

try:
    from src.satellite.create_timelapse import TimelapseCreator
    from src.satellite.fetch_images import SatelliteFetcher
    from src.satellite.change_detector import ChangeDetector, get_events, find_band_files
    from src.satellite.sar_fetcher import SARFetcher
    from src.satellite.sar_detector import detect_sar_changes
    from src.satellite.planet_fetcher import PlanetFetcher, planet_available
    from src.satellite.multi_source import MultiSourceAggregator
    from src.osint.osint_engine import OSINTEngine, KNOWN_TARGETS
    from src.osint.correlation import CorrelationEngine
    from src.osint.target_manager import TargetManager, AutoDiscovery, migrate_hardcoded_targets, get_target_manager
    from src.core.config import AOI_CONFIG, TIMELAPSE_OUTPUT
    TARGET_MANAGER_AVAILABLE = True
    MODULES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Some modules not available: {e}")
    MODULES_AVAILABLE = False
    TARGET_MANAGER_AVAILABLE = False
    AOI_CONFIG = {}
    TIMELAPSE_OUTPUT = "timelapse_output"
    KNOWN_TARGETS = {}

# React frontend build path
REACT_DIST = Path(__file__).parent / 'frontend' / 'dist'

app = Flask(
    __name__,
    static_folder=str(REACT_DIST / 'assets'),
    static_url_path='/assets',
)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024

# Ensure directories exist
Path(TIMELAPSE_OUTPUT).mkdir(parents=True, exist_ok=True)
for city_config in AOI_CONFIG.values():
    Path(city_config['folder']).mkdir(parents=True, exist_ok=True)

# Initialize components only if modules are available
if MODULES_AVAILABLE:
    try:
        change_detector = ChangeDetector()
        osint = OSINTEngine()
        correlation = CorrelationEngine()
        print("✅ All satellite processing modules loaded successfully")
    except Exception as e:
        print(f"⚠️ Error initializing modules: {e}")
        MODULES_AVAILABLE = False
        change_detector = osint = correlation = None
else:
    change_detector = osint = correlation = None
    print("⚠️ Running in limited mode - satellite processing disabled")

# Initialize dynamic target manager
target_mgr = None
if TARGET_MANAGER_AVAILABLE:
    try:
        target_mgr = get_target_manager()
        # Migrate hardcoded 217 targets to DB (idempotent)
        migrate_hardcoded_targets(target_mgr)
        print(f"✅ Dynamic target system initialized ({target_mgr.get_target_count()} targets)")
    except Exception as e:
        print(f"⚠️ Target manager init error: {e}")
        target_mgr = None

def get_all_targets_dynamic():
    """Get targets from database (dynamic) or fallback to hardcoded."""
    if target_mgr:
        return target_mgr.get_all_targets()
    return KNOWN_TARGETS

# ────────────────────────────────────────────────────────────────────
# BACKGROUND SCHEDULER - Refreshes OSINT data every 5 hours
# ────────────────────────────────────────────────────────────────────

# Global cache for background OSINT results
_background_cache = {
    'last_refresh': None,
    'osint_data': None,
    'correlation_data': None,
    'is_running': False,
}

REFRESH_INTERVAL_HOURS = 5  # Refresh every 5 hours

def background_osint_refresh():
    """Background thread that refreshes OSINT data periodically."""
    global _background_cache
    
    if not MODULES_AVAILABLE:
        print("[SCHEDULER] Modules not available, scheduler disabled")
        return
    
    while True:
        try:
            # Check if already running
            if _background_cache['is_running']:
                time.sleep(60)
                continue
            
            _background_cache['is_running'] = True
            print(f"\n[SCHEDULER] Starting background OSINT refresh at {datetime.now().isoformat()}")
            
            # Run OSINT scan
            osint_result = osint.full_scan()
            
            # Use dynamic targets instead of hardcoded 217
            all_targets = get_all_targets_dynamic()
            targets = list(all_targets.keys())
            correlation_result = correlation.correlate_all(targets, osint_result)
            
            # Auto-discover NEW targets from news (the magic!)
            if target_mgr:
                try:
                    discovery = AutoDiscovery(target_mgr)
                    new_targets = discovery.scan_for_new_targets(max_records=50, num_queries=4)
                    if new_targets:
                        print(f"[DISCOVERY] 🆕 Found {len(new_targets)} NEW targets from OSINT!")
                        for t in new_targets:
                            print(f"  + {t['name']} ({t['type']}) - {t.get('province', 'Unknown')}")
                        _background_cache['new_targets'] = new_targets
                except Exception as de:
                    print(f"[DISCOVERY] Error: {de}")
            
            # Update cache
            _background_cache['osint_data'] = osint_result
            _background_cache['correlation_data'] = correlation_result
            _background_cache['last_refresh'] = datetime.now().isoformat()
            _background_cache['target_count'] = len(targets)
            _background_cache['is_running'] = False
            
            print(f"[SCHEDULER] Background refresh complete. {len(targets)} targets, {len(osint_result.get('articles', []))} articles")
            print(f"[SCHEDULER] Next refresh in {REFRESH_INTERVAL_HOURS} hours")
            
        except Exception as e:
            print(f"[SCHEDULER] Error in background refresh: {e}")
            _background_cache['is_running'] = False
        
        # Wait for next refresh interval
        time.sleep(REFRESH_INTERVAL_HOURS * 60 * 60)


def start_background_scheduler():
    """Start the background OSINT refresh thread (only once)."""
    global _scheduler_started
    if _scheduler_started:
        return  # Already running
    _scheduler_started = True
    scheduler_thread = threading.Thread(target=background_osint_refresh, daemon=True)
    scheduler_thread.start()
    print(f"[SCHEDULER] Background OSINT scheduler started (refresh every {REFRESH_INTERVAL_HOURS} hours)")


# Auto-start scheduler when module loads (for gunicorn --preload)
_scheduler_started = False

# Check if we should start scheduler automatically (gunicorn with --preload)
if os.environ.get('GUNICORN_PRELOAD') or os.environ.get('START_SCHEDULER'):
    start_background_scheduler()


@app.route('/')
def index():
    """Serve React SPA if built, else fall back to Jinja template."""
    react_index = REACT_DIST / 'index.html'
    if react_index.exists():
        return send_file(str(react_index))
    # Fallback to old template
    cities = {code: info['name'] for code, info in AOI_CONFIG.items()}
    return render_template('index.html', cities=cities)


# ── Server-Sent Events for LIVE data updates ────────────────────────
@app.route('/api/stream')
def stream_updates():
    """
    SSE endpoint for real-time updates.
    Streams OSINT data changes to connected clients.
    """
    from flask import Response
    
    def generate():
        last_refresh = None
        while True:
            try:
                # Check if data has updated
                current_refresh = _background_cache.get('last_refresh')
                if current_refresh and current_refresh != last_refresh:
                    last_refresh = current_refresh
                    # Send update event
                    data = {
                        'type': 'osint_update',
                        'timestamp': current_refresh,
                        'articles_count': len(_background_cache.get('osint_data', {}).get('articles', [])),
                        'has_new_data': True
                    }
                    yield f"data: {json.dumps(data)}\n\n"
                else:
                    # Send heartbeat every 30 seconds
                    yield f"data: {{\"type\": \"heartbeat\", \"timestamp\": \"{datetime.now().isoformat()}\"}}\n\n"
                
                time.sleep(30)  # Check every 30 seconds
            except GeneratorExit:
                break
            except Exception as e:
                yield f"data: {{\"type\": \"error\", \"message\": \"{str(e)}\"}}\n\n"
                time.sleep(60)
    
    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no',
        }
    )


@app.route('/api/generate-timelapse', methods=['POST'])
def generate_timelapse():
    try:
        data = request.json or {}
        city = data.get('city', '').lower()
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        if city not in AOI_CONFIG or not start_date or not end_date:
            return jsonify({'success': False, 'error': 'Invalid parameters. Provide city, start_date, end_date.'}), 400

        city_name = AOI_CONFIG[city]['name']
        image_folder = str(Path(AOI_CONFIG[city]['folder']).absolute())

        # Step 1: Search STAC and download COG crops
        fetcher = SatelliteFetcher()
        downloaded = fetcher.search_and_download(city, start_date, end_date)

        if not downloaded:
            return jsonify({
                'success': False,
                'error': f'No satellite data found for {city_name} between {start_date} and {end_date}. Try a wider date range (Sentinel-2 revisits every 5 days).'
            }), 404

        # Step 2: Load downloaded images and create GIF
        creator = TimelapseCreator()
        loaded = creator.load_images(image_folder, start_date=start_date, end_date=end_date)

        if loaded == 0:
            return jsonify({
                'success': False,
                'error': f'Downloaded {len(downloaded)} files but none could be loaded. Check disk space.'
            }), 500

        # Step 3: Create timelapse GIF
        output_filename = f"timelapse_{city}_{start_date}_{end_date}.gif"
        output_path = Path(TIMELAPSE_OUTPUT) / output_filename

        if not creator.create_gif(str(output_path)):
            return jsonify({'success': False, 'error': 'GIF creation failed'}), 500

        # Step 4: Save before/after frames as separate PNGs
        before_filename = f"before_{city}_{start_date}.png"
        after_filename = f"after_{city}_{end_date}.png"

        before_path = Path(TIMELAPSE_OUTPUT) / before_filename
        after_path = Path(TIMELAPSE_OUTPUT) / after_filename

        creator.save_frame(creator.images[0], before_path, caption=f"BEFORE: {creator.dates[0]}")
        creator.save_frame(creator.images[-1], after_path, caption=f"AFTER: {creator.dates[-1]}")

        return jsonify({
            'success': True,
            'filename': output_filename,
            'before_image': before_filename,
            'after_image': after_filename,
            'before_date': creator.dates[0],
            'after_date': creator.dates[-1],
            'city': city_name,
            'count': loaded,
            'dates': creator.dates
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'Server error: {str(e)}'}), 500


@app.route('/timelapse_output/<path:filename>')
def serve_output(filename):
    return send_from_directory(str(Path(TIMELAPSE_OUTPUT).absolute()), filename)


@app.route('/api/download/<filename>')
def download_file(filename):
    file_path = Path(TIMELAPSE_OUTPUT) / filename
    if not file_path.exists():
        return "File not found", 404
    return send_file(file_path, as_attachment=True)


# ── Change Detection Endpoints ──────────────────────────────────────

@app.route('/api/detect-changes', methods=['POST'])
def detect_changes():
    """
    Run change detection between two dates for a given city.
    Downloads before/after imagery, computes pixel diff + NDVI diff,
    vectorizes change blobs, scores confidence, returns events + heatmap.
    """
    try:
        data = request.json or {}
        city = data.get('city', '').lower()
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        if city not in AOI_CONFIG or not start_date or not end_date:
            return jsonify({'success': False, 'error': 'Provide city, start_date, end_date'}), 400

        city_name = AOI_CONFIG[city]['name']
        image_folder = str(Path(AOI_CONFIG[city]['folder']).absolute())

        # Step 1: Download imagery for both dates
        fetcher = SatelliteFetcher()

        # Fetch earliest scene (before)
        before_items = fetcher.search_and_download(city, start_date, start_date, max_images=1)
        if not before_items:
            # Try wider window: up to 10 days after start_date
            from datetime import datetime, timedelta
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            wider_end = (start_dt + timedelta(days=10)).strftime('%Y-%m-%d')
            before_items = fetcher.search_and_download(city, start_date, wider_end, max_images=1)

        # Fetch latest scene (after)
        after_items = fetcher.search_and_download(city, end_date, end_date, max_images=1)
        if not after_items:
            from datetime import datetime, timedelta
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            wider_start = (end_dt - timedelta(days=10)).strftime('%Y-%m-%d')
            after_items = fetcher.search_and_download(city, wider_start, end_date, max_images=1)

        if not before_items:
            return jsonify({'success': False, 'error': f'No before-image found near {start_date}'}), 404
        if not after_items:
            return jsonify({'success': False, 'error': f'No after-image found near {end_date}'}), 404

        before_path = before_items[0]
        after_path = after_items[-1] if len(after_items) > 1 else after_items[0]

        # Ensure before and after are actually different images
        if before_path == after_path and len(before_items) > 1:
            before_path = before_items[0]
            after_path = before_items[-1]

        # Step 2: Find band files for NDVI
        before_date_str = os.path.basename(before_path).split('_')[1]
        after_date_str = os.path.basename(after_path).split('_')[1]

        before_red, before_nir = find_band_files(image_folder, before_date_str)
        after_red, after_nir = find_band_files(image_folder, after_date_str)

        # Step 3: Run change detection
        result = change_detector.detect(
            city, before_path, after_path,
            before_red_path=before_red,
            before_nir_path=before_nir,
            after_red_path=after_red,
            after_nir_path=after_nir,
        )

        # Also save before/after PNGs for the UI
        from create_timelapse import TimelapseCreator
        creator = TimelapseCreator()
        before_img = creator._load_tif_as_pil(before_path)
        after_img = creator._load_tif_as_pil(after_path)

        if before_img:
            before_png = f"change_before_{city}_{before_date_str}.png"
            creator.save_frame(before_img, Path(TIMELAPSE_OUTPUT) / before_png,
                               caption=f"BEFORE: {before_date_str}")
            result['before_image'] = before_png

        if after_img:
            after_png = f"change_after_{city}_{after_date_str}.png"
            creator.save_frame(after_img, Path(TIMELAPSE_OUTPUT) / after_png,
                               caption=f"AFTER: {after_date_str}")
            result['after_image'] = after_png

        return jsonify(result)

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'Change detection error: {str(e)}'}), 500


@app.route('/api/change-events')
def list_change_events():
    """
    Retrieve stored change events, optionally filtered by city.
    GET /api/change-events?city=tehran&limit=50
    """
    try:
        city = request.args.get('city', '').lower() or None
        limit = int(request.args.get('limit', 50))
        events = get_events(aoi_id=city, limit=limit)
        return jsonify({'success': True, 'events': events, 'count': len(events)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/search-scenes', methods=['POST'])
def search_scenes():
    """
    Search STAC catalog without downloading.
    Returns metadata for available scenes.
    """
    try:
        data = request.json or {}
        city = data.get('city', '').lower()
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        max_items = data.get('max_items', 20)

        if city not in AOI_CONFIG or not start_date or not end_date:
            return jsonify({'success': False, 'error': 'Provide city, start_date, end_date'}), 400

        fetcher = SatelliteFetcher()
        scenes = fetcher.search_only(city, start_date, end_date, max_items=max_items)
        return jsonify({'success': True, 'scenes': scenes, 'count': len(scenes)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/detect-changes-custom', methods=['POST'])
def detect_changes_custom():
    """
    Run change detection on a user-drawn custom boundary.
    Accepts a raw bbox [lon_min, lat_min, lon_max, lat_max] instead of a city name.
    """
    try:
        data = request.json or {}
        bbox = data.get('bbox')  # [lon_min, lat_min, lon_max, lat_max]
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        if not bbox or len(bbox) != 4 or not start_date or not end_date:
            return jsonify({'success': False, 'error': 'Provide bbox [lon_min,lat_min,lon_max,lat_max], start_date, end_date'}), 400

        # Validate bbox values
        try:
            bbox = [float(x) for x in bbox]
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': 'bbox must contain 4 numeric values'}), 400

        custom_folder = str(Path('archive/custom').absolute())
        Path(custom_folder).mkdir(parents=True, exist_ok=True)

        fetcher = SatelliteFetcher()

        # Fetch before image
        before_items = fetcher.search_and_download_bbox(bbox, custom_folder, start_date, start_date, max_images=1)
        if not before_items:
            from datetime import datetime, timedelta
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            wider_end = (start_dt + timedelta(days=10)).strftime('%Y-%m-%d')
            before_items = fetcher.search_and_download_bbox(bbox, custom_folder, start_date, wider_end, max_images=1)

        # Fetch after image
        after_items = fetcher.search_and_download_bbox(bbox, custom_folder, end_date, end_date, max_images=1)
        if not after_items:
            from datetime import datetime, timedelta
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            wider_start = (end_dt - timedelta(days=10)).strftime('%Y-%m-%d')
            after_items = fetcher.search_and_download_bbox(bbox, custom_folder, wider_start, end_date, max_images=1)

        if not before_items:
            return jsonify({'success': False, 'error': f'No before-image found near {start_date}. Try widening the date range.'}), 404
        if not after_items:
            return jsonify({'success': False, 'error': f'No after-image found near {end_date}. Try widening the date range.'}), 404

        before_path = before_items[0]
        after_path = after_items[-1] if len(after_items) > 1 else after_items[0]

        if before_path == after_path and len(before_items) > 1:
            before_path = before_items[0]
            after_path = before_items[-1]

        before_date_str = os.path.basename(before_path).split('_')[1]
        after_date_str = os.path.basename(after_path).split('_')[1]

        before_red, before_nir = find_band_files(custom_folder, before_date_str)
        after_red, after_nir = find_band_files(custom_folder, after_date_str)

        result = change_detector.detect(
            'custom', before_path, after_path,
            before_red_path=before_red,
            before_nir_path=before_nir,
            after_red_path=after_red,
            after_nir_path=after_nir,
            bbox=bbox,
        )

        from create_timelapse import TimelapseCreator
        creator = TimelapseCreator()
        before_img = creator._load_tif_as_pil(before_path)
        after_img = creator._load_tif_as_pil(after_path)

        if before_img:
            before_png = f"change_before_custom_{before_date_str}.png"
            creator.save_frame(before_img, Path(TIMELAPSE_OUTPUT) / before_png,
                               caption=f"BEFORE: {before_date_str}")
            result['before_image'] = before_png

        if after_img:
            after_png = f"change_after_custom_{after_date_str}.png"
            creator.save_frame(after_img, Path(TIMELAPSE_OUTPUT) / after_png,
                               caption=f"AFTER: {after_date_str}")
            result['after_image'] = after_png

        return jsonify(result)

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'Custom detection error: {str(e)}'}), 500


@app.route('/api/sar-analysis', methods=['POST'])
def sar_analysis():
    """
    Run SAR (radar) change detection using Sentinel-1 GRD.
    SAR works through clouds and at night — critical for rapid damage assessment.
    Uses log-ratio backscatter comparison (standard method).
    """
    try:
        data = request.json or {}
        city = data.get('city', '').lower()
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        bbox = data.get('bbox')  # optional custom bbox

        if not start_date or not end_date:
            return jsonify({'success': False, 'error': 'Provide start_date and end_date'}), 400

        if bbox and len(bbox) == 4:
            bbox = [float(x) for x in bbox]
            label = 'custom'
        elif city in AOI_CONFIG:
            bbox = AOI_CONFIG[city]['bbox']
            label = city
        else:
            return jsonify({'success': False, 'error': 'Provide city or bbox'}), 400

        fetcher = SARFetcher()

        # Download SAR pair
        pair = fetcher.download_sar_pair_bbox(bbox, label, start_date, end_date)
        if not pair:
            return jsonify({
                'success': False,
                'error': f'No SAR image pair found between {start_date} and {end_date}. '
                         f'Sentinel-1 revisits every 6-12 days. Try widening the date range.'
            }), 404

        # Run SAR change detection
        result = detect_sar_changes(
            pair['before_path'],
            pair['after_path'],
            bbox,
            city=label
        )

        return jsonify(result)

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'SAR analysis error: {str(e)}'}), 500


@app.route('/api/sar-availability', methods=['POST'])
def sar_availability():
    """Check what SAR scenes are available for a city/bbox."""
    try:
        data = request.json or {}
        city = data.get('city', '').lower()
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        if not start_date or not end_date:
            return jsonify({'success': False, 'error': 'Provide start_date, end_date'}), 400

        fetcher = SARFetcher()
        if city in AOI_CONFIG:
            scenes = fetcher.check_availability(city, start_date, end_date)
        else:
            return jsonify({'success': False, 'error': 'Unknown city'}), 400

        return jsonify({'success': True, 'scenes': scenes, 'count': len(scenes)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/data-availability', methods=['POST'])
def data_availability():
    """
    Check ALL data sources for available imagery.
    Returns comprehensive availability report:
      - Sentinel-2 (free, 10m optical)
      - Sentinel-1 SAR (free, 10m radar)
      - PlanetScope (commercial, ~3m optical)
      - CDSE Sentinel-2 (free with auth)
    Plus recommendations and data gap analysis.
    """
    try:
        data = request.json or {}
        city = data.get('city', '').lower()
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        bbox = data.get('bbox')
        cloud_cover = int(data.get('cloud_cover', 50))

        if not start_date or not end_date:
            return jsonify({'success': False, 'error': 'Provide start_date, end_date'}), 400

        if bbox and len(bbox) == 4:
            bbox = [float(x) for x in bbox]
        elif city in AOI_CONFIG:
            bbox = AOI_CONFIG[city]['bbox']
        else:
            return jsonify({'success': False, 'error': 'Provide city or bbox'}), 400

        agg = MultiSourceAggregator()
        report = agg.check_all_sources(bbox, start_date, end_date, cloud_cover)
        report['success'] = True
        return jsonify(report)

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/settings', methods=['GET', 'POST'])
def settings():
    """
    GET: Return current provider configuration status.
    POST: Update API keys (stored in environment for session).
    """
    if request.method == 'GET':
        return jsonify({
            'success': True,
            'providers': {
                'element84': {
                    'name': 'Element84 STAC (Sentinel-2 + Sentinel-1)',
                    'status': 'active',
                    'auth_required': False,
                    'configured': True,
                    'description': 'Free, no API key needed. Sentinel-2 (10m optical) + Sentinel-1 SAR (10m radar).'
                },
                'planet': {
                    'name': 'PlanetScope (~3m)',
                    'status': 'active' if planet_available() else 'unconfigured',
                    'auth_required': True,
                    'configured': planet_available(),
                    'description': 'Commercial ~3m daily imagery. Set PL_API_KEY env var.'
                },
                'cdse': {
                    'name': 'Copernicus CDSE',
                    'status': 'active' if os.environ.get('CDSE_CLIENT_ID') else 'unconfigured',
                    'auth_required': True,
                    'configured': bool(os.environ.get('CDSE_CLIENT_ID')),
                    'description': 'Free Sentinel Hub access. Set CDSE_CLIENT_ID + CDSE_CLIENT_SECRET.'
                }
            }
        })

    # POST: set API keys for session
    data = request.json or {}
    updated = []

    if 'pl_api_key' in data and data['pl_api_key'].strip():
        os.environ['PL_API_KEY'] = data['pl_api_key'].strip()
        # Validate
        pf = PlanetFetcher()
        valid, msg = pf.validate_key()
        if valid:
            updated.append('Planet API key set and validated')
        else:
            del os.environ['PL_API_KEY']
            return jsonify({'success': False, 'error': f'Planet key invalid: {msg}'}), 400

    if 'cdse_client_id' in data and 'cdse_client_secret' in data:
        os.environ['CDSE_CLIENT_ID'] = data['cdse_client_id'].strip()
        os.environ['CDSE_CLIENT_SECRET'] = data['cdse_client_secret'].strip()
        updated.append('CDSE credentials set')

    return jsonify({'success': True, 'updated': updated})


@app.route('/api/planet-analysis', methods=['POST'])
def planet_analysis():
    """
    Run change detection using PlanetScope ~3m imagery.
    Requires PL_API_KEY to be configured.
    Downloads 3m ortho pair, runs same pixel diff + NDVI pipeline.
    """
    try:
        if not planet_available():
            return jsonify({
                'success': False,
                'error': 'Planet API key not configured. Set PL_API_KEY environment variable '
                         'or enter it in Settings. Get a key at planet.com/account'
            }), 400

        data = request.json or {}
        city = data.get('city', '').lower()
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        bbox = data.get('bbox')

        if not start_date or not end_date:
            return jsonify({'success': False, 'error': 'Provide start_date and end_date'}), 400

        if bbox and len(bbox) == 4:
            bbox = [float(x) for x in bbox]
            label = 'custom'
        elif city in AOI_CONFIG:
            bbox = AOI_CONFIG[city]['bbox']
            label = city
        else:
            return jsonify({'success': False, 'error': 'Provide city or bbox'}), 400

        pf = PlanetFetcher()
        pair = pf.download_pair(bbox, label, start_date, end_date)
        if not pair:
            return jsonify({
                'success': False,
                'error': f'No PlanetScope pair found between {start_date} and {end_date}.'
            }), 404

        # Run change detection on PlanetScope imagery
        result = change_detector.detect(
            label, pair['before_path'], pair['after_path'],
            bbox=bbox,
        )

        # Also save PNGs for UI
        from create_timelapse import TimelapseCreator
        creator = TimelapseCreator()
        before_img = creator._load_tif_as_pil(pair['before_path'])
        after_img = creator._load_tif_as_pil(pair['after_path'])

        if before_img:
            png = f"planet_before_{label}_{pair['before_date']}.png"
            creator.save_frame(before_img, Path(TIMELAPSE_OUTPUT) / png,
                               caption=f"PLANET 3m BEFORE: {pair['before_date']}")
            result['before_image'] = png

        if after_img:
            png = f"planet_after_{label}_{pair['after_date']}.png"
            creator.save_frame(after_img, Path(TIMELAPSE_OUTPUT) / png,
                               caption=f"PLANET 3m AFTER: {pair['after_date']}")
            result['after_image'] = png

        result['source'] = 'PlanetScope'
        result['resolution'] = '~3m'
        return jsonify(result)

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'Planet analysis error: {str(e)}'}), 500


@app.route('/api/news')
def get_news():
    """
    Proxy to GDELT for conflict/damage related news.
    Free API, no key needed. Returns recent articles matching the query.
    Rate limited to 1 request per 5 seconds by GDELT.
    """
    try:
        import requests as http_req
        from urllib.parse import quote
        query = request.args.get('q', 'iran military damage')
        max_records = min(int(request.args.get('limit', 10)), 25)
        encoded_query = quote(query)
        url = (
            f"https://api.gdeltproject.org/api/v2/doc/doc"
            f"?query={encoded_query}&mode=ArtList&maxrecords={max_records}"
            f"&format=json&sort=datedesc"
        )
        resp = http_req.get(url, timeout=15, headers={
            'User-Agent': 'DamageAssessmentPlatform/3.0'
        })
        if resp.status_code == 429:
            return jsonify({'articles': [], 'error': 'GDELT rate limit - wait 5 seconds and try again'})
        if resp.status_code == 200:
            try:
                data = resp.json()
                return jsonify(data)
            except Exception:
                # GDELT sometimes returns non-JSON
                return jsonify({'articles': [], 'error': 'GDELT returned non-JSON response'})
        return jsonify({'articles': [], 'error': f'GDELT returned status {resp.status_code}'})
    except Exception as e:
        return jsonify({'articles': [], 'error': str(e)})


# ── OSINT Intelligence Endpoints ────────────────────────────────────

@app.route('/api/osint-scan', methods=['POST'])
def osint_scan():
    """
    Run OSINT intelligence scan.
    Searches GDELT + known targets, builds attack timeline.
    POST body: { "mode": "full" | "quick", "query": "optional search" }
    """
    try:
        data = request.json or {}
        mode = data.get('mode', 'quick')
        query = data.get('query')

        if mode == 'full':
            report = osint.full_scan(since_date='2026-03-01')
        else:
            report = osint.quick_scan(query=query)

        report['success'] = True
        return jsonify(report)

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/attack-timeline')
def attack_timeline():
    """
    Get stored attack timeline from DB.
    Returns all strikes since war start with evidence.
    """
    try:
        since = request.args.get('since', '2026-03-01')
        limit = int(request.args.get('limit', 100))
        strikes = osint.get_attack_timeline(since=since, limit=limit)
        return jsonify({'success': True, 'strikes': strikes, 'count': len(strikes)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/scheduler-status')
def scheduler_status():
    """
    Check background scheduler status and last refresh time.
    """
    return jsonify({
        'success': True,
        'scheduler_running': True,
        'refresh_interval_hours': REFRESH_INTERVAL_HOURS,
        'last_refresh': _background_cache.get('last_refresh'),
        'is_refreshing': _background_cache.get('is_running', False),
        'has_cached_data': _background_cache.get('osint_data') is not None,
    })


@app.route('/api/quick-stats')
def quick_stats():
    """
    FAST endpoint for initial page load.
    Returns cached targets + basic stats without hitting GDELT.
    Uses background-cached OSINT data when available.
    """
    try:
        # Use dynamic database for targets
        if target_mgr:
            targets = target_mgr.get_targets_list()
        else:
            targets = osint.get_known_targets() if MODULES_AVAILABLE else []
        
        # Count by category
        category_counts = {}
        for t in targets:
            cat = t.get('category', 'other')
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        # Get cached data from background refresh
        osint_articles = 0
        strike_count = 0
        confirmed = 0
        likely = 0
        last_refresh = None
        
        if _background_cache.get('osint_data'):
            osint_articles = _background_cache['osint_data'].get('articles_found', 0)
            last_refresh = _background_cache.get('last_refresh')
        
        if _background_cache.get('correlation_data'):
            assessments = _background_cache['correlation_data'].get('assessments', [])
            strike_count = len(assessments)
            confirmed = sum(1 for a in assessments if (a.get('combined_score') or 0) >= 0.7)
            likely = sum(1 for a in assessments if 0.4 <= (a.get('combined_score') or 0) < 0.7)
        
        return jsonify({
            'success': True,
            'target_count': len(targets),
            'strike_count': strike_count,
            'osint_articles': osint_articles,
            'confirmed': confirmed,
            'likely': likely,
            'categories': category_counts,
            'provinces': list(set(t['province'] for t in targets if t.get('province'))),
            'last_osint_refresh': last_refresh,
            'cached': True,
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'target_count': 0}), 500


@app.route('/api/known-targets')
def known_targets():
    """
    List all known Iranian military/strategic targets.
    NOW DYNAMIC: Uses database instead of hardcoded 217!
    Optional filters: ?category=nuclear_facility&province=Isfahan
    """
    try:
        category = request.args.get('category')
        province = request.args.get('province')
        
        # Use dynamic database if available
        if target_mgr:
            targets = target_mgr.get_targets_list(category=category, province=province)
            source = 'database'
        else:
            targets = osint.get_known_targets(category=category, province=province)
            source = 'hardcoded'
        
        return jsonify({
            'success': True,
            'targets': targets,
            'count': len(targets),
            'source': source,
            'categories': list(set(t['category'] for t in targets if t.get('category'))),
            'provinces': list(set(t['province'] for t in targets if t.get('province'))),
            'new_targets': _background_cache.get('new_targets', [])[:5]  # Recently discovered
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/targets', methods=['POST'])
def add_target():
    """
    Add a new target manually to the dynamic database.
    POST body: { "name": "...", "lat": 35.5, "lon": 51.5, "type": "military_base", ... }
    """
    if not target_mgr:
        return jsonify({'success': False, 'error': 'Dynamic target system not available'}), 503
    
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        required = ['name', 'lat', 'lon']
        for field in required:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        # Generate ID from name
        import re
        target_id = re.sub(r'[^a-z0-9]+', '_', data['name'].lower().strip())
        
        success = target_mgr.add_target(
            target_id=target_id,
            name=data['name'],
            lat=float(data['lat']),
            lon=float(data['lon']),
            target_type=data.get('type', 'unknown'),
            category=data.get('category', 'unknown'),
            province=data.get('province', 'Unknown'),
            description=data.get('description'),
            keywords=data.get('keywords'),
            source='api_manual',
            priority=data.get('priority', 5)
        )
        
        if success:
            return jsonify({
                'success': True,
                'target_id': target_id,
                'message': f'Target "{data["name"]}" added successfully',
                'total_targets': target_mgr.get_target_count()
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to add target'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/trigger-discovery', methods=['POST'])
def trigger_discovery():
    """
    Manually trigger target auto-discovery from OSINT.
    This scans GDELT news for new attack locations.
    """
    if not target_mgr:
        return jsonify({'success': False, 'error': 'Dynamic target system not available'}), 503
    
    try:
        discovery = AutoDiscovery(target_mgr)
        new_targets = discovery.scan_for_new_targets(max_records=50, num_queries=4)
        
        return jsonify({
            'success': True,
            'discovered': len(new_targets),
            'new_targets': new_targets,
            'total_targets': target_mgr.get_target_count()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/assess-strike', methods=['POST'])
def assess_strike():
    """
    Run full OSINT + satellite assessment for a specific target.
    POST body: { "target_id": "parchin_complex" } or { "lat": ..., "lon": ... }
    Optionally: "with_satellite": true to also run change detection (slow).
    """
    try:
        data = request.json or {}
        target_id = data.get('target_id')
        with_satellite = data.get('with_satellite', False)

        if target_id:
            # Try dynamic DB first, fallback to hardcoded
            target = None
            if target_mgr:
                target = target_mgr.get_target(target_id)
            if not target:
                target = KNOWN_TARGETS.get(target_id)
            if not target:
                return jsonify({'success': False, 'error': f'Unknown target: {target_id}'}), 404
            strike = {
                'id': target_id,
                'target_id': target_id,
                'target_name': target['name'],
                'target_type': target['type'],
                'lat': target['lat'],
                'lon': target['lon'],
                'bbox': target.get('bbox', [target['lon']-0.03, target['lat']-0.03, target['lon']+0.03, target['lat']+0.03]),
                'date': data.get('date', '2026-03-01'),
                'province': target.get('province', ''),
                'confidence': 'reported',
                'source_count': 1,
            }
        else:
            lat = data.get('lat')
            lon = data.get('lon')
            if not lat or not lon:
                return jsonify({'success': False, 'error': 'Provide target_id or lat/lon'}), 400
            strike = {
                'id': f'custom_{lat}_{lon}',
                'target_id': 'custom',
                'target_name': data.get('name', f'Custom ({lat:.4f}, {lon:.4f})'),
                'target_type': 'custom',
                'lat': float(lat),
                'lon': float(lon),
                'date': data.get('date', '2026-03-01'),
                'confidence': 'unconfirmed',
                'source_count': 0,
            }

        if with_satellite:
            fetcher_obj = SatelliteFetcher()
            result = correlation.assess_strike(strike, fetcher=fetcher_obj, change_detector=change_detector)
        else:
            result = correlation.assess_strike(strike)

        result['success'] = True
        return jsonify(result)

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/full-assessment', methods=['POST'])
def full_assessment():
    """
    Run OSINT scan + satellite correlation for all reported strikes.
    This is the main "big picture" endpoint.
    POST body: { "with_satellite": false, "max_satellite_checks": 3 }
    """
    try:
        data = request.json or {}
        with_satellite = data.get('with_satellite', False)
        max_checks = int(data.get('max_satellite_checks', 3))

        # Step 1: OSINT scan
        osint_report = osint.full_scan(since_date='2026-03-01')
        strikes = osint_report.get('strikes', [])

        # Step 2: Assess each strike
        if with_satellite:
            fetcher_obj = SatelliteFetcher()
            assessments = correlation.batch_assess(
                strikes, fetcher=fetcher_obj,
                change_detector=change_detector,
                max_sat_checks=max_checks
            )
        else:
            assessments = correlation.batch_assess(strikes)

        # Step 3: Generate summary
        summary = correlation.generate_summary(assessments)

        return jsonify({
            'success': True,
            'osint': {
                'articles_found': osint_report['articles_found'],
                'articles_with_locations': osint_report['articles_with_locations'],
                'targets_mentioned': osint_report['targets_mentioned'],
            },
            'assessments': assessments,
            'summary': summary,
            'timeline': osint_report.get('timeline', {}),
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("  IRAN DAMAGE ASSESSMENT PLATFORM — v5.0")
    print("  Data : Multi-source satellite + OSINT intelligence")
    print("    [FREE ] Sentinel-2 L2A (10m optical) via Element84 STAC")
    print("    [FREE ] Sentinel-1 SAR (10m radar) via Element84 STAC")
    print("    [FREE ] GDELT OSINT news intelligence (no key needed)")
    print(f"    [FREE ] {len(KNOWN_TARGETS)} known strategic targets in database")
    if planet_available():
        print("    [READY] PlanetScope (~3m optical) — API key configured")
    else:
        print("    [SETUP] PlanetScope (~3m) — set PL_API_KEY to enable")
    if os.environ.get('CDSE_CLIENT_ID'):
        print("    [READY] Copernicus CDSE — credentials configured")
    else:
        print("    [SETUP] Copernicus CDSE — set CDSE_CLIENT_ID to enable")
    print("  Method: COG windowed crop (~17s/image, 512x512)")
    print("  ML    : Pixel diff + NDVI + SAR log-ratio + blob vectorization")
    print("  DB    : SQLite change_events.db")
    print(f"  SCHED : Background OSINT refresh every {REFRESH_INTERVAL_HOURS} hours")
    print("=" * 60 + "\n")
    
    # Start background OSINT scheduler
    start_background_scheduler()
    
    app.run(host='0.0.0.0', port=9000)
