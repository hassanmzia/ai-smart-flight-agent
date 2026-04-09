"""
Autonomous Booking Agent
Handles end-to-end booking: search -> evaluate -> select -> book -> confirm.
User only approves the final summary before payment.
"""
import logging
import uuid
from typing import Dict, Any, List
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


class AutonomousBookingAgent:
    """End-to-end autonomous booking agent."""

    def __init__(self, user=None):
        self.user = user
        self.stages = []

    def plan_and_book(self, destination, start_date, end_date,
                      origin='', budget=None, travelers=1, preferences=None):
        """Execute full autonomous booking pipeline."""
        preferences = preferences or {}
        self._log('initiated', f'Starting: {origin} -> {destination}')

        self._log('searching', 'Searching flights, hotels, and activities...')
        results = self._search_all(destination, origin, start_date, end_date, travelers, preferences)

        self._log('evaluating', 'Evaluating options with AI agents...')
        ranked = self._evaluate(results, budget)

        self._log('selecting', 'Selecting optimal travel package...')
        package = self._select_package(ranked, budget, travelers)

        self._log('ready', 'Package ready for approval')
        summary = self._make_summary(package, destination, origin, start_date, end_date, travelers)

        return {
            'success': True,
            'status': 'awaiting_approval',
            'package': package,
            'summary': summary,
            'stages': self.stages,
            'estimated_total': package.get('total_cost', 0),
        }

    def _search_all(self, dest, origin, start, end, travelers, prefs):
        results = {}
        with ThreadPoolExecutor(max_workers=4) as ex:
            futs = {}
            if origin:
                futs['flights'] = ex.submit(self._search_flights, origin, dest, start, end, travelers)
            futs['hotels'] = ex.submit(self._search_hotels, dest, start, end, travelers)
            futs['restaurants'] = ex.submit(self._search_restaurants, dest, prefs.get('cuisine', ''))
            for k, f in futs.items():
                try:
                    results[k] = f.result(timeout=30)
                except Exception as e:
                    logger.warning(f"Search {k} failed: {e}")
                    results[k] = None
        return results

    def _search_flights(self, origin, dest, start, end, travelers):
        try:
            from .agent_tools import FlightSearchTool
            return FlightSearchTool.search_flights(origin=origin, destination=dest, date=start, return_date=end, passengers=travelers)
        except Exception:
            return None

    def _search_hotels(self, dest, start, end, travelers):
        try:
            from .agent_tools import HotelSearchTool
            return HotelSearchTool.search_hotels(location=dest, check_in=start, check_out=end, guests=travelers)
        except Exception:
            return None

    def _search_restaurants(self, dest, cuisine):
        try:
            from .agent_tools import RestaurantSearchTool
            return RestaurantSearchTool().search(location=dest, cuisine=cuisine)
        except Exception:
            return None

    def _evaluate(self, results, budget):
        ranked = {}
        flights = results.get('flights')
        if flights and isinstance(flights, dict):
            all_f = (flights.get('best_flights') or []) + (flights.get('other_flights') or [])
            ranked['flights'] = self._rank(all_f, 'flight', budget)
        hotels = results.get('hotels')
        if hotels and isinstance(hotels, dict):
            ranked['hotels'] = self._rank(hotels.get('properties', []), 'hotel', budget)
        return ranked

    def _rank(self, items, item_type, budget):
        scored = []
        for item in items[:20]:
            score = self._score(item, item_type, budget)
            scored.append({'data': item, 'score': score, 'type': item_type})
        scored.sort(key=lambda x: x['score'], reverse=True)
        return scored[:5]

    def _score(self, item, item_type, budget):
        score = 50.0
        try:
            if item_type == 'flight':
                price = self._extract_price(item.get('price', 0))
                if budget and price and price <= budget * 0.3:
                    score += 20
                legs = item.get('flights', [])
                if len(legs) <= 1:
                    score += 15
            elif item_type == 'hotel':
                rating = float(item.get('overall_rating', 0) or 0)
                score += rating * 5
                reviews = item.get('reviews', 0) or 0
                if isinstance(reviews, (int, float)) and reviews > 100:
                    score += 10
        except Exception:
            pass
        return min(score, 100)

    def _extract_price(self, price):
        if isinstance(price, (int, float)):
            return float(price)
        try:
            return float(str(price).replace('$', '').replace(',', ''))
        except (ValueError, TypeError):
            return 0

    def _select_package(self, ranked, budget, travelers):
        package = {'items': [], 'total_cost': 0}
        flights = ranked.get('flights', [])
        if flights:
            f = flights[0]['data']
            price = self._extract_price(f.get('price', 0))
            legs = f.get('flights', [])
            name = f"{legs[0].get('airline', 'Flight')}" if legs else "Flight"
            dep = legs[0].get('departure_airport', {}).get('id', '') if legs else ''
            arr = legs[-1].get('arrival_airport', {}).get('id', '') if legs else ''
            if dep and arr:
                name = f"{name} {dep}->{arr}"
            package['items'].append({'type': 'flight', 'name': name, 'price': price * travelers, 'details': f, 'score': flights[0]['score']})
            package['total_cost'] += price * travelers

        hotels = ranked.get('hotels', [])
        if hotels:
            h = hotels[0]['data']
            rate = h.get('rate_per_night', {})
            price = self._extract_price(rate.get('extracted_lowest') or rate.get('lowest') or 0)
            name = h.get('name', 'Hotel')
            rating = h.get('overall_rating', '')
            package['items'].append({'type': 'hotel', 'name': f"{name} ({rating}★)" if rating else name, 'price_per_night': price, 'details': h, 'score': hotels[0]['score']})

        package['alternatives'] = {
            'flights': [{'name': 'Alt flight', 'score': f['score']} for f in flights[1:3]],
            'hotels': [{'name': h['data'].get('name', ''), 'score': h['score']} for h in hotels[1:3]],
        }
        return package

    def _make_summary(self, package, dest, origin, start, end, travelers):
        items_text = []
        for item in package.get('items', []):
            if item['type'] == 'flight':
                items_text.append(f"✈️ {item['name']} — ${item['price']:.0f}")
            elif item['type'] == 'hotel':
                items_text.append(f"🏨 {item['name']} — ${item.get('price_per_night', 0):.0f}/night")
        return {
            'title': f"Trip to {dest}",
            'route': f"{origin} → {dest}" if origin else dest,
            'dates': f"{start} to {end}",
            'travelers': travelers,
            'items': items_text,
            'total_estimate': f"${package.get('total_cost', 0):.0f}",
            'approval_required': True,
        }

    def confirm_booking(self, package, payment_method_id=None):
        """Create booking records after user approval."""
        try:
            from apps.bookings.models import Booking
            if not self.user:
                return {'success': False, 'error': 'User not authenticated'}

            booking_number = f"AUTO-{uuid.uuid4().hex[:8].upper()}"
            total = Decimal(str(package.get('total_cost', 0)))

            booking = Booking.objects.create(
                user=self.user,
                booking_number=booking_number,
                status='pending',
                total_amount=total,
                currency='USD',
                primary_traveler_name=f"{self.user.first_name} {self.user.last_name}".strip() or self.user.email,
                primary_traveler_email=self.user.email,
                primary_traveler_phone=getattr(self.user, 'phone_number', ''),
                notes='Booked via Autonomous AI Agent',
            )
            return {'success': True, 'booking_number': booking_number, 'booking_id': booking.id, 'total': float(total)}
        except Exception as e:
            logger.error(f"Booking failed: {e}")
            return {'success': False, 'error': str(e)}

    def _log(self, stage, msg):
        self.stages.append({'stage': stage, 'message': msg, 'timestamp': timezone.now().isoformat()})
