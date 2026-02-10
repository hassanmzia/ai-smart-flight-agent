#!/usr/bin/env python
"""
Test script for SerpAPI flight search
Run this to debug why flights aren't being found
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, '/home/user/ai-smart-flight-agent/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'travel_agent.settings')
django.setup()

from apps.agents.agent_tools import FlightSearchTool
from django.conf import settings
import json
from datetime import datetime, timedelta

print("=" * 80)
print("FLIGHT SEARCH TEST")
print("=" * 80)

# Check API key
if not settings.SERP_API_KEY:
    print("❌ ERROR: SERP_API_KEY is not set!")
    sys.exit(1)
else:
    print(f"✅ SERP_API_KEY is configured: {settings.SERP_API_KEY[:10]}...")

# Test with future date
future_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')

print(f"\nTest Parameters:")
print(f"  Origin: JFK (New York)")
print(f"  Destination: LAX (Los Angeles)")
print(f"  Date: {future_date}")
print(f"  Passengers: 1")
print(f"  Trip Type: One-way")

print("\n" + "=" * 80)
print("Searching flights...")
print("=" * 80 + "\n")

# Run the search
result = FlightSearchTool.search_flights(
    origin='JFK',
    destination='LAX',
    date=future_date,
    trip_type=2,
    passengers=1
)

# Display results
print(f"\nSearch Result:")
print(f"  Success: {result.get('success', False)}")
print(f"  Flights Found: {len(result.get('flights', []))}")

if 'error' in result:
    print(f"  ❌ Error: {result.get('error')}")
    print(f"  Message: {result.get('message')}")

if 'raw_keys' in result:
    print(f"  Raw Response Keys: {result['raw_keys']}")

if result.get('flights'):
    print(f"\n✅ Found {len(result['flights'])} flights:")
    for i, flight in enumerate(result['flights'][:3], 1):
        print(f"\n  Flight {i}:")
        print(f"    Airline: {flight.get('airline')}")
        print(f"    Price: ${flight.get('price')}")
        print(f"    Departure: {flight.get('departure_time')}")
        print(f"    Arrival: {flight.get('arrival_time')}")
else:
    print(f"\n❌ No flights found!")
    if 'search_metadata' in result:
        print(f"\nSearch Metadata:")
        print(json.dumps(result['search_metadata'], indent=2))

print("\n" + "=" * 80)
print("Full Response (for debugging):")
print("=" * 80)
print(json.dumps(result, indent=2, default=str))
