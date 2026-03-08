"""
Early Warning System - CENTCOM/IDF Pre-Strike Monitoring
=========================================================
Monitors official military sources for pre-strike announcements
to provide evacuation warnings for civilians.

Sources monitored:
1. CENTCOM (US Central Command) official announcements
2. IDF (Israel Defense Forces) spokesperson
3. Major news agencies (Reuters, AP, AFP)
4. Twitter/X official military accounts (via RSS)

WARNING: This is for CIVILIAN SAFETY information only.
"""

import requests
import re
import json
import feedparser
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# ═══════════════════════════════════════════════════════════════════════
# OFFICIAL MILITARY SOURCES
# ═══════════════════════════════════════════════════════════════════════

# Twitter/X accounts to monitor (using multiple Nitter instances for reliability)
NITTER_INSTANCES = [
    'https://nitter.privacydev.net',
    'https://nitter.poast.org', 
    'https://nitter.woodland.cafe',
    'https://nitter.net',
    'https://nitter.cz',
    'https://nitter.1d4.us',
]

# THE THREE OFFICIAL ACCOUNTS TO MONITOR
TWITTER_ACCOUNTS = {
    # IDF - Israel Defense Forces Official
    'idf_official': {
        'handle': 'IDF',
        'name': 'Israel Defense Forces',
        'priority': 'critical',
        'keywords': ['iran', 'strike', 'operation', 'warning', 'civilian', 'attack', 'target', 
                     'isfahan', 'shiraz', 'tehran', 'nuclear', 'military', 'irgc', 'missile',
                     'air force', 'jets', 'bombs', 'פיקוד'],
    },
    # CENTCOM - US Central Command Official  
    'centcom_official': {
        'handle': 'CENTCOM',
        'name': 'US CENTCOM',
        'priority': 'critical',
        'keywords': ['iran', 'strike', 'operation', 'centcom', 'military action', 'target',
                     'isfahan', 'shiraz', 'tehran', 'middle east', 'persian gulf'],
    },
    # Vahid Online - Iranian journalist (critical local intel)
    'vahid_online': {
        'handle': 'Vahid',
        'name': 'Vahid Online',
        'priority': 'critical',
        'keywords': ['حمله', 'اصفهان', 'شیراز', 'تهران', 'strike', 'attack', 'explosion', 
                     'پدافند', 'موشک', 'israel', 'اسرائیل', 'انفجار', 'هشدار', 'بمباران',
                     'alert', 'warning', 'air defense', 'siren', 'آژیر'],
    },
}

# ═══════════════════════════════════════════════════════════════════════
# LOCATION DATABASE - For matching mentioned places to coordinates
# ═══════════════════════════════════════════════════════════════════════

