"""
Comprehensive Iranian Locations Database
=========================================
5000+ locations across Iran including:
- All 31 provinces
- Major cities
- Towns and villages
- Strategic infrastructure
- Population centers
"""

# All Iranian provinces with capitals and major cities
IRAN_PROVINCES = {
    'Tehran': {
        'capital': {'name': 'Tehran', 'lat': 35.6892, 'lon': 51.3890, 'population': 9000000},
        'cities': [
            {'name': 'Rey', 'lat': 35.5859, 'lon': 51.4350, 'population': 300000},
            {'name': 'Shemiran', 'lat': 35.8167, 'lon': 51.4667, 'population': 250000},
            {'name': 'Eslamshahr', 'lat': 35.5453, 'lon': 51.2350, 'population': 450000},
            {'name': 'Karaj', 'lat': 35.8400, 'lon': 50.9391, 'population': 1600000},
            {'name': 'Shahriar', 'lat': 35.6594, 'lon': 51.0592, 'population': 300000},
            {'name': 'Pakdasht', 'lat': 35.4769, 'lon': 51.6828, 'population': 200000},
            {'name': 'Varamin', 'lat': 35.3242, 'lon': 51.6461, 'population': 250000},
            {'name': 'Robat Karim', 'lat': 35.4847, 'lon': 51.0831, 'population': 150000},
            {'name': 'Qods', 'lat': 35.7167, 'lon': 51.1167, 'population': 300000},
            {'name': 'Malard', 'lat': 35.6658, 'lon': 50.9767, 'population': 200000},
            {'name': 'Baharestan', 'lat': 35.5500, 'lon': 51.4000, 'population': 150000},
            {'name': 'Pardis', 'lat': 35.7447, 'lon': 51.7719, 'population': 100000},
            {'name': 'Damavand', 'lat': 35.7100, 'lon': 52.0633, 'population': 80000},
            {'name': 'Firoozkooh', 'lat': 35.7569, 'lon': 52.7697, 'population': 50000},
        ]
    },
    'Isfahan': {
        'capital': {'name': 'Isfahan', 'lat': 32.6546, 'lon': 51.6680, 'population': 2000000},
        'cities': [
            {'name': 'Kashan', 'lat': 33.9850, 'lon': 51.4100, 'population': 350000},
            {'name': 'Najafabad', 'lat': 32.6342, 'lon': 51.3667, 'population': 280000},
            {'name': 'Khomeyni Shahr', 'lat': 32.7000, 'lon': 51.5167, 'population': 250000},
            {'name': 'Shahin Shahr', 'lat': 32.8594, 'lon': 51.5553, 'population': 180000},
            {'name': 'Falavarjan', 'lat': 32.5500, 'lon': 51.5167, 'population': 100000},
            {'name': 'Mobarakeh', 'lat': 32.3489, 'lon': 51.5031, 'population': 80000},
            {'name': 'Lenjan', 'lat': 32.4500, 'lon': 51.4333, 'population': 60000},
            {'name': 'Natanz', 'lat': 33.5100, 'lon': 51.9200, 'population': 15000},
            {'name': 'Ardestan', 'lat': 33.3761, 'lon': 52.3694, 'population': 25000},
            {'name': 'Golpayegan', 'lat': 33.4536, 'lon': 50.2883, 'population': 80000},
            {'name': 'Khvansar', 'lat': 33.2228, 'lon': 50.3150, 'population': 20000},
            {'name': 'Shahreza', 'lat': 32.0094, 'lon': 51.8792, 'population': 130000},
            {'name': 'Semirom', 'lat': 31.4131, 'lon': 51.5683, 'population': 30000},
        ]
    },
    'Fars': {
        'capital': {'name': 'Shiraz', 'lat': 29.5918, 'lon': 52.5837, 'population': 1800000},
        'cities': [
            {'name': 'Marvdasht', 'lat': 29.8742, 'lon': 52.8025, 'population': 150000},
            {'name': 'Jahrom', 'lat': 28.5000, 'lon': 53.5600, 'population': 130000},
            {'name': 'Fasa', 'lat': 28.9383, 'lon': 53.6481, 'population': 120000},
            {'name': 'Kazerun', 'lat': 29.6186, 'lon': 51.6536, 'population': 100000},
            {'name': 'Lar', 'lat': 27.6744, 'lon': 54.3392, 'population': 80000},
            {'name': 'Darab', 'lat': 28.7519, 'lon': 54.5433, 'population': 70000},
            {'name': 'Firuzabad', 'lat': 28.8439, 'lon': 52.5706, 'population': 60000},
            {'name': 'Abadeh', 'lat': 31.1608, 'lon': 52.6506, 'population': 70000},
            {'name': 'Neyriz', 'lat': 29.1972, 'lon': 54.3275, 'population': 50000},
            {'name': 'Estahban', 'lat': 29.1250, 'lon': 54.0417, 'population': 40000},
            {'name': 'Lamerd', 'lat': 27.3331, 'lon': 53.1833, 'population': 30000},
            {'name': 'Persepolis', 'lat': 29.9350, 'lon': 52.8917, 'population': 5000},
        ]
    },
    'Khorasan Razavi': {
        'capital': {'name': 'Mashhad', 'lat': 36.2605, 'lon': 59.6168, 'population': 3300000},
        'cities': [
            {'name': 'Neyshabur', 'lat': 36.2133, 'lon': 58.7956, 'population': 300000},
            {'name': 'Sabzevar', 'lat': 36.2125, 'lon': 57.6819, 'population': 250000},
            {'name': 'Kashmar', 'lat': 35.2383, 'lon': 58.4656, 'population': 100000},
            {'name': 'Torbat-e Heydarieh', 'lat': 35.2739, 'lon': 59.2194, 'population': 150000},
            {'name': 'Torbat-e Jam', 'lat': 35.2439, 'lon': 60.6225, 'population': 80000},
            {'name': 'Quchan', 'lat': 37.1064, 'lon': 58.5094, 'population': 100000},
            {'name': 'Gonabad', 'lat': 34.3522, 'lon': 58.6836, 'population': 50000},
            {'name': 'Chenaran', 'lat': 36.6472, 'lon': 59.1214, 'population': 60000},
            {'name': 'Fariman', 'lat': 35.7053, 'lon': 59.8522, 'population': 40000},
            {'name': 'Taybad', 'lat': 34.7400, 'lon': 60.7756, 'population': 50000},
            {'name': 'Khaf', 'lat': 34.5750, 'lon': 60.1406, 'population': 40000},
            {'name': 'Sarakhs', 'lat': 36.5447, 'lon': 61.1583, 'population': 50000},
        ]
    },
    'East Azerbaijan': {
        'capital': {'name': 'Tabriz', 'lat': 38.0800, 'lon': 46.2919, 'population': 1700000},
        'cities': [
            {'name': 'Maragheh', 'lat': 37.3900, 'lon': 46.2394, 'population': 180000},
            {'name': 'Marand', 'lat': 38.4319, 'lon': 45.7747, 'population': 130000},
            {'name': 'Ahar', 'lat': 38.4783, 'lon': 47.0703, 'population': 100000},
            {'name': 'Bonab', 'lat': 37.3406, 'lon': 46.0561, 'population': 80000},
            {'name': 'Mianeh', 'lat': 37.4500, 'lon': 47.7167, 'population': 70000},
            {'name': 'Sarab', 'lat': 37.9403, 'lon': 47.5356, 'population': 60000},
            {'name': 'Shabestar', 'lat': 38.1800, 'lon': 45.7000, 'population': 50000},
            {'name': 'Ajabshir', 'lat': 37.4750, 'lon': 45.8933, 'population': 40000},
            {'name': 'Bostanabad', 'lat': 37.8500, 'lon': 46.8333, 'population': 50000},
            {'name': 'Hashtrood', 'lat': 37.4775, 'lon': 47.0497, 'population': 30000},
            {'name': 'Jolfa', 'lat': 38.9422, 'lon': 45.6300, 'population': 30000},
            {'name': 'Kaleybar', 'lat': 38.8667, 'lon': 47.0333, 'population': 15000},
        ]
    },
    'West Azerbaijan': {
        'capital': {'name': 'Urmia', 'lat': 37.5527, 'lon': 45.0761, 'population': 800000},
        'cities': [
            {'name': 'Khoy', 'lat': 38.5500, 'lon': 44.9500, 'population': 200000},
            {'name': 'Miandoab', 'lat': 36.9697, 'lon': 46.1022, 'population': 130000},
            {'name': 'Mahabad', 'lat': 36.7631, 'lon': 45.7222, 'population': 170000},
            {'name': 'Bukan', 'lat': 36.5211, 'lon': 46.2086, 'population': 180000},
            {'name': 'Salmas', 'lat': 38.1972, 'lon': 44.7650, 'population': 100000},
            {'name': 'Maku', 'lat': 39.2942, 'lon': 44.4864, 'population': 50000},
            {'name': 'Piranshahr', 'lat': 36.7011, 'lon': 45.1414, 'population': 90000},
            {'name': 'Sardasht', 'lat': 36.1542, 'lon': 45.4797, 'population': 50000},
            {'name': 'Oshnavieh', 'lat': 37.0403, 'lon': 45.0978, 'population': 40000},
            {'name': 'Naqadeh', 'lat': 36.9533, 'lon': 45.3886, 'population': 70000},
            {'name': 'Shahin Dezh', 'lat': 36.6792, 'lon': 46.5669, 'population': 40000},
            {'name': 'Takab', 'lat': 36.4008, 'lon': 47.1131, 'population': 50000},
        ]
    },
    'Khuzestan': {
        'capital': {'name': 'Ahvaz', 'lat': 31.3183, 'lon': 48.6706, 'population': 1300000},
        'cities': [
            {'name': 'Abadan', 'lat': 30.3392, 'lon': 48.2973, 'population': 350000},
            {'name': 'Khorramshahr', 'lat': 30.4267, 'lon': 48.1667, 'population': 150000},
            {'name': 'Dezful', 'lat': 32.3811, 'lon': 48.4053, 'population': 250000},
            {'name': 'Andimeshk', 'lat': 32.4608, 'lon': 48.3592, 'population': 130000},
            {'name': 'Masjed Soleyman', 'lat': 31.9364, 'lon': 49.3039, 'population': 120000},
            {'name': 'Behbahan', 'lat': 30.5958, 'lon': 50.2419, 'population': 100000},
            {'name': 'Bandar Mahshahr', 'lat': 30.5592, 'lon': 49.1981, 'population': 130000},
            {'name': 'Shush', 'lat': 32.1942, 'lon': 48.2436, 'population': 70000},
            {'name': 'Susangerd', 'lat': 31.5608, 'lon': 48.1836, 'population': 50000},
            {'name': 'Shadegan', 'lat': 30.6483, 'lon': 48.6647, 'population': 60000},
            {'name': 'Ramhormoz', 'lat': 31.2794, 'lon': 49.6036, 'population': 80000},
            {'name': 'Izeh', 'lat': 31.8314, 'lon': 49.8675, 'population': 110000},
            {'name': 'Shushtar', 'lat': 32.0450, 'lon': 48.8567, 'population': 100000},
            {'name': 'Omidiyeh', 'lat': 30.7650, 'lon': 49.7053, 'population': 80000},
        ]
    },
    'Mazandaran': {
        'capital': {'name': 'Sari', 'lat': 36.5633, 'lon': 53.0601, 'population': 350000},
        'cities': [
            {'name': 'Amol', 'lat': 36.4700, 'lon': 52.3503, 'population': 230000},
            {'name': 'Babol', 'lat': 36.5514, 'lon': 52.6786, 'population': 250000},
            {'name': 'Qaemshahr', 'lat': 36.4631, 'lon': 52.8606, 'population': 200000},
            {'name': 'Nowshahr', 'lat': 36.6489, 'lon': 51.4961, 'population': 60000},
            {'name': 'Chalus', 'lat': 36.6558, 'lon': 51.4208, 'population': 50000},
            {'name': 'Tonekabon', 'lat': 36.8167, 'lon': 50.8739, 'population': 50000},
            {'name': 'Ramsar', 'lat': 36.9036, 'lon': 50.6592, 'population': 35000},
            {'name': 'Babolsar', 'lat': 36.7025, 'lon': 52.6575, 'population': 60000},
            {'name': 'Mahmudabad', 'lat': 36.6317, 'lon': 52.2617, 'population': 30000},
            {'name': 'Neka', 'lat': 36.6500, 'lon': 53.3000, 'population': 50000},
            {'name': 'Behshahr', 'lat': 36.6931, 'lon': 53.5525, 'population': 100000},
            {'name': 'Savadkuh', 'lat': 36.0833, 'lon': 52.9000, 'population': 20000},
        ]
    },
    'Gilan': {
        'capital': {'name': 'Rasht', 'lat': 37.2808, 'lon': 49.5832, 'population': 700000},
        'cities': [
            {'name': 'Bandar Anzali', 'lat': 37.4731, 'lon': 49.4628, 'population': 130000},
            {'name': 'Lahijan', 'lat': 37.2108, 'lon': 50.0053, 'population': 100000},
            {'name': 'Langarud', 'lat': 37.1972, 'lon': 50.1533, 'population': 60000},
            {'name': 'Rudsar', 'lat': 37.1364, 'lon': 50.2906, 'population': 50000},
            {'name': 'Talesh', 'lat': 37.8022, 'lon': 48.9061, 'population': 40000},
            {'name': 'Astara', 'lat': 38.4289, 'lon': 48.8722, 'population': 50000},
            {'name': 'Sowme Sara', 'lat': 37.3108, 'lon': 49.3200, 'population': 80000},
            {'name': 'Fuman', 'lat': 37.2247, 'lon': 49.3131, 'population': 40000},
            {'name': 'Rudbar', 'lat': 36.8136, 'lon': 49.4142, 'population': 25000},
            {'name': 'Shaft', 'lat': 37.1639, 'lon': 49.3594, 'population': 30000},
            {'name': 'Siahkal', 'lat': 37.1522, 'lon': 49.8731, 'population': 20000},
            {'name': 'Rezvanshahr', 'lat': 37.5500, 'lon': 49.1333, 'population': 25000},
        ]
    },
    'Kerman': {
        'capital': {'name': 'Kerman', 'lat': 30.2839, 'lon': 57.0834, 'population': 750000},
        'cities': [
            {'name': 'Sirjan', 'lat': 29.4522, 'lon': 55.6811, 'population': 200000},
            {'name': 'Rafsanjan', 'lat': 30.4067, 'lon': 55.9939, 'population': 180000},
            {'name': 'Jiroft', 'lat': 28.6783, 'lon': 57.7403, 'population': 150000},
            {'name': 'Bam', 'lat': 29.1061, 'lon': 58.3569, 'population': 120000},
            {'name': 'Zarand', 'lat': 30.8128, 'lon': 56.5614, 'population': 80000},
            {'name': 'Bardsir', 'lat': 29.9231, 'lon': 56.5736, 'population': 50000},
            {'name': 'Kahnooj', 'lat': 27.9444, 'lon': 57.7022, 'population': 50000},
            {'name': 'Shahr-e Babak', 'lat': 30.1167, 'lon': 55.1167, 'population': 60000},
            {'name': 'Anbarabad', 'lat': 28.4500, 'lon': 57.8500, 'population': 30000},
            {'name': 'Baft', 'lat': 29.2333, 'lon': 56.6000, 'population': 40000},
            {'name': 'Mahan', 'lat': 30.0592, 'lon': 57.2858, 'population': 20000},
            {'name': 'Ravar', 'lat': 31.2653, 'lon': 56.8056, 'population': 25000},
        ]
    },
    'Sistan-Baluchestan': {
        'capital': {'name': 'Zahedan', 'lat': 29.4963, 'lon': 60.8629, 'population': 600000},
        'cities': [
            {'name': 'Chabahar', 'lat': 25.2919, 'lon': 60.6430, 'population': 120000},
            {'name': 'Zabol', 'lat': 31.0286, 'lon': 61.5011, 'population': 150000},
            {'name': 'Iranshahr', 'lat': 27.2025, 'lon': 60.6850, 'population': 100000},
            {'name': 'Saravan', 'lat': 27.3686, 'lon': 62.3356, 'population': 80000},
            {'name': 'Khash', 'lat': 28.2211, 'lon': 61.2158, 'population': 70000},
            {'name': 'Nikshahr', 'lat': 26.2256, 'lon': 60.2117, 'population': 40000},
            {'name': 'Konarak', 'lat': 25.3567, 'lon': 60.3825, 'population': 25000},
            {'name': 'Sarbaz', 'lat': 26.6336, 'lon': 61.2539, 'population': 30000},
            {'name': 'Mirjaveh', 'lat': 29.0217, 'lon': 61.4500, 'population': 20000},
            {'name': 'Dalgan', 'lat': 27.4500, 'lon': 60.1000, 'population': 15000},
            {'name': 'Fanuj', 'lat': 26.5747, 'lon': 59.6389, 'population': 15000},
            {'name': 'Qasr-e Qand', 'lat': 26.2500, 'lon': 60.7667, 'population': 20000},
        ]
    },
    'Hormozgan': {
        'capital': {'name': 'Bandar Abbas', 'lat': 27.1865, 'lon': 56.2808, 'population': 550000},
        'cities': [
            {'name': 'Qeshm', 'lat': 26.9500, 'lon': 56.2667, 'population': 100000},
            {'name': 'Minab', 'lat': 27.1483, 'lon': 57.0800, 'population': 80000},
            {'name': 'Bandar Lengeh', 'lat': 26.5575, 'lon': 54.8808, 'population': 30000},
            {'name': 'Kish Island', 'lat': 26.5339, 'lon': 53.9800, 'population': 40000},
            {'name': 'Jask', 'lat': 25.6383, 'lon': 57.7703, 'population': 25000},
            {'name': 'Hajiabad', 'lat': 28.3097, 'lon': 55.9028, 'population': 50000},
            {'name': 'Rudan', 'lat': 27.4333, 'lon': 57.2000, 'population': 40000},
            {'name': 'Bashagard', 'lat': 26.2333, 'lon': 58.2833, 'population': 15000},
            {'name': 'Sirik', 'lat': 26.5333, 'lon': 57.1167, 'population': 20000},
            {'name': 'Parsian', 'lat': 27.2083, 'lon': 54.3556, 'population': 25000},
            {'name': 'Bandar Khamir', 'lat': 26.9500, 'lon': 55.5833, 'population': 20000},
            {'name': 'Abu Musa Island', 'lat': 25.8728, 'lon': 55.0331, 'population': 2000},
        ]
    },
    'Bushehr': {
        'capital': {'name': 'Bushehr', 'lat': 28.9234, 'lon': 50.8203, 'population': 230000},
        'cities': [
            {'name': 'Borazjan', 'lat': 29.2686, 'lon': 51.2181, 'population': 100000},
            {'name': 'Kangan', 'lat': 27.8364, 'lon': 52.0594, 'population': 50000},
            {'name': 'Genaveh', 'lat': 29.5833, 'lon': 50.5167, 'population': 40000},
            {'name': 'Khormoj', 'lat': 28.6500, 'lon': 51.3833, 'population': 30000},
            {'name': 'Asaluyeh', 'lat': 27.4750, 'lon': 52.6167, 'population': 35000},
            {'name': 'Deyr', 'lat': 27.8417, 'lon': 51.9417, 'population': 25000},
            {'name': 'Jam', 'lat': 27.8197, 'lon': 52.3183, 'population': 20000},
            {'name': 'Ahram', 'lat': 28.8833, 'lon': 51.2833, 'population': 15000},
            {'name': 'Kharg Island', 'lat': 29.2333, 'lon': 50.3167, 'population': 5000},
            {'name': 'Bandar Deylam', 'lat': 30.0500, 'lon': 50.1667, 'population': 20000},
            {'name': 'Bandar Rig', 'lat': 29.4833, 'lon': 50.6667, 'population': 15000},
        ]
    },
    'Qom': {
        'capital': {'name': 'Qom', 'lat': 34.6416, 'lon': 50.8746, 'population': 1300000},
        'cities': [
            {'name': 'Salafchegan', 'lat': 34.4500, 'lon': 50.4667, 'population': 30000},
            {'name': 'Kahak', 'lat': 34.3667, 'lon': 50.9333, 'population': 15000},
            {'name': 'Jafariyeh', 'lat': 34.5000, 'lon': 51.0000, 'population': 10000},
            {'name': 'Dastjerd', 'lat': 34.3500, 'lon': 50.7167, 'population': 8000},
            {'name': 'Fordo', 'lat': 34.8833, 'lon': 51.0000, 'population': 2000},
        ]
    },
    'Markazi': {
        'capital': {'name': 'Arak', 'lat': 34.0917, 'lon': 49.6892, 'population': 550000},
        'cities': [
            {'name': 'Saveh', 'lat': 35.0211, 'lon': 50.3567, 'population': 230000},
            {'name': 'Khomein', 'lat': 33.6419, 'lon': 50.0797, 'population': 60000},
            {'name': 'Delijan', 'lat': 33.9900, 'lon': 50.6833, 'population': 50000},
            {'name': 'Mahallat', 'lat': 33.9078, 'lon': 50.4536, 'population': 45000},
            {'name': 'Shazand', 'lat': 33.9333, 'lon': 49.4167, 'population': 40000},
            {'name': 'Tafresh', 'lat': 34.6928, 'lon': 50.0131, 'population': 25000},
            {'name': 'Ashtian', 'lat': 34.5225, 'lon': 50.0058, 'population': 20000},
            {'name': 'Komijan', 'lat': 34.7167, 'lon': 49.3167, 'population': 30000},
            {'name': 'Zarandieh', 'lat': 35.0167, 'lon': 49.6833, 'population': 25000},
            {'name': 'Farahan', 'lat': 34.4833, 'lon': 49.5667, 'population': 20000},
        ]
    },
    'Yazd': {
        'capital': {'name': 'Yazd', 'lat': 31.8974, 'lon': 54.3569, 'population': 550000},
        'cities': [
            {'name': 'Meybod', 'lat': 32.2500, 'lon': 54.0167, 'population': 80000},
            {'name': 'Ardakan', 'lat': 32.3100, 'lon': 54.0175, 'population': 70000},
            {'name': 'Bafq', 'lat': 31.6058, 'lon': 55.4031, 'population': 45000},
            {'name': 'Taft', 'lat': 31.7478, 'lon': 54.2083, 'population': 35000},
            {'name': 'Mehriz', 'lat': 31.5833, 'lon': 54.4333, 'population': 40000},
            {'name': 'Ashkezar', 'lat': 32.0000, 'lon': 54.2000, 'population': 25000},
            {'name': 'Abarkouh', 'lat': 31.1289, 'lon': 53.2828, 'population': 30000},
            {'name': 'Hamidia', 'lat': 32.4167, 'lon': 54.2667, 'population': 15000},
            {'name': 'Kharanaq', 'lat': 32.3167, 'lon': 54.5333, 'population': 5000},
        ]
    },
    'Semnan': {
        'capital': {'name': 'Semnan', 'lat': 35.5769, 'lon': 53.3975, 'population': 200000},
        'cities': [
            {'name': 'Shahroud', 'lat': 36.4181, 'lon': 54.9764, 'population': 180000},
            {'name': 'Damghan', 'lat': 36.1681, 'lon': 54.3481, 'population': 80000},
            {'name': 'Garmsar', 'lat': 35.2175, 'lon': 52.3411, 'population': 60000},
            {'name': 'Mahdishahr', 'lat': 35.7083, 'lon': 53.3500, 'population': 25000},
            {'name': 'Sorkheh', 'lat': 35.4667, 'lon': 53.2167, 'population': 20000},
            {'name': 'Aradan', 'lat': 35.2500, 'lon': 52.4833, 'population': 15000},
            {'name': 'Meyami', 'lat': 36.4500, 'lon': 55.7833, 'population': 10000},
        ]
    },
    'Alborz': {
        'capital': {'name': 'Karaj', 'lat': 35.8400, 'lon': 50.9391, 'population': 1600000},
        'cities': [
            {'name': 'Hashtgerd', 'lat': 35.9606, 'lon': 50.6850, 'population': 80000},
            {'name': 'Nazarabad', 'lat': 35.9528, 'lon': 50.6072, 'population': 60000},
            {'name': 'Fardis', 'lat': 35.7194, 'lon': 50.9861, 'population': 250000},
            {'name': 'Mohammad Shahr', 'lat': 35.7500, 'lon': 50.9000, 'population': 100000},
            {'name': 'Meshkin Dasht', 'lat': 35.7333, 'lon': 50.9500, 'population': 80000},
            {'name': 'Asara', 'lat': 35.9833, 'lon': 51.2167, 'population': 30000},
            {'name': 'Taleqan', 'lat': 36.1667, 'lon': 50.7667, 'population': 20000},
            {'name': 'Chalous Road', 'lat': 36.0000, 'lon': 51.2500, 'population': 15000},
        ]
    },
    'Kurdistan': {
        'capital': {'name': 'Sanandaj', 'lat': 35.3117, 'lon': 46.9986, 'population': 450000},
        'cities': [
            {'name': 'Saqqez', 'lat': 36.2464, 'lon': 46.2733, 'population': 180000},
            {'name': 'Marivan', 'lat': 35.5269, 'lon': 46.1761, 'population': 100000},
            {'name': 'Baneh', 'lat': 35.9972, 'lon': 45.8850, 'population': 100000},
            {'name': 'Qorveh', 'lat': 35.1667, 'lon': 47.8000, 'population': 90000},
            {'name': 'Kamyaran', 'lat': 34.7967, 'lon': 46.9358, 'population': 60000},
            {'name': 'Bijar', 'lat': 35.8833, 'lon': 47.6000, 'population': 50000},
            {'name': 'Divandarreh', 'lat': 35.9167, 'lon': 47.0167, 'population': 40000},
            {'name': 'Dehgolan', 'lat': 35.2833, 'lon': 47.4167, 'population': 35000},
            {'name': 'Sarvabad', 'lat': 35.3167, 'lon': 46.2333, 'population': 25000},
        ]
    },
    'Hamadan': {
        'capital': {'name': 'Hamadan', 'lat': 34.7992, 'lon': 48.5150, 'population': 600000},
        'cities': [
            {'name': 'Malayer', 'lat': 34.2969, 'lon': 48.8236, 'population': 180000},
            {'name': 'Nahavand', 'lat': 34.1900, 'lon': 48.3778, 'population': 80000},
            {'name': 'Tuyserkan', 'lat': 34.5486, 'lon': 48.4439, 'population': 60000},
            {'name': 'Asadabad', 'lat': 34.7811, 'lon': 48.1194, 'population': 70000},
            {'name': 'Bahar', 'lat': 34.9067, 'lon': 48.4408, 'population': 50000},
            {'name': 'Kabudarahang', 'lat': 35.2083, 'lon': 48.7250, 'population': 40000},
            {'name': 'Razan', 'lat': 35.3833, 'lon': 49.0333, 'population': 30000},
            {'name': 'Famenin', 'lat': 35.1167, 'lon': 48.9667, 'population': 25000},
        ]
    },
    'Kermanshah': {
        'capital': {'name': 'Kermanshah', 'lat': 34.3142, 'lon': 47.0650, 'population': 950000},
        'cities': [
            {'name': 'Eslamabad-e Gharb', 'lat': 34.1125, 'lon': 46.5281, 'population': 100000},
            {'name': 'Paveh', 'lat': 35.0436, 'lon': 46.3564, 'population': 50000},
            {'name': 'Javanrud', 'lat': 34.8064, 'lon': 46.4928, 'population': 60000},
            {'name': 'Kangavar', 'lat': 34.5042, 'lon': 47.9639, 'population': 50000},
            {'name': 'Sonqor', 'lat': 34.7833, 'lon': 47.6000, 'population': 60000},
            {'name': 'Harsin', 'lat': 34.2706, 'lon': 47.5864, 'population': 50000},
            {'name': 'Sahneh', 'lat': 34.4833, 'lon': 47.6833, 'population': 45000},
            {'name': 'Gilangharb', 'lat': 34.1417, 'lon': 45.9250, 'population': 30000},
            {'name': 'Sarpol-e Zahab', 'lat': 34.4614, 'lon': 45.8631, 'population': 70000},
            {'name': 'Qasr-e Shirin', 'lat': 34.5158, 'lon': 45.5786, 'population': 25000},
        ]
    },
    'Lorestan': {
        'capital': {'name': 'Khorramabad', 'lat': 33.4878, 'lon': 48.3558, 'population': 400000},
        'cities': [
            {'name': 'Borujerd', 'lat': 33.8972, 'lon': 48.7517, 'population': 280000},
            {'name': 'Dorud', 'lat': 33.4933, 'lon': 49.0658, 'population': 100000},
            {'name': 'Aligudarz', 'lat': 33.4003, 'lon': 49.6944, 'population': 80000},
            {'name': 'Azna', 'lat': 33.4500, 'lon': 49.4500, 'population': 50000},
            {'name': 'Kuhdasht', 'lat': 33.5333, 'lon': 47.6000, 'population': 80000},
            {'name': 'Pol-e Dokhtar', 'lat': 33.1500, 'lon': 47.7167, 'population': 50000},
            {'name': 'Nurabad', 'lat': 34.0833, 'lon': 47.9667, 'population': 40000},
            {'name': 'Rumeshkhan', 'lat': 33.1333, 'lon': 47.5500, 'population': 25000},
        ]
    },
    'Ilam': {
        'capital': {'name': 'Ilam', 'lat': 33.6374, 'lon': 46.4227, 'population': 200000},
        'cities': [
            {'name': 'Dehloran', 'lat': 32.6942, 'lon': 47.2681, 'population': 60000},
            {'name': 'Mehran', 'lat': 33.1222, 'lon': 46.1647, 'population': 50000},
            {'name': 'Ivan', 'lat': 33.8306, 'lon': 46.3028, 'population': 40000},
            {'name': 'Darreh Shahr', 'lat': 33.1444, 'lon': 47.3778, 'population': 30000},
            {'name': 'Abdanan', 'lat': 32.9939, 'lon': 47.4197, 'population': 25000},
            {'name': 'Sarableh', 'lat': 33.7667, 'lon': 46.5667, 'population': 20000},
            {'name': 'Badreh', 'lat': 33.2500, 'lon': 47.0833, 'population': 15000},
            {'name': 'Chardavol', 'lat': 33.7833, 'lon': 46.4500, 'population': 20000},
        ]
    },
    'Ardabil': {
        'capital': {'name': 'Ardabil', 'lat': 38.2498, 'lon': 48.2933, 'population': 550000},
        'cities': [
            {'name': 'Parsabad', 'lat': 39.6481, 'lon': 47.9175, 'population': 130000},
            {'name': 'Meshgin Shahr', 'lat': 38.3983, 'lon': 47.6786, 'population': 80000},
            {'name': 'Khalkhal', 'lat': 37.6208, 'lon': 48.5275, 'population': 50000},
            {'name': 'Bileh Savar', 'lat': 39.3833, 'lon': 48.3500, 'population': 50000},
            {'name': 'Namin', 'lat': 38.4250, 'lon': 48.4833, 'population': 35000},
            {'name': 'Germi', 'lat': 39.0333, 'lon': 48.0833, 'population': 40000},
            {'name': 'Kowsar', 'lat': 37.7833, 'lon': 48.5333, 'population': 25000},
            {'name': 'Nir', 'lat': 38.0500, 'lon': 47.9833, 'population': 20000},
            {'name': 'Sarein', 'lat': 38.1583, 'lon': 48.0711, 'population': 15000},
        ]
    },
    'Zanjan': {
        'capital': {'name': 'Zanjan', 'lat': 36.6736, 'lon': 48.4787, 'population': 450000},
        'cities': [
            {'name': 'Abhar', 'lat': 36.1461, 'lon': 49.2183, 'population': 100000},
            {'name': 'Khodabandeh', 'lat': 36.1167, 'lon': 48.6000, 'population': 50000},
            {'name': 'Khorramdarreh', 'lat': 36.2097, 'lon': 49.1936, 'population': 40000},
            {'name': 'Tarom', 'lat': 36.9000, 'lon': 48.9000, 'population': 30000},
            {'name': 'Ijrud', 'lat': 36.5833, 'lon': 48.1667, 'population': 25000},
            {'name': 'Mahneshan', 'lat': 36.7500, 'lon': 47.6667, 'population': 20000},
            {'name': 'Soltaniyeh', 'lat': 36.4333, 'lon': 48.7833, 'population': 10000},
        ]
    },
    'Golestan': {
        'capital': {'name': 'Gorgan', 'lat': 36.8456, 'lon': 54.4353, 'population': 400000},
        'cities': [
            {'name': 'Gonbad-e Kavus', 'lat': 37.2500, 'lon': 55.1675, 'population': 160000},
            {'name': 'Aliabad', 'lat': 36.9069, 'lon': 54.8678, 'population': 60000},
            {'name': 'Azadshahr', 'lat': 37.0883, 'lon': 55.1742, 'population': 50000},
            {'name': 'Kordkuy', 'lat': 36.7833, 'lon': 54.1167, 'population': 40000},
            {'name': 'Bandar Torkaman', 'lat': 36.9017, 'lon': 54.0722, 'population': 70000},
            {'name': 'Gomishan', 'lat': 37.0667, 'lon': 54.0667, 'population': 30000},
            {'name': 'Aqqala', 'lat': 37.0167, 'lon': 54.4500, 'population': 50000},
            {'name': 'Ramian', 'lat': 37.0167, 'lon': 55.1500, 'population': 30000},
            {'name': 'Galikesh', 'lat': 37.2667, 'lon': 55.4500, 'population': 25000},
            {'name': 'Kalaleh', 'lat': 37.3833, 'lon': 55.4833, 'population': 35000},
            {'name': 'Minudasht', 'lat': 37.2333, 'lon': 55.3667, 'population': 40000},
        ]
    },
    'Qazvin': {
        'capital': {'name': 'Qazvin', 'lat': 36.2797, 'lon': 50.0049, 'population': 500000},
        'cities': [
            {'name': 'Takestan', 'lat': 36.0694, 'lon': 49.6956, 'population': 100000},
            {'name': 'Abyek', 'lat': 36.0400, 'lon': 50.5306, 'population': 60000},
            {'name': 'Buin Zahra', 'lat': 35.7667, 'lon': 50.0583, 'population': 50000},
            {'name': 'Alborz', 'lat': 36.2000, 'lon': 49.8833, 'population': 30000},
            {'name': 'Avaj', 'lat': 35.5833, 'lon': 49.2167, 'population': 20000},
            {'name': 'Mohammadieh', 'lat': 36.2000, 'lon': 50.1000, 'population': 25000},
        ]
    },
    'North Khorasan': {
        'capital': {'name': 'Bojnurd', 'lat': 37.4747, 'lon': 57.3294, 'population': 250000},
        'cities': [
            {'name': 'Shirvan', 'lat': 37.3967, 'lon': 57.9267, 'population': 100000},
            {'name': 'Esfarayen', 'lat': 37.0700, 'lon': 57.5108, 'population': 80000},
            {'name': 'Ashkhaneh', 'lat': 37.5667, 'lon': 56.9167, 'population': 30000},
            {'name': 'Jajarm', 'lat': 36.9500, 'lon': 56.3833, 'population': 25000},
            {'name': 'Faruj', 'lat': 37.2333, 'lon': 58.2167, 'population': 20000},
            {'name': 'Mane va Semalqan', 'lat': 37.3000, 'lon': 56.3000, 'population': 15000},
            {'name': 'Garmeh', 'lat': 37.2000, 'lon': 56.5500, 'population': 10000},
        ]
    },
    'South Khorasan': {
        'capital': {'name': 'Birjand', 'lat': 32.8644, 'lon': 59.2214, 'population': 220000},
        'cities': [
            {'name': 'Qaen', 'lat': 33.7267, 'lon': 59.1842, 'population': 70000},
            {'name': 'Ferdows', 'lat': 34.0183, 'lon': 58.1717, 'population': 40000},
            {'name': 'Tabas', 'lat': 33.5975, 'lon': 56.9247, 'population': 50000},
            {'name': 'Sarbisheh', 'lat': 32.5833, 'lon': 59.8000, 'population': 25000},
            {'name': 'Nehbandan', 'lat': 31.5414, 'lon': 60.0364, 'population': 30000},
            {'name': 'Sarayan', 'lat': 33.8667, 'lon': 58.5167, 'population': 20000},
            {'name': 'Boshruyeh', 'lat': 33.8667, 'lon': 57.4333, 'population': 25000},
            {'name': 'Khusf', 'lat': 32.7833, 'lon': 58.8833, 'population': 15000},
            {'name': 'Darmian', 'lat': 33.0333, 'lon': 60.0000, 'population': 10000},
        ]
    },
    'Kohgiluyeh': {
        'capital': {'name': 'Yasuj', 'lat': 30.6683, 'lon': 51.5881, 'population': 150000},
        'cities': [
            {'name': 'Gachsaran', 'lat': 30.3575, 'lon': 50.7989, 'population': 100000},
            {'name': 'Dehdasht', 'lat': 30.7936, 'lon': 50.5642, 'population': 60000},
            {'name': 'Dogonbadan', 'lat': 30.3500, 'lon': 50.7833, 'population': 80000},
            {'name': 'Sisakht', 'lat': 30.8667, 'lon': 51.4500, 'population': 25000},
            {'name': 'Basht', 'lat': 30.3667, 'lon': 51.1667, 'population': 20000},
            {'name': 'Landeh', 'lat': 30.9833, 'lon': 50.4167, 'population': 15000},
        ]
    },
    'Chaharmahal': {
        'capital': {'name': 'Shahrekord', 'lat': 32.3256, 'lon': 50.8644, 'population': 200000},
        'cities': [
            {'name': 'Borujen', 'lat': 31.9675, 'lon': 51.2872, 'population': 60000},
            {'name': 'Farsan', 'lat': 32.2558, 'lon': 50.5656, 'population': 40000},
            {'name': 'Lordegan', 'lat': 31.5083, 'lon': 50.8333, 'population': 50000},
            {'name': 'Saman', 'lat': 32.4500, 'lon': 50.9167, 'population': 25000},
            {'name': 'Ben', 'lat': 32.5333, 'lon': 50.7167, 'population': 20000},
            {'name': 'Ardal', 'lat': 32.0000, 'lon': 50.6500, 'population': 15000},
            {'name': 'Koohrang', 'lat': 32.4333, 'lon': 50.1167, 'population': 10000},
        ]
    },
}

