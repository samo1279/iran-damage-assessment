"""
OSINT Intelligence Engine — Iran War Damage Assessment
=====================================================
Collects open-source intelligence from multiple free sources:
  1. GDELT Project — global news monitoring (free API, no key)
  2. Known targets database — pre-compiled from public IDF/OSINT reports
  3. Location extraction — maps city/base names to coordinates
  4. Wikipedia/public references for Iranian military installations

The engine answers: WHAT was hit, WHERE, WHEN, and by WHOM — based on
publicly available news and military announcements.

Israel typically announces target areas before/after operations.
This data, combined with whatever satellite imagery we have, creates
a multi-source damage assessment with confidence scoring.
"""

import requests
import json
import re
import sqlite3
import hashlib
import time
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import quote

# ────────────────────────────────────────────────────────────────────
# KNOWN IRANIAN MILITARY / STRATEGIC TARGETS
# Sources: public OSINT, Wikipedia, IDF press releases, Reuters, AP
# These are locations that have been publicly discussed in media
# ────────────────────────────────────────────────────────────────────

def _t(name, typ, cat, lat, lon, kw, prov, desc=''):
    """Helper to build a target dict compactly."""
    d = 0.03
    return {
        'name': name, 'type': typ, 'category': cat,
        'lat': lat, 'lon': lon,
        'bbox': [lon-d, lat-d, lon+d, lat+d],
        'description': desc or name,
        'keywords': kw if isinstance(kw, list) else [kw],
        'province': prov
    }