IRAN_LOCATIONS = {
    # Oil & Energy facilities
    'shiraz oil depot': {'lat': 29.59, 'lon': 52.52, 'type': 'oil_depot', 'name': 'Shiraz Oil Depot'},
    'shiraz oil': {'lat': 29.59, 'lon': 52.52, 'type': 'oil_depot', 'name': 'Shiraz Oil Facility'},
    'isfahan refinery': {'lat': 32.62, 'lon': 51.67, 'type': 'refinery', 'name': 'Isfahan Oil Refinery'},
    'isfahan oil': {'lat': 32.62, 'lon': 51.67, 'type': 'refinery', 'name': 'Isfahan Oil Refinery'},
    'tehran refinery': {'lat': 35.54, 'lon': 51.42, 'type': 'refinery', 'name': 'Tehran Oil Refinery'},
    'abadan refinery': {'lat': 30.34, 'lon': 48.28, 'type': 'refinery', 'name': 'Abadan Refinery'},
    'bandar abbas oil': {'lat': 27.19, 'lon': 56.28, 'type': 'oil_terminal', 'name': 'Bandar Abbas Oil Terminal'},
    'kharg island': {'lat': 29.24, 'lon': 50.31, 'type': 'oil_terminal', 'name': 'Kharg Island Oil Terminal'},
    
    # Nuclear facilities
    'natanz': {'lat': 33.72, 'lon': 51.73, 'type': 'nuclear', 'name': 'Natanz Nuclear Facility'},
    'fordow': {'lat': 34.88, 'lon': 50.98, 'type': 'nuclear', 'name': 'Fordow Nuclear Facility'},
    'arak reactor': {'lat': 34.38, 'lon': 49.24, 'type': 'nuclear', 'name': 'Arak Heavy Water Reactor'},
    'bushehr nuclear': {'lat': 28.83, 'lon': 50.89, 'type': 'nuclear', 'name': 'Bushehr Nuclear Plant'},
    'isfahan nuclear': {'lat': 32.70, 'lon': 51.54, 'type': 'nuclear', 'name': 'Isfahan Nuclear Research Center'},
    
    # Military bases
    'isfahan air base': {'lat': 32.57, 'lon': 51.69, 'type': 'airbase', 'name': 'Isfahan 8th Tactical Air Base'},
    'shiraz air base': {'lat': 29.54, 'lon': 52.59, 'type': 'airbase', 'name': 'Shiraz Air Base'},
    'tehran air base': {'lat': 35.69, 'lon': 51.31, 'type': 'airbase', 'name': 'Mehrabad Air Base'},
    'parchin': {'lat': 35.52, 'lon': 51.77, 'type': 'military', 'name': 'Parchin Military Complex'},
    'khojir': {'lat': 35.56, 'lon': 51.85, 'type': 'missile', 'name': 'Khojir Missile Facility'},
    
    # Cities (fallback)
    'isfahan': {'lat': 32.65, 'lon': 51.67, 'type': 'city', 'name': 'Isfahan'},
    'shiraz': {'lat': 29.59, 'lon': 52.58, 'type': 'city', 'name': 'Shiraz'},
    'tehran': {'lat': 35.69, 'lon': 51.39, 'type': 'city', 'name': 'Tehran'},
    'tabriz': {'lat': 38.08, 'lon': 46.29, 'type': 'city', 'name': 'Tabriz'},
    'mashhad': {'lat': 36.31, 'lon': 59.60, 'type': 'city', 'name': 'Mashhad'},
    'bushehr': {'lat': 28.97, 'lon': 50.84, 'type': 'city', 'name': 'Bushehr'},
    'bandar abbas': {'lat': 27.19, 'lon': 56.28, 'type': 'city', 'name': 'Bandar Abbas'},
    'ahvaz': {'lat': 31.32, 'lon': 48.67, 'type': 'city', 'name': 'Ahvaz'},
    'kermanshah': {'lat': 34.31, 'lon': 47.07, 'type': 'city', 'name': 'Kermanshah'},
    
    # Persian names
    'اصفهان': {'lat': 32.65, 'lon': 51.67, 'type': 'city', 'name': 'Isfahan'},
    'شیراز': {'lat': 29.59, 'lon': 52.58, 'type': 'city', 'name': 'Shiraz'},
    'تهران': {'lat': 35.69, 'lon': 51.39, 'type': 'city', 'name': 'Tehran'},
    'تبریز': {'lat': 38.08, 'lon': 46.29, 'type': 'city', 'name': 'Tabriz'},
    'بوشهر': {'lat': 28.97, 'lon': 50.84, 'type': 'city', 'name': 'Bushehr'},
    'نطنز': {'lat': 33.72, 'lon': 51.73, 'type': 'nuclear', 'name': 'Natanz'},
    'پارچین': {'lat': 35.52, 'lon': 51.77, 'type': 'military', 'name': 'Parchin'},
}

OFFICIAL_SOURCES = {
    # US CENTCOM RSS
    'centcom': {
        'name': 'US Central Command',
        'rss': 'https://www.centcom.mil/MEDIA/PRESS-RELEASES/Press-Release-View/Article/rss/',
        'keywords': ['iran', 'isfahan', 'shiraz', 'tehran', 'strike', 'operation', 'target'],
        'priority': 'critical',
    },
    # Reuters Breaking
    'reuters': {
        'name': 'Reuters',
        'rss': 'https://feeds.reuters.com/reuters/worldNews',
        'keywords': ['iran strike', 'israel attack iran', 'centcom iran', 'isfahan', 'shiraz'],
        'priority': 'high',
    },
    # AP News
    'ap': {
        'name': 'Associated Press',
        'rss': 'https://rsshub.app/apnews/topics/world-news',
        'keywords': ['iran strike', 'israel iran', 'military operation iran'],
        'priority': 'high',
    },
}

