"""
Multi-Source Data Aggregator

From deep-research-report:
  - Use PlanetScope (~3m) as primary commercial source
  - Sentinel-2 (10m, free) and Sentinel-1 SAR (free) as fallbacks
  - Copernicus Data Space Ecosystem (CDSE) as alternative Sentinel access
  - Check all sources, pick best available data

This module unifies:
  1. Element84 STAC (free) — Sentinel-2 L2A + Sentinel-1 GRD
  2. Planet Data API (commercial) — PlanetScope ~3m
  3. Copernicus CDSE (free with auth) — Sentinel-2/1 via Sentinel Hub

It provides a single "what data exists?" endpoint and a
"get me the best available pair" function.
"""

import os
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path

from src.core.config import AOI_CONFIG, MCP_CLOUD_THRESHOLD

# Element84 free STAC
ELEMENT84_STAC = "https://earth-search.aws.element84.com/v1/search"

# Copernicus CDSE endpoints (from research report)
CDSE_TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
CDSE_CATALOG_URL = "https://sh.dataspace.copernicus.eu/api/v1/catalog/1.0.0/search"


def get_cdse_credentials():
    """Get CDSE OAuth2 credentials from environment."""
    client_id = os.environ.get('CDSE_CLIENT_ID', '').strip()
    client_secret = os.environ.get('CDSE_CLIENT_SECRET', '').strip()
    return client_id, client_secret


def cdse_available():
    """Check if CDSE credentials are configured."""
    cid, csec = get_cdse_credentials()
    return bool(cid and csec)