KNOWN_TARGETS = {
    # ═══════════════════════════════════════════════════════════════
    # TEHRAN PROVINCE  (capital — densest target cluster)
    # ═══════════════════════════════════════════════════════════════
    'parchin_complex':        _t('Parchin Military Complex','military_base','weapons_research',35.52,51.77,['parchin','military complex'],'Tehran','Major weapons R&D/testing complex SE of Tehran'),
    'tehran_refinery':        _t('Tehran Oil Refinery (Rey)','energy','refinery',35.54,51.42,['tehran refinery','oil refinery tehran','rey refinery','shahran oil','oil depot tehran','iran oil depot','tehran oil depot'],'Tehran','Major oil refinery south of Tehran, also known as Rey/Shahran'),
    'mehrabad_airport':       _t('Mehrabad Airport / Air Base','airbase','air_defense',35.6892,51.3134,['mehrabad','tehran airport'],'Tehran'),
    'khojir_missile':         _t('Khojir Missile Development','military_base','missile',35.63,51.67,['khojir','missile complex'],'Tehran'),
    'tehran_ikia':            _t('Imam Khomeini Intl Airport','infrastructure','logistics',35.4161,51.1522,['imam khomeini airport','ikia'],'Tehran'),
    'lavizan_tech':           _t('Lavizan Technology Center','military_base','weapons_research',35.7500,51.5050,['lavizan','technology center'],'Tehran'),
    'shahid_hemmat_missile':  _t('Shahid Hemmat Missile Industries','military_base','missile',35.72,51.42,['hemmat missile','shahid hemmat'],'Tehran'),
    'shahid_bagheri_missile': _t('Shahid Bagheri Industrial Group','military_base','missile',35.73,51.30,['bagheri industrial','shahid bagheri'],'Tehran'),
    'irgc_sarallah_hq':      _t('IRGC Sarallah HQ Tehran','military_base','command_control',35.6950,51.4230,['sarallah','irgc headquarters tehran'],'Tehran'),
    'doshan_tappeh_afb':      _t('Doshan Tappeh Air Base','airbase','air_defense',35.7028,51.4739,['doshan tappeh','doshan tapeh'],'Tehran'),
    'tehran_telecom_tower':   _t('Tehran Milad Tower / Telecom Hub','infrastructure','communications',35.7448,51.3753,['milad tower','tehran telecom','tehran tower'],'Tehran'),
    'tehran_ministry_defense':_t('Ministry of Defense Complex','government','command_control',35.7000,51.4600,['ministry of defense','defense ministry tehran'],'Tehran'),
    'tehran_irgc_navy_hq':    _t('IRGC Navy Headquarters Tehran','military_base','naval',35.7150,51.3900,['irgc navy hq','irgc navy headquarters'],'Tehran'),
    'tehran_power_plants':    _t('Tehran Thermal Power Plants','energy','power_generation',35.6000,51.4500,['tehran power plant','besat power'],'Tehran'),
    'aja_ground_forces_hq':   _t('Army Ground Forces HQ Tehran','military_base','command_control',35.7100,51.4100,['ground forces hq','army headquarters'],'Tehran'),
    'shahid_bakeri_barracks': _t('Shahid Bakeri Barracks','military_base','army',35.7400,51.3500,['bakeri barracks','shahid bakeri'],'Tehran'),
    'karaj_ammo_depot':       _t('Karaj Ammunition Depot','military_base','ammunition',35.8200,50.9900,['karaj ammunition','karaj depot','karaj ammo'],'Tehran'),
    'tehran_gas_storage':     _t('Tehran Gas Storage Complex','energy','gas_storage',35.5500,51.5000,['tehran gas storage','gas reservoir'],'Tehran'),
    'shahid_rajaei_highway_bridge': _t('Shahid Rajaei Bridge/Infrastructure','infrastructure','transport',35.4600,51.3800,['rajaei bridge','shahid rajaei'],'Tehran'),
    'lavasan_radar':          _t('Lavasan Radar Installation','military_base','air_defense',35.8100,51.6300,['lavasan radar','lavasan military'],'Tehran'),

    # ═══════════════════════════════════════════════════════════════
    # ISFAHAN PROVINCE  (nuclear + military hub)
    # ═══════════════════════════════════════════════════════════════
    'isfahan_nuclear':        _t('Isfahan Nuclear Technology Center (UCF)','nuclear','nuclear_facility',32.67,51.68,['isfahan nuclear','ucf','uranium conversion'],'Isfahan'),
    'isfahan_airbase':        _t('Isfahan (Shahid Babaei) Air Base','airbase','air_defense',32.75,51.86,['isfahan air base','babaei air base','shahid babaei'],'Isfahan'),
    'isfahan_steel':          _t('Mobarakeh Steel Complex','industry','strategic_industry',32.35,51.51,['mobarakeh steel','isfahan steel'],'Isfahan'),
    'natanz_nuclear':         _t('Natanz Nuclear Enrichment Facility','nuclear','nuclear_facility',33.72,51.73,['natanz','enrichment'],'Isfahan'),
    'isfahan_refinery':       _t('Isfahan Oil Refinery','energy','refinery',32.59,51.73,['isfahan refinery','isfahan oil'],'Isfahan'),
    'isfahan_missile_prod':   _t('Isfahan Missile Production Facility','military_base','missile',32.70,51.75,['isfahan missile','missile production isfahan'],'Isfahan'),
    'isfahan_army_garrison':  _t('Isfahan Army Garrison','military_base','army',32.68,51.62,['isfahan garrison','isfahan army'],'Isfahan'),
    'isfahan_power_plant':    _t('Isfahan Power Plant','energy','power_generation',32.60,51.60,['isfahan power','isfahan thermal'],'Isfahan'),
    'najafabad_garrison':     _t('Najafabad Military Garrison','military_base','army',32.63,51.37,['najafabad garrison','najafabad military'],'Isfahan'),
    'shahinshahr_depot':      _t('Shahinshahr Ammunition Depot','military_base','ammunition',32.87,51.56,['shahinshahr depot','shahinshahr ammo'],'Isfahan'),
    'isfahan_electronics':    _t('Isfahan Electronics Industries','industry','strategic_industry',32.66,51.70,['isfahan electronics','electronic warfare'],'Isfahan'),
    'dorcheh_chemical':       _t('Dorcheh Chemical Complex','industry','chemical',32.61,51.55,['dorcheh chemical','isfahan chemical'],'Isfahan'),

    # ═══════════════════════════════════════════════════════════════
    # KHUZESTAN PROVINCE  (oil heartland + border)
    # ═══════════════════════════════════════════════════════════════
    'abadan_refinery':        _t('Abadan Oil Refinery','energy','refinery',30.34,48.28,['abadan refinery','abadan oil'],'Khuzestan'),
    'bandar_imam_port':       _t('Bandar Imam Khomeini Port','port','logistics',30.43,49.08,['bandar imam','imam khomeini port'],'Khuzestan'),
    'dezful_missile_base':    _t('Dezful Underground Missile Base','military_base','missile',32.38,48.40,['dezful missile','dezful base','underground missile'],'Khuzestan'),
    'ahvaz_airbase':          _t('Ahvaz Air Base (Shahid Vatanpour)','airbase','air_defense',31.34,48.76,['ahvaz air base','vatanpour','ahvaz airbase'],'Khuzestan'),
    'ahvaz_refinery':         _t('Ahvaz Oil Refinery','energy','refinery',31.30,48.70,['ahvaz refinery','ahvaz oil'],'Khuzestan'),
    'masjed_soleiman_oil':    _t('Masjed Soleiman Oil Fields','energy','oil_field',31.94,49.30,['masjed soleiman','masjid suleiman oil'],'Khuzestan'),
    'gachsaran_oil':          _t('Gachsaran Oil Field','energy','oil_field',30.36,50.80,['gachsaran oil','gachsaran field'],'Khuzestan'),
    'aghajari_oil':           _t('Aghajari Oil Field','energy','oil_field',30.73,49.86,['aghajari oil','aghajari field'],'Khuzestan'),
    'ahvaz_oil_field':        _t('Ahvaz Oil Field','energy','oil_field',31.33,48.68,['ahvaz oil field'],'Khuzestan'),
    'karoon_dam':             _t('Karoon Dam & Power Station','energy','power_generation',31.53,49.83,['karoon dam','karun dam'],'Khuzestan'),
    'mahshahr_petrochemical':  _t('Mahshahr Petrochemical Zone','energy','petrochemical',30.47,49.17,['mahshahr petrochemical','mahshahr petrochem'],'Khuzestan'),
    'omidiyeh_airbase':       _t('Omidiyeh Air Base','airbase','air_defense',30.83,49.53,['omidiyeh air base','omidiyeh airbase'],'Khuzestan'),
    'andimeshk_army_base':    _t('Andimeshk Army Base','military_base','army',32.46,48.36,['andimeshk army','andimeshk base'],'Khuzestan'),
    'kharg_island_terminal':  _t('Kharg Island Oil Terminal','energy','oil_terminal',29.23,50.33,['kharg island','kharg oil','kharg terminal'],'Khuzestan','Handles 90% of Iran oil exports'),
    'shadegan_oil':           _t('Shadegan Wetland Oil Infra','energy','oil_field',30.95,48.64,['shadegan oil'],'Khuzestan'),

    # ═══════════════════════════════════════════════════════════════
    # FARS PROVINCE  (Shiraz — southern military)
    # ═══════════════════════════════════════════════════════════════
    'shiraz_airbase':         _t('Shiraz (Shahid Doran) Air Base','airbase','air_defense',29.54,52.59,['shiraz air base','shahid doran'],'Fars'),
    'shiraz_electronics':     _t('Shiraz Electronics Industries','industry','strategic_industry',29.60,52.55,['shiraz electronics'],'Fars'),
    'shiraz_garrison':        _t('Shiraz Army Garrison','military_base','army',29.58,52.52,['shiraz garrison','shiraz army'],'Fars'),
    'marvdasht_missile':      _t('Marvdasht Missile Storage','military_base','missile',29.87,52.80,['marvdasht missile'],'Fars'),
    'shiraz_refinery':        _t('Shiraz Oil Refinery','energy','refinery',29.63,52.48,['shiraz refinery'],'Fars'),
    'persepolis_radar':       _t('Persepolis Area Radar Station','military_base','air_defense',29.93,52.89,['persepolis radar'],'Fars'),
    'firuzabad_training':     _t('Firuzabad Military Training','military_base','army',28.84,52.57,['firuzabad military','firuzabad training'],'Fars'),

    # ═══════════════════════════════════════════════════════════════
    # BUSHEHR PROVINCE  (nuclear + Persian Gulf coast)
    # ═══════════════════════════════════════════════════════════════
    'bushehr_nuclear':        _t('Bushehr Nuclear Power Plant','nuclear','nuclear_facility',28.83,50.89,['bushehr nuclear','bushehr power plant'],'Bushehr'),
    'bushehr_naval':          _t('Bushehr Naval Base','naval_base','naval',28.97,50.83,['bushehr naval','bushehr navy'],'Bushehr'),
    'bushehr_port':           _t('Bushehr Commercial Port','port','logistics',28.97,50.84,['bushehr port'],'Bushehr'),
    'asaluyeh_refinery':      _t('South Pars / Asaluyeh Gas Complex','energy','gas_refinery',27.47,52.62,['asaluyeh','south pars','pars gas'],'Bushehr','Largest natural gas field in world'),
    'kangan_gas':             _t('Kangan Gas Processing','energy','gas_refinery',27.83,52.06,['kangan gas'],'Bushehr'),
    'genaveh_port':           _t('Genaveh Port / Naval Facility','port','naval',29.58,50.52,['genaveh port','genaveh naval'],'Bushehr'),

    # ═══════════════════════════════════════════════════════════════
    # HORMOZGAN PROVINCE  (Strait of Hormuz control)
    # ═══════════════════════════════════════════════════════════════
    'bandar_abbas_naval':     _t('Bandar Abbas Naval Base','naval_base','naval',27.15,56.28,['bandar abbas','naval base','strait of hormuz'],'Hormozgan'),
    'bandar_abbas_refinery':  _t('Bandar Abbas Oil Refinery','energy','refinery',27.20,56.22,['bandar abbas refinery'],'Hormozgan'),
    'jask_naval':             _t('Jask Naval Base','naval_base','naval',25.64,57.77,['jask naval','jask base'],'Hormozgan'),
    'qeshm_island_naval':     _t('Qeshm Island Naval / IRGC','naval_base','naval',26.95,56.27,['qeshm island','qeshm naval'],'Hormozgan'),
    'abu_musa_island':        _t('Abu Musa Island Military','military_base','naval',25.87,55.03,['abu musa','abu musa island'],'Hormozgan'),
    'hormuz_missile_battery':  _t('Strait of Hormuz Missile Batteries','military_base','coastal_defense',26.45,56.45,['hormuz missile','coastal missile battery'],'Hormozgan'),
    'bandar_lengeh_port':     _t('Bandar Lengeh Port','port','logistics',26.56,54.88,['bandar lengeh'],'Hormozgan'),
    'minab_airfield':         _t('Minab Airfield','airbase','air_defense',27.13,57.07,['minab airfield','minab air'],'Hormozgan'),
    'sirri_island_oil':       _t('Sirri Island Oil Terminal','energy','oil_terminal',25.89,54.54,['sirri island','sirri oil'],'Hormozgan'),
    'larak_island':           _t('Larak Island Military Post','military_base','naval',26.86,56.35,['larak island'],'Hormozgan'),

    # ═══════════════════════════════════════════════════════════════
    # KHORASAN PROVINCES  (NE — air defense + missile)
    # ═══════════════════════════════════════════════════════════════
    'mashhad_airbase':        _t('Mashhad (Shahid Hasheminejad) Air Base','airbase','air_defense',36.24,59.64,['mashhad air base','hasheminejad'],'Khorasan'),
    'mashhad_garrison':       _t('Mashhad Army Garrison','military_base','army',36.28,59.55,['mashhad garrison','mashhad army'],'Khorasan'),
    'birjand_airbase':        _t('Birjand Air Base','airbase','air_defense',32.90,59.27,['birjand air base','birjand airbase'],'Khorasan'),
    'tabas_airbase':          _t('Tabas Emergency Air Base','airbase','air_defense',33.67,56.90,['tabas air base','tabas airfield'],'Khorasan'),
    'neyshabur_ammo':         _t('Neyshabur Ammunition Depot','military_base','ammunition',36.21,58.79,['neyshabur ammo','neyshabur ammunition'],'Khorasan'),
    'torbat_missile':         _t('Torbat-e-Heydarieh Missile Site','military_base','missile',35.27,59.22,['torbat missile','torbat heydarieh'],'Khorasan'),

    # ═══════════════════════════════════════════════════════════════
    # KERMANSHAH PROVINCE  (western border with Iraq)
    # ═══════════════════════════════════════════════════════════════
    'kermanshah_airbase':     _t('Kermanshah Air Base','airbase','air_defense',34.35,47.16,['kermanshah air base'],'Kermanshah'),
    'kermanshah_garrison':    _t('Kermanshah Army Garrison','military_base','army',34.32,47.10,['kermanshah garrison','kermanshah army'],'Kermanshah'),
    'bisotun_base':           _t('Bisotun Military Base','military_base','army',34.39,47.44,['bisotun base','bisotun military'],'Kermanshah'),
    'eslamabad_base':         _t('Eslamabad-e-Gharb Base','military_base','army',34.11,46.53,['eslamabad gharb','eslamabad base'],'Kermanshah'),
    'kangavar_arms_depot':    _t('Kangavar Arms Depot','military_base','ammunition',34.50,47.97,['kangavar arms','kangavar depot'],'Kermanshah'),

    # ═══════════════════════════════════════════════════════════════
    # QOM PROVINCE  (nuclear)
    # ═══════════════════════════════════════════════════════════════
    'fordow_nuclear':         _t('Fordow Fuel Enrichment Plant','nuclear','nuclear_facility',34.89,51.26,['fordow','fuel enrichment'],'Qom'),
    'qom_garrison':           _t('Qom Military Garrison','military_base','army',34.60,50.85,['qom garrison','qom military'],'Qom'),
    'qom_irgc_base':          _t('Qom IRGC Regional Base','military_base','irgc',34.62,50.90,['qom irgc'],'Qom'),

    # ═══════════════════════════════════════════════════════════════
    # SEMNAN PROVINCE  (missile testing + space)
    # ═══════════════════════════════════════════════════════════════
    'shahrud_missile':        _t('Shahrud Missile Test Site','military_base','missile',36.06,55.57,['shahrud missile','shahrud test'],'Semnan'),
    'semnan_space_center':    _t('Semnan Space Launch Center','military_base','missile',35.23,53.92,['semnan space','semnan launch','imam khomeini space'],'Semnan'),
    'semnan_garrison':        _t('Semnan Military Garrison','military_base','army',35.55,53.40,['semnan garrison'],'Semnan'),
    'garmsar_depot':          _t('Garmsar Military Depot','military_base','ammunition',35.21,52.34,['garmsar depot','garmsar military'],'Semnan'),

    # ═══════════════════════════════════════════════════════════════
    # EAST AZERBAIJAN  (NW border)
    # ═══════════════════════════════════════════════════════════════
    'tabriz_airbase':         _t('Tabriz Air Base','airbase','air_defense',38.13,46.24,['tabriz air base','tabriz military'],'East Azerbaijan'),
    'tabriz_garrison':        _t('Tabriz Army Garrison','military_base','army',38.07,46.30,['tabriz garrison','tabriz army'],'East Azerbaijan'),
    'tabriz_refinery':        _t('Tabriz Oil Refinery','energy','refinery',38.00,46.35,['tabriz refinery','tabriz oil'],'East Azerbaijan'),
    'tabriz_machinery':       _t('Tabriz Machinery Manufacturing','industry','strategic_industry',38.05,46.35,['tabriz machinery','tabriz manufacturing'],'East Azerbaijan'),
    'sahand_air_defense':     _t('Sahand Air Defense Site','military_base','air_defense',37.75,46.10,['sahand air defense','sahand radar'],'East Azerbaijan'),
    'urmia_airbase':          _t('Urmia Air Base','airbase','air_defense',37.67,45.07,['urmia air base','urmia airbase'],'West Azerbaijan'),
    'urmia_garrison':         _t('Urmia Army Garrison','military_base','army',37.55,45.04,['urmia garrison','urmia army'],'West Azerbaijan'),

    # ═══════════════════════════════════════════════════════════════
    # MARKAZI PROVINCE  (Arak — heavy water + industry)
    # ═══════════════════════════════════════════════════════════════
    'arak_heavy_water':       _t('Arak Heavy Water Reactor','nuclear','nuclear_facility',34.04,49.24,['arak heavy water','arak reactor','arak nuclear','ir-40'],'Markazi'),
    'arak_machinery':         _t('Arak Machine Manufacturing','industry','strategic_industry',34.09,49.70,['arak machinery','arak machine','hepco'],'Markazi'),
    'arak_refinery':          _t('Arak Oil Refinery','energy','refinery',34.05,49.65,['arak refinery','arak oil'],'Markazi'),
    'arak_garrison':          _t('Arak Military Garrison','military_base','army',34.10,49.68,['arak garrison','arak military'],'Markazi'),
    'arak_aluminum':          _t('Iran Aluminum Company (IRALCO)','industry','strategic_industry',34.06,49.72,['iralco','arak aluminum'],'Markazi'),

    # ═══════════════════════════════════════════════════════════════
    # LORESTAN PROVINCE  (western mountains)
    # ═══════════════════════════════════════════════════════════════
    'khorramabad_airbase':    _t('Khorramabad Air Base','airbase','air_defense',33.44,48.28,['khorramabad air base','khorramabad airbase'],'Lorestan'),
    'khorramabad_garrison':   _t('Khorramabad Garrison','military_base','army',33.49,48.35,['khorramabad garrison'],'Lorestan'),
    'doroud_ammo':            _t('Doroud Ammunition Factory','military_base','ammunition',33.49,49.06,['doroud ammo','doroud ammunition'],'Lorestan'),
    'borujerd_garrison':      _t('Borujerd Military Garrison','military_base','army',33.90,48.75,['borujerd garrison','borujerd army'],'Lorestan'),

    # ═══════════════════════════════════════════════════════════════
    # KURDISTAN / ILAM  (western border)
    # ═══════════════════════════════════════════════════════════════
    'sanandaj_garrison':      _t('Sanandaj Military Garrison','military_base','army',35.31,47.00,['sanandaj garrison','sanandaj army'],'Kurdistan'),
    'sanandaj_airbase':       _t('Sanandaj Air Base','airbase','air_defense',35.25,47.01,['sanandaj air base'],'Kurdistan'),
    'ilam_garrison':          _t('Ilam Border Garrison','military_base','army',33.64,46.42,['ilam garrison','ilam military'],'Ilam'),
    'mehran_border_base':     _t('Mehran Border Military Base','military_base','army',33.12,46.17,['mehran border','mehran base'],'Ilam'),

    # ═══════════════════════════════════════════════════════════════
    # KERMAN PROVINCE  (SE — missile + copper)
    # ═══════════════════════════════════════════════════════════════
    'kerman_garrison':        _t('Kerman Army Garrison','military_base','army',30.28,57.08,['kerman garrison','kerman army'],'Kerman'),
    'rafsanjan_copper':       _t('Rafsanjan Copper Complex','industry','strategic_industry',30.41,55.99,['rafsanjan copper'],'Kerman'),
    'bam_garrison':           _t('Bam Military Garrison','military_base','army',29.10,58.36,['bam garrison','bam military'],'Kerman'),
    'sirjan_depot':           _t('Sirjan Military Depot','military_base','ammunition',29.45,55.68,['sirjan depot','sirjan military'],'Kerman'),

    # ═══════════════════════════════════════════════════════════════
    # SISTAN-BALUCHESTAN  (SE border + Chabahar)
    # ═══════════════════════════════════════════════════════════════
    'chabahar_naval':         _t('Chabahar Naval Base','naval_base','naval',25.29,60.64,['chabahar naval','chabahar base'],'Sistan-Baluchestan'),
    'chabahar_port':          _t('Chabahar Port (Shahid Beheshti)','port','logistics',25.30,60.62,['chabahar port','shahid beheshti port'],'Sistan-Baluchestan'),
    'zahedan_airbase':        _t('Zahedan Air Base','airbase','air_defense',29.48,60.91,['zahedan air base','zahedan airbase'],'Sistan-Baluchestan'),
    'zahedan_garrison':       _t('Zahedan Army Garrison','military_base','army',29.50,60.86,['zahedan garrison'],'Sistan-Baluchestan'),
    'iranshahr_garrison':     _t('Iranshahr Military Base','military_base','army',27.20,60.69,['iranshahr garrison','iranshahr military'],'Sistan-Baluchestan'),
    'konarak_naval':          _t('Konarak Naval Facility','naval_base','naval',25.35,60.38,['konarak naval'],'Sistan-Baluchestan'),

    # ═══════════════════════════════════════════════════════════════
    # MAZANDARAN / GOLESTAN  (Caspian coast)
    # ═══════════════════════════════════════════════════════════════
    'noshahr_naval':          _t('Noshahr Naval Base','naval_base','naval',36.65,51.50,['noshahr naval','noshahr navy'],'Mazandaran'),
    'babol_garrison':         _t('Babol Military Garrison','military_base','army',36.55,52.68,['babol garrison','babol army'],'Mazandaran'),
    'sari_garrison':          _t('Sari Military Garrison','military_base','army',36.57,53.06,['sari garrison','sari army'],'Mazandaran'),
    'bandar_torkaman':        _t('Bandar Torkaman Naval Post','naval_base','naval',36.89,54.07,['bandar torkaman','torkaman naval'],'Golestan'),
    'gorgan_training':        _t('Gorgan Military Training Center','military_base','army',36.84,54.44,['gorgan training','gorgan military'],'Golestan'),
    'amol_radar':             _t('Amol Long-Range Radar','military_base','air_defense',36.47,52.35,['amol radar','amol air defense'],'Mazandaran'),
    'neka_power_plant':       _t('Neka Thermal Power Plant','energy','power_generation',36.64,53.29,['neka power','neka thermal'],'Mazandaran'),

    # ═══════════════════════════════════════════════════════════════
    # HAMADAN PROVINCE
    # ═══════════════════════════════════════════════════════════════
    'hamadan_airbase':        _t('Hamadan (Shahid Nojeh) Air Base','airbase','air_defense',35.21,48.65,['hamadan air base','nojeh air base','shahid nojeh'],'Hamadan'),
    'hamadan_garrison':       _t('Hamadan Army Garrison','military_base','army',34.80,48.52,['hamadan garrison','hamadan army'],'Hamadan'),
    'malayer_depot':          _t('Malayer Ammunition Depot','military_base','ammunition',34.30,48.82,['malayer depot','malayer ammo'],'Hamadan'),

    # ═══════════════════════════════════════════════════════════════
    # ZANJAN / ARDABIL  (NW)
    # ═══════════════════════════════════════════════════════════════
    'zanjan_garrison':        _t('Zanjan Military Garrison','military_base','army',36.67,48.50,['zanjan garrison'],'Zanjan'),
    'ardabil_garrison':       _t('Ardabil Military Garrison','military_base','army',38.25,48.29,['ardabil garrison','ardabil army'],'Ardabil'),
    'parsabad_border':        _t('Parsabad Border Garrison','military_base','army',39.65,47.92,['parsabad border','parsabad military'],'Ardabil'),

    # ═══════════════════════════════════════════════════════════════
    # YAZD PROVINCE  (nuclear research + desert)
    # ═══════════════════════════════════════════════════════════════
    'yazd_radiation_center':  _t('Yazd Radiation Processing Center','nuclear','nuclear_facility',31.89,54.37,['yazd radiation','yazd nuclear'],'Yazd'),
    'yazd_garrison':          _t('Yazd Military Garrison','military_base','army',31.90,54.35,['yazd garrison','yazd army'],'Yazd'),
    'saghand_uranium_mine':   _t('Saghand Uranium Mine','nuclear','nuclear_facility',32.58,55.17,['saghand uranium','saghand mine'],'Yazd'),
    'ardakan_yellowcake':     _t('Ardakan Yellowcake Production','nuclear','nuclear_facility',32.31,54.02,['ardakan yellowcake','ardakan uranium'],'Yazd'),

    # ═══════════════════════════════════════════════════════════════
    # CHAHARMAHAL-BAKHTIARI / KOHGILUYEH
    # ═══════════════════════════════════════════════════════════════
    'shahrekord_garrison':    _t('Shahrekord Garrison','military_base','army',32.33,50.86,['shahrekord garrison'],'Chaharmahal'),
    'yasuj_garrison':         _t('Yasuj Military Garrison','military_base','army',30.67,51.59,['yasuj garrison','yasuj army'],'Kohgiluyeh'),

    # ═══════════════════════════════════════════════════════════════
    # MAJOR ENERGY INFRASTRUCTURE  (refineries + pipelines)
    # ═══════════════════════════════════════════════════════════════
    'bandar_abbas_refinery_star': _t('Persian Gulf Star Refinery','energy','refinery',27.16,56.08,['persian gulf star','star refinery','bandar abbas star'],'Hormozgan','Largest gas condensate refinery'),
    'lavan_island_refinery':  _t('Lavan Island Oil Refinery','energy','refinery',26.81,53.36,['lavan island','lavan refinery'],'Hormozgan'),
    'kerman_refinery':        _t('Kerman Oil Refinery','energy','refinery',30.24,57.10,['kerman refinery'],'Kerman'),
    'shazand_refinery':       _t('Shazand (Imam Khomeini) Refinery','energy','refinery',33.93,49.43,['shazand refinery','imam khomeini refinery'],'Markazi'),
    'bidboland_gas':          _t('Bidboland Gas Processing','energy','gas_refinery',31.16,49.78,['bidboland gas'],'Khuzestan'),
    'fajr_jam_gas':           _t('Fajr-e-Jam Gas Refinery','energy','gas_refinery',27.84,52.30,['fajr jam','fajr gas'],'Bushehr'),
    'sarkhun_gas':            _t('Sarkhun Gas Storage','energy','gas_storage',27.30,56.00,['sarkhun gas'],'Hormozgan'),
    'hashtgerd_pipeline':     _t('Hashtgerd Gas Pipeline Hub','energy','pipeline',35.96,50.68,['hashtgerd pipeline','hashtgerd gas'],'Alborz'),
    'goureh_jask_pipeline':   _t('Goureh-Jask Oil Pipeline','energy','pipeline',27.50,57.50,['goureh jask','jask pipeline'],'Hormozgan','Strategic pipeline bypassing Hormuz'),

    # ═══════════════════════════════════════════════════════════════
    # IRGC / BASIJ REGIONAL COMMAND CENTERS
    # ═══════════════════════════════════════════════════════════════
    'irgc_isfahan_hq':        _t('IRGC Isfahan Regional HQ','military_base','irgc',32.65,51.66,['irgc isfahan'],'Isfahan'),
    'irgc_shiraz_hq':         _t('IRGC Fars Regional HQ','military_base','irgc',29.61,52.53,['irgc shiraz','irgc fars'],'Fars'),
    'irgc_ahvaz_hq':          _t('IRGC Khuzestan Regional HQ','military_base','irgc',31.31,48.68,['irgc ahvaz','irgc khuzestan'],'Khuzestan'),
    'irgc_mashhad_hq':        _t('IRGC Khorasan Regional HQ','military_base','irgc',36.29,59.60,['irgc mashhad','irgc khorasan'],'Khorasan'),
    'irgc_tabriz_hq':         _t('IRGC East Azerbaijan HQ','military_base','irgc',38.08,46.28,['irgc tabriz'],'East Azerbaijan'),
    'irgc_kermanshah_hq':     _t('IRGC Kermanshah HQ','military_base','irgc',34.33,47.08,['irgc kermanshah'],'Kermanshah'),
    'irgc_bandar_abbas_hq':   _t('IRGC Hormozgan HQ','military_base','irgc',27.19,56.26,['irgc bandar abbas','irgc hormozgan'],'Hormozgan'),

    # ═══════════════════════════════════════════════════════════════
    # AIR DEFENSE NETWORK  (S-300 / Bavar-373 sites)
    # ═══════════════════════════════════════════════════════════════
    'ad_tehran_north':        _t('Tehran North Air Defense','military_base','air_defense',35.85,51.45,['tehran air defense north'],'Tehran'),
    'ad_tehran_south':        _t('Tehran South Air Defense','military_base','air_defense',35.55,51.35,['tehran air defense south'],'Tehran'),
    'ad_isfahan':             _t('Isfahan Air Defense Battery','military_base','air_defense',32.72,51.72,['isfahan air defense'],'Isfahan'),
    'ad_bushehr':             _t('Bushehr Air Defense Battery','military_base','air_defense',28.90,50.85,['bushehr air defense'],'Bushehr'),
    'ad_natanz':              _t('Natanz Air Defense Battery','military_base','air_defense',33.73,51.70,['natanz air defense'],'Isfahan'),
    'ad_bandar_abbas':        _t('Bandar Abbas Air Defense','military_base','air_defense',27.18,56.30,['bandar abbas air defense'],'Hormozgan'),
    'ad_khatam_al_anbia':     _t('Khatam al-Anbia AD HQ','military_base','air_defense',35.70,51.40,['khatam al anbia','khatam air defense'],'Tehran','Central air defense command'),
    'ad_tabriz':              _t('Tabriz Air Defense Battery','military_base','air_defense',38.10,46.22,['tabriz air defense'],'East Azerbaijan'),

    # ═══════════════════════════════════════════════════════════════
    # GOVERNMENT / STRATEGIC BUILDINGS
    # ═══════════════════════════════════════════════════════════════
    'supreme_leader_compound': _t('Supreme Leader Compound','government','command_control',35.70,51.42,['supreme leader compound','rahbar compound','beit rahbari'],'Tehran'),
    'majlis_parliament':      _t('Islamic Parliament (Majlis)','government','government',35.68,51.42,['majlis','parliament','islamic parliament'],'Tehran'),
    'presidency_saadabad':    _t('Sa\'adabad Presidential Complex','government','command_control',35.82,51.41,['saadabad','sa\'adabad','presidential palace'],'Tehran'),
    'expediency_council':     _t('Expediency Council Building','government','government',35.70,51.41,['expediency council'],'Tehran'),
    'guardian_council':       _t('Guardian Council Building','government','government',35.69,51.42,['guardian council'],'Tehran'),
    'irib_broadcasting':      _t('IRIB State Broadcasting HQ','infrastructure','communications',35.72,51.38,['irib','state broadcasting','irib hq','iran tv','islamic republic broadcasting'],'Tehran'),
    'irib_jaam_e_jam':        _t('IRIB Jaam-e-Jam Tower Complex','infrastructure','communications',35.7636,51.4108,['jaam e jam','jame jam tower','tv tower tehran'],'Tehran','Main TV broadcast tower'),
    'irib_radio_tehran':      _t('IRIB Radio Tehran Transmitter','infrastructure','communications',35.6950,51.4400,['radio tehran','irib radio'],'Tehran'),
    'press_tv_hq':            _t('Press TV Headquarters','infrastructure','communications',35.7180,51.3950,['press tv','presstv'],'Tehran'),
    'mois_intelligence_hq':   _t('MOIS Intelligence Ministry HQ','government','command_control',35.69,51.43,['mois','intelligence ministry'],'Tehran'),
    'interior_ministry':      _t('Interior Ministry (Keshvar)','government','government',35.6990,51.4210,['interior ministry','vezarat keshvar'],'Tehran'),
    'foreign_ministry':       _t('Foreign Ministry','government','government',35.7120,51.4050,['foreign ministry','vezarat kharejeh'],'Tehran'),
    'oil_ministry':           _t('Oil Ministry Building','government','government',35.7050,51.4180,['oil ministry','vezarat naft'],'Tehran'),
    
    # ═══════════════════════════════════════════════════════════════
    # MEDIA / PROPAGANDA INFRASTRUCTURE
    # ═══════════════════════════════════════════════════════════════
    'tehran_tv_studios':      _t('Tehran TV Studios Complex','infrastructure','communications',35.7200,51.3850,['tehran tv studios','irib studios'],'Tehran'),
    'fars_news_agency':       _t('Fars News Agency HQ','infrastructure','communications',35.7000,51.4300,['fars news','farsnews'],'Tehran'),
    'tasnim_news':            _t('Tasnim News Agency','infrastructure','communications',35.7100,51.4100,['tasnim news','tasnim'],'Tehran'),
    'mehr_news':              _t('Mehr News Agency','infrastructure','communications',35.7050,51.4200,['mehr news','mehrnews'],'Tehran'),
    'isna_news':              _t('ISNA Student News Agency','infrastructure','communications',35.7080,51.4150,['isna','student news'],'Tehran'),
    'khamenei_media':         _t('Khamenei.ir Media Center','infrastructure','communications',35.7010,51.4220,['khamenei.ir','leader website'],'Tehran'),
    
    # ═══════════════════════════════════════════════════════════════
    # CONFIRMED STRIKE LOCATIONS (March 2026)
    # ═══════════════════════════════════════════════════════════════
    'tehran_strike_zone_1':   _t('Tehran Northern Strike Zone','strike_zone','confirmed_strike',35.7800,51.4200,['tehran north strike','tehran bombing north'],'Tehran','Confirmed strike zone March 2026'),
    'tehran_strike_zone_2':   _t('Tehran Central Strike Zone','strike_zone','confirmed_strike',35.6900,51.4100,['tehran center strike','tehran central bombing'],'Tehran','Confirmed strike zone March 2026'),
    'tehran_strike_zone_3':   _t('Tehran South Strike Zone','strike_zone','confirmed_strike',35.6200,51.4000,['tehran south strike','tehran southern bombing'],'Tehran','Confirmed strike zone March 2026'),
    'isfahan_strike_zone_1':  _t('Isfahan Strike Zone','strike_zone','confirmed_strike',32.6700,51.6800,['isfahan strike','isfahan bombing'],'Isfahan','Confirmed strike zone'),
    
    # ═══════════════════════════════════════════════════════════════
    # ADDITIONAL CIVILIAN INFRASTRUCTURE
    # ═══════════════════════════════════════════════════════════════
    'tehran_bazaar':          _t('Tehran Grand Bazaar','infrastructure','commercial',35.6724,51.4234,['tehran bazaar','grand bazaar'],'Tehran'),
    'azadi_tower':            _t('Azadi Tower Complex','infrastructure','landmark',35.6997,51.3381,['azadi tower','shahyad','freedom tower'],'Tehran'),
    'tabiat_bridge':          _t('Tabiat Bridge','infrastructure','landmark',35.7677,51.4037,['tabiat bridge','nature bridge'],'Tehran'),
    'tehran_university':      _t('University of Tehran','infrastructure','education',35.7033,51.3969,['tehran university','daneshgah tehran'],'Tehran'),
    'sharif_university':      _t('Sharif University of Technology','infrastructure','education',35.7025,51.3515,['sharif university','sharif tech'],'Tehran'),
    'imam_khomeini_hospital': _t('Imam Khomeini Hospital Complex','infrastructure','medical',35.6936,51.4139,['imam khomeini hospital','tehran hospital'],'Tehran'),
    'milad_hospital':         _t('Milad Hospital','infrastructure','medical',35.7440,51.3760,['milad hospital'],'Tehran'),
    'tehran_metro_hub':       _t('Tehran Metro Central Hub','infrastructure','transport',35.6960,51.4100,['tehran metro','metro tehran'],'Tehran'),
    'rah_ahan_station':       _t('Tehran Railway Station (Rah Ahan)','infrastructure','transport',35.6770,51.4470,['rah ahan','tehran railway','tehran train station'],'Tehran'),
    
    # ═══════════════════════════════════════════════════════════════
    # INDUSTRIAL / MANUFACTURING
    # ═══════════════════════════════════════════════════════════════
    'iran_khodro':            _t('Iran Khodro Auto Factory','industry','manufacturing',35.7580,51.2700,['iran khodro','ikco','irankhodro'],'Tehran','Largest automaker'),
    'saipa_factory':          _t('SAIPA Auto Factory','industry','manufacturing',35.6400,51.2600,['saipa','saipa auto'],'Tehran'),
    'hepco_construction':     _t('HEPCO Heavy Equipment','industry','manufacturing',34.0950,49.7200,['hepco','heavy equipment'],'Markazi'),
    'azarab_industries':      _t('Azarab Industries (heavy machinery)','industry','manufacturing',34.0880,49.7150,['azarab','azarab industries'],'Markazi'),
    'mapna_group_tehran':     _t('MAPNA Group (power equipment)','industry','manufacturing',35.7350,51.4650,['mapna','mapna group'],'Tehran'),
    'tehran_cement':          _t('Tehran Cement Factory','industry','manufacturing',35.5800,51.5200,['tehran cement'],'Tehran'),
    
    # ═══════════════════════════════════════════════════════════════
    # OIL & GAS INFRASTRUCTURE
    # ═══════════════════════════════════════════════════════════════
    'south_pars_onshore':     _t('South Pars Onshore Facilities','energy','gas_field',27.5200,52.5800,['south pars','pars gas'],'Bushehr'),
    'asaluyeh_gas_complex':   _t('Asaluyeh Gas Processing Complex','energy','gas_processing',27.4700,52.6200,['asaluyeh','asaluyeh gas'],'Bushehr'),
    'bandar_abbas_refinery':  _t('Bandar Abbas Oil Refinery','energy','refinery',27.2000,56.2500,['bandar abbas refinery'],'Hormozgan'),
    'lavan_refinery':         _t('Lavan Island Refinery','energy','refinery',26.8100,53.3600,['lavan refinery','lavan island'],'Hormozgan'),
    'tabriz_refinery':        _t('Tabriz Oil Refinery','energy','refinery',38.1500,46.1800,['tabriz refinery'],'East Azerbaijan'),
    'shiraz_refinery':        _t('Shiraz Oil Refinery','energy','refinery',29.6300,52.4800,['shiraz refinery'],'Fars'),
    'arak_refinery':          _t('Arak Oil Refinery','energy','refinery',34.0500,49.6800,['arak refinery'],'Markazi'),
    'kermanshah_refinery':    _t('Kermanshah Oil Refinery','energy','refinery',34.3800,47.0200,['kermanshah refinery'],'Kermanshah'),
    
    # ═══════════════════════════════════════════════════════════════
    # PORTS & LOGISTICS
    # ═══════════════════════════════════════════════════════════════
    'shahid_rajaei_port':     _t('Shahid Rajaei Port (Bandar Abbas)','port','logistics',27.1200,56.0500,['shahid rajaei port','bandar abbas port'],'Hormozgan'),
    'chabahar_port':          _t('Chabahar Port','port','logistics',25.2900,60.6400,['chabahar port','chabahar'],'Sistan-Baluchestan'),
    'khorramshahr_port':      _t('Khorramshahr Port','port','logistics',30.4400,48.1600,['khorramshahr port'],'Khuzestan'),
    'anzali_port':            _t('Anzali Port (Caspian)','port','logistics',37.4700,49.4600,['anzali port','bandar anzali'],'Gilan'),
    'nowshahr_port':          _t('Nowshahr Port (Caspian)','port','logistics',36.6500,51.5000,['nowshahr port','noshahr'],'Mazandaran'),
    
    # ═══════════════════════════════════════════════════════════════
    # RELIGIOUS / CULTURAL SITES (for civilian damage tracking)
    # ═══════════════════════════════════════════════════════════════
    'imam_reza_shrine':       _t('Imam Reza Shrine Complex','religious','religious_site',36.2879,59.6168,['imam reza shrine','haram mashhad','astan quds'],'Khorasan'),
    'qom_shrine':             _t('Fatima Masumeh Shrine','religious','religious_site',34.6416,50.8762,['qom shrine','masumeh shrine','fatima masumeh'],'Qom'),
    'shah_cheragh_shrine':    _t('Shah Cheragh Shrine','religious','religious_site',29.6070,52.5408,['shah cheragh','shiraz shrine'],'Fars'),

    # ═══════════════════════════════════════════════════════════════
    # CRITICAL INFRASTRUCTURE  (dams, power, water, telecom)
    # ═══════════════════════════════════════════════════════════════
    'isfahan_power_station':  _t('Isfahan Combined Cycle Power','energy','power_generation',32.58,51.75,['isfahan power station'],'Isfahan'),
    'ramin_power_plant':      _t('Ramin Power Plant Ahvaz','energy','power_generation',31.40,48.75,['ramin power','ahvaz power'],'Khuzestan'),
    'shahid_rajaei_power':    _t('Shahid Rajaei Power Plant','energy','power_generation',36.07,52.95,['shahid rajaei power','qaemshahr power'],'Mazandaran'),
    'montazer_qaem_power':    _t('Montazer Qaem Power Plant','energy','power_generation',35.61,51.38,['montazer qaem','tehran south power'],'Tehran'),
    'karun3_dam':             _t('Karun-3 Hydroelectric Dam','energy','power_generation',31.93,49.90,['karun 3 dam','karun dam'],'Khuzestan'),
    'dez_dam':                _t('Dez Dam & Hydroelectric','energy','power_generation',32.61,48.47,['dez dam'],'Khuzestan'),
    'iran_telecom_infrastructure': _t('Iran Telecommunication Infra Hub','infrastructure','communications',35.73,51.40,['iran telecom','tic hub'],'Tehran'),
}