# ═══════════════════════════════════════════════════════════════════════
# IRANIAN CITIES / AREAS FOR EVACUATION WARNINGS
# ═══════════════════════════════════════════════════════════════════════

EVACUATION_ZONES = {
    'isfahan': {
        'name': 'Isfahan',
        'name_fa': 'اصفهان',
        'lat': 32.6546,
        'lon': 51.6680,
        'radius_km': 15,
        'population': 2_000_000,
        'keywords': ['isfahan', 'esfahan', 'اصفهان', 'natanz', 'nuclear'],
        'facilities': ['Isfahan Nuclear Center', 'Natanz Enrichment', 'Isfahan Air Base', 'Mobarakeh Steel'],
    },
    'shiraz': {
        'name': 'Shiraz',
        'name_fa': 'شیراز',
        'lat': 29.5918,
        'lon': 52.5837,
        'radius_km': 10,
        'population': 1_900_000,
        'keywords': ['shiraz', 'شیراز', 'fars province'],
        'facilities': ['Shiraz Air Base', 'Fars Military Garrison'],
    },
    'tehran': {
        'name': 'Tehran',
        'name_fa': 'تهران',
        'lat': 35.6892,
        'lon': 51.3890,
        'radius_km': 20,
        'population': 9_000_000,
        'keywords': ['tehran', 'تهران', 'parchin', 'khojir', 'capital'],
        'facilities': ['Parchin Complex', 'Khojir Missile Site', 'Tehran Refinery'],
    },
    'bushehr': {
        'name': 'Bushehr',
        'name_fa': 'بوشهر',
        'lat': 28.9684,
        'lon': 50.8385,
        'radius_km': 15,
        'population': 250_000,
        'keywords': ['bushehr', 'بوشهر', 'nuclear plant', 'reactor'],
        'facilities': ['Bushehr Nuclear Power Plant'],
    },
    'tabriz': {
        'name': 'Tabriz',
        'name_fa': 'تبریز',
        'lat': 38.0800,
        'lon': 46.2919,
        'radius_km': 10,
        'population': 1_600_000,
        'keywords': ['tabriz', 'تبریز', 'east azerbaijan'],
        'facilities': ['Tabriz Air Base', 'Tabriz Refinery'],
    },
    'bandar_abbas': {
        'name': 'Bandar Abbas',
        'name_fa': 'بندرعباس',
        'lat': 27.1865,
        'lon': 56.2808,
        'radius_km': 10,
        'population': 500_000,
        'keywords': ['bandar abbas', 'بندرعباس', 'hormuz', 'strait', 'naval'],
        'facilities': ['Bandar Abbas Naval Base', 'IRGC Navy HQ'],
    },
}

# ═══════════════════════════════════════════════════════════════════════
# WARNING LEVELS
# ═══════════════════════════════════════════════════════════════════════

WARNING_LEVELS = {
    'IMMINENT': {
        'level': 5,
        'color': '#FF0000',
        'message_en': '⚠️ IMMEDIATE EVACUATION - Strike imminent (0-30 min)',
        'message_fa': '⚠️ تخلیه فوری - حمله قریب‌الوقوع',
        'action': 'LEAVE IMMEDIATELY - Move 10+ km from military/industrial areas',
    },
    'WARNING': {
        'level': 4,
        'color': '#FF6600',
        'message_en': '🔶 WARNING - Prepare to evacuate (30-60 min)',
        'message_fa': '🔶 هشدار - آماده تخلیه شوید',
        'action': 'Prepare to leave - gather essentials, identify safe routes',
    },
    'ALERT': {
        'level': 3,
        'color': '#FFCC00',
        'message_en': '🟡 ALERT - Military activity reported (1-3 hours)',
        'message_fa': '🟡 هشدار - فعالیت نظامی گزارش شده',
        'action': 'Stay informed - monitor official channels',
    },
    'WATCH': {
        'level': 2,
        'color': '#00CCFF',
        'message_en': '🔵 WATCH - Elevated threat level',
        'message_fa': '🔵 مراقبت - سطح تهدید بالا',
        'action': 'Be aware of surroundings, know evacuation routes',
    },
}


