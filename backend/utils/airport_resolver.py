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

    # Africa
    'cairo': 'CAI',
    'johannesburg': 'JNB',
    'cape town': 'CPT',
    'nairobi': 'NBO',
    'casablanca': 'CMN',
    'marrakech': 'RAK',
    'addis ababa': 'ADD',
    'lagos': 'LOS',
    'accra': 'ACC',
    'dar es salaam': 'DAR',

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

    # No match found - return original for the API to attempt
    logger.warning(f"Could not resolve '{location}' to airport code, passing as-is")
    return stripped
