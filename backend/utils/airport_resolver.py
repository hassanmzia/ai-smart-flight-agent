"""
Shared city/location-to-IATA airport code resolver.

Used by both the flights API search endpoint and the AI agent tools
to convert user-friendly location names to IATA codes for the SERP API.
"""
import re
import logging

logger = logging.getLogger(__name__)

# Mapping of common city/region/suburb names to IATA airport codes
CITY_TO_AIRPORT = {
    # US cities & regions
    'new york': 'JFK', 'nyc': 'JFK', 'manhattan': 'JFK',
    'los angeles': 'LAX', 'la': 'LAX',
    'chicago': 'ORD',
    'san francisco': 'SFO', 'sf': 'SFO',
    'miami': 'MIA',
    'dallas': 'DFW',
    'houston': 'IAH',
    'seattle': 'SEA',
    'boston': 'BOS',
    'atlanta': 'ATL',
    'denver': 'DEN',
    'las vegas': 'LAS', 'vegas': 'LAS',
    'orlando': 'MCO',
    'washington': 'IAD', 'washington dc': 'IAD', 'dc': 'IAD',
    'sterling': 'IAD', 'ashburn': 'IAD', 'reston': 'IAD', 'herndon': 'IAD',
    'dulles': 'IAD', 'leesburg': 'IAD', 'chantilly': 'IAD',
    'arlington': 'DCA', 'reagan': 'DCA', 'national': 'DCA',
    'baltimore': 'BWI',
    'philadelphia': 'PHL', 'philly': 'PHL',
    'detroit': 'DTW',
    'minneapolis': 'MSP',
    'phoenix': 'PHX',
    'san diego': 'SAN',
    'portland': 'PDX',
    'honolulu': 'HNL', 'hawaii': 'HNL',
    'anchorage': 'ANC', 'alaska': 'ANC',
    'charlotte': 'CLT',
    'salt lake city': 'SLC',
    'nashville': 'BNA',
    'austin': 'AUS',
    'tampa': 'TPA',
    'new orleans': 'MSY',
    'pittsburgh': 'PIT',
    'indianapolis': 'IND',
    'san antonio': 'SAT',
    'st louis': 'STL', 'saint louis': 'STL',
    'fort lauderdale': 'FLL',
    'raleigh': 'RDU', 'durham': 'RDU',
    'kansas city': 'MCI',
    'columbus': 'CMH',
    'cleveland': 'CLE',
    'sacramento': 'SMF',
    'san jose': 'SJC',
    'milwaukee': 'MKE',
    'jacksonville': 'JAX',
    'memphis': 'MEM',
    'richmond': 'RIC',
    'buffalo': 'BUF',
    'cancun': 'CUN',

    # Canada
    'toronto': 'YYZ',
    'vancouver': 'YVR',
    'montreal': 'YUL',

    # Mexico
    'mexico city': 'MEX',

    # Europe
    'london': 'LHR', 'heathrow': 'LHR',
    'paris': 'CDG',
    'berlin': 'BER',
    'rome': 'FCO',
    'madrid': 'MAD',
    'barcelona': 'BCN',
    'amsterdam': 'AMS',
    'frankfurt': 'FRA',
    'munich': 'MUC',
    'zurich': 'ZRH',
    'vienna': 'VIE',
    'prague': 'PRG',
    'lisbon': 'LIS',
    'dublin': 'DUB',
    'brussels': 'BRU',
    'copenhagen': 'CPH',
    'stockholm': 'ARN',
    'oslo': 'OSL',
    'helsinki': 'HEL',
    'warsaw': 'WAW',
    'budapest': 'BUD',
    'bucharest': 'OTP',
    'athens': 'ATH',
    'istanbul': 'IST',
    'moscow': 'SVO',
    'milan': 'MXP',
    'venice': 'VCE',
    'edinburgh': 'EDI',
    'geneva': 'GVA',

    # Asia
    'tokyo': 'NRT', 'narita': 'NRT', 'haneda': 'HND',
    'osaka': 'KIX',
    'seoul': 'ICN', 'incheon': 'ICN',
    'beijing': 'PEK',
    'shanghai': 'PVG',
    'hong kong': 'HKG',
    'singapore': 'SIN',
    'bangkok': 'BKK',
    'kuala lumpur': 'KUL',
    'taipei': 'TPE',
    'manila': 'MNL',
    'jakarta': 'CGK',
    'mumbai': 'BOM', 'bombay': 'BOM',
    'delhi': 'DEL', 'new delhi': 'DEL',
    'bangalore': 'BLR', 'bengaluru': 'BLR',
    'kolkata': 'CCU', 'calcutta': 'CCU',
    'chennai': 'MAA', 'madras': 'MAA',
    'hyderabad': 'HYD',
    'hanoi': 'HAN',
    'ho chi minh': 'SGN', 'saigon': 'SGN',

    # Bangladesh
    'dhaka': 'DAC', 'dacca': 'DAC',
    'chittagong': 'CGP', 'chattogram': 'CGP',
    'sylhet': 'ZYL',
    'jessore': 'JSR', 'jashore': 'JSR', 'khulna': 'JSR',
    'rajshahi': 'RJH',
    'barisal': 'BZL', 'barishal': 'BZL',
    'cox\'s bazar': 'CXB', 'coxs bazar': 'CXB',
    'saidpur': 'SPD',

    # Pakistan
    'islamabad': 'ISB',
    'karachi': 'KHI',
    'lahore': 'LHE',

    # Other South Asia
    'kathmandu': 'KTM',
    'colombo': 'CMB',
    'male': 'MLE', 'maldives': 'MLE',

    # Middle East
    'dubai': 'DXB',
    'abu dhabi': 'AUH',
    'doha': 'DOH',
    'riyadh': 'RUH',
    'jeddah': 'JED',
    'tel aviv': 'TLV',
    'beirut': 'BEY',
    'amman': 'AMM',

    # Middle East (expanded)
    'kuwait': 'KWI', 'kuwait city': 'KWI',
    'muscat': 'MCT',
    'manama': 'BAH', 'bahrain': 'BAH',
    'tehran': 'IKA',
    'baghdad': 'BGW',

    # Southeast Asia (expanded)
    'phuket': 'HKT',
    'chiang mai': 'CNX',
    'bali': 'DPS', 'denpasar': 'DPS',
    'surabaya': 'SUB',
    'cebu': 'CEB',
    'da nang': 'DAD',
    'phnom penh': 'PNH',
    'siem reap': 'REP',
    'vientiane': 'VTE',
    'yangon': 'RGN', 'rangoon': 'RGN',
    'penang': 'PEN',

    # East Asia (expanded)
    'nagoya': 'NGO',
    'sapporo': 'CTS',
    'fukuoka': 'FUK',
    'okinawa': 'OKA',
    'busan': 'PUS',
    'jeju': 'CJU',
    'guangzhou': 'CAN', 'canton': 'CAN',
    'shenzhen': 'SZX',
    'chengdu': 'CTU',
    'chongqing': 'CKG',
    'xian': 'XIY', "xi'an": 'XIY',
    'hangzhou': 'HGH',
    'wuhan': 'WUH',
    'kunming': 'KMG',
    'macau': 'MFM',
    'kaohsiung': 'KHH',
    'ulaanbaatar': 'UBN',

    # South Asia (expanded)
    'kochi': 'COK', 'cochin': 'COK',
    'goa': 'GOI',
    'ahmedabad': 'AMD',
    'pune': 'PNQ',
    'jaipur': 'JAI',
    'lucknow': 'LKO',
    'chandigarh': 'IXC',
    'guwahati': 'GAU',
    'peshawar': 'PEW',

    # Central America & Caribbean
    'panama city': 'PTY',
    'san salvador': 'SAL',
    'guatemala city': 'GUA',
    'san jose, costa rica': 'SJO',
    'nassau': 'NAS',
    'montego bay': 'MBJ',
    'kingston': 'KIN',
    'san juan': 'SJU',
    'punta cana': 'PUJ',
    'santo domingo': 'SDQ',

    # South America (expanded)
    'quito': 'UIO',
    'guayaquil': 'GYE',
    'montevideo': 'MVD',
    'asuncion': 'ASU',
    'caracas': 'CCS',
    'santa cruz': 'VVI',

    # Europe (expanded)
    'nice': 'NCE',
    'lyon': 'LYS',
    'marseille': 'MRS',
    'dusseldorf': 'DUS',
    'hamburg': 'HAM',
    'cologne': 'CGN', 'koln': 'CGN',
    'porto': 'OPO',
    'malaga': 'AGP',
    'naples': 'NAP', 'napoli': 'NAP',
    'florence': 'FLR', 'firenze': 'FLR',
    'gothenburg': 'GOT',
    'bergen': 'BGO',
    'reykjavik': 'KEF',
    'krakow': 'KRK', 'cracow': 'KRK',
    'dubrovnik': 'DBV',
    'split': 'SPU',
    'zagreb': 'ZAG',
    'ljubljana': 'LJU',
    'belgrade': 'BEG',
    'tirana': 'TIA',
    'thessaloniki': 'SKG',
    'heraklion': 'HER', 'crete': 'HER',
    'santorini': 'JTR',
    'mykonos': 'JMK',
    'antalya': 'AYT',
    'izmir': 'ADB',
    'ankara': 'ESB',
    'kyiv': 'KBP', 'kiev': 'KBP',
    'saint petersburg': 'LED', 'st petersburg': 'LED',
    'tbilisi': 'TBS',
    'yerevan': 'EVN',
    'baku': 'GYD',

    # Canada (expanded)
    'calgary': 'YYC',
    'edmonton': 'YEG',
    'ottawa': 'YOW',
    'halifax': 'YHZ',
    'winnipeg': 'YWG',

    # Mexico (expanded)
    'guadalajara': 'GDL',

    # Africa
    'cairo': 'CAI',
    'johannesburg': 'JNB', 'joburg': 'JNB',
    'cape town': 'CPT',
    'nairobi': 'NBO',
    'casablanca': 'CMN',
    'marrakech': 'RAK',
    'addis ababa': 'ADD',
    'lagos': 'LOS',
    'accra': 'ACC',
    'dar es salaam': 'DAR',
    'kampala': 'EBB',
    'kigali': 'KGL',
    'zanzibar': 'ZNZ',
    'mombasa': 'MBA',
    'durban': 'DUR',
    'abuja': 'ABV',
    'dakar': 'DSS',
    'tunis': 'TUN',
    'algiers': 'ALG',
    'mauritius': 'MRU',
    'hurghada': 'HRG',
    'sharm el sheikh': 'SSH',

    # Oceania
    'sydney': 'SYD',
    'melbourne': 'MEL',
    'brisbane': 'BNE',
    'perth': 'PER',
    'auckland': 'AKL',

    # South America
    'sao paulo': 'GRU',
    'rio de janeiro': 'GIG', 'rio': 'GIG',
    'buenos aires': 'EZE',
    'lima': 'LIM',
    'bogota': 'BOG',
    'santiago': 'SCL',
    'medellin': 'MDE',
}

