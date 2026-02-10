#!/usr/bin/env python
"""
Quick diagnostic script to debug flight search issues
"""
import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django
sys.path.insert(0, '/home/user/ai-smart-flight-agent/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'travel_agent.settings')
django.setup()

from apps.agents.agent_tools import FlightSearchTool
from django.conf import settings
from serpapi import GoogleSearch
import json

print("=" * 80)
print("FLIGHT SEARCH DIAGNOSTIC")
print("=" * 80)

# 1. Check API key
print("\n1. API Key Check:")
if not settings.SERP_API_KEY:
    print("   ❌ SERP_API_KEY is NOT set!")
    sys.exit(1)
else:
    print(f"   ✅ API key present: {settings.SERP_API_KEY[:10]}...{settings.SERP_API_KEY[-4:]}")

# 2. Test date (30 days from now to ensure it's valid)
future_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
print(f"\n2. Using future date: {future_date}")

# 3. Test direct SerpAPI call
print("\n3. Direct SerpAPI Test:")
print("   Testing with IAD → LAX...")

params = {
    "api_key": settings.SERP_API_KEY,
    "engine": "google_flights",
    "hl": "en",
    "gl": "us",
    "departure_id": "IAD",
    "arrival_id": "LAX",
    "outbound_date": future_date,
    "type": 2,  # One-way
    "currency": "USD",
    "adults": 1,
    "travel_class": 1  # 1=Economy, 2=Premium economy, 3=Business, 4=First
}

print(f"   Params: {json.dumps(params, indent=2)}")

try:
    print("\n   Calling SerpAPI...")
    results = GoogleSearch(params).get_dict()

    print(f"\n4. SerpAPI Response:")
    print(f"   Response keys: {list(results.keys())}")

    if 'error' in results:
        print(f"   ❌ ERROR: {results['error']}")
        if 'message' in results:
            print(f"   Message: {results['message']}")
    else:
        print(f"   ✅ No error in response")

    best_flights = results.get('best_flights', [])
    other_flights = results.get('other_flights', [])

    print(f"\n5. Flight Counts:")
    print(f"   Best flights: {len(best_flights)}")
    print(f"   Other flights: {len(other_flights)}")
    print(f"   Total: {len(best_flights) + len(other_flights)}")

    if best_flights:
        print(f"\n6. Sample Flight:")
        flight = best_flights[0]
        print(f"   Price: ${flight.get('price', 'N/A')}")
        if 'flights' in flight and flight['flights']:
            f = flight['flights'][0]
            print(f"   Airline: {f.get('airline', 'N/A')}")
            print(f"   Departure: {f.get('departure_airport', {}).get('time', 'N/A')}")
            print(f"   Arrival: {f.get('arrival_airport', {}).get('time', 'N/A')}")

    # Save full response for inspection
    with open('/tmp/serp_response.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n7. Full response saved to: /tmp/serp_response.json")

    # 8. Test with FlightSearchTool
    print(f"\n8. Testing FlightSearchTool wrapper:")
    tool_result = FlightSearchTool.search_flights(
        origin='IAD',
        destination='LAX',
        date=future_date,
        trip_type=2,
        passengers=1
    )

    print(f"   Success: {tool_result.get('success')}")
    print(f"   Flights found: {len(tool_result.get('flights', []))}")
    if 'error' in tool_result:
        print(f"   Error: {tool_result['error']}")

except Exception as e:
    print(f"\n   ❌ EXCEPTION: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("DIAGNOSTIC COMPLETE")
print("=" * 80)
