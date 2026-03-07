#!/usr/bin/env python3
"""
Expand target database to 500+ locations with mahsaalert-style categories
"""
import sqlite3
import os

DB_PATH = "timelapse_output/targets.db"

# Iranian cities by province with populations
IRAN_CITIES = [
    # Tehran Province
    ("Tehran", 35.6892, 51.3890, "tehran", "population_center", 8700000),
    ("Karaj", 35.8400, 50.9391, "alborz", "population_center", 1973000),
    ("Shahr-e Rey", 35.5859, 51.4250, "tehran", "population_center", 700000),
    ("Eslamshahr", 35.5522, 51.2353, "tehran", "population_center", 450000),
    ("Varamin", 35.3247, 51.6461, "tehran", "population_center", 250000),
    
    # Isfahan Province
    ("Isfahan", 32.6546, 51.6680, "isfahan", "population_center", 2000000),
    ("Kashan", 33.9850, 51.4100, "isfahan", "population_center", 400000),
    ("Najafabad", 32.6342, 51.3667, "isfahan", "population_center", 280000),
    ("Shahin Shahr", 32.8614, 51.5500, "isfahan", "population_center", 170000),
    
    # Khorasan Razavi
    ("Mashhad", 36.2605, 59.6168, "khorasan_razavi", "population_center", 3000000),
    ("Neyshabur", 36.2133, 58.7956, "khorasan_razavi", "population_center", 280000),
    ("Sabzevar", 36.2125, 57.6819, "khorasan_razavi", "population_center", 250000),
    ("Torbat-e Heydarieh", 35.2739, 59.2192, "khorasan_razavi", "population_center", 150000),
    ("Quchan", 37.1064, 58.5097, "khorasan_razavi", "population_center", 110000),
    
    # Fars Province
    ("Shiraz", 29.5918, 52.5837, "fars", "population_center", 1800000),
    ("Marvdasht", 29.8742, 52.8025, "fars", "population_center", 150000),
    ("Jahrom", 28.5000, 53.5600, "fars", "population_center", 140000),
    ("Fasa", 28.9383, 53.6483, "fars", "population_center", 120000),
    ("Kazerun", 29.6186, 51.6544, "fars", "population_center", 110000),
    ("Lar", 27.6747, 54.3397, "fars", "population_center", 100000),
    
    # Khuzestan Province
    ("Ahvaz", 31.3183, 48.6706, "khuzestan", "population_center", 1300000),
    ("Abadan", 30.3392, 48.3043, "khuzestan", "population_center", 350000),
    ("Khorramshahr", 30.4267, 48.1667, "khuzestan", "population_center", 170000),
    ("Dezful", 32.3839, 48.4056, "khuzestan", "population_center", 280000),
    ("Bandar Mahshahr", 30.5583, 49.1986, "khuzestan", "population_center", 140000),
    ("Andimeshk", 32.4608, 48.3544, "khuzestan", "population_center", 120000),
    ("Shush", 32.1942, 48.2436, "khuzestan", "population_center", 80000),
    
    # East Azerbaijan
    ("Tabriz", 38.0800, 46.2919, "east_azerbaijan", "population_center", 1700000),
    ("Maragheh", 37.3900, 46.2400, "east_azerbaijan", "population_center", 180000),
    ("Marand", 38.4331, 45.7742, "east_azerbaijan", "population_center", 130000),
    ("Ahar", 38.4783, 47.0700, "east_azerbaijan", "population_center", 110000),
    
    # West Azerbaijan
    ("Urmia", 37.5527, 45.0761, "west_azerbaijan", "population_center", 750000),
    ("Khoy", 38.5500, 44.9500, "west_azerbaijan", "population_center", 200000),
    ("Mahabad", 36.7633, 45.7222, "west_azerbaijan", "population_center", 170000),
    ("Miandoab", 36.9700, 46.1000, "west_azerbaijan", "population_center", 130000),
    
    # Kermanshah Province
    ("Kermanshah", 34.3142, 47.0650, "kermanshah", "population_center", 950000),
    ("Eslamabad-e Gharb", 34.1100, 46.5300, "kermanshah", "population_center", 120000),
    ("Javanrud", 34.8000, 46.5000, "kermanshah", "population_center", 80000),
    
    # Kerman Province
    ("Kerman", 30.2839, 57.0834, "kerman", "population_center", 820000),
    ("Rafsanjan", 30.4067, 55.9939, "kerman", "population_center", 180000),
    ("Sirjan", 29.4539, 55.6806, "kerman", "population_center", 200000),
    ("Jiroft", 28.6767, 57.7400, "kerman", "population_center", 150000),
    ("Bam", 29.1061, 58.3569, "kerman", "population_center", 120000),
    ("Zarand", 30.8125, 56.5614, "kerman", "population_center", 80000),
    
    # Sistan-Baluchestan
    ("Zahedan", 29.4963, 60.8629, "sistan_baluchestan", "population_center", 600000),
    ("Chabahar", 25.2919, 60.6430, "sistan_baluchestan", "population_center", 120000),
    ("Iranshahr", 27.2025, 60.6850, "sistan_baluchestan", "population_center", 100000),
    ("Zabol", 31.0286, 61.5011, "sistan_baluchestan", "population_center", 150000),
    ("Saravan", 27.3714, 62.3367, "sistan_baluchestan", "population_center", 80000),
    
    # Hormozgan Province
    ("Bandar Abbas", 27.1865, 56.2808, "hormozgan", "population_center", 530000),
    ("Minab", 27.1061, 57.0811, "hormozgan", "population_center", 90000),
    ("Qeshm", 26.9500, 56.2700, "hormozgan", "population_center", 40000),
    ("Bandar Lengeh", 26.5578, 54.8808, "hormozgan", "population_center", 30000),
    
    # Bushehr Province
    ("Bushehr", 28.9234, 50.8203, "bushehr", "population_center", 230000),
    ("Borazjan", 29.2667, 51.2167, "bushehr", "population_center", 130000),
    ("Genaveh", 29.5811, 50.5161, "bushehr", "population_center", 50000),
    ("Kangan", 27.8353, 52.0622, "bushehr", "population_center", 40000),
    
    # Yazd Province
    ("Yazd", 31.8974, 54.3569, "yazd", "population_center", 530000),
    ("Meybod", 32.2500, 54.0167, "yazd", "population_center", 80000),
    ("Ardakan", 32.3103, 54.0178, "yazd", "population_center", 80000),
    
    # Gilan Province
    ("Rasht", 37.2808, 49.5832, "gilan", "population_center", 700000),
    ("Bandar Anzali", 37.4731, 49.4628, "gilan", "population_center", 120000),
    ("Lahijan", 37.2011, 50.0053, "gilan", "population_center", 100000),
    ("Langrud", 37.1972, 50.1531, "gilan", "population_center", 70000),
    
    # Mazandaran Province
    ("Sari", 36.5633, 53.0601, "mazandaran", "population_center", 350000),
    ("Babol", 36.5514, 52.6786, "mazandaran", "population_center", 250000),
    ("Amol", 36.4697, 52.3503, "mazandaran", "population_center", 230000),
    ("Qaem Shahr", 36.4647, 52.8628, "mazandaran", "population_center", 200000),
    ("Nowshahr", 36.6489, 51.4961, "mazandaran", "population_center", 60000),
    ("Chalus", 36.6558, 51.4206, "mazandaran", "population_center", 50000),
    
    # Qom Province
    ("Qom", 34.6401, 50.8764, "qom", "population_center", 1200000),
    
    # Markazi Province
    ("Arak", 34.0917, 49.6892, "markazi", "population_center", 550000),
    ("Saveh", 35.0214, 50.3564, "markazi", "population_center", 220000),
    ("Khomein", 33.6400, 50.0800, "markazi", "population_center", 90000),
    
    # Lorestan Province
    ("Khorramabad", 33.4878, 48.3558, "lorestan", "population_center", 380000),
    ("Borujerd", 33.8972, 48.7517, "lorestan", "population_center", 280000),
    ("Dorud", 33.4944, 49.0575, "lorestan", "population_center", 120000),
    
    # Hamadan Province
    ("Hamadan", 34.7992, 48.5146, "hamadan", "population_center", 600000),
    ("Malayer", 34.2969, 48.8239, "hamadan", "population_center", 180000),
    ("Nahavand", 34.1900, 48.3700, "hamadan", "population_center", 90000),
    
    # Golestan Province
    ("Gorgan", 36.8386, 54.4347, "golestan", "population_center", 400000),
    ("Gonbad-e Kavus", 37.2500, 55.1700, "golestan", "population_center", 160000),
    ("Aliabad", 36.9083, 54.8639, "golestan", "population_center", 60000),
    
    # North Khorasan
    ("Bojnurd", 37.4747, 57.3292, "north_khorasan", "population_center", 230000),
    ("Shirvan", 37.3969, 57.9269, "north_khorasan", "population_center", 80000),
    ("Esfarayen", 37.0747, 57.5100, "north_khorasan", "population_center", 70000),
    
    # South Khorasan
    ("Birjand", 32.8644, 59.2211, "south_khorasan", "population_center", 200000),
    ("Tabas", 33.5958, 56.9244, "south_khorasan", "population_center", 50000),
    ("Ferdows", 34.0178, 58.1731, "south_khorasan", "population_center", 40000),
    
    # Kurdistan Province
    ("Sanandaj", 35.3108, 46.9989, "kurdistan", "population_center", 430000),
    ("Saqqez", 36.2469, 46.2733, "kurdistan", "population_center", 170000),
    ("Marivan", 35.5167, 46.1769, "kurdistan", "population_center", 100000),
    ("Baneh", 35.9975, 45.8853, "kurdistan", "population_center", 90000),
    
    # Ilam Province
    ("Ilam", 33.6374, 46.4227, "ilam", "population_center", 200000),
    ("Mehran", 33.1222, 46.1644, "ilam", "population_center", 40000),
    ("Dehloran", 32.6942, 47.2675, "ilam", "population_center", 50000),
    
    # Ardabil Province
    ("Ardabil", 38.2498, 48.2933, "ardabil", "population_center", 530000),
    ("Parsabad", 39.6483, 47.9175, "ardabil", "population_center", 100000),
    ("Meshgin Shahr", 38.3947, 47.6792, "ardabil", "population_center", 80000),
    
    # Zanjan Province
    ("Zanjan", 36.6736, 48.4787, "zanjan", "population_center", 430000),
    ("Abhar", 36.1467, 49.2178, "zanjan", "population_center", 90000),
    
    # Semnan Province
    ("Semnan", 35.5769, 53.3975, "semnan", "population_center", 200000),
    ("Shahroud", 36.4181, 54.9764, "semnan", "population_center", 180000),
    ("Damghan", 36.1683, 54.3481, "semnan", "population_center", 70000),
    
    # Qazvin Province
    ("Qazvin", 36.2797, 50.0049, "qazvin", "population_center", 400000),
    ("Takestan", 36.0703, 49.6956, "qazvin", "population_center", 90000),
    
    # Kohgiluyeh Province
    ("Yasuj", 30.6683, 51.5878, "kohgiluyeh", "population_center", 130000),
    ("Gachsaran", 30.3583, 50.7981, "kohgiluyeh", "population_center", 80000),
    ("Dehdasht", 30.7947, 50.5647, "kohgiluyeh", "population_center", 60000),
    
    # Chaharmahal Province
    ("Shahr-e Kord", 32.3256, 50.8644, "chaharmahal", "population_center", 180000),
    ("Borujen", 31.9683, 51.2869, "chaharmahal", "population_center", 60000),
    
    # Alborz Province (additional)
    ("Hashtgerd", 35.9619, 50.6836, "alborz", "population_center", 120000),
    ("Nazarabad", 35.9525, 50.6019, "alborz", "population_center", 80000),
]