class EarlyWarningSystem:
    """
    Monitors military sources for pre-strike announcements
    and generates evacuation warnings for civilians.
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.active_warnings = []
        self.last_check = None
        self.working_nitter = None  # Cache working Nitter instance
    
    def _find_working_nitter(self) -> Optional[str]:
        """Find a working Nitter instance for Twitter scraping."""
        if self.working_nitter:
            return self.working_nitter
        
        for instance in NITTER_INSTANCES:
            try:
                resp = self.session.get(f"{instance}/IDF/rss", timeout=5)
                if resp.status_code == 200 and '<rss' in resp.text:
                    self.working_nitter = instance
                    print(f"[TWITTER] Using Nitter instance: {instance}")
                    return instance
            except:
                continue
        
        print("[TWITTER] No working Nitter instance found")
        return None
    
    def check_all_sources(self) -> List[Dict]:
        """
        Check all official sources for strike-related announcements.
        Returns list of potential warnings.
        """
        warnings = []
        
        # 1. Check Twitter/X accounts (IDF, Pentagon, Vahid Online)
        twitter_warnings = self._check_twitter_accounts()
        warnings.extend(twitter_warnings)
        
        # 2. Check RSS feeds (CENTCOM, Reuters, AP)
        for source_id, source in OFFICIAL_SOURCES.items():
            try:
                rss_url = source.get('rss') or source.get('twitter_rss')
                if rss_url:
                    feed_warnings = self._check_rss_feed(source_id, source, rss_url)
                    warnings.extend(feed_warnings)
            except Exception as e:
                print(f"[WARNING] Error checking {source_id}: {e}")
        
        # 3. Check GDELT for urgent news
        gdelt_warnings = self._check_gdelt_urgent()
        warnings.extend(gdelt_warnings)
        
        self.last_check = datetime.now().isoformat()
        return warnings
    
    def _check_twitter_accounts(self) -> List[Dict]:
        """Check Twitter/X accounts via Nitter RSS."""
        warnings = []
        
        nitter = self._find_working_nitter()
        if not nitter:
            # Try direct scraping as fallback
            print("[TWITTER] Nitter unavailable, trying RSSHub fallback...")
            return self._check_twitter_rsshub()
        
        for account_id, account in TWITTER_ACCOUNTS.items():
            try:
                handle = account['handle']
                rss_url = f"{nitter}/{handle}/rss"
                
                resp = self.session.get(rss_url, timeout=10)
                if resp.status_code != 200:
                    continue
                
                feed = feedparser.parse(resp.text)
                keywords = account.get('keywords', [])
                
                for entry in feed.entries[:15]:  # Check latest 15 tweets
                    title = entry.get('title', '')
                    description = entry.get('description', '')
                    content = (title + ' ' + description).lower()
                    link = entry.get('link', f"https://twitter.com/{handle}")
                    
                    # Check if any keywords match
                    matched_keywords = [kw for kw in keywords if kw.lower() in content]
                    
                    if matched_keywords:
                        # Extract exact location coordinates from text
                        location_data = self._extract_location_coordinates(content)
                        
                        # Extract video URLs from description
                        video_urls = self._extract_video_urls(description, link)
                        
                        # Determine which cities are mentioned
                        affected_zones = self._extract_affected_zones(content)
                        
                        # Use extracted location or fall back to zone
                        target_location = location_data if location_data else None
                        
                        # For critical military accounts, create warning even without specific zone
                        if affected_zones or account.get('priority') == 'critical':
                            # If no specific zone but mentions Iran, add all zones as "potential"
                            if not affected_zones and 'iran' in content:
                                affected_zones = [{
                                    'zone_id': 'isfahan',
                                    'name': 'Isfahan',
                                    'name_fa': 'اصفهان',
                                    'lat': EVACUATION_ZONES['isfahan']['lat'],
                                    'lon': EVACUATION_ZONES['isfahan']['lon'],
                                    'radius_km': EVACUATION_ZONES['isfahan']['radius_km'],
                                    'population': EVACUATION_ZONES['isfahan']['population'],
                                    'facilities': EVACUATION_ZONES['isfahan']['facilities'],
                                }]
                            
                            if affected_zones:
                                warning = self._create_warning(
                                    source_id=account_id,
                                    source_name=f"𝕏 @{handle} ({account['name']})",
                                    title=title[:200],
                                    url=link,
                                    published=entry.get('published', ''),
                                    affected_zones=affected_zones,
                                    priority=account.get('priority', 'high'),
                                    matched_keywords=matched_keywords,
                                    target_location=target_location,
                                    video_urls=video_urls,
                                )
                                warnings.append(warning)
                                print(f"[TWITTER] ⚠️ @{handle}: {title[:60]}...")
                                if video_urls:
                                    print(f"[TWITTER] 🎥 Video found: {video_urls[0][:50]}...")
                                if target_location:
                                    print(f"[TWITTER] 📍 Location: {target_location['name']} ({target_location['lat']}, {target_location['lon']})")
                
                import time
                time.sleep(1)  # Rate limit between accounts
                
            except Exception as e:
                print(f"[TWITTER] Error checking @{account.get('handle', account_id)}: {e}")
        
        return warnings
    
    def _check_twitter_rsshub(self) -> List[Dict]:
        """Fallback: Check Twitter via RSSHub."""
        warnings = []
        rsshub_instances = [
            'https://rsshub.app',
            'https://rsshub.rssforever.com',
        ]
        
        for instance in rsshub_instances:
            try:
                for account_id, account in TWITTER_ACCOUNTS.items():
                    handle = account['handle']
                    rss_url = f"{instance}/twitter/user/{handle}"
                    
                    resp = self.session.get(rss_url, timeout=10)
                    if resp.status_code == 200:
                        feed = feedparser.parse(resp.text)
                        keywords = account.get('keywords', [])
                        
                        for entry in feed.entries[:10]:
                            content = (entry.get('title', '') + ' ' + entry.get('description', '')).lower()
                            matched = [kw for kw in keywords if kw.lower() in content]
                            
                            if matched:
                                affected_zones = self._extract_affected_zones(content)
                                location_data = self._extract_location_coordinates(content)
                                video_urls = self._extract_video_urls(entry.get('description', ''), entry.get('link', ''))
                                
                                if affected_zones or ('iran' in content and account.get('priority') == 'critical'):
                                    if not affected_zones:
                                        affected_zones = [{'zone_id': 'iran_general', 'name': 'Iran', 'name_fa': 'ایران', 
                                                          'lat': 32.0, 'lon': 53.0, 'radius_km': 50, 'population': 0, 'facilities': []}]
                                    
                                    warning = self._create_warning(
                                        source_id=account_id,
                                        source_name=f"𝕏 @{handle}",
                                        title=entry.get('title', '')[:200],
                                        url=entry.get('link', ''),
                                        published=entry.get('published', ''),
                                        affected_zones=affected_zones,
                                        priority=account.get('priority', 'high'),
                                        matched_keywords=matched,
                                        target_location=location_data,
                                        video_urls=video_urls,
                                    )
                                    warnings.append(warning)
                    
                    import time
                    time.sleep(1)
                
                if warnings:
                    return warnings
                    
            except Exception as e:
                print(f"[RSSHUB] Error with {instance}: {e}")
        
        return warnings
    
    def _extract_location_coordinates(self, text: str) -> Optional[Dict]:
        """Extract exact coordinates for mentioned locations."""
        text_lower = text.lower()
        
        # Check specific locations first (more precise)
        for location_key, location_data in IRAN_LOCATIONS.items():
            if location_key.lower() in text_lower:
                return {
                    'name': location_data['name'],
                    'lat': location_data['lat'],
                    'lon': location_data['lon'],
                    'type': location_data['type'],
                }
        
        return None
    
    def _extract_video_urls(self, html_content: str, tweet_url: str) -> List[str]:
        """Extract video URLs from tweet content."""
        video_urls = []
        
        # Look for video indicators in Nitter HTML
        video_patterns = [
            r'video src="([^"]+)"',
            r'<source src="([^"]+)"',
            r'https://video\.twimg\.com/[^\s"<>]+',
            r'https://pbs\.twimg\.com/[^\s"<>]+\.mp4',
        ]
        
        for pattern in video_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            video_urls.extend(matches)
        
        # If tweet URL exists and no video found, create embed URL
        if not video_urls and tweet_url and 'twitter.com' in tweet_url:
            # Twitter embed URL (will show video if exists)
            video_urls.append(tweet_url)
        
        return list(set(video_urls))[:3]  # Max 3 videos
    
    def _check_rss_feed(self, source_id: str, source: Dict, rss_url: str) -> List[Dict]:
        """Parse RSS feed for strike-related content."""
        warnings = []
        
        try:
            feed = feedparser.parse(rss_url)
            keywords = source.get('keywords', [])
            
            for entry in feed.entries[:10]:  # Check latest 10 entries
                title = entry.get('title', '').lower()
                summary = entry.get('summary', '').lower()
                content = title + ' ' + summary
                
                # Check if any keywords match
                matched_keywords = [kw for kw in keywords if kw.lower() in content]
                
                if matched_keywords:
                    # Determine which cities are mentioned
                    affected_zones = self._extract_affected_zones(content)
                    
                    if affected_zones:
                        warning = self._create_warning(
                            source_id=source_id,
                            source_name=source['name'],
                            title=entry.get('title', ''),
                            url=entry.get('link', ''),
                            published=entry.get('published', ''),
                            affected_zones=affected_zones,
                            priority=source.get('priority', 'medium'),
                            matched_keywords=matched_keywords,
                        )
                        warnings.append(warning)
        
        except Exception as e:
            print(f"[WARNING] RSS parse error for {source_id}: {e}")
        
        return warnings
    
    def _check_gdelt_urgent(self) -> List[Dict]:
        """Check GDELT for urgent Iran strike news."""
        warnings = []
        
        urgent_queries = [
            'centcom iran strike',
            'idf warns iran',
            'israel attack iran imminent',
            'evacuate isfahan',
            'evacuate shiraz',
        ]
        
        for query in urgent_queries:
            try:
                url = f"https://api.gdeltproject.org/api/v2/doc/doc?query={query}&mode=artlist&maxrecords=5&format=json"
                resp = self.session.get(url, timeout=10)
                
                if resp.status_code == 200:
                    data = resp.json()
                    articles = data.get('articles', [])
                    
                    for article in articles:
                        # Check if article is recent (within 2 hours)
                        pub_date = article.get('seendate', '')
                        if self._is_recent(pub_date, hours=2):
                            affected_zones = self._extract_affected_zones(
                                article.get('title', '') + ' ' + article.get('url', '')
                            )
                            
                            if affected_zones:
                                warning = self._create_warning(
                                    source_id='gdelt',
                                    source_name='GDELT News',
                                    title=article.get('title', ''),
                                    url=article.get('url', ''),
                                    published=pub_date,
                                    affected_zones=affected_zones,
                                    priority='high',
                                    matched_keywords=[query],
                                )
                                warnings.append(warning)
                
                import time
                time.sleep(2)  # Rate limit
                
            except Exception as e:
                print(f"[WARNING] GDELT urgent check error: {e}")
        
        return warnings
    
    def _extract_affected_zones(self, text: str) -> List[Dict]:
        """Extract which evacuation zones are mentioned in text."""
        text_lower = text.lower()
        affected = []
        
        for zone_id, zone in EVACUATION_ZONES.items():
            for keyword in zone['keywords']:
                if keyword.lower() in text_lower:
                    affected.append({
                        'zone_id': zone_id,
                        'name': zone['name'],
                        'name_fa': zone['name_fa'],
                        'lat': zone['lat'],
                        'lon': zone['lon'],
                        'radius_km': zone['radius_km'],
                        'population': zone['population'],
                        'facilities': zone['facilities'],
                    })
                    break  # Only add each zone once
        
        return affected
    
    def _create_warning(self, source_id: str, source_name: str, title: str,
                       url: str, published: str, affected_zones: List[Dict],
                       priority: str, matched_keywords: List[str],
                       target_location: Optional[Dict] = None,
                       video_urls: Optional[List[str]] = None) -> Dict:
        """Create a warning object with location and video data."""
        
        # Determine warning level based on priority and keywords
        if any(kw in title.lower() for kw in ['imminent', 'immediate', 'now', '30 min', 'evacuate']):
            level = 'IMMINENT'
        elif any(kw in title.lower() for kw in ['warning', 'prepare', 'alert']):
            level = 'WARNING'
        elif priority == 'critical':
            level = 'ALERT'
        else:
            level = 'WATCH'
        
        level_info = WARNING_LEVELS[level]
        
        # Use target_location for precise map marker, or first zone
        map_marker = None
        if target_location:
            map_marker = {
                'lat': target_location['lat'],
                'lon': target_location['lon'],
                'name': target_location['name'],
                'type': target_location.get('type', 'unknown'),
            }
        elif affected_zones:
            map_marker = {
                'lat': affected_zones[0]['lat'],
                'lon': affected_zones[0]['lon'],
                'name': affected_zones[0]['name'],
                'type': 'zone',
            }
        
        return {
            'id': f"warn_{hash(title + url) % 100000}",
            'source_id': source_id,
            'source_name': source_name,
            'title': title,
            'url': url,
            'published': published,
            'detected_at': datetime.now().isoformat(),
            'level': level,
            'level_num': level_info['level'],
            'color': level_info['color'],
            'message_en': level_info['message_en'],
            'message_fa': level_info['message_fa'],
            'action': level_info['action'],
            'affected_zones': affected_zones,
            'matched_keywords': matched_keywords,
            'expires_at': (datetime.now() + timedelta(hours=3)).isoformat(),
            # NEW: Precise location for map marker
            'target_location': target_location,
            'map_marker': map_marker,
            # NEW: Video URLs for media display
            'video_urls': video_urls or [],
        }
    
    def _is_recent(self, date_str: str, hours: int = 2) -> bool:
        """Check if a date string is within the last N hours."""
        try:
            # GDELT format: YYYYMMDDTHHMMSSZ
            if 'T' in date_str:
                dt = datetime.strptime(date_str[:15], '%Y%m%dT%H%M%S')
            else:
                dt = datetime.strptime(date_str[:14], '%Y%m%d%H%M%S')
            
            return datetime.now() - dt < timedelta(hours=hours)
        except:
            return True  # If can't parse, assume recent
    
    def get_active_warnings(self) -> List[Dict]:
        """Get all currently active warnings (not expired)."""
        now = datetime.now()
        active = []
        
        for warning in self.active_warnings:
            try:
                expires = datetime.fromisoformat(warning['expires_at'])
                if now < expires:
                    active.append(warning)
            except:
                active.append(warning)  # Keep if can't parse
        
        # Sort by severity (highest first)
        active.sort(key=lambda w: w.get('level_num', 0), reverse=True)
        return active
    
    def update_warnings(self) -> Dict:
        """
        Full update cycle:
        1. Check all sources
        2. Update active warnings list
        3. Return summary
        """
        print(f"[EARLY WARNING] Checking sources at {datetime.now().isoformat()}")
        
        new_warnings = self.check_all_sources()
        
        # Add new warnings to active list (deduplicate by ID)
        existing_ids = {w['id'] for w in self.active_warnings}
        for warning in new_warnings:
            if warning['id'] not in existing_ids:
                self.active_warnings.append(warning)
                print(f"[EARLY WARNING] NEW: {warning['level']} - {warning['title'][:50]}")
                for zone in warning['affected_zones']:
                    print(f"  → Affected: {zone['name']} ({zone['name_fa']}) - {zone['population']:,} people")
        
        # Clean expired warnings
        self.active_warnings = self.get_active_warnings()
        
        return {
            'checked_at': self.last_check,
            'new_warnings': len(new_warnings),
            'active_warnings': len(self.active_warnings),
            'warnings': self.active_warnings,
        }


# Singleton instance
_warning_system = None

def get_warning_system() -> EarlyWarningSystem:
    """Get or create the singleton warning system."""
    global _warning_system
    if _warning_system is None:
        _warning_system = EarlyWarningSystem()
    return _warning_system
