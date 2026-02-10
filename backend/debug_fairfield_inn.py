#!/usr/bin/env python3
"""Debug Fairfield Inn hotel data"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'travel_agent.settings')
sys.path.insert(0, '/home/user/ai-smart-flight-agent/backend')
django.setup()

from django.conf import settings
import requests
import json

# SerpAPI hotel search for JFK
params = {
    "engine": "google_hotels",
    "q": "New York JFK Airport",
    "check_in_date": "2026-02-20",
    "check_out_date": "2026-02-27",
    "adults": 2,
    "currency": "USD",
    "gl": "us",
    "hl": "en",
    "api_key": settings.SERP_API_KEY
}

print("🔍 Searching for Fairfield Inn...\n")
response = requests.get("https://serpapi.com/search", params=params, timeout=30)
data = response.json()

if 'properties' in data:
    # Find Fairfield Inn
    fairfield = None
    for hotel in data['properties']:
        if 'Fairfield Inn' in hotel.get('name', ''):
            fairfield = hotel
            break

    if fairfield:
        print(f"✅ Found: {fairfield.get('name', 'Unknown')}\n")

        # Check star rating
        print("⭐ Star Rating:")
        print(f"  overall_rating: {fairfield.get('overall_rating')}")
        print(f"  Type: {type(fairfield.get('overall_rating'))}\n")

        # Check images
        print("📸 Images:")
        images = fairfield.get('images', [])
        print(f"  Total images: {len(images)}")
        if images:
            print(f"  First image type: {type(images[0])}")
            if isinstance(images[0], dict):
                print(f"  First image object: {json.dumps(images[0], indent=4)}")
            else:
                print(f"  First image: {images[0]}")
        else:
            print("  No images found")

        # Check price
        print("\n💰 Price:")
        rate_per_night = fairfield.get('rate_per_night')
        print(f"  rate_per_night: {rate_per_night}")
        print(f"  Type: {type(rate_per_night)}")
        if isinstance(rate_per_night, dict):
            print(f"  extracted_lowest: {rate_per_night.get('extracted_lowest')}")
            print(f"  lowest: {rate_per_night.get('lowest')}")

        # Show all fields
        print("\n📋 All fields:")
        for key in sorted(fairfield.keys()):
            if key not in ['images', 'amenities', 'nearby_places']:
                print(f"  {key}: {fairfield[key]}")
    else:
        print("❌ Fairfield Inn not found in results")
        print(f"\nAvailable hotels:")
        for hotel in data['properties'][:5]:
            print(f"  - {hotel.get('name', 'Unknown')}")
else:
    print("❌ No properties in response")
    print(f"Response keys: {data.keys()}")
