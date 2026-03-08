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

OFFICIAL_SOURCES = {
    # US CENTCOM
    'centcom': {
        'name': 'US Central Command',
        'rss': 'https://www.centcom.mil/MEDIA/PRESS-RELEASES/Press-Release-View/Article/rss/',
        'keywords': ['iran', 'isfahan', 'shiraz', 'tehran', 'strike', 'operation', 'target'],
        'priority': 'critical',
    },
    # IDF Spokesperson
    'idf': {
        'name': 'IDF Spokesperson',
        'twitter_rss': 'https://nitter.net/IDF/rss',  # Nitter RSS for Twitter
        'keywords': ['iran', 'strike', 'operation', 'warning', 'civilian', 'evacuate'],
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
            'User-Agent': 'CivilianSafetyMonitor/1.0'
        })
        self.active_warnings = []
        self.last_check = None
    
    def check_all_sources(self) -> List[Dict]:
        """
        Check all official sources for strike-related announcements.
        Returns list of potential warnings.
        """
        warnings = []
        
        # Check RSS feeds
        for source_id, source in OFFICIAL_SOURCES.items():
            try:
                rss_url = source.get('rss') or source.get('twitter_rss')
                if rss_url:
                    feed_warnings = self._check_rss_feed(source_id, source, rss_url)
                    warnings.extend(feed_warnings)
            except Exception as e:
                print(f"[WARNING] Error checking {source_id}: {e}")
        
        # Also check GDELT for urgent news
        gdelt_warnings = self._check_gdelt_urgent()
        warnings.extend(gdelt_warnings)
        
        self.last_check = datetime.now().isoformat()
        return warnings
    
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
                       priority: str, matched_keywords: List[str]) -> Dict:
        """Create a warning object."""
        
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
