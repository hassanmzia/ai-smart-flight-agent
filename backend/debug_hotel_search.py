#!/usr/bin/env python
"""
Quick diagnostic script to debug hotel search pricing issues
"""
import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django
sys.path.insert(0, '/home/user/ai-smart-flight-agent/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'travel_agent.settings')
django.setup()

from apps.agents.agent_tools import HotelSearchTool
from django.conf import settings
from serpapi import GoogleSearch
import json

print("=" * 80)
print("HOTEL SEARCH DIAGNOSTIC")
print("=" * 80)

# 1. Check API key
print("\n1. API Key Check:")
if not settings.SERP_API_KEY:
    print("   ❌ SERP_API_KEY is NOT set!")
    sys.exit(1)
else:
    print(f"   ✅ API key present: {settings.SERP_API_KEY[:10]}...{settings.SERP_API_KEY[-4:]}")

# 2. Test dates
check_in = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
check_out = (datetime.now() + timedelta(days=37)).strftime('%Y-%m-%d')
print(f"\n2. Using dates: {check_in} to {check_out} (7 nights)")

# 3. Test direct SerpAPI call
print("\n3. Direct SerpAPI Test:")
print("   Testing hotels in Los Angeles Airport...")

params = {
    "api_key": settings.SERP_API_KEY,
    "engine": "google_hotels",
    "q": "Los Angeles Airport",
    "check_in_date": check_in,
    "check_out_date": check_out,
    "adults": 1,
    "currency": "USD",
    "gl": "us",
    "hl": "en",
}

print(f"   Params: {json.dumps(params, indent=2)}")

try:
    print("\n   Calling SerpAPI...")
    results = GoogleSearch(params).get_dict()

    print(f"\n4. SerpAPI Response:")
    print(f"   Response keys: {list(results.keys())}")

    if 'error' in results:
        print(f"   ❌ ERROR: {results['error']}")
    else:
        print(f"   ✅ No error in response")

    properties = results.get('properties', [])
    print(f"\n5. Hotel Counts:")
    print(f"   Hotels found: {len(properties)}")

    if properties:
        print(f"\n6. First 3 Hotels (RAW DATA):")
        for i, hotel in enumerate(properties[:3]):
            print(f"\n   --- Hotel {i+1} ---")
            print(f"   Name: {hotel.get('name', 'N/A')}")
            print(f"   Overall rating: {hotel.get('overall_rating', 'N/A')}")

            # Check all possible price fields
            print(f"\n   Price fields in response:")
            print(f"   - rate_per_night: {hotel.get('rate_per_night', 'NOT FOUND')}")
            print(f"   - total_rate: {hotel.get('total_rate', 'NOT FOUND')}")
            print(f"   - price: {hotel.get('price', 'NOT FOUND')}")

            # Show ALL keys for this hotel
            print(f"\n   All available keys: {list(hotel.keys())[:20]}")

    # Save full response for inspection
    with open('/tmp/hotel_response.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n7. Full response saved to: /tmp/hotel_response.json")

    # 8. Test with HotelSearchTool
    print(f"\n8. Testing HotelSearchTool wrapper:")
    tool_result = HotelSearchTool.search_hotels(
        location='Los Angeles Airport',
        check_in_date=check_in,
        check_out_date=check_out,
        adults=1
    )

    print(f"   Success: {tool_result.get('success')}")
    hotels = tool_result.get('hotels', [])
    print(f"   Hotels found: {len(hotels)}")

    if hotels:
        print(f"\n   First hotel after parsing:")
        h = hotels[0]
        print(f"   - Name: {h.get('hotel_name')}")
        print(f"   - Price per night: {h.get('price_per_night')}")
        print(f"   - Total rate: {h.get('total_rate')}")
        print(f"   - Star rating: {h.get('star_rating')}")

except Exception as e:
    print(f"\n   ❌ EXCEPTION: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("DIAGNOSTIC COMPLETE")
print("=" * 80)
