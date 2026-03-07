"""
Social Media OSINT Engine
=========================
Collects real-time incident reports from:
1. Twitter/X (via Nitter instances - no API key)
2. Telegram public channels (via web preview)
3. Reddit (via JSON API)
4. RSS feeds from news sources

Similar to mahsaalert.com approach.
"""

import requests
import re
import json
import time
from datetime import datetime, timedelta
from urllib.parse import quote

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False
    BeautifulSoup = None

# Try to import shared locations, fallback to local copy
try:
    from .target_manager import IRAN_LOCATIONS
except ImportError:
    # Fallback: define locally if import fails
    IRAN_LOCATIONS = {
        'tehran': {'lat': 35.6892, 'lon': 51.3890, 'province': 'Tehran'},
        'isfahan': {'lat': 32.6546, 'lon': 51.6680, 'province': 'Isfahan'},
        'esfahan': {'lat': 32.6546, 'lon': 51.6680, 'province': 'Isfahan'},
        'shiraz': {'lat': 29.5918, 'lon': 52.5837, 'province': 'Fars'},
        'mashhad': {'lat': 36.2605, 'lon': 59.6168, 'province': 'Khorasan'},
        'tabriz': {'lat': 38.0800, 'lon': 46.2919, 'province': 'Azerbaijan'},
        'ahvaz': {'lat': 31.3183, 'lon': 48.6706, 'province': 'Khuzestan'},
        'karaj': {'lat': 35.8400, 'lon': 50.9391, 'province': 'Alborz'},
        'qom': {'lat': 34.6416, 'lon': 50.8746, 'province': 'Qom'},
        'natanz': {'lat': 33.5100, 'lon': 51.9200, 'province': 'Isfahan'},
        'parchin': {'lat': 35.5200, 'lon': 51.7700, 'province': 'Tehran'},
        'fordow': {'lat': 34.8833, 'lon': 51.0000, 'province': 'Qom'},
        'bushehr': {'lat': 28.9234, 'lon': 50.8203, 'province': 'Bushehr'},
        'arak': {'lat': 34.0917, 'lon': 49.6892, 'province': 'Markazi'},
        'bandar abbas': {'lat': 27.1865, 'lon': 56.2808, 'province': 'Hormozgan'},
    }

# Keywords that indicate an attack/incident
ATTACK_KEYWORDS = [
    'attack', 'strike', 'hit', 'bomb', 'explosion', 'blast', 'missile',
    'drone', 'air raid', 'airstrike', 'destroyed', 'damage', 'fire',
    'smoke', 'explosion', 'sirens', 'alert', 'target', 'military',
    # Persian keywords
    'حمله', 'انفجار', 'موشک', 'پهپاد', 'آتش', 'دود', 'آژیر',
]