class MultiSourceAggregator:
    """
    Checks all available satellite data sources and reports what's available.
    Helps users understand data gaps and pick the best source.
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
        self._cdse_token = None
        self._cdse_token_expiry = None

    def check_all_sources(self, bbox, start_date, end_date, cloud_cover=50):
        """
        Check ALL available data sources for a given area and date range.

        Returns a comprehensive availability report:
        {
            'sources': {
                'sentinel2': { 'available': True, 'scenes': [...], 'count': N },
                'sentinel1_sar': { 'available': True, 'scenes': [...], 'count': N },
                'planetscope': { 'available': True/False, 'scenes': [...], 'count': N },
                'cdse_sentinel2': { 'available': True/False, 'scenes': [...], 'count': N },
            },
            'best_optical': { 'source': '...', 'date': '...', 'resolution': '...' },
            'best_radar': { 'source': '...', 'date': '...', ... },
            'summary': '...',
            'data_gap_days': N  (days since last usable image)
        }
        """
        report = {
            'sources': {},
            'best_optical': None,
            'best_radar': None,
            'total_scenes': 0,
            'summary': '',
            'recommendations': [],
        }

        # 1. Element84 STAC — Sentinel-2 (free, no auth)
        s2_scenes = self._check_element84_s2(bbox, start_date, end_date, cloud_cover)
        report['sources']['sentinel2'] = {
            'name': 'Sentinel-2 L2A',
            'provider': 'Element84 (free)',
            'resolution': '10m',
            'type': 'optical',
            'available': len(s2_scenes) > 0,
            'scenes': s2_scenes,
            'count': len(s2_scenes),
            'auth_required': False,
            'configured': True,
        }

        # 2. Element84 STAC — Sentinel-1 SAR (free, no auth)
        s1_scenes = self._check_element84_s1(bbox, start_date, end_date)
        report['sources']['sentinel1_sar'] = {
            'name': 'Sentinel-1 SAR (Radar)',
            'provider': 'Element84 (free)',
            'resolution': '10m',
            'type': 'radar',
            'available': len(s1_scenes) > 0,
            'scenes': s1_scenes,
            'count': len(s1_scenes),
            'auth_required': False,
            'configured': True,
        }

        # 3. PlanetScope (commercial, needs API key)
        from planet_fetcher import planet_available, PlanetFetcher
        ps_configured = planet_available()
        ps_scenes = []
        if ps_configured:
            try:
                pf = PlanetFetcher()
                ps_scenes = pf.check_availability(bbox, start_date, end_date, cloud_cover)
            except Exception as e:
                print(f"[MULTI] Planet check failed: {e}")

        report['sources']['planetscope'] = {
            'name': 'PlanetScope (~3m)',
            'provider': 'Planet Labs (commercial)',
            'resolution': '~3m',
            'type': 'optical',
            'available': len(ps_scenes) > 0,
            'scenes': ps_scenes,
            'count': len(ps_scenes),
            'auth_required': True,
            'configured': ps_configured,
        }

        # 4. Copernicus CDSE — Sentinel-2 (free with auth)
        cdse_configured = cdse_available()
        cdse_scenes = []
        if cdse_configured:
            try:
                cdse_scenes = self._check_cdse_s2(bbox, start_date, end_date, cloud_cover)
            except Exception as e:
                print(f"[MULTI] CDSE check failed: {e}")

        report['sources']['cdse_sentinel2'] = {
            'name': 'Sentinel-2 (CDSE)',
            'provider': 'Copernicus (free+auth)',
            'resolution': '10m',
            'type': 'optical',
            'available': len(cdse_scenes) > 0,
            'scenes': cdse_scenes,
            'count': len(cdse_scenes),
            'auth_required': True,
            'configured': cdse_configured,
        }

        # Compute totals
        all_scenes = s2_scenes + ps_scenes + cdse_scenes + s1_scenes
        report['total_scenes'] = len(all_scenes)

        # Find best optical (newest, lowest cloud)
        optical = s2_scenes + ps_scenes + cdse_scenes
        optical.sort(key=lambda s: s.get('datetime', ''), reverse=True)
        for s in optical:
            cc = s.get('cloud_cover', 100)
            if cc < cloud_cover:
                report['best_optical'] = s
                break

        # Find best radar (newest)
        if s1_scenes:
            report['best_radar'] = s1_scenes[-1]  # Most recent

        # Calculate data gap
        today = datetime.now().strftime('%Y-%m-%d')
        if report['best_optical']:
            last_date = report['best_optical'].get('datetime', '')[:10]
            try:
                gap = (datetime.strptime(today, '%Y-%m-%d') - datetime.strptime(last_date, '%Y-%m-%d')).days
                report['data_gap_days'] = gap
            except:
                report['data_gap_days'] = -1
        else:
            report['data_gap_days'] = -1

        # Generate summary and recommendations
        report['summary'], report['recommendations'] = self._generate_summary(report)

        return report

    def check_city(self, city, start_date, end_date, cloud_cover=50):
        """Check all sources for a preset city."""
        if city not in AOI_CONFIG:
            return {'error': f'Unknown city: {city}'}
        bbox = AOI_CONFIG[city]['bbox']
        return self.check_all_sources(bbox, start_date, end_date, cloud_cover)

    def _check_element84_s2(self, bbox, start_date, end_date, cloud_cover):
        """Check Element84 STAC for Sentinel-2 L2A scenes."""
        payload = {
            "collections": ["sentinel-2-l2a"],
            "bbox": bbox,
            "datetime": f"{start_date}T00:00:00Z/{end_date}T23:59:59Z",
            "query": {"eo:cloud_cover": {"lt": cloud_cover}},
            "sortby": [{"field": "properties.datetime", "direction": "asc"}],
            "limit": 30,
        }
        try:
            resp = self.session.post(ELEMENT84_STAC, json=payload, timeout=15)
            resp.raise_for_status()
            features = resp.json().get('features', [])
            return [self._s2_to_scene(f) for f in features]
        except Exception as e:
            print(f"[MULTI-S2] {e}")
            return []

    def _check_element84_s1(self, bbox, start_date, end_date):
        """Check Element84 STAC for Sentinel-1 GRD scenes."""
        payload = {
            "collections": ["sentinel-1-grd"],
            "bbox": bbox,
            "datetime": f"{start_date}T00:00:00Z/{end_date}T23:59:59Z",
            "limit": 30,
        }
        try:
            resp = self.session.post(ELEMENT84_STAC, json=payload, timeout=15)
            resp.raise_for_status()
            features = resp.json().get('features', [])
            return [self._s1_to_scene(f) for f in features]
        except Exception as e:
            print(f"[MULTI-S1] {e}")
            return []

    def _check_cdse_s2(self, bbox, start_date, end_date, cloud_cover):
        """
        Check Copernicus CDSE for Sentinel-2 scenes.
        From research report: OAuth2 token-based auth, STAC-like catalog.
        Token reuse is critical (don't fetch per request).
        """
        token = self._get_cdse_token()
        if not token:
            return []

        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        }

        payload = {
            "bbox": bbox,
            "datetime": f"{start_date}T00:00:00Z/{end_date}T23:59:59Z",
            "collections": ["sentinel-2-l2a"],
            "limit": 20,
            "filter": {
                "op": "<=",
                "args": [{"property": "eo:cloud_cover"}, cloud_cover]
            }
        }

        try:
            resp = requests.post(CDSE_CATALOG_URL, json=payload, headers=headers, timeout=15)
            resp.raise_for_status()
            features = resp.json().get('features', [])
            return [{
                'id': f.get('id', ''),
                'datetime': f.get('properties', {}).get('datetime', ''),
                'cloud_cover': f.get('properties', {}).get('eo:cloud_cover', -1),
                'source': 'CDSE Sentinel-2',
                'resolution': '10m',
                'type': 'optical',
            } for f in features]
        except Exception as e:
            print(f"[MULTI-CDSE] {e}")
            return []

    def _get_cdse_token(self):
        """
        Get CDSE OAuth2 token. Reuses cached token if not expired.
        From research report: "reuse access tokens; do not fetch per request"
        """
        if self._cdse_token and self._cdse_token_expiry:
            if datetime.now() < self._cdse_token_expiry:
                return self._cdse_token

        client_id, client_secret = get_cdse_credentials()
        if not client_id or not client_secret:
            return None

        try:
            resp = requests.post(
                CDSE_TOKEN_URL,
                data={
                    'grant_type': 'client_credentials',
                    'client_id': client_id,
                    'client_secret': client_secret,
                },
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=10
            )
            resp.raise_for_status()
            token_data = resp.json()
            self._cdse_token = token_data.get('access_token')
            expires_in = token_data.get('expires_in', 300)
            self._cdse_token_expiry = datetime.now() + timedelta(seconds=expires_in - 30)
            return self._cdse_token
        except Exception as e:
            print(f"[CDSE-AUTH] {e}")
            return None

    def _s2_to_scene(self, feature):
        """Convert STAC Sentinel-2 feature to unified scene dict."""
        props = feature.get('properties', {})
        return {
            'id': feature.get('id', ''),
            'datetime': props.get('datetime', ''),
            'cloud_cover': round(props.get('eo:cloud_cover', -1), 1),
            'source': 'Sentinel-2 (Element84)',
            'resolution': '10m',
            'type': 'optical',
        }

    def _s1_to_scene(self, feature):
        """Convert STAC Sentinel-1 feature to unified scene dict."""
        props = feature.get('properties', {})
        return {
            'id': feature.get('id', ''),
            'datetime': props.get('datetime', ''),
            'cloud_cover': 0,  # SAR doesn't care about clouds
            'mode': props.get('sar:instrument_mode', ''),
            'orbit': props.get('sat:orbit_state', ''),
            'source': 'Sentinel-1 SAR (Element84)',
            'resolution': '10m',
            'type': 'radar',
        }

    def _generate_summary(self, report):
        """Generate human-readable summary and recommendations."""
        sources = report['sources']
        total = report['total_scenes']
        recs = []

        # Count what we have
        s2_count = sources['sentinel2']['count']
        s1_count = sources['sentinel1_sar']['count']
        ps_count = sources['planetscope']['count']
        ps_configured = sources['planetscope']['configured']
        cdse_configured = sources['cdse_sentinel2']['configured']

        lines = []
        lines.append(f"Found {total} total scenes across all sources.")

        if s2_count > 0:
            lines.append(f"Sentinel-2 (10m optical): {s2_count} scenes available.")
        else:
            lines.append("Sentinel-2: No clear scenes in date range.")

        if s1_count > 0:
            lines.append(f"Sentinel-1 SAR (radar): {s1_count} scenes — cloud-proof.")
        else:
            lines.append("Sentinel-1 SAR: No scenes in date range.")

        if ps_configured and ps_count > 0:
            lines.append(f"PlanetScope (3m): {ps_count} high-res scenes available!")
        elif ps_configured:
            lines.append("PlanetScope: API configured but no scenes found.")

        # Recommendations
        if not ps_configured:
            recs.append({
                'type': 'setup',
                'priority': 'high',
                'message': 'Set PL_API_KEY to unlock PlanetScope ~3m imagery — daily revisit, best for damage assessment.',
                'action': 'Add PL_API_KEY environment variable with your Planet Labs API key.',
            })

        if not cdse_configured:
            recs.append({
                'type': 'setup',
                'priority': 'medium',
                'message': 'Set CDSE_CLIENT_ID + CDSE_CLIENT_SECRET for Copernicus Sentinel Hub access (free).',
                'action': 'Register at dataspace.copernicus.eu and create OAuth2 credentials.',
            })

        if s2_count == 0 and s1_count > 0:
            recs.append({
                'type': 'analysis',
                'priority': 'high',
                'message': 'No clear optical images — use SAR Radar Analysis instead (works through 100% cloud cover).',
                'action': 'Click SAR RADAR ANALYSIS button.',
            })

        if report.get('data_gap_days', 0) > 5:
            gap = report['data_gap_days']
            recs.append({
                'type': 'gap',
                'priority': 'medium',
                'message': f'Latest usable optical image is {gap} days old. Consider widening date range or using SAR.',
                'action': 'Try extending the After date or use SAR for cloud-proof analysis.',
            })

        if total == 0:
            recs.append({
                'type': 'critical',
                'priority': 'critical',
                'message': 'No data found from any source. Try widening the date range.',
                'action': 'Extend the date range by at least 2 weeks.',
            })

        summary = ' '.join(lines)
        return summary, recs