# Military installations - expanded with mahsaalert-style categories
MILITARY_TARGETS = [
    # Nuclear Program (برنامه هسته‌ای)
    ("Natanz Nuclear Facility", 33.7214, 51.7275, "isfahan", "nuclear_facility", "Uranium enrichment - 60% purity capability"),
    ("Fordow Nuclear Site", 34.8833, 50.9667, "qom", "nuclear_facility", "Underground enrichment facility - hardened"),
    ("Isfahan Nuclear Technology Center", 32.6547, 51.5500, "isfahan", "nuclear_facility", "UCF - Uranium conversion"),
    ("Arak Heavy Water Reactor", 34.3833, 49.2333, "markazi", "nuclear_facility", "IR-40 reactor site"),
    ("Bushehr Nuclear Power Plant", 28.8294, 50.8872, "bushehr", "nuclear_facility", "1000MW reactor - Russian built"),
    ("Saghand Uranium Mine", 32.5333, 55.1833, "yazd", "nuclear_facility", "Uranium mining operations"),
    ("Gchine Uranium Mine", 27.4500, 56.8833, "hormozgan", "nuclear_facility", "Secondary uranium source"),
    ("Parchin Military Complex", 35.5167, 51.7667, "tehran", "nuclear_facility", "Suspected weapons research"),
    
    # Missile Program (برنامه موشکی)
    ("Shahrud Missile Test Site", 36.4167, 55.1000, "semnan", "missile", "ICBM testing - Simorgh launches"),
    ("Tabriz Missile Production", 38.0833, 46.2500, "east_azerbaijan", "missile", "Ballistic missile factory"),
    ("Isfahan Missile Industries", 32.7500, 51.6667, "isfahan", "missile", "Solid fuel production"),
    ("Semnan Space Center", 35.2342, 53.9208, "semnan", "missile", "Space launch / ICBM test"),
    ("Khojir Missile Base", 35.5833, 51.8333, "tehran", "missile", "Underground missile storage"),
    ("Imam Ali Missile Base", 34.7667, 50.8333, "qom", "missile", "IRGC missile garrison"),
    ("Bid Kaneh Missile Complex", 35.5500, 51.7000, "tehran", "missile", "Research and storage"),
    ("Dezful Missile Base", 32.3800, 48.4000, "khuzestan", "missile", "Western front missiles"),
    ("Khorramabad Missile Storage", 33.4900, 48.3600, "lorestan", "missile", "Underground depot"),
    
    # Air Defense (پدافند هوایی)
    ("Khark Island Air Defense", 29.2500, 50.3000, "bushehr", "air_defense", "S-300 protecting oil terminals"),
    ("Bushehr Air Defense Ring", 28.9200, 50.8200, "bushehr", "air_defense", "Nuclear plant defense"),
    ("Isfahan Air Defense Network", 32.6500, 51.6500, "isfahan", "air_defense", "Multi-layer coverage"),
    ("Tehran Central Defense", 35.7000, 51.4000, "tehran", "air_defense", "Capital protection - Bavar-373"),
    ("Bandar Abbas AD Site", 27.1800, 56.2800, "hormozgan", "air_defense", "Strait protection"),
    ("Tabriz Air Defense", 38.0800, 46.3000, "east_azerbaijan", "air_defense", "Northwestern coverage"),
    ("Shiraz Air Defense", 29.6000, 52.5800, "fars", "air_defense", "Southern region"),
    ("Mashhad Air Defense", 36.2700, 59.6200, "khorasan_razavi", "air_defense", "Eastern border"),
    ("Natanz Defense Ring", 33.7200, 51.7300, "isfahan", "air_defense", "Nuclear site protection"),
    ("Fordow Defense System", 34.8800, 50.9700, "qom", "air_defense", "Underground facility defense"),
    
    # Radar Sites (رادار)
    ("Garmsar Radar Station", 35.2167, 52.3500, "semnan", "radar", "Long-range early warning"),
    ("Khorramabad OTH Radar", 33.5000, 48.3500, "lorestan", "radar", "Over-the-horizon radar"),
    ("Ahvaz Radar Complex", 31.3200, 48.6700, "khuzestan", "radar", "Western early warning"),
    ("Zahedan Radar Site", 29.5000, 60.8600, "sistan_baluchestan", "radar", "Eastern coverage"),
    ("Bandar Abbas Coastal Radar", 27.1900, 56.2700, "hormozgan", "radar", "Maritime surveillance"),
    
    # Air Bases (پایگاه هوایی/پهپادی)
    ("Mehrabad Air Base", 35.6892, 51.3134, "tehran", "airbase", "Tehran military airport"),
    ("Isfahan (Shahid Babaei) AB", 32.7500, 51.8500, "isfahan", "airbase", "F-14 base"),
    ("Shiraz (Shahid Doran) AB", 29.5500, 52.6000, "fars", "airbase", "Major tactical base"),
    ("Tabriz AB", 38.1333, 46.2333, "east_azerbaijan", "airbase", "Northwestern air command"),
    ("Bandar Abbas AB", 27.2167, 56.3778, "hormozgan", "airbase", "Coastal operations"),
    ("Bushehr AB", 28.9500, 50.8333, "bushehr", "airbase", "Persian Gulf coverage"),
    ("Dezful AB", 32.4333, 48.3833, "khuzestan", "airbase", "Western front"),
    ("Hamadan AB", 34.8667, 48.5500, "hamadan", "airbase", "Central staging"),
    ("Kerman AB", 30.2667, 56.9500, "kerman", "airbase", "Southeastern coverage"),
    ("Mashhad (Shahid Hashemi Nejad) AB", 36.2356, 59.6400, "khorasan_razavi", "airbase", "Eastern command"),
    ("Omidiyeh AB", 30.8350, 49.5350, "khuzestan", "airbase", "Major tactical"),
    ("Chabahar AB", 25.4433, 60.3822, "sistan_baluchestan", "airbase", "Indian Ocean access"),
    
    # IRGC Bases
    ("IRGC Navy HQ Bandar Abbas", 27.1900, 56.2800, "hormozgan", "irgc", "Naval force command"),
    ("IRGC Aerospace Tehran", 35.7200, 51.4200, "tehran", "irgc", "Missile force HQ"),
    ("IRGC Ground Force Shiraz", 29.6000, 52.5800, "fars", "irgc", "Southern command"),
    ("IRGC Intelligence Tehran", 35.6800, 51.4000, "tehran", "irgc", "Intelligence operations"),
    ("IRGC Quds Force HQ", 35.7000, 51.4100, "tehran", "irgc", "External operations"),
    ("Ashraf-3 IRGC Base", 35.6300, 51.4500, "tehran", "irgc", "Training facility"),
    
    # Naval Bases
    ("Bandar Abbas Naval Base", 27.1500, 56.2500, "hormozgan", "naval", "Main Persian Gulf port"),
    ("Bushehr Naval Base", 28.9800, 50.8300, "bushehr", "naval", "Northern Gulf operations"),
    ("Chabahar Naval Base", 25.2900, 60.6400, "sistan_baluchestan", "naval", "Indian Ocean base"),
    ("Jask Naval Base", 25.6400, 57.7700, "hormozgan", "naval", "Strategic new base"),
    ("Kharg Island Naval", 29.2500, 50.3200, "bushehr", "naval", "Oil terminal defense"),
    ("Bandar Anzali Naval", 37.4700, 49.4600, "gilan", "naval", "Caspian Sea fleet"),
    ("Khorramshahr Naval", 30.4300, 48.1700, "khuzestan", "naval", "Shatt al-Arab access"),
    
    # Army Bases
    ("21st Infantry Division Tabriz", 38.0500, 46.2800, "east_azerbaijan", "army", "Northwestern front"),
    ("28th Infantry Division Sanandaj", 35.3100, 47.0000, "kurdistan", "army", "Kurdish border"),
    ("77th Infantry Division Mashhad", 36.2600, 59.6100, "khorasan_razavi", "army", "Afghan border"),
    ("88th Armored Division Zahedan", 29.4900, 60.8600, "sistan_baluchestan", "army", "Eastern border"),
    ("92nd Armored Division Khuzestan", 31.3200, 48.6700, "khuzestan", "army", "Iraq border"),
    ("Dezful Ground Forces", 32.3800, 48.4000, "khuzestan", "army", "Forward deployment"),
    
    # Energy Infrastructure
    ("Abadan Refinery", 30.3500, 48.2833, "khuzestan", "refinery", "Oldest and largest refinery"),
    ("Tehran Refinery", 35.4667, 51.4333, "tehran", "refinery", "Capital fuel supply"),
    ("Isfahan Refinery", 32.5833, 51.5667, "isfahan", "refinery", "Central Iran supply"),
    ("Tabriz Refinery", 38.0167, 46.3500, "east_azerbaijan", "refinery", "Northwestern supply"),
    ("Bandar Abbas Refinery", 27.2000, 56.2500, "hormozgan", "refinery", "Persian Gulf export"),
    ("Shiraz Refinery", 29.5333, 52.5167, "fars", "refinery", "Southern Iran"),
    ("Arak Refinery", 34.0500, 49.7000, "markazi", "refinery", "Central production"),
    ("Lavan Refinery", 26.8167, 53.3667, "hormozgan", "refinery", "Island facility"),
    
    # Oil/Gas Fields
    ("South Pars Gas Field", 27.5000, 52.0000, "bushehr", "oil_field", "Largest gas field - shared with Qatar"),
    ("Ahwaz Oil Field", 31.3333, 48.6667, "khuzestan", "oil_field", "Major onshore field"),
    ("Gachsaran Oil Field", 30.3500, 50.8000, "kohgiluyeh", "oil_field", "Southern production"),
    ("Marun Oil Field", 31.6667, 49.1667, "khuzestan", "oil_field", "Major producer"),
    ("Aghajari Oil Field", 30.7000, 49.8333, "khuzestan", "oil_field", "Historic field"),
    ("Kharg Island Terminal", 29.2500, 50.3167, "bushehr", "oil_terminal", "Main export terminal"),
    
    # Power Plants
    ("Neka Power Plant", 36.6500, 53.2833, "mazandaran", "power_generation", "Caspian coast - largest"),
    ("Ramin Power Plant", 31.3333, 48.7500, "khuzestan", "power_generation", "Southern grid anchor"),
    ("Montazeri Power Plant", 32.6333, 51.4500, "isfahan", "power_generation", "Central grid"),
    ("Shahid Rajai Power Plant", 36.1333, 52.6000, "mazandaran", "power_generation", "Northern grid"),
    ("Bandar Abbas Power Plant", 27.2167, 56.3000, "hormozgan", "power_generation", "Southern coast"),
    ("Zarand Power Plant", 30.8000, 56.5500, "kerman", "power_generation", "Southeast grid"),
    
    # Government / Repression Centers (مکان‌های سرکوب)
    ("Supreme Leader Compound", 35.7147, 51.4214, "tehran", "government", "Beit Rahbari - main residence"),
    ("Presidential Complex", 35.7000, 51.4100, "tehran", "government", "Pasteur St - executive offices"),
    ("Majlis (Parliament)", 35.6892, 51.3911, "tehran", "government", "Islamic Consultative Assembly"),
    ("Ministry of Intelligence", 35.6950, 51.4000, "tehran", "intelligence", "VEVAK headquarters"),
    ("IRGC Intelligence HQ", 35.7100, 51.4150, "tehran", "intelligence", "Parallel intel service"),
    ("Evin Prison", 35.8000, 51.4333, "tehran", "prison", "Political prisoner facility"),
    ("Gohardasht Prison", 35.8333, 50.9500, "alborz", "prison", "High security - Rajai Shahr"),
    ("Judiciary Complex Tehran", 35.6900, 51.4200, "tehran", "judicial", "Supreme Court complex"),
    
    # Communications
    ("Milad Tower", 35.7447, 51.3753, "tehran", "communications", "Main telecom hub"),
    ("Tehran Telecom Center", 35.7000, 51.4200, "tehran", "communications", "Switching center"),
    ("Isfahan Telecom Hub", 32.6500, 51.6700, "isfahan", "communications", "Regional node"),
    ("Shiraz Telecom Center", 29.5900, 52.5800, "fars", "communications", "Southern hub"),
    ("Mashhad Telecom Center", 36.2600, 59.6100, "khorasan_razavi", "communications", "Eastern hub"),
]