# Keywords for GDELT searches
OSINT_SEARCH_QUERIES = [
    'israel strike iran',
    'IDF iran operation',
    'iran military base attacked',
    'iran air defense destroyed',
    'iran nuclear facility strike',
    'iran refinery attack',
    'iran missile site destroyed',
    'iran bomb damage',
    'iran explosion military',
    'isfahan attack',
    'tehran strike',
    'iran war damage satellite',
    'iran IRGC base hit',
    'iran air base strike',
    # NEW: Media / Infrastructure targets
    'IRIB destroyed',
    'iran tv hit',
    'iran broadcasting strike',
    'tehran tv tower',
    'press tv destroyed',
    'iran news agency bombed',
    'tehran infrastructure damage',
    'iran power plant strike',
    'iran oil refinery explosion',
    'iran gas facility attack',
    'tehran civilian damage',
    'iran bridge destroyed',
    'iran factory bombing',
    'iran telecommunications down',
    # NEW: Specific location searches
    'milad tower damage',
    'azadi tower strike',
    'tehran bazaar explosion',
    'iran port attack',
    'bandar abbas strike',
    'chabahar attack',
    'asaluyeh explosion',
    'south pars damage',
    # NEW: General war terms
    'iran war casualties',
    'iran bombing campaign',
    'israel iran war',
    'iran infrastructure destroyed',
    'iran civilian casualties',
]