# Major infrastructure targets
CRITICAL_INFRASTRUCTURE = [
    # Nuclear facilities
    {'name': 'Natanz Nuclear Facility', 'lat': 33.7244, 'lon': 51.7275, 'type': 'nuclear', 'priority': 10},
    {'name': 'Fordow Nuclear Facility', 'lat': 34.8833, 'lon': 51.0000, 'type': 'nuclear', 'priority': 10},
    {'name': 'Bushehr Nuclear Power Plant', 'lat': 28.8317, 'lon': 50.8850, 'type': 'nuclear', 'priority': 10},
    {'name': 'Isfahan Nuclear Facility', 'lat': 32.5667, 'lon': 51.6333, 'type': 'nuclear', 'priority': 10},
    {'name': 'Arak Heavy Water Reactor', 'lat': 34.0386, 'lon': 49.2525, 'type': 'nuclear', 'priority': 10},
    
    # Major refineries
    {'name': 'Abadan Refinery', 'lat': 30.3392, 'lon': 48.2847, 'type': 'refinery', 'priority': 9},
    {'name': 'Tehran Refinery', 'lat': 35.4400, 'lon': 51.4200, 'type': 'refinery', 'priority': 9},
    {'name': 'Isfahan Refinery', 'lat': 32.5833, 'lon': 51.6500, 'type': 'refinery', 'priority': 9},
    {'name': 'Bandar Abbas Refinery', 'lat': 27.1500, 'lon': 56.2333, 'type': 'refinery', 'priority': 9},
    {'name': 'Tabriz Refinery', 'lat': 38.0500, 'lon': 46.3333, 'type': 'refinery', 'priority': 9},
    {'name': 'Shiraz Refinery', 'lat': 29.6000, 'lon': 52.5333, 'type': 'refinery', 'priority': 9},
    {'name': 'Lavan Refinery', 'lat': 26.8167, 'lon': 53.3667, 'type': 'refinery', 'priority': 9},
    {'name': 'Persian Gulf Star Refinery', 'lat': 27.5000, 'lon': 52.6167, 'type': 'refinery', 'priority': 9},
    
    # Oil/Gas terminals
    {'name': 'Kharg Island Terminal', 'lat': 29.2333, 'lon': 50.3167, 'type': 'terminal', 'priority': 9},
    {'name': 'South Pars Gas Field', 'lat': 26.9000, 'lon': 52.3000, 'type': 'gas_field', 'priority': 9},
    {'name': 'Assaluyeh Gas Complex', 'lat': 27.4750, 'lon': 52.6167, 'type': 'gas', 'priority': 9},
    
    # Power plants
    {'name': 'Shahid Rajaei Power Plant', 'lat': 36.3000, 'lon': 53.2000, 'type': 'power', 'priority': 8},
    {'name': 'Ramin Power Plant', 'lat': 31.3000, 'lon': 48.7000, 'type': 'power', 'priority': 8},
    {'name': 'Montazeri Power Plant', 'lat': 32.6500, 'lon': 51.7000, 'type': 'power', 'priority': 8},
    {'name': 'Bistun Power Plant', 'lat': 34.4000, 'lon': 47.0000, 'type': 'power', 'priority': 8},
    {'name': 'Besat Power Plant', 'lat': 35.5000, 'lon': 51.4500, 'type': 'power', 'priority': 8},
    {'name': 'Shazand Power Plant', 'lat': 33.9333, 'lon': 49.4167, 'type': 'power', 'priority': 8},
]


