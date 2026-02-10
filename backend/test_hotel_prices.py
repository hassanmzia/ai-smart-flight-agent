from serpapi import GoogleSearch
from datetime import datetime, timedelta
from django.conf import settings
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'travel_agent.settings')
django.setup()

check_in = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
check_out = (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')

params = {
    "api_key": settings.SERP_API_KEY,
    "engine": "google_hotels",
    "q": "New York JFK Airport",
    "check_in_date": check_in,
    "check_out_date": check_out,
    "adults": 1,
    "currency": "USD",
    "gl": "us",
    "hl": "en",
}

results = GoogleSearch(params).get_dict()
properties = results.get('properties', [])

print(f"\n{'='*80}")
print(f"Testing price extraction for JFK hotels")
print(f"{'='*80}\n")

for i, hotel in enumerate(properties[:5]):
    print(f"\nHotel {i+1}: {hotel.get('name')}")
    print(f"  rate_per_night: {hotel.get('rate_per_night')}")
    print(f"  total_rate: {hotel.get('total_rate')}")
    
    # Extract using our logic
    rpn = hotel.get('rate_per_night')
    if isinstance(rpn, dict):
        extracted = rpn.get('extracted_lowest', rpn.get('extracted_before_taxes_fees', 0))
        print(f"  → Extracted price: {extracted}")
    else:
        print(f"  → Extracted price: {rpn}")