# Location name → coordinate mapping for extracting locations from text
LOCATION_KEYWORDS = {}
for tid, target in KNOWN_TARGETS.items():
    for kw in target['keywords']:
        LOCATION_KEYWORDS[kw.lower()] = {
            'target_id': tid,
            'lat': target['lat'],
            'lon': target['lon'],
            'name': target['name'],
            'type': target['type']
        }
# Also add province names
PROVINCE_COORDS = {
    'tehran': (35.69, 51.39), 'isfahan': (32.65, 51.67),
    'shiraz': (29.59, 52.58), 'tabriz': (38.07, 46.30),
    'mashhad': (36.30, 59.60), 'bushehr': (28.97, 50.84),
    'bandar abbas': (27.18, 56.28), 'kermanshah': (34.31, 47.07),
    'ahvaz': (31.32, 48.67), 'abadan': (30.34, 48.28),
    'khuzestan': (31.32, 48.67), 'qom': (34.64, 50.88),
    'arak': (34.09, 49.70), 'semnan': (35.58, 53.39),
    'dezful': (32.38, 48.40), 'kharg island': (29.23, 50.33),
    'chabahar': (25.29, 60.64), 'kerman': (30.28, 57.08),
    'hamadan': (34.80, 48.52), 'sanandaj': (35.31, 47.00),
    'urmia': (37.55, 45.04), 'zanjan': (36.67, 48.50),
    'ardabil': (38.25, 48.29), 'yazd': (31.89, 54.37),
    'khorramabad': (33.49, 48.35), 'ilam': (33.64, 46.42),
    'gorgan': (36.84, 54.44), 'sari': (36.57, 53.06),
    'karaj': (35.82, 50.99), 'natanz': (33.72, 51.73),
    'fordow': (34.89, 51.26), 'parchin': (35.52, 51.77),
    'khojir': (35.63, 51.67), 'jask': (25.64, 57.77),
    'noshahr': (36.65, 51.50), 'birjand': (32.90, 59.27),
    'zahedan': (29.50, 60.86), 'bam': (29.10, 58.36),
    'rafsanjan': (30.41, 55.99), 'sirjan': (29.45, 55.68),
    'persepolis': (29.93, 52.89), 'asaluyeh': (27.47, 52.62),
    'bandar lengeh': (26.56, 54.88), 'qeshm': (26.95, 56.27),
    'hormuz': (26.45, 56.45), 'lavan': (26.81, 53.36),
    'mahshahr': (30.47, 49.17), 'gachsaran': (30.36, 50.80),
    'omidiyeh': (30.83, 49.53), 'doroud': (33.49, 49.06),
    'borujerd': (33.90, 48.75), 'malayer': (34.30, 48.82),
    'shahrekord': (32.33, 50.86), 'yasuj': (30.67, 51.59),
    'tabas': (33.67, 56.90),
}


