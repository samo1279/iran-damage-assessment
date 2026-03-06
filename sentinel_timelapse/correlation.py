"""
OSINT-Satellite Correlation Engine
===================================
Cross-references OSINT intelligence with satellite imagery to produce
multi-source damage verdicts.

Logic:
  1. For each reported strike, fetch pre-war BASELINE imagery (clear, good quality)
  2. Fetch whatever post-war imagery is available (may be poor quality)
  3. Run change detection between pre/post
  4. Combine: OSINT confidence + satellite evidence + temporal match = final verdict

Confidence levels:
  - CONFIRMED: Multiple news sources + satellite shows change
  - LIKELY: Multiple news sources OR satellite shows change
  - REPORTED: Single news source, no satellite confirmation
  - UNCONFIRMED: Mentioned but not corroborated

War started: March 1, 2026
Pre-war baseline: any clear image before March 1
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path

from config import TIMELAPSE_OUTPUT


class CorrelationEngine:
    """
    Cross-references OSINT reports with satellite imagery.
    Produces damage verdicts for each reported strike location.
    """

    WAR_START = '2026-03-01'

    def __init__(self):
        self.output_dir = Path(TIMELAPSE_OUTPUT)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def assess_strike(self, strike, fetcher=None, change_detector=None):
        """
        Run full assessment for a single strike:
        1. Get pre-war baseline imagery
        2. Get post-war imagery (whatever's available)
        3. Run change detection
        4. Combine with OSINT confidence
        5. Return verdict

        Args:
            strike: dict with target_id, lat, lon, date, confidence, source_count, bbox
            fetcher: SatelliteFetcher instance
            change_detector: ChangeDetector instance

        Returns:
            dict with verdict, satellite_result, combined_confidence
        """
        result = {
            'strike_id': strike.get('id', ''),
            'target_name': strike.get('target_name', ''),
            'lat': strike.get('lat', 0),
            'lon': strike.get('lon', 0),
            'osint_confidence': strike.get('confidence', 'unconfirmed'),
            'osint_sources': strike.get('source_count', 0),
            'satellite_checked': False,
            'satellite_change_detected': False,
            'satellite_change_percent': 0,
            'satellite_event_count': 0,
            'before_image': None,
            'after_image': None,
            'heatmap': None,
            'verdict': 'unconfirmed',
            'verdict_reasons': [],
            'combined_score': 0.0,
        }

        if not fetcher or not change_detector:
            # No satellite check — OSINT only verdict
            result['verdict'] = self._osint_only_verdict(strike)
            result['verdict_reasons'].append('OSINT assessment only — no satellite check performed')
            result['combined_score'] = self._osint_score(strike)
            return result

        # Build bbox from target coordinates (approx 3km box)
        bbox = strike.get('bbox')
        if not bbox:
            lat, lon = strike['lat'], strike['lon']
            delta = 0.015  # ~1.5km
            bbox = [lon - delta, lat - delta, lon + delta, lat + delta]

        label = strike.get('target_id', 'strike')[:20]

        try:
            # ── Step 1: Pre-war baseline (before March 1, clear imagery)
            baseline_end = '2026-02-28'
            baseline_start = '2025-12-01'  # Look back 3 months for clear image

            from fetch_images import SatelliteFetcher as S2Fetcher
            custom_folder = str(Path(f'archive/strikes/{label}').absolute())
            Path(custom_folder).mkdir(parents=True, exist_ok=True)

            s2 = S2Fetcher()
            before_items = s2.search_and_download_bbox(
                bbox, custom_folder, baseline_start, baseline_end, max_images=1
            )

            if not before_items:
                result['verdict_reasons'].append('No pre-war baseline image found')
                result['verdict'] = self._osint_only_verdict(strike)
                result['combined_score'] = self._osint_score(strike)
                return result

            # ── Step 2: Post-war image (after strike date, whatever's available)
            strike_date = strike.get('date', self.WAR_START)
            if strike_date == 'unknown':
                strike_date = self.WAR_START

            # Look for post-war image up to today
            post_start = strike_date
            post_end = datetime.utcnow().strftime('%Y-%m-%d')

            after_items = s2.search_and_download_bbox(
                bbox, custom_folder, post_start, post_end, max_images=1
            )

            if not after_items:
                result['verdict_reasons'].append(
                    f'No post-war satellite image available after {strike_date}. '
                    'This is expected — post-war coverage is limited.'
                )
                result['verdict'] = self._osint_only_verdict(strike)
                result['verdict_reasons'].append(
                    f'OSINT verdict based on {strike.get("source_count", 0)} news sources'
                )
                result['combined_score'] = self._osint_score(strike)
                return result

            # ── Step 3: Run change detection
            before_path = before_items[0]
            after_path = after_items[-1] if len(after_items) > 1 else after_items[0]

            cd_result = change_detector.detect(
                label, before_path, after_path, bbox=bbox
            )

            if cd_result.get('success'):
                result['satellite_checked'] = True
                result['satellite_change_percent'] = cd_result.get('stats', {}).get('change_percent', 0)
                result['satellite_event_count'] = cd_result.get('event_count', 0)
                result['satellite_change_detected'] = result['satellite_change_percent'] > 2.0
                result['before_image'] = cd_result.get('before_image')
                result['after_image'] = cd_result.get('after_image')
                result['heatmap'] = cd_result.get('heatmap')
                result['before_date'] = cd_result.get('before_date')
                result['after_date'] = cd_result.get('after_date')
                result['events'] = cd_result.get('events', [])

                # Save before/after PNGs
                try:
                    from create_timelapse import TimelapseCreator
                    creator = TimelapseCreator()
                    before_img = creator._load_tif_as_pil(before_path)
                    after_img = creator._load_tif_as_pil(after_path)
                    if before_img:
                        png = f"strike_{label}_before.png"
                        creator.save_frame(before_img, self.output_dir / png,
                                         caption=f"BASELINE: {cd_result.get('before_date','')}")
                        result['before_image'] = png
                    if after_img:
                        png = f"strike_{label}_after.png"
                        creator.save_frame(after_img, self.output_dir / png,
                                         caption=f"POST-STRIKE: {cd_result.get('after_date','')}")
                        result['after_image'] = png
                except Exception:
                    pass

            # ── Step 4: Combined verdict
            result['verdict'], result['combined_score'], reasons = self._combined_verdict(
                strike, result
            )
            result['verdict_reasons'] = reasons

        except Exception as e:
            result['verdict_reasons'].append(f'Satellite check failed: {str(e)}')
            result['verdict'] = self._osint_only_verdict(strike)
            result['combined_score'] = self._osint_score(strike)

        return result

    def _osint_score(self, strike):
        """Calculate OSINT-only confidence score (0-1)."""
        n = strike.get('source_count', 0)
        conf = strike.get('confidence', 'unconfirmed')
        base = {'confirmed': 0.8, 'likely': 0.6, 'reported': 0.4, 'unconfirmed': 0.2}
        score = base.get(conf, 0.2)
        # Boost for more sources
        score += min(0.15, n * 0.03)
        return min(1.0, score)

    def _osint_only_verdict(self, strike):
        """Determine verdict from OSINT alone."""
        conf = strike.get('confidence', 'unconfirmed')
        n = strike.get('source_count', 0)
        if conf == 'confirmed' or n >= 5:
            return 'likely'
        elif conf == 'likely' or n >= 3:
            return 'reported'
        else:
            return 'unconfirmed'

    def _combined_verdict(self, strike, sat_result):
        """
        Combine OSINT + satellite evidence for final verdict.
        Returns (verdict_str, score_float, reasons_list).
        """
        reasons = []
        osint_score = self._osint_score(strike)
        sat_change = sat_result.get('satellite_change_percent', 0)
        sat_events = sat_result.get('satellite_event_count', 0)

        # Satellite score
        sat_score = 0.0
        if sat_result.get('satellite_checked'):
            if sat_change > 10:
                sat_score = 0.9
                reasons.append(f'Satellite shows {sat_change:.1f}% area change — significant damage visible')
            elif sat_change > 5:
                sat_score = 0.7
                reasons.append(f'Satellite shows {sat_change:.1f}% change — moderate damage')
            elif sat_change > 2:
                sat_score = 0.5
                reasons.append(f'Satellite shows {sat_change:.1f}% change — some visible changes')
            else:
                sat_score = 0.2
                reasons.append(f'Satellite shows minimal change ({sat_change:.1f}%) — damage may be below detection threshold')
        else:
            reasons.append('No satellite imagery available for this location')

        # OSINT reasons
        n = strike.get('source_count', 0)
        conf = strike.get('confidence', 'unconfirmed')
        if n > 0:
            reasons.append(f'{n} news sources report this strike (OSINT confidence: {conf})')
        else:
            reasons.append('No news sources found for this specific target')

        # Combined score (weighted)
        if sat_result.get('satellite_checked'):
            combined = osint_score * 0.4 + sat_score * 0.6  # Satellite weighs more when available
        else:
            combined = osint_score  # OSINT only

        # Final verdict
        if combined >= 0.75:
            verdict = 'confirmed'
            reasons.insert(0, 'CONFIRMED — multiple sources corroborate damage')
        elif combined >= 0.55:
            verdict = 'likely'
            reasons.insert(0, 'LIKELY — evidence suggests damage but not fully confirmed')
        elif combined >= 0.35:
            verdict = 'reported'
            reasons.insert(0, 'REPORTED — news sources report strike, awaiting confirmation')
        else:
            verdict = 'unconfirmed'
            reasons.insert(0, 'UNCONFIRMED — insufficient evidence')

        return verdict, round(combined, 3), reasons

    def batch_assess(self, strikes, fetcher=None, change_detector=None, max_sat_checks=5):
        """
        Assess multiple strikes. Only runs satellite checks on top N by OSINT confidence.
        """
        results = []

        # Sort by source count (most reported first)
        sorted_strikes = sorted(strikes, key=lambda s: s.get('source_count', 0), reverse=True)

        for i, strike in enumerate(sorted_strikes):
            # Only do satellite checks for top N
            if i < max_sat_checks:
                r = self.assess_strike(strike, fetcher, change_detector)
            else:
                r = self.assess_strike(strike)  # OSINT-only
            results.append(r)

        # Sort results by combined score
        results.sort(key=lambda r: r['combined_score'], reverse=True)
        return results

    def generate_summary(self, assessments):
        """Generate human-readable damage summary from assessments."""
        confirmed = [a for a in assessments if a['verdict'] == 'confirmed']
        likely = [a for a in assessments if a['verdict'] == 'likely']
        reported = [a for a in assessments if a['verdict'] == 'reported']
        unconfirmed = [a for a in assessments if a['verdict'] == 'unconfirmed']

        summary = {
            'total_strikes': len(assessments),
            'confirmed': len(confirmed),
            'likely': len(likely),
            'reported': len(reported),
            'unconfirmed': len(unconfirmed),
            'confirmed_targets': [a['target_name'] for a in confirmed],
            'likely_targets': [a['target_name'] for a in likely],
            'narrative': '',
        }

        parts = []
        parts.append(f"Assessment of {len(assessments)} reported strike locations "
                     f"since the conflict began on March 1, 2026.")
        if confirmed:
            parts.append(f"\n\nCONFIRMED DAMAGE ({len(confirmed)}): "
                        + ', '.join(a['target_name'] for a in confirmed))
        if likely:
            parts.append(f"\n\nLIKELY DAMAGE ({len(likely)}): "
                        + ', '.join(a['target_name'] for a in likely))
        if reported:
            parts.append(f"\n\nREPORTED ({len(reported)}): "
                        + ', '.join(a['target_name'] for a in reported))
        if unconfirmed:
            parts.append(f"\n\nUNCONFIRMED ({len(unconfirmed)}): "
                        + ', '.join(a['target_name'] for a in unconfirmed))

        summary['narrative'] = ''.join(parts)
        return summary