class SocialOSINT:
    """
    Multi-source social media OSINT collector.
    """
    
    # Public Nitter instances for Twitter scraping
    NITTER_INSTANCES = [
        'https://nitter.net',
        'https://nitter.privacydev.net',
        'https://nitter.poast.org',
    ]
    
    # Twitter accounts to monitor for Iran war news
    TWITTER_ACCOUNTS = [
        'IntelDoge',        # OSINT account
        'sentdefender',     # Military news
        'AuroraIntel',      # OSINT
        'NotWoofers',       # Middle East
        'FightingNews',     # War news
        'MahsaAlert',       # Iran protests/attacks
        'IranIntl',         # Iran International
        'manikieh',         # Iran news
    ]
    
    # Telegram channels (public, web preview only)
    TELEGRAM_CHANNELS = [
        'IranIntl_En',
        'MahsaAlert',
    ]
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.incidents = []
    
    def scan_all_sources(self, hours_back=24):
        """Scan all social media sources for incidents."""
        incidents = []
        
        print(f'[SocialOSINT] Starting scan across all sources (past {hours_back}h)...')
        
        # 1. News RSS feeds (most reliable)
        rss_incidents = self.scan_news_rss()
        incidents.extend(rss_incidents)
        print(f'[SocialOSINT] RSS feeds: {len(rss_incidents)} incidents')
        
        # 2. Reddit (public JSON API)
        reddit_incidents = self.scan_reddit(hours_back)
        incidents.extend(reddit_incidents)
        print(f'[SocialOSINT] Reddit: {len(reddit_incidents)} incidents')
        
        # 3. Twitter via Nitter (often blocked)
        twitter_incidents = self.scan_twitter(hours_back)
        incidents.extend(twitter_incidents)
        print(f'[SocialOSINT] Twitter: {len(twitter_incidents)} incidents')
        
        # Deduplicate by location
        seen = set()
        unique = []
        for inc in incidents:
            key = f"{inc.get('lat', 0):.2f}_{inc.get('lon', 0):.2f}"
            if key not in seen:
                seen.add(key)
                unique.append(inc)
        
        print(f'[SocialOSINT] Total unique incidents: {len(unique)}')
        self.incidents = unique
        return unique
    
    def scan_twitter(self, hours_back=24):
        """Scan Twitter accounts via Nitter for Iran-related incidents."""
        incidents = []
        
        if not HAS_BS4:
            print('[SocialOSINT] BeautifulSoup not available, skipping Twitter scan')
            return incidents
        
        for account in self.TWITTER_ACCOUNTS[:3]:  # Limit to avoid rate limits
            for nitter_url in self.NITTER_INSTANCES:
                try:
                    url = f"{nitter_url}/{account}"
                    resp = self.session.get(url, timeout=10)
                    if resp.status_code != 200:
                        continue
                    
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    tweets = soup.select('.timeline-item, .tweet-body')
                    
                    for tweet in tweets[:10]:
                        text = tweet.get_text()
                        
                        # Check if it mentions Iran and attacks
                        if not any(kw in text.lower() for kw in ['iran', 'tehran', 'isfahan', 'ایران']):
                            continue
                        if not any(kw in text.lower() for kw in ATTACK_KEYWORDS):
                            continue
                        
                        # Extract location
                        location = self._extract_location(text)
                        if location:
                            incidents.append({
                                'source': 'twitter',
                                'account': account,
                                'text': text[:200],
                                'location': location['name'],
                                'lat': location['lat'],
                                'lon': location['lon'],
                                'province': location['province'],
                                'timestamp': datetime.now().isoformat(),
                                'type': self._detect_incident_type(text),
                            })
                    
                    break  # Success, don't try other Nitter instances
                    
                except Exception as e:
                    continue
            
            time.sleep(2)  # Rate limit
        
        return incidents
    
    def scan_reddit(self, hours_back=24):
        """Scan Reddit for Iran-related incidents."""
        incidents = []
        subreddits = ['worldnews', 'CombatFootage', 'geopolitics', 'iran']
        
        for sub in subreddits:
            try:
                url = f"https://www.reddit.com/r/{sub}/search.json?q=iran+attack&sort=new&t=day&limit=25"
                resp = self.session.get(url, timeout=10)
                if resp.status_code != 200:
                    continue
                
                data = resp.json()
                posts = data.get('data', {}).get('children', [])
                
                for post in posts:
                    pdata = post.get('data', {})
                    title = pdata.get('title', '')
                    
                    # Check if relevant
                    if not any(kw in title.lower() for kw in ATTACK_KEYWORDS):
                        continue
                    
                    # Extract location
                    location = self._extract_location(title)
                    if location:
                        incidents.append({
                            'source': 'reddit',
                            'subreddit': sub,
                            'text': title[:200],
                            'url': f"https://reddit.com{pdata.get('permalink', '')}",
                            'location': location['name'],
                            'lat': location['lat'],
                            'lon': location['lon'],
                            'province': location['province'],
                            'timestamp': datetime.fromtimestamp(pdata.get('created_utc', 0)).isoformat(),
                            'type': self._detect_incident_type(title),
                            'score': pdata.get('score', 0),
                        })
                
                time.sleep(1)
                
            except Exception as e:
                continue
        
        return incidents
    
    def scan_news_rss(self):
        """Scan news RSS feeds for Iran incidents."""
        incidents = []
        
        # More reliable feeds
        feeds = [
            # Google News RSS
            'https://news.google.com/rss/search?q=iran+attack+strike&hl=en-US&gl=US&ceid=US:en',
            'https://news.google.com/rss/search?q=iran+explosion+military&hl=en-US&gl=US&ceid=US:en',
            # Al Jazeera
            'https://www.aljazeera.com/xml/rss/all.xml',
            # Reuters Middle East
            'https://www.reutersagency.com/feed/?best-topics=middle-east&post_type=best',
        ]
        
        for feed_url in feeds:
            try:
                resp = self.session.get(feed_url, timeout=15)
                if resp.status_code != 200:
                    continue
                
                # Simple RSS parsing
                items = re.findall(r'<item>(.*?)</item>', resp.text, re.DOTALL)
                
                for item in items[:20]:
                    title_match = re.search(r'<title>(.*?)</title>', item)
                    if not title_match:
                        continue
                    
                    title = title_match.group(1)
                    title = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', title)
                    
                    # Check relevance - must mention Iran
                    if 'iran' not in title.lower():
                        continue
                    if not any(kw in title.lower() for kw in ATTACK_KEYWORDS):
                        continue
                    
                    # Extract location
                    location = self._extract_location(title)
                    if location:
                        incidents.append({
                            'source': 'news_rss',
                            'text': title[:200],
                            'location': location['name'],
                            'lat': location['lat'],
                            'lon': location['lon'],
                            'province': location['province'],
                            'timestamp': datetime.now().isoformat(),
                            'type': self._detect_incident_type(title),
                        })
                        print(f'[SocialOSINT] Found RSS incident: {location["name"]} - {title[:50]}')
                
                time.sleep(1)
                
            except Exception as e:
                print(f'[SocialOSINT] RSS error: {e}')
                continue
        
        return incidents
    
    def _extract_location(self, text):
        """Extract Iranian location from text."""
        text_lower = text.lower()
        
        for loc_name, loc_data in IRAN_LOCATIONS.items():
            if loc_name in text_lower:
                return {
                    'name': loc_name.title(),
                    'lat': loc_data['lat'],
                    'lon': loc_data['lon'],
                    'province': loc_data['province'],
                }
        
        return None
    
    def _detect_incident_type(self, text):
        """Detect type of incident from text."""
        text_lower = text.lower()
        
        if any(kw in text_lower for kw in ['nuclear', 'natanz', 'fordow', 'enrichment']):
            return 'nuclear'
        if any(kw in text_lower for kw in ['missile', 'rocket', 'ballistic']):
            return 'missile'
        if any(kw in text_lower for kw in ['drone', 'uav', 'shahed']):
            return 'drone'
        if any(kw in text_lower for kw in ['air base', 'airbase', 'air force']):
            return 'airbase'
        if any(kw in text_lower for kw in ['refinery', 'oil', 'gas', 'energy']):
            return 'energy'
        if any(kw in text_lower for kw in ['irgc', 'military', 'army', 'base']):
            return 'military'
        
        return 'unknown'


def scan_social_media():
    """Quick function to scan all social media sources."""
    osint = SocialOSINT()
    incidents = osint.scan_all_sources(hours_back=24)
    return incidents


if __name__ == '__main__':
    print("Scanning social media for Iran incidents...")
    osint = SocialOSINT()
    incidents = osint.scan_all_sources()
    print(f"\nFound {len(incidents)} incidents:")
    for inc in incidents:
        print(f"  - {inc['location']}: {inc['type']} ({inc['source']})")
        print(f"    {inc['text'][:80]}...")