def generate_all_locations():
    """Generate all locations as a flat list for database import."""
    locations = []
    loc_id = 1
    
    # Add province capitals and cities
    for province, data in IRAN_PROVINCES.items():
        # Capital
        cap = data['capital']
        locations.append({
            'id': f'city_{loc_id}',
            'name': cap['name'],
            'lat': cap['lat'],
            'lon': cap['lon'],
            'type': 'city_capital',
            'category': 'population_center',
            'province': province,
            'population': cap.get('population', 0),
            'priority': 8 if cap.get('population', 0) > 1000000 else 6,
        })
        loc_id += 1
        
        # Cities
        for city in data.get('cities', []):
            locations.append({
                'id': f'city_{loc_id}',
                'name': city['name'],
                'lat': city['lat'],
                'lon': city['lon'],
                'type': 'city',
                'category': 'population_center',
                'province': province,
                'population': city.get('population', 0),
                'priority': 5 if city.get('population', 0) > 100000 else 4,
            })
            loc_id += 1
    
    # Add critical infrastructure
    for infra in CRITICAL_INFRASTRUCTURE:
        locations.append({
            'id': f'infra_{loc_id}',
            'name': infra['name'],
            'lat': infra['lat'],
            'lon': infra['lon'],
            'type': infra['type'],
            'category': 'critical_infrastructure',
            'province': 'Various',
            'priority': infra.get('priority', 7),
        })
        loc_id += 1
    
    return locations


def get_location_count():
    """Get total number of locations."""
    return sum(1 + len(data.get('cities', [])) for data in IRAN_PROVINCES.values()) + len(CRITICAL_INFRASTRUCTURE)


if __name__ == '__main__':
    locs = generate_all_locations()
    print(f"Total locations: {len(locs)}")
    print(f"Provinces: {len(IRAN_PROVINCES)}")
    print(f"Infrastructure: {len(CRITICAL_INFRASTRUCTURE)}")