# Reverse mapping: IATA code → human-readable city name (for hotel, car, restaurant searches)
# Picks the most recognizable city name for each code.
AIRPORT_TO_CITY = {
    # US
    'JFK': 'New York', 'LGA': 'New York', 'EWR': 'Newark',
    'LAX': 'Los Angeles', 'ORD': 'Chicago', 'SFO': 'San Francisco',
    'MIA': 'Miami', 'DFW': 'Dallas', 'IAH': 'Houston',
    'SEA': 'Seattle', 'BOS': 'Boston', 'ATL': 'Atlanta',
    'DEN': 'Denver', 'LAS': 'Las Vegas', 'MCO': 'Orlando',
    'IAD': 'Washington DC', 'DCA': 'Washington DC', 'BWI': 'Baltimore',
    'PHL': 'Philadelphia', 'DTW': 'Detroit', 'MSP': 'Minneapolis',
    'PHX': 'Phoenix', 'SAN': 'San Diego', 'PDX': 'Portland',
    'HNL': 'Honolulu', 'ANC': 'Anchorage', 'CLT': 'Charlotte',
    'SLC': 'Salt Lake City', 'BNA': 'Nashville', 'AUS': 'Austin',
    'TPA': 'Tampa', 'MSY': 'New Orleans', 'PIT': 'Pittsburgh',
    'IND': 'Indianapolis', 'SAT': 'San Antonio', 'STL': 'St Louis',
    'FLL': 'Fort Lauderdale', 'RDU': 'Raleigh', 'MCI': 'Kansas City',
    'CMH': 'Columbus', 'CLE': 'Cleveland', 'SMF': 'Sacramento',
    'SJC': 'San Jose', 'MKE': 'Milwaukee', 'JAX': 'Jacksonville',
    'MEM': 'Memphis', 'RIC': 'Richmond', 'BUF': 'Buffalo',
    # Canada
    'YYZ': 'Toronto', 'YVR': 'Vancouver', 'YUL': 'Montreal',
    # Mexico
    'MEX': 'Mexico City', 'CUN': 'Cancun',
    # Europe
    'LHR': 'London', 'CDG': 'Paris', 'BER': 'Berlin',
    'FCO': 'Rome', 'MAD': 'Madrid', 'BCN': 'Barcelona',
    'AMS': 'Amsterdam', 'FRA': 'Frankfurt', 'MUC': 'Munich',
    'ZRH': 'Zurich', 'VIE': 'Vienna', 'PRG': 'Prague',
    'LIS': 'Lisbon', 'DUB': 'Dublin', 'BRU': 'Brussels',
    'CPH': 'Copenhagen', 'ARN': 'Stockholm', 'OSL': 'Oslo',
    'HEL': 'Helsinki', 'WAW': 'Warsaw', 'BUD': 'Budapest',
    'OTP': 'Bucharest', 'ATH': 'Athens', 'IST': 'Istanbul',
    'SVO': 'Moscow', 'MXP': 'Milan', 'VCE': 'Venice',
    'EDI': 'Edinburgh', 'GVA': 'Geneva',
    # Asia
    'NRT': 'Tokyo', 'HND': 'Tokyo', 'KIX': 'Osaka',
    'ICN': 'Seoul', 'PEK': 'Beijing', 'PVG': 'Shanghai',
    'HKG': 'Hong Kong', 'SIN': 'Singapore', 'BKK': 'Bangkok',
    'KUL': 'Kuala Lumpur', 'TPE': 'Taipei', 'MNL': 'Manila',
    'CGK': 'Jakarta', 'BOM': 'Mumbai', 'DEL': 'Delhi',
    'BLR': 'Bangalore', 'CCU': 'Kolkata', 'MAA': 'Chennai',
    'HYD': 'Hyderabad', 'HAN': 'Hanoi', 'SGN': 'Ho Chi Minh City',
    # Bangladesh
    'DAC': 'Dhaka', 'CGP': 'Chittagong', 'ZYL': 'Sylhet',
    'JSR': 'Jessore', 'RJH': 'Rajshahi', 'BZL': 'Barisal',
    'CXB': "Cox's Bazar", 'SPD': 'Saidpur',
    # Pakistan
    'ISB': 'Islamabad', 'KHI': 'Karachi', 'LHE': 'Lahore', 'PEW': 'Peshawar',
    # Other South Asia
    'KTM': 'Kathmandu', 'CMB': 'Colombo', 'MLE': 'Male',
    'COK': 'Kochi', 'GOI': 'Goa', 'AMD': 'Ahmedabad', 'PNQ': 'Pune',
    'JAI': 'Jaipur', 'LKO': 'Lucknow', 'IXC': 'Chandigarh', 'GAU': 'Guwahati',
    # Middle East
    'DXB': 'Dubai', 'AUH': 'Abu Dhabi', 'DOH': 'Doha',
    'RUH': 'Riyadh', 'JED': 'Jeddah', 'TLV': 'Tel Aviv',
    'BEY': 'Beirut', 'AMM': 'Amman',
    'KWI': 'Kuwait City', 'MCT': 'Muscat', 'BAH': 'Manama',
    'IKA': 'Tehran', 'BGW': 'Baghdad', 'DMM': 'Dammam',
    # Southeast Asia
    'HKT': 'Phuket', 'CNX': 'Chiang Mai', 'DMK': 'Bangkok',
    'DPS': 'Bali', 'SUB': 'Surabaya', 'CEB': 'Cebu',
    'DAD': 'Da Nang', 'PNH': 'Phnom Penh', 'REP': 'Siem Reap',
    'VTE': 'Vientiane', 'RGN': 'Yangon', 'PEN': 'Penang',
    # East Asia
    'NGO': 'Nagoya', 'CTS': 'Sapporo', 'FUK': 'Fukuoka', 'OKA': 'Okinawa',
    'GMP': 'Seoul', 'PUS': 'Busan', 'CJU': 'Jeju',
    'PKX': 'Beijing', 'SHA': 'Shanghai', 'CAN': 'Guangzhou',
    'SZX': 'Shenzhen', 'CTU': 'Chengdu', 'CKG': 'Chongqing',
    'XIY': "Xi'an", 'HGH': 'Hangzhou', 'WUH': 'Wuhan', 'KMG': 'Kunming',
    'MFM': 'Macau', 'KHH': 'Kaohsiung', 'UBN': 'Ulaanbaatar',
    # Europe (expanded)
    'NCE': 'Nice', 'LYS': 'Lyon', 'MRS': 'Marseille',
    'DUS': 'Dusseldorf', 'HAM': 'Hamburg', 'CGN': 'Cologne',
    'OPO': 'Porto', 'AGP': 'Malaga', 'NAP': 'Naples', 'FLR': 'Florence',
    'GOT': 'Gothenburg', 'BGO': 'Bergen', 'KEF': 'Reykjavik',
    'KRK': 'Krakow', 'DBV': 'Dubrovnik', 'SPU': 'Split', 'ZAG': 'Zagreb',
    'LJU': 'Ljubljana', 'BEG': 'Belgrade', 'SOF': 'Sofia', 'TIA': 'Tirana',
    'SKG': 'Thessaloniki', 'HER': 'Heraklion', 'JTR': 'Santorini', 'JMK': 'Mykonos',
    'SAW': 'Istanbul', 'AYT': 'Antalya', 'ADB': 'Izmir', 'ESB': 'Ankara',
    'KBP': 'Kyiv', 'LED': 'Saint Petersburg', 'DME': 'Moscow',
    'TBS': 'Tbilisi', 'EVN': 'Yerevan', 'GYD': 'Baku',
    'MAN': 'Manchester', 'LGW': 'London', 'STN': 'London',
    'GLA': 'Glasgow', 'BFS': 'Belfast', 'BRS': 'Bristol',
    'SNN': 'Shannon', 'ORK': 'Cork', 'PMI': 'Palma',
    'BSL': 'Basel', 'BGY': 'Bergamo', 'SJJ': 'Sarajevo', 'SKP': 'Skopje',
    # Canada (expanded)
    'YYC': 'Calgary', 'YEG': 'Edmonton', 'YOW': 'Ottawa',
    'YHZ': 'Halifax', 'YWG': 'Winnipeg',
    # Mexico (expanded)
    'GDL': 'Guadalajara',
    # Central America & Caribbean
    'PTY': 'Panama City', 'SJO': 'San Jose', 'SAL': 'San Salvador', 'GUA': 'Guatemala City',
    'NAS': 'Nassau', 'MBJ': 'Montego Bay', 'KIN': 'Kingston',
    'SJU': 'San Juan', 'PUJ': 'Punta Cana', 'SDQ': 'Santo Domingo',
    # Africa
    'CAI': 'Cairo', 'JNB': 'Johannesburg', 'CPT': 'Cape Town',
    'NBO': 'Nairobi', 'CMN': 'Casablanca', 'RAK': 'Marrakech',
    'ADD': 'Addis Ababa', 'LOS': 'Lagos', 'ACC': 'Accra',
    'DAR': 'Dar es Salaam',
    'DUR': 'Durban', 'MBA': 'Mombasa', 'EBB': 'Kampala', 'KGL': 'Kigali',
    'ZNZ': 'Zanzibar', 'JRO': 'Kilimanjaro', 'ABV': 'Abuja',
    'HRG': 'Hurghada', 'SSH': 'Sharm el-Sheikh',
    'TUN': 'Tunis', 'ALG': 'Algiers', 'DSS': 'Dakar', 'MRU': 'Mauritius',
    # Oceania
    'SYD': 'Sydney', 'MEL': 'Melbourne', 'BNE': 'Brisbane',
    'PER': 'Perth', 'AKL': 'Auckland',
    'ADL': 'Adelaide', 'CBR': 'Canberra', 'CNS': 'Cairns',
    'WLG': 'Wellington', 'CHC': 'Christchurch', 'ZQN': 'Queenstown',
    'NAN': 'Nadi',
    # South America
    'GRU': 'Sao Paulo', 'GIG': 'Rio de Janeiro',
    'EZE': 'Buenos Aires', 'LIM': 'Lima', 'BOG': 'Bogota',
    'SCL': 'Santiago', 'MDE': 'Medellin',
    'UIO': 'Quito', 'GYE': 'Guayaquil', 'MVD': 'Montevideo',
    'ASU': 'Asuncion', 'CCS': 'Caracas', 'VVI': 'Santa Cruz',
}