def expand_database():
    """Add all targets to database"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Check current count
    cur.execute("SELECT COUNT(*) FROM targets")
    initial_count = cur.fetchone()[0]
    print(f"Initial targets: {initial_count}")
    
    added = 0
    
    # Add cities
    for city in IRAN_CITIES:
        name, lat, lon, province, ttype, pop = city
        cur.execute("SELECT id FROM targets WHERE name = ? AND province = ?", (name, province))
        if not cur.fetchone():
            import uuid
            cur.execute("""
                INSERT INTO targets (id, name, lat, lon, province, type, category, description, priority)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (str(uuid.uuid4())[:8], name, lat, lon, province, ttype, "city", f"Population: {pop:,}", 1))
            added += 1
    
    # Add military targets
    for target in MILITARY_TARGETS:
        name, lat, lon, province, ttype, desc = target
        cur.execute("SELECT id FROM targets WHERE name = ? AND province = ?", (name, province))
        if not cur.fetchone():
            import uuid
            # Determine category
            if ttype in ['nuclear_facility']:
                cat = 'nuclear'
            elif ttype in ['missile']:
                cat = 'missile'
            elif ttype in ['air_defense', 'radar']:
                cat = 'air_defense'
            elif ttype in ['airbase']:
                cat = 'airbase'
            elif ttype in ['irgc', 'army', 'naval']:
                cat = 'military'
            elif ttype in ['refinery', 'oil_field', 'oil_terminal', 'power_generation']:
                cat = 'energy'
            elif ttype in ['government', 'intelligence', 'prison', 'judicial']:
                cat = 'government'
            elif ttype in ['communications']:
                cat = 'communications'
            else:
                cat = 'other'
            
            priority = 5 if ttype == 'nuclear_facility' else 4 if ttype == 'missile' else 3
            
            cur.execute("""
                INSERT INTO targets (id, name, lat, lon, province, type, category, description, priority)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (str(uuid.uuid4())[:8], name, lat, lon, province, ttype, cat, desc, priority))
            added += 1
            added += 1
    
    conn.commit()
    
    # Final count
    cur.execute("SELECT COUNT(*) FROM targets")
    final_count = cur.fetchone()[0]
    print(f"Added: {added}")
    print(f"Final targets: {final_count}")
    
    # Show breakdown
    print("\nBreakdown by type:")
    cur.execute("SELECT type, COUNT(*) as cnt FROM targets GROUP BY type ORDER BY cnt DESC")
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]}")
    
    conn.close()

if __name__ == "__main__":
    expand_database()
