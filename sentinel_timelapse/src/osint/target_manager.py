"""
Dynamic Target Management System
================================
Replaces hardcoded KNOWN_TARGETS with database-backed dynamic targets.
Automatically discovers new attack locations from OSINT and adds them.
"""

import sqlite3
import json
import hashlib
import requests
import re
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import quote

class TargetManager:
    """
    Manages strategic targets in SQLite database.
    - Load/save targets dynamically
    - Auto-discover new locations from news
    - Geocode new attack sites
    - Trigger satellite analysis for new targets
    """
    
    def __init__(self, db_path='timelapse_output/targets.db'):
        self.db_path = db_path
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'IranDamageAssessment/5.0 TargetManager'
        })
        self._init_db()
    
    def _init_db(self):
        """Create targets database with proper schema."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''CREATE TABLE IF NOT EXISTS targets (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT,
            category TEXT,
            lat REAL,
            lon REAL,
            bbox TEXT,
            description TEXT,
            keywords TEXT,
            province TEXT,
            source TEXT DEFAULT 'manual',
            discovered_date TEXT,
            last_satellite_check TEXT,
            satellite_images_count INTEGER DEFAULT 0,
            strike_count INTEGER DEFAULT 0,
            active INTEGER DEFAULT 1,
            priority INTEGER DEFAULT 5,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS discovery_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_type TEXT,
            source_url TEXT,
            location_name TEXT,
            location_raw TEXT,
            lat REAL,
            lon REAL,
            target_id TEXT,
            action TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''')
        
        c.execute('''CREATE INDEX IF NOT EXISTS idx_targets_category ON targets(category)''')
        c.execute('''CREATE INDEX IF NOT EXISTS idx_targets_province ON targets(province)''')
        c.execute('''CREATE INDEX IF NOT EXISTS idx_targets_active ON targets(active)''')
        
        conn.commit()
        conn.close()
    
    def get_all_targets(self, active_only=True, category=None, province=None):
        """Get all targets as dict (keyed by id)."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        query = 'SELECT * FROM targets WHERE 1=1'
        params = []
        
        if active_only:
            query += ' AND active = 1'
        if category:
            query += ' AND category = ?'
            params.append(category)
        if province:
            query += ' AND province = ?'
            params.append(province)
        
        c.execute(query, params)
        rows = c.fetchall()
        conn.close()
        
        targets = {}
        for row in rows:
            d = 0.03
            targets[row['id']] = {
                'name': row['name'],
                'type': row['type'],
                'category': row['category'],
                'lat': row['lat'],
                'lon': row['lon'],
                'bbox': json.loads(row['bbox']) if row['bbox'] else [row['lon']-d, row['lat']-d, row['lon']+d, row['lat']+d],
                'description': row['description'] or row['name'],
                'keywords': json.loads(row['keywords']) if row['keywords'] else [row['name'].lower()],
                'province': row['province'],
                'source': row['source'],
                'priority': row['priority'],
                'strike_count': row['strike_count'],
                'satellite_images_count': row['satellite_images_count']
            }
        return targets
    
    def get_targets_list(self, active_only=True, category=None, province=None):
        """Get targets as a list (for API responses)."""
        targets_dict = self.get_all_targets(active_only, category, province)
        return [{'id': k, **v} for k, v in targets_dict.items()]
    
    def get_target_count(self):
        """Get total count of active targets."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM targets WHERE active = 1')
        count = c.fetchone()[0]
        conn.close()
        return count
    
    def add_target(self, target_id, name, lat, lon, target_type='unknown', 
                   category='unknown', province='Unknown', description=None,
                   keywords=None, source='manual', priority=5, silent=False):
        """Add a new target to the database."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        d = 0.03
        bbox = json.dumps([lon-d, lat-d, lon+d, lat+d])
        kw = json.dumps(keywords if keywords else [name.lower()])
        
        try:
            c.execute('''INSERT OR REPLACE INTO targets 
                (id, name, type, category, lat, lon, bbox, description, 
                 keywords, province, source, discovered_date, priority)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (target_id, name, target_type, category, lat, lon, bbox,
                 description or name, kw, province, source, 
                 datetime.now().isoformat(), priority))
            conn.commit()
            if not silent:
                print(f'[TargetManager] Added target: {target_id} ({name})')
            return True
        except Exception as e:
            print(f'[TargetManager] Error adding target: {e}')
            return False
        finally:
            conn.close()
    
    def update_target(self, target_id, **kwargs):
        """Update target fields."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        valid_fields = ['name', 'type', 'category', 'lat', 'lon', 'description',
                        'province', 'priority', 'active', 'strike_count',
                        'last_satellite_check', 'satellite_images_count']
        
        updates = []
        params = []
        for k, v in kwargs.items():
            if k in valid_fields:
                updates.append(f'{k} = ?')
                params.append(v)
        
        if not updates:
            conn.close()
            return False
        
        params.append(datetime.now().isoformat())
        params.append(target_id)
        
        c.execute(f'''UPDATE targets SET {', '.join(updates)}, updated_at = ? WHERE id = ?''', params)
        conn.commit()
        conn.close()
        return True
    
    def delete_target(self, target_id, soft=True):
        """Delete or deactivate a target."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        if soft:
            c.execute('UPDATE targets SET active = 0, updated_at = ? WHERE id = ?',
                      (datetime.now().isoformat(), target_id))
        else:
            c.execute('DELETE FROM targets WHERE id = ?', (target_id,))
        conn.commit()
        conn.close()
        return True
    
    def target_exists(self, target_id):
        """Check if target exists."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT id FROM targets WHERE id = ?', (target_id,))
        exists = c.fetchone() is not None
        conn.close()
        return exists
    
    def get_target(self, target_id):
        """Get a single target by ID."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT * FROM targets WHERE id = ?', (target_id,))
        row = c.fetchone()
        conn.close()
        if row:
            d = 0.03
            return {
                'id': row['id'],
                'name': row['name'],
                'type': row['type'],
                'category': row['category'],
                'lat': row['lat'],
                'lon': row['lon'],
                'bbox': json.loads(row['bbox']) if row['bbox'] else [row['lon']-d, row['lat']-d, row['lon']+d, row['lat']+d],
                'description': row['description'] or row['name'],
                'keywords': json.loads(row['keywords']) if row['keywords'] else [row['name'].lower()],
                'province': row['province'],
                'source': row['source'],
                'priority': row['priority'],
                'strike_count': row['strike_count']
            }
        return None
    
    def increment_strike_count(self, target_id):
        """Increment the strike count for a target."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('UPDATE targets SET strike_count = strike_count + 1, updated_at = ? WHERE id = ?',
                  (datetime.now().isoformat(), target_id))
        conn.commit()
        conn.close()
    
    def log_discovery(self, source_type, source_url, location_name, 
                      lat, lon, target_id=None, action='discovered'):
        """Log a discovery event."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''INSERT INTO discovery_log 
            (source_type, source_url, location_name, lat, lon, target_id, action)
            VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (source_type, source_url, location_name, lat, lon, target_id, action))
        conn.commit()
        conn.close()
    
    def get_discovery_log(self, limit=50):
        """Get recent discovery log entries."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT * FROM discovery_log ORDER BY created_at DESC LIMIT ?', (limit,))
        rows = c.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_new_targets_needing_satellite(self, limit=10):
        """Get targets that haven't been checked by satellite yet."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('''SELECT * FROM targets 
                     WHERE active = 1 AND (last_satellite_check IS NULL OR satellite_images_count = 0)
                     ORDER BY priority DESC, created_at DESC
                     LIMIT ?''', (limit,))
        rows = c.fetchall()
        conn.close()
        return [dict(row) for row in rows]


# Iranian provinces and major cities for geocoding
IRAN_LOCATIONS = {
    'tehran': {'lat': 35.6892, 'lon': 51.3890, 'province': 'Tehran'},
    'isfahan': {'lat': 32.6546, 'lon': 51.6680, 'province': 'Isfahan'},
    'shiraz': {'lat': 29.5918, 'lon': 52.5837, 'province': 'Fars'},
    'mashhad': {'lat': 36.2605, 'lon': 59.6168, 'province': 'Khorasan'},
    'tabriz': {'lat': 38.0800, 'lon': 46.2919, 'province': 'Azerbaijan'},
    'ahvaz': {'lat': 31.3183, 'lon': 48.6706, 'province': 'Khuzestan'},
    'karaj': {'lat': 35.8400, 'lon': 50.9391, 'province': 'Alborz'},
    'qom': {'lat': 34.6416, 'lon': 50.8746, 'province': 'Qom'},
    'kermanshah': {'lat': 34.3142, 'lon': 47.0650, 'province': 'Kermanshah'},
    'yazd': {'lat': 31.8974, 'lon': 54.3569, 'province': 'Yazd'},
    'bandar abbas': {'lat': 27.1865, 'lon': 56.2808, 'province': 'Hormozgan'},
    'bushehr': {'lat': 28.9234, 'lon': 50.8203, 'province': 'Bushehr'},
    'natanz': {'lat': 33.5100, 'lon': 51.9200, 'province': 'Isfahan'},
    'arak': {'lat': 34.0917, 'lon': 49.6892, 'province': 'Markazi'},
    'parchin': {'lat': 35.5200, 'lon': 51.7700, 'province': 'Tehran'},
    'fordow': {'lat': 34.8833, 'lon': 51.0000, 'province': 'Qom'},
    'semnan': {'lat': 35.5769, 'lon': 53.3975, 'province': 'Semnan'},
    'dezful': {'lat': 32.3811, 'lon': 48.4053, 'province': 'Khuzestan'},
    'abadan': {'lat': 30.3392, 'lon': 48.2973, 'province': 'Khuzestan'},
    'esfahan': {'lat': 32.6546, 'lon': 51.6680, 'province': 'Isfahan'},
    'esfehan': {'lat': 32.6546, 'lon': 51.6680, 'province': 'Isfahan'},
    'khorramshahr': {'lat': 30.4267, 'lon': 48.1667, 'province': 'Khuzestan'},
    'bandar lengeh': {'lat': 26.5575, 'lon': 54.8808, 'province': 'Hormozgan'},
    'chabahar': {'lat': 25.2919, 'lon': 60.6430, 'province': 'Sistan'},
    'kerman': {'lat': 30.2839, 'lon': 57.0834, 'province': 'Kerman'},
    'rasht': {'lat': 37.2808, 'lon': 49.5832, 'province': 'Gilan'},
    'hamadan': {'lat': 34.7992, 'lon': 48.5150, 'province': 'Hamadan'},
    'sanandaj': {'lat': 35.3117, 'lon': 46.9986, 'province': 'Kurdistan'},
    'urmia': {'lat': 37.5527, 'lon': 45.0761, 'province': 'West Azerbaijan'},
    'khoy': {'lat': 38.5500, 'lon': 44.9500, 'province': 'West Azerbaijan'},
}


class LocationExtractor:
    """Extract and geocode locations from news articles."""
    
    # Patterns to find location references
    LOCATION_PATTERNS = [
        r'(?:attack|strike|hit|target|bomb|explosion|blast)(?:ed|ing|s)?\s+(?:on|at|in|near)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:was|were|has been)\s+(?:hit|struck|attacked|bombed|targeted)',
        r'(?:in|near|at)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),?\s+Iran',
        r'Iranian\s+(?:city|town|base|facility|site)\s+(?:of|in)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'(?:military|air|nuclear|missile)\s+(?:base|facility|site|complex)\s+(?:in|at|near)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'Iran[\'s]*\s+([A-Z][a-z]+)\s+(?:nuclear|missile|military|air)',
    ]
    
    # Facility type patterns
    FACILITY_PATTERNS = {
        'nuclear': r'nuclear|enrichment|centrifuge|uranium|plutonium|reactor',
        'missile': r'missile|rocket|ballistic|icbm|launcher|warhead',
        'airbase': r'air\s*base|airfield|air\s*force|fighter|jet|aircraft|f-\d+',
        'naval': r'naval|navy|port|ship|submarine|destroyer|frigate',
        'refinery': r'refinery|oil|petroleum|petrochem|gas\s*plant|lng',
        'military': r'military|army|irgc|guard|barracks|garrison|base',
        'radar': r'radar|air\s*defense|sam|s-300|s-400|anti-aircraft|tor-m|bavar',
        'command': r'headquarters|command|control|intelligence|ministry',
        'drone': r'drone|uav|shahed|ababil|mohajer',
        'research': r'research|development|lab|laboratory|tech|technology',
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'IranDamageAssessment/5.0'})
    
    def extract_locations(self, text):
        """Extract location names from article text."""
        locations = set()
        for pattern in self.LOCATION_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                loc = match.strip()
                if len(loc) > 2 and loc.lower() not in ['the', 'and', 'iran', 'iranian', 'israel', 'israeli', 'its', 'has', 'have', 'been', 'are', 'was', 'were']:
                    locations.add(loc)
        return list(locations)
    
    def detect_facility_type(self, text):
        """Detect what type of facility is mentioned."""
        text_lower = text.lower()
        for ftype, pattern in self.FACILITY_PATTERNS.items():
            if re.search(pattern, text_lower):
                return ftype
        return 'unknown'
    
    def geocode_location(self, location_name):
        """
        Geocode a location in Iran using Nominatim.
        Returns: {'lat': float, 'lon': float, 'province': str} or None
        """
        # First check our known locations
        name_lower = location_name.lower().strip()
        if name_lower in IRAN_LOCATIONS:
            return IRAN_LOCATIONS[name_lower]
        
        # Try Nominatim geocoding (free, no API key)
        try:
            import time
            time.sleep(1)  # Rate limit for Nominatim
            url = 'https://nominatim.openstreetmap.org/search'
            params = {
                'q': f'{location_name}, Iran',
                'format': 'json',
                'limit': 1,
                'countrycodes': 'ir'
            }
            resp = self.session.get(url, params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data:
                    lat = float(data[0]['lat'])
                    lon = float(data[0]['lon'])
                    # Check if coordinates are within Iran bounds
                    if 25 <= lat <= 40 and 44 <= lon <= 64:
                        display = data[0].get('display_name', '')
                        province = 'Unknown'
                        for city, info in IRAN_LOCATIONS.items():
                            if city in display.lower():
                                province = info['province']
                                break
                        return {'lat': lat, 'lon': lon, 'province': province}
        except Exception as e:
            print(f'[LocationExtractor] Geocoding error: {e}')
        
        return None


class AutoDiscovery:
    """
    Automatically discovers new attack targets from OSINT sources.
    - Scans GDELT for Iran attack news
    - Scans social media (Twitter, Reddit, Telegram)
    - Extracts location mentions
    - Geocodes new locations
    - Adds them to targets database
    """
    
    DISCOVERY_QUERIES = [
        'Iran attack strike military',
        'Israel strike Iran base',
        'Iran nuclear facility attack',
        'Iran missile site strike',
        'Iran refinery explosion attack',
        'IRGC base attacked',
        'Iran air defense strike',
        'Iran military installation hit',
        'Iran drone factory strike',
        'Iran weapons facility',
    ]
    
    def __init__(self, target_manager):
        self.tm = target_manager
        self.extractor = LocationExtractor()
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'IranDamageAssessment/5.0 AutoDiscovery'})
        self._social_osint = None
    
    @property
    def social_osint(self):
        """Lazy load social media OSINT scanner."""
        if self._social_osint is None:
            try:
                from .social_osint import SocialOSINT
                self._social_osint = SocialOSINT()
            except ImportError:
                self._social_osint = None
        return self._social_osint
    
    def scan_for_new_targets(self, max_records=50, num_queries=4):
        """
        Scan GDELT AND social media for articles and discover new target locations.
        Returns list of newly added targets.
        """
        import time
        new_targets = []
        
        # 1. Scan Social Media FIRST (faster, more real-time)
        social_targets = self._scan_social_media()
        new_targets.extend(social_targets)
        
        # 2. Scan GDELT news (slower but more comprehensive)
        gdelt_targets = self._scan_gdelt(max_records, num_queries)
        new_targets.extend(gdelt_targets)
        
        print(f'[AutoDiscovery] Total new targets discovered: {len(new_targets)}')
        return new_targets
    
    def _scan_social_media(self):
        """Scan social media for new targets."""
        new_targets = []
        
        if not self.social_osint:
            print('[AutoDiscovery] Social OSINT module not available')
            return new_targets
        
        try:
            print('[AutoDiscovery] Scanning social media (Twitter, Reddit, RSS)...')
            incidents = self.social_osint.scan_all_sources(hours_back=24)
            print(f'[AutoDiscovery] Found {len(incidents)} social media incidents')
            
            for incident in incidents:
                lat = incident.get('lat')
                lon = incident.get('lon')
                location = incident.get('location', 'Unknown')
                
                if not lat or not lon:
                    continue
                
                # Generate target ID from location
                target_id = self._generate_target_id(f"incident_{location}")
                
                # Check if similar target exists nearby
                if self._has_nearby_target(lat, lon, radius_km=5):
                    continue
                
                if not self.tm.target_exists(target_id):
                    incident_type = incident.get('type', 'unknown')
                    
                    self.tm.add_target(
                        target_id=target_id,
                        name=f"{location} Incident",
                        lat=lat,
                        lon=lon,
                        target_type=incident_type,
                        category=incident_type,
                        province=incident.get('province', 'Unknown'),
                        description=f"Social media incident: {incident.get('text', '')[:150]}",
                        keywords=[location.lower(), incident_type],
                        source=f"social_{incident.get('source', 'unknown')}",
                        priority=8  # Higher priority for live incidents
                    )
                    
                    self.tm.log_discovery(
                        source_type=f"social_{incident.get('source', '')}",
                        source_url=incident.get('url', ''),
                        location_name=location,
                        lat=lat,
                        lon=lon,
                        target_id=target_id,
                        action='social_discovered'
                    )
                    
                    new_targets.append({
                        'id': target_id,
                        'name': f"{location} Incident",
                        'lat': lat,
                        'lon': lon,
                        'type': incident_type,
                        'source': incident.get('source'),
                    })
                    print(f'[AutoDiscovery] NEW from social: {location} ({incident_type})')
        
        except Exception as e:
            print(f'[AutoDiscovery] Social media scan error: {e}')
            import traceback
            traceback.print_exc()
        
        return new_targets
    
    def _has_nearby_target(self, lat, lon, radius_km=2):
        """Check if there's already a target within radius_km of this location.
        Reduced to 2km to allow more fine-grained target discovery."""
        try:
            existing = self.tm.get_all_targets()
            for target in existing:
                tlat = target.get('lat', 0)
                tlon = target.get('lon', 0)
                # Simple distance approximation (1 degree ≈ 111km)
                dlat = abs(lat - tlat) * 111
                dlon = abs(lon - tlon) * 111 * 0.7  # cos(35°) for Iran
                if (dlat**2 + dlon**2)**0.5 < radius_km:
                    return True
        except:
            pass
        return False
    
    def _scan_gdelt(self, max_records=50, num_queries=4):
        """Scan GDELT for new targets."""
        import time
        new_targets = []
        seen_locations = set()
        
        for query in self.DISCOVERY_QUERIES[:num_queries]:
            try:
                articles = self._gdelt_search(query, max_records)
                print(f'[AutoDiscovery] Query "{query}": {len(articles)} articles')
                
                for article in articles:
                    title = article.get('title', '')
                    # Extract locations from title
                    locations = self.extractor.extract_locations(title)
                    
                    for loc in locations:
                        if loc.lower() in seen_locations:
                            continue
                        seen_locations.add(loc.lower())
                        
                        # Try to geocode
                        coords = self.extractor.geocode_location(loc)
                        if coords:
                            # Generate target ID
                            target_id = self._generate_target_id(loc)
                            
                            # Check if already exists
                            if not self.tm.target_exists(target_id):
                                ftype = self.extractor.detect_facility_type(title)
                                
                                self.tm.add_target(
                                    target_id=target_id,
                                    name=loc,
                                    lat=coords['lat'],
                                    lon=coords['lon'],
                                    target_type=ftype,
                                    category=ftype,
                                    province=coords['province'],
                                    description=f'Auto-discovered from: {title[:100]}',
                                    keywords=[loc.lower()],
                                    source='osint_auto',
                                    priority=7
                                )
                                
                                self.tm.log_discovery(
                                    source_type='gdelt',
                                    source_url=article.get('url', ''),
                                    location_name=loc,
                                    lat=coords['lat'],
                                    lon=coords['lon'],
                                    target_id=target_id,
                                    action='auto_added'
                                )
                                
                                new_targets.append({
                                    'id': target_id,
                                    'name': loc,
                                    'lat': coords['lat'],
                                    'lon': coords['lon'],
                                    'type': ftype,
                                    'source_article': article.get('url')
                                })
                                print(f'[AutoDiscovery] NEW TARGET: {target_id} ({loc}) at {coords["lat"]:.4f}, {coords["lon"]:.4f}')
                
                time.sleep(6)  # GDELT rate limit
                
            except Exception as e:
                print(f'[AutoDiscovery] Error scanning: {e}')
                import traceback
                traceback.print_exc()
                time.sleep(5)
        
        return new_targets
    
    def _gdelt_search(self, query, max_records=50):
        """Search GDELT for articles."""
        import time
        try:
            encoded = quote(query)
            url = f'https://api.gdeltproject.org/api/v2/doc/doc?query={encoded}&mode=ArtList&maxrecords={max_records}&format=json&sort=datedesc&timespan=3months'
            
            for attempt in range(3):
                resp = self.session.get(url, timeout=20)
                if resp.status_code == 429 or 'Please limit' in resp.text:
                    time.sleep(10 + attempt * 5)
                    continue
                if resp.status_code == 200:
                    try:
                        return resp.json().get('articles', [])
                    except:
                        return []
                time.sleep(5)
        except Exception as e:
            print(f'[AutoDiscovery] GDELT error: {e}')
        return []
    
    def _generate_target_id(self, name):
        """Generate a unique target ID from name."""
        clean = re.sub(r'[^a-z0-9]+', '_', name.lower().strip())
        return f'auto_{clean}'


def migrate_hardcoded_targets(target_manager):
    """
    Migrate the 217 hardcoded KNOWN_TARGETS to the database.
    Fast check: if DB has targets, skip migration entirely.
    """
    try:
        # Quick check: if we already have targets, skip migration
        existing_count = target_manager.get_target_count()
        if existing_count >= 200:  # Most targets already imported
            return 0
        
        try:
            from .osint_engine import KNOWN_TARGETS
        except ImportError:
            try:
                from src.osint.osint_engine import KNOWN_TARGETS
            except ImportError:
                print("⚠️ Could not import KNOWN_TARGETS for migration")
                return 0
        
        count = 0
        for target_id, target in KNOWN_TARGETS.items():
            if not target_manager.target_exists(target_id):
                target_manager.add_target(
                    target_id=target_id,
                    name=target['name'],
                    lat=target['lat'],
                    lon=target['lon'],
                    target_type=target['type'],
                    category=target['category'],
                    province=target['province'],
                    description=target.get('description', target['name']),
                    keywords=target.get('keywords', [target['name'].lower()]),
                    source='initial_hardcoded',
                    priority=5,
                    silent=True  # Don't log each add
                )
                count += 1
        
        if count > 0:
            print(f'[Migration] Imported {count} new targets')
        return count
    except Exception as e:
        print(f'[Migration] Error: {e}')
        return 0


def migrate_all_iran_locations(target_manager):
    """
    Import ALL Iranian cities and infrastructure - 400+ locations.
    This makes the system comprehensive like mahsaalert.com.
    """
    try:
        # Quick check: if we already have 300+ targets, skip
        existing_count = target_manager.get_target_count()
        if existing_count >= 400:
            print(f'[Migration] Already have {existing_count} targets, skipping mass import')
            return 0
        
        from src.data.iran_locations import generate_all_locations
        
        locations = generate_all_locations()
        count = 0
        
        for loc in locations:
            target_id = f"loc_{loc['name'].lower().replace(' ', '_').replace('-', '_')[:40]}"
            
            if not target_manager.target_exists(target_id):
                target_manager.add_target(
                    target_id=target_id,
                    name=loc['name'],
                    lat=loc['lat'],
                    lon=loc['lon'],
                    target_type=loc.get('type', 'city'),
                    category=loc.get('category', 'population_center'),
                    province=loc.get('province', 'Unknown'),
                    description=f"{loc['name']} - {loc.get('category', 'location')}",
                    keywords=[loc['name'].lower()],
                    source='iran_locations_db',
                    priority=loc.get('priority', 5),
                    silent=True
                )
                count += 1
        
        if count > 0:
            print(f'[Migration] Imported {count} Iranian locations (cities + infrastructure)')
        return count
    except Exception as e:
        print(f'[Migration] Location import error: {e}')
        import traceback
        traceback.print_exc()
        return 0


# Singleton instance
_target_manager = None

def get_target_manager():
    """Get or create the global TargetManager instance."""
    global _target_manager
    if _target_manager is None:
        _target_manager = TargetManager()
    return _target_manager


if __name__ == '__main__':
    # Test the system
    tm = get_target_manager()
    
    # Migrate existing targets
    print('Migrating hardcoded targets...')
    count = migrate_hardcoded_targets(tm)
    print(f'Migrated {count} targets')
    
    print(f'Total targets in DB: {tm.get_target_count()}')
    
    # Run auto-discovery
    print('\nRunning auto-discovery scan...')
    discovery = AutoDiscovery(tm)
    new_targets = discovery.scan_for_new_targets(max_records=25, num_queries=2)
    
    print(f'\nDiscovered {len(new_targets)} new targets')
    for t in new_targets:
        print(f'  - {t["name"]} ({t["type"]}): {t["lat"]:.4f}, {t["lon"]:.4f}')
    
    print(f'\nTotal targets now: {tm.get_target_count()}')