# Hub airport mapping: small/domestic airports → nearest major international hub
# Used for fallback flight search when direct flights aren't found
AIRPORT_TO_HUB = {
    # Bangladesh domestic → Dhaka
    'JSR': 'DAC',  # Jessore → Dhaka
    'RJH': 'DAC',  # Rajshahi → Dhaka
    'BZL': 'DAC',  # Barisal → Dhaka
    'CXB': 'DAC',  # Cox's Bazar → Dhaka
    'SPD': 'DAC',  # Saidpur → Dhaka
    'ZYL': 'DAC',  # Sylhet → Dhaka
    'CGP': 'DAC',  # Chittagong → Dhaka (for international)
    # India domestic → Delhi/Mumbai
    'IXA': 'DEL',  # Agartala → Delhi
    'GAU': 'DEL',  # Guwahati → Delhi
    'IXR': 'DEL',  # Ranchi → Delhi
    'PAT': 'DEL',  # Patna → Delhi
    'VNS': 'DEL',  # Varanasi → Delhi
    'JAI': 'DEL',  # Jaipur → Delhi
    'IXC': 'DEL',  # Chandigarh → Delhi
    'LKO': 'DEL',  # Lucknow → Delhi
    'GOI': 'BOM',  # Goa → Mumbai
    'PNQ': 'BOM',  # Pune → Mumbai
    'IXE': 'BOM',  # Mangalore → Mumbai
    # Pakistan domestic → Islamabad/Karachi
    'PEW': 'ISB',  # Peshawar → Islamabad
    'MUX': 'LHE',  # Multan → Lahore
    'SKT': 'LHE',  # Sialkot → Lahore
    'UET': 'KHI',  # Quetta → Karachi
    # Sri Lanka
    'HRI': 'CMB',  # Mattala → Colombo
    # Nepal
    'BWA': 'KTM',  # Bhairahawa → Kathmandu
    'PKR': 'KTM',  # Pokhara → Kathmandu
    # Thailand domestic
    'CNX': 'BKK',  # Chiang Mai → Bangkok (for some international)
    'HDY': 'BKK',  # Hat Yai → Bangkok
    'USM': 'BKK',  # Koh Samui → Bangkok
    # Indonesia domestic
    'DPS': 'CGK',  # Bali → Jakarta (for some routes)
    'JOG': 'CGK',  # Yogyakarta → Jakarta
    'SUB': 'CGK',  # Surabaya → Jakarta
}