class OSINTEngine:
    """
    Collects and processes open-source intelligence about strikes on Iran.
    Uses free APIs (GDELT) + pre-compiled known targets database.
    
    PERFORMANCE: Results are cached in-memory for 5 minutes to avoid
    slow repeated GDELT API calls (rate limited to 1 req/5s).
    """
    
    # In-memory cache for OSINT results
    _cache = {}
    _cache_ttl = 300  # 5 minutes

    def __init__(self, db_path='timelapse_output/osint_attacks.db'):
        self.db_path = db_path
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'IranDamageAssessment/5.0 OSINT'
        })
        self._init_db()
    
    def _get_cached(self, key):
        """Get cached value if not expired."""
        if key in self._cache:
            data, timestamp = self._cache[key]
            if time.time() - timestamp < self._cache_ttl:
                print(f"[OSINT] Cache HIT: {key}")
                return data
        return None
    
    def _set_cached(self, key, value):
        """Cache a value with current timestamp."""
        self._cache[key] = (value, time.time())
        print(f"[OSINT] Cache SET: {key}")

    def _init_db(self):
        """Create the attacks/evidence database if it doesn't exist."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute('''CREATE TABLE IF NOT EXISTS strikes (
            id TEXT PRIMARY KEY,
            target_id TEXT,
            target_name TEXT,
            target_type TEXT,
            lat REAL, lon REAL,
            date TEXT,
            province TEXT,
            description TEXT,
            confidence TEXT DEFAULT 'unconfirmed',
            source_count INTEGER DEFAULT 0,
            satellite_checked INTEGER DEFAULT 0,
            satellite_confirmed INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS evidence (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            strike_id TEXT,
            source_type TEXT,
            source_name TEXT,
            url TEXT,
            title TEXT,
            snippet TEXT,
            date TEXT,
            relevance_score REAL DEFAULT 0.5,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(strike_id) REFERENCES strikes(id)
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS osint_articles (
            id TEXT PRIMARY KEY,
            url TEXT,
            title TEXT,
            domain TEXT,
            date TEXT,
            language TEXT,
            matched_targets TEXT,
            matched_locations TEXT,
            relevance_score REAL DEFAULT 0,
            processed INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''')

        conn.commit()
        conn.close()

    # ────────────────────────────────────────────────────────────
    # GDELT NEWS SCANNING
    # ────────────────────────────────────────────────────────────

    def scan_gdelt(self, query=None, max_records=25, days_back=7):
        """
        Scan GDELT for recent articles about Iran strikes.
        Returns list of articles with matched target locations.
        """
        if query is None:
            results = []
            import time
            for q in OSINT_SEARCH_QUERIES[:5]:  # Use top 5 queries
                articles = self._gdelt_search(q, max_records=max_records)
                results.extend(articles)
                # GDELT rate limit: 1 request per 5 seconds
                time.sleep(6)
            # Deduplicate by URL
            seen = set()
            unique = []
            for a in results:
                if a.get('url') not in seen:
                    seen.add(a.get('url'))
                    unique.append(a)
            return unique
        else:
            return self._gdelt_search(query, max_records=max_records)

    def _gdelt_search(self, query, max_records=25, timespan='3months'):
        """Single GDELT API search with retry on rate limit."""
        import time
        for attempt in range(4):
            try:
                encoded = quote(query)
                url = (
                    f"https://api.gdeltproject.org/api/v2/doc/doc"
                    f"?query={encoded}&mode=ArtList&maxrecords={max_records}"
                    f"&format=json&sort=datedesc&timespan={timespan}"
                )
                resp = self.session.get(url, timeout=20)
                text = resp.text.strip()

                # Rate limited (429) or 200 with rate-limit message
                if resp.status_code == 429 or 'Please limit' in text or (resp.status_code == 200 and not text.startswith('{')):
                    wait = 10 + attempt * 5
                    print(f"[OSINT] GDELT rate limited (HTTP {resp.status_code}), waiting {wait}s (attempt {attempt+1}/4)")
                    time.sleep(wait)
                    continue

                if resp.status_code == 200:
                    try:
                        data = resp.json()
                        articles = data.get('articles', [])
                        for article in articles:
                            article['matched_targets'] = self._match_article_to_targets(article)
                        print(f"[OSINT] GDELT: {len(articles)} articles for '{query}'")
                        return articles
                    except (json.JSONDecodeError, ValueError):
                        print(f"[OSINT] GDELT JSON parse error for '{query}'")
                        return []
                else:
                    print(f"[OSINT] GDELT HTTP {resp.status_code} for '{query}'")
                    time.sleep(8)
            except Exception as e:
                print(f"[OSINT] GDELT search error: {e}")
                time.sleep(8)
        print(f"[OSINT] GDELT: all retries exhausted for '{query}'")
        return []

    # Generic facility patterns that map to known targets when no specific location is mentioned
    GENERIC_FACILITY_MAPPINGS = {
        r'iran.*oil\s*depot': 'tehran_refinery',
        r'oil\s*depot.*iran': 'tehran_refinery',
        r'hits?\s+iran.*oil': 'tehran_refinery',
        r'iran.*fuel\s*depot': 'tehran_refinery',
        r'iran.*refiner': 'isfahan_refinery',
        r'iran.*nuclear.*facility': 'natanz_nuclear',
        r'iran.*enrichment': 'natanz_nuclear',
        r'iran.*missile.*site': 'khojir_missile',
        r'iran.*air\s*defense': 'isfahan_airbase',
        r'iran.*radar.*site': 'lavasan_radar',
        r'iran.*power\s*plant': 'tehran_power_plants',
    }

    def _match_article_to_targets(self, article):
        """
        Analyze article title/URL for mentions of known targets.
        Returns list of matched target IDs with relevance scores.
        """
        text = (
            (article.get('title', '') + ' ' + article.get('url', '')).lower()
        )

        matches = []
        
        # First check for generic facility mentions (like "Iran oil depots")
        for pattern, target_id in self.GENERIC_FACILITY_MAPPINGS.items():
            if re.search(pattern, text):
                if target_id in KNOWN_TARGETS:
                    target = KNOWN_TARGETS[target_id]
                    matches.append({
                        'target_id': target_id,
                        'name': target['name'],
                        'lat': target['lat'],
                        'lon': target['lon'],
                        'type': target['type'],
                        'keyword': pattern,
                        'relevance': 0.75  # High relevance for facility type matches
                    })
        
        # Then check specific keyword matches
        for keyword, info in LOCATION_KEYWORDS.items():
            if keyword in text:
                matches.append({
                    'target_id': info['target_id'],
                    'name': info['name'],
                    'lat': info['lat'],
                    'lon': info['lon'],
                    'type': info['type'],
                    'keyword': keyword,
                    'relevance': 0.8 if len(keyword) > 8 else 0.6
                })

        # Also check province/city names
        for city, coords in PROVINCE_COORDS.items():
            if city in text:
                matches.append({
                    'target_id': f'city_{city}',
                    'name': city.title(),
                    'lat': coords[0],
                    'lon': coords[1],
                    'type': 'city',
                    'keyword': city,
                    'relevance': 0.4
                })

        # Deduplicate by target_id, keep highest relevance
        seen = {}
        for m in matches:
            tid = m['target_id']
            if tid not in seen or m['relevance'] > seen[tid]['relevance']:
                seen[tid] = m
        return list(seen.values())

    # ────────────────────────────────────────────────────────────
    # FULL OSINT SCAN — builds attack timeline
    # ────────────────────────────────────────────────────────────

    def full_scan(self, since_date='2026-03-01', use_cache=True):
        """
        Run comprehensive OSINT scan:
        1. Search GDELT for all Iran strike related news
        2. Extract locations from articles
        3. Build/update attack timeline
        4. Cross-reference with known targets
        
        PERFORMANCE: Results cached for 5 minutes. Pass use_cache=False to force refresh.
        Returns complete attack report.
        """
        cache_key = f"full_scan_{since_date}"
        
        # Check cache first (5-minute TTL)
        if use_cache:
            cached = self._get_cached(cache_key)
            if cached:
                return cached
        
        print("[OSINT] Starting full intelligence scan...")

        all_articles = []
        # OPTIMIZATION: Use only top 8 most relevant queries instead of all 44
        # This reduces scan time from ~4 minutes to ~50 seconds
        priority_queries = [
            'israel strike iran',
            'IDF iran operation',
            'iran military base attacked',
            'tehran strike',
            'isfahan attack',
            'iran nuclear facility strike',
            'iran air defense destroyed',
            'iran IRGC base hit',
        ]
        
        for i, q in enumerate(priority_queries):
            print(f"  [{i+1}/{len(priority_queries)}] Searching: {q}")
            arts = self._gdelt_search(q, max_records=20)
            all_articles.extend(arts)
            if i < len(priority_queries) - 1:
                time.sleep(5)  # Respect GDELT rate limits (1 req per 5s)

        # Deduplicate
        seen_urls = set()
        unique_articles = []
        for a in all_articles:
            url = a.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_articles.append(a)

        print(f"[OSINT] {len(unique_articles)} unique articles found")

        # Store articles and build strike records
        strikes = self._process_articles_to_strikes(unique_articles, since_date)

        # Generate report
        report = {
            'scan_date': datetime.utcnow().isoformat(),
            'articles_found': len(unique_articles),
            'articles_with_locations': sum(1 for a in unique_articles if a.get('matched_targets')),
            'strikes': strikes,
            'strike_count': len(strikes),
            'targets_mentioned': self._count_target_mentions(unique_articles),
            'timeline': self._build_timeline(strikes),
            'recent_articles': unique_articles[:20],
        }
        
        # Cache the result for 5 minutes
        self._set_cached(cache_key, report)

        return report

    def _process_articles_to_strikes(self, articles, since_date):
        """
        Process articles into strike records.
        Groups by target location and date.
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        strike_map = {}  # target_id → strike info

        for article in articles:
            # Parse date
            art_date = ''
            if article.get('seendate'):
                try:
                    sd = article['seendate']
                    art_date = f"{sd[:4]}-{sd[4:6]}-{sd[6:8]}"
                except (IndexError, TypeError):
                    art_date = ''

            # Skip if before war start
            if art_date and art_date < since_date:
                continue

            # Store article
            art_id = hashlib.md5(article.get('url', '').encode()).hexdigest()[:12]
            matched = article.get('matched_targets', [])
            try:
                c.execute('''INSERT OR IGNORE INTO osint_articles
                    (id, url, title, domain, date, matched_targets, relevance_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?)''',
                    (art_id, article.get('url',''), article.get('title',''),
                     article.get('domain',''), art_date,
                     json.dumps([m['target_id'] for m in matched]),
                     max([m['relevance'] for m in matched]) if matched else 0.1)
                )
            except Exception:
                pass

            # Process matched targets into strikes
            for match in matched:
                tid = match['target_id']
                key = f"{tid}_{art_date[:7]}"  # Group by target + month

                if key not in strike_map:
                    strike_map[key] = {
                        'target_id': tid,
                        'target_name': match['name'],
                        'target_type': match['type'],
                        'lat': match['lat'],
                        'lon': match['lon'],
                        'date': art_date or 'unknown',
                        'province': KNOWN_TARGETS.get(tid, {}).get('province', ''),
                        'sources': [],
                        'source_count': 0,
                        'confidence': 'unconfirmed',
                    }

                strike_map[key]['sources'].append({
                    'title': article.get('title', ''),
                    'url': article.get('url', ''),
                    'domain': article.get('domain', ''),
                    'date': art_date,
                    'relevance': match['relevance'],
                })
                strike_map[key]['source_count'] = len(strike_map[key]['sources'])

        # Calculate confidence based on source count
        for key, strike in strike_map.items():
            n = strike['source_count']
            max_rel = max([s['relevance'] for s in strike['sources']], default=0)
            if n >= 5 and max_rel >= 0.7:
                strike['confidence'] = 'confirmed'
            elif n >= 3 or max_rel >= 0.7:
                strike['confidence'] = 'likely'
            elif n >= 1:
                strike['confidence'] = 'reported'
            else:
                strike['confidence'] = 'unconfirmed'

            # Store/update in DB
            strike_id = hashlib.md5(key.encode()).hexdigest()[:12]
            strike['id'] = strike_id

            try:
                c.execute('''INSERT OR REPLACE INTO strikes
                    (id, target_id, target_name, target_type, lat, lon, date,
                     province, description, confidence, source_count, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (strike_id, strike['target_id'], strike['target_name'],
                     strike['target_type'], strike['lat'], strike['lon'],
                     strike['date'], strike['province'],
                     f"Reported strike on {strike['target_name']}",
                     strike['confidence'], strike['source_count'],
                     datetime.utcnow().isoformat())
                )

                # Store evidence links
                for src in strike['sources'][:10]:  # Max 10 per strike
                    ev_id = hashlib.md5((strike_id + src.get('url','')).encode()).hexdigest()[:12]
                    c.execute('''INSERT OR IGNORE INTO evidence
                        (strike_id, source_type, source_name, url, title, date, relevance_score)
                        VALUES (?, ?, ?, ?, ?, ?, ?)''',
                        (strike_id, 'news', src.get('domain',''), src.get('url',''),
                         src.get('title',''), src.get('date',''), src.get('relevance', 0.5))
                    )
            except Exception as e:
                print(f"[OSINT] DB error: {e}")

        conn.commit()
        conn.close()

        # Convert to list sorted by date
        strikes_list = sorted(strike_map.values(), key=lambda s: s.get('date', ''), reverse=True)
        return strikes_list

    def _count_target_mentions(self, articles):
        """Count how many times each known target is mentioned across articles."""
        counts = {}
        for article in articles:
            for match in article.get('matched_targets', []):
                name = match['name']
                if name not in counts:
                    counts[name] = {'count': 0, 'target_id': match['target_id'],
                                    'lat': match['lat'], 'lon': match['lon'],
                                    'type': match['type']}
                counts[name]['count'] += 1
        # Sort by count
        return dict(sorted(counts.items(), key=lambda x: x[1]['count'], reverse=True))

    def _build_timeline(self, strikes):
        """Build a day-by-day timeline of events."""
        timeline = {}
        for strike in strikes:
            d = strike.get('date', 'unknown')[:10]
            if d not in timeline:
                timeline[d] = []
            timeline[d].append({
                'target': strike['target_name'],
                'type': strike['target_type'],
                'confidence': strike['confidence'],
                'sources': strike['source_count'],
            })
        return dict(sorted(timeline.items(), reverse=True))

    # ────────────────────────────────────────────────────────────
    # KNOWN TARGETS RETRIEVAL
    # ────────────────────────────────────────────────────────────

    def get_known_targets(self, category=None, province=None):
        """Return known targets, optionally filtered."""
        targets = []
        for tid, t in KNOWN_TARGETS.items():
            if category and t['category'] != category:
                continue
            if province and t['province'].lower() != province.lower():
                continue
            targets.append({
                'id': tid,
                **t,
                'keywords': t['keywords'][:3],  # Trim for JSON
            })
        return targets

    def get_target_by_id(self, target_id):
        """Get a specific target's full details."""
        t = KNOWN_TARGETS.get(target_id)
        if t:
            return {'id': target_id, **t}
        return None

    # ────────────────────────────────────────────────────────────
    # ATTACK TIMELINE FROM DB
    # ────────────────────────────────────────────────────────────

    def get_attack_timeline(self, since='2026-03-01', limit=100):
        """
        Retrieve stored attack timeline from database.
        Returns strikes with their evidence sources.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        c.execute('''SELECT * FROM strikes
                     WHERE date >= ? OR date = 'unknown'
                     ORDER BY date DESC LIMIT ?''', (since, limit))
        strikes = [dict(row) for row in c.fetchall()]

        # Attach evidence
        for strike in strikes:
            c.execute('''SELECT * FROM evidence WHERE strike_id = ?
                        ORDER BY relevance_score DESC LIMIT 5''', (strike['id'],))
            strike['evidence'] = [dict(row) for row in c.fetchall()]

        conn.close()
        return strikes

    def get_strike_report(self, strike_id):
        """Get detailed report for a single strike."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        c.execute('SELECT * FROM strikes WHERE id = ?', (strike_id,))
        strike = c.fetchone()
        if not strike:
            conn.close()
            return None

        strike = dict(strike)

        # Get all evidence
        c.execute('''SELECT * FROM evidence WHERE strike_id = ?
                     ORDER BY relevance_score DESC''', (strike_id,))
        strike['evidence'] = [dict(row) for row in c.fetchall()]

        # Get target details
        target = KNOWN_TARGETS.get(strike.get('target_id'))
        if target:
            strike['target_details'] = target

        conn.close()
        return strike

    # ────────────────────────────────────────────────────────────
    # QUICK SCAN — lighter version for UI
    # ────────────────────────────────────────────────────────────

    def quick_scan(self, query=None):
        """
        Quick OSINT scan — single query, fast results.
        Good for UI updates without hitting rate limits.
        """
        if not query:
            query = 'israel iran strike attack'

        articles = self._gdelt_search(query, max_records=25)

        # Count location hits
        location_hits = {}
        for a in articles:
            for m in a.get('matched_targets', []):
                name = m['name']
                if name not in location_hits:
                    location_hits[name] = {
                        'count': 0, 'target_id': m['target_id'],
                        'lat': m['lat'], 'lon': m['lon'],
                        'type': m['type']
                    }
                location_hits[name]['count'] += 1

        return {
            'articles': articles[:15],
            'article_count': len(articles),
            'locations_mentioned': location_hits,
            'location_count': len(location_hits),
        }