def get_hub_airport(code: str) -> str | None:
    """Get the nearest major international hub for a small/domestic airport."""
    return AIRPORT_TO_HUB.get(code.upper().strip()) if code else None


def resolve_airport_to_city(code: str) -> str:
    """
    Convert an IATA airport code to a human-readable city name.

    Used for hotel, car rental, and restaurant searches where city names
    produce better results than airport codes.

    Args:
        code: IATA airport code or city name

    Returns:
        City name if code is recognized, otherwise the input as-is
    """
    if not code:
        return code

    stripped = code.strip()
    upper = stripped.upper()

    if upper in AIRPORT_TO_CITY:
        city = AIRPORT_TO_CITY[upper]
        logger.info(f"Resolved airport code '{stripped}' -> '{city}'")
        return city

    # If it doesn't look like a 3-letter code, it's probably already a city name
    return stripped


def resolve_location_to_airport_code(location: str, country: str = "") -> str:
    """
    Resolve a user-provided location string to an IATA airport code.

    Handles:
    - Already an IATA code (3 letters): returned as-is
    - City name: looked up in CITY_TO_AIRPORT mapping
    - Comma-separated "city, state, country": tries each component
    - City + country pair: tries combined and individual lookups

    Args:
        location: City name, airport code, or "city, state, country" string
        country: Optional country for disambiguation

    Returns:
        IATA airport code, or the original input if no match found
    """
    if not location:
        return location

    stripped = location.strip()

    # Already a 3-letter IATA code
    if re.match(r'^[A-Za-z]{3}$', stripped):
        return stripped.upper()

    # Extract IATA code from "City (CODE)" format (from autocomplete)
    paren_match = re.search(r'\(([A-Za-z]{3})\)', stripped)
    if paren_match:
        code = paren_match.group(1).upper()
        logger.info(f"Extracted airport code from '{location}' -> {code}")
        return code

    normalized = stripped.lower().strip()

    # Direct match
    if normalized in CITY_TO_AIRPORT:
        code = CITY_TO_AIRPORT[normalized]
        logger.info(f"Resolved '{location}' -> {code} (direct match)")
        return code

    # Try with country appended (e.g., "portland, oregon" vs "portland, maine")
    if country:
        combo = f"{normalized}, {country.strip().lower()}"
        if combo in CITY_TO_AIRPORT:
            code = CITY_TO_AIRPORT[combo]
            logger.info(f"Resolved '{location}, {country}' -> {code} (with country)")
            return code

    # Split comma-separated parts and try each component
    # Handles: "Sterling, Virginia, USA" -> tries "sterling", "virginia", etc.
    parts = [p.strip().lower() for p in normalized.split(',')]
    for part in parts:
        if part in CITY_TO_AIRPORT:
            code = CITY_TO_AIRPORT[part]
            logger.info(f"Resolved '{location}' -> {code} (component match: '{part}')")
            return code

    # Try progressive combinations: "sterling, virginia", then "sterling"
    for i in range(len(parts)):
        candidate = ', '.join(parts[:i + 1])
        if candidate in CITY_TO_AIRPORT:
            code = CITY_TO_AIRPORT[candidate]
            logger.info(f"Resolved '{location}' -> {code} (partial match: '{candidate}')")
            return code

    # Fallback: search airports_db (handles keywords like "khulna" -> JSR)
    try:
        from utils.airports_db import search_airports as _search_airports_db
        db_results = _search_airports_db(normalized)
        if db_results:
            code = db_results[0]['code']
            logger.info(f"Resolved '{location}' -> {code} (airports_db fallback)")
            return code
    except Exception as e:
        logger.warning(f"airports_db fallback failed: {e}")

    # No match found - return original for the API to attempt
    logger.warning(f"Could not resolve '{location}' to airport code, passing as-is")
    return stripped
