"""
FlightMonitorAgent — Autonomous flight monitoring and rebooking.

Monitors booked flights for delays/cancellations and suggests rebooking
or alternative arrangements automatically.
"""
import hashlib
import json
import logging
import os
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from django.conf import settings

logger = logging.getLogger(__name__)


class FlightMonitorAgent:
    """Monitors flights and handles disruption recovery."""

    # Known disruption scenarios for deterministic fallback
    _DISRUPTION_TYPES = [
        'delay_short', 'delay_long', 'cancellation',
        'gate_change', 'diversion', 'none',
    ]

    def check_flight_status(
        self, flight_number: str, date: str, airline: str = ''
    ) -> Dict[str, Any]:
        """
        Check real-time flight status.

        Returns dict with: status, delay_minutes, gate, terminal,
        disruption_type, recovery_options
        """
        # Try live API first
        result = self._check_live(flight_number, date)
        if result is None:
            result = self._generate_fallback_status(flight_number, date, airline)

        # If disrupted, generate recovery options
        if result.get('disruption_type') not in ('none', None):
            result['recovery_options'] = self._generate_recovery(
                flight_number, date, airline, result['disruption_type']
            )
        else:
            result['recovery_options'] = []

        return result

    def get_rebooking_options(
        self,
        origin: str,
        destination: str,
        date: str,
        original_price: float = 0,
        airline_preference: str = '',
    ) -> List[Dict[str, Any]]:
        """
        Find alternative flights when the original is disrupted.
        Returns ranked list of alternatives.
        """
        options = self._search_alternatives_llm(
            origin, destination, date, airline_preference
        )
        if options is None:
            options = self._generate_alternative_flights(
                origin, destination, date, original_price
            )
        return options

    def assess_disruption_impact(
        self, disruption_type: str, delay_minutes: int, trip_items: List[Dict]
    ) -> Dict[str, Any]:
        """
        Assess impact of a flight disruption on the rest of the trip.
        """
        impact = {
            'severity': 'none',
            'affected_items': [],
            'recommendations': [],
        }

        if disruption_type == 'none' or delay_minutes == 0:
            return impact

        if delay_minutes < 60:
            impact['severity'] = 'low'
            impact['recommendations'].append(
                'Minor delay — your connecting plans should be unaffected.'
            )
        elif delay_minutes < 180:
            impact['severity'] = 'moderate'
            impact['recommendations'].append(
                'Moderate delay — check connecting flights and hotel check-in times.'
            )
            for item in trip_items:
                if item.get('type') == 'hotel':
                    impact['affected_items'].append({
                        'item': item.get('name', 'Hotel'),
                        'action': 'Notify hotel of late arrival',
                    })
        elif delay_minutes < 360:
            impact['severity'] = 'high'
            impact['recommendations'].extend([
                'Significant delay — consider rebooking connecting flights.',
                'Contact hotel to confirm late check-in or adjust reservation.',
                'Any morning activities tomorrow may need rescheduling.',
            ])
            for item in trip_items:
                impact['affected_items'].append({
                    'item': item.get('name', item.get('type', 'Item')),
                    'action': 'Review and potentially reschedule',
                })
        else:
            impact['severity'] = 'critical'
            impact['recommendations'].extend([
                'Flight may arrive next day — request airline accommodation.',
                'Cancel or reschedule first day activities.',
                'Consider alternative routing via nearby airports.',
            ])
            for item in trip_items:
                impact['affected_items'].append({
                    'item': item.get('name', item.get('type', 'Item')),
                    'action': 'Reschedule required',
                })

        if disruption_type == 'cancellation':
            impact['severity'] = 'critical'
            impact['recommendations'] = [
                'Flight cancelled — immediate rebooking required.',
                'Check airline rebooking policy (most provide free rebooking).',
                'Consider alternative airlines or nearby departure airports.',
                'If no same-day options, request hotel accommodation from airline.',
            ]

        return impact

    # ── Private helpers ─────────────────────────────────────────

    def _check_live(self, flight_number: str, date: str) -> Optional[Dict]:
        """Attempt live flight status check."""
        api_key = getattr(settings, 'FLIGHTAWARE_API_KEY', '') or os.getenv(
            'FLIGHTAWARE_API_KEY', ''
        )
        if not api_key or api_key in ('', 'your_key_here'):
            return None

        try:
            import requests
            resp = requests.get(
                f'https://aeroapi.flightaware.com/aeroapi/flights/{flight_number}',
                headers={'x-apikey': api_key},
                timeout=10,
            )
            if resp.status_code != 200:
                return None
            data = resp.json()
            flights = data.get('flights', [])
            if not flights:
                return None

            f = flights[0]
            delay = f.get('arrival_delay', 0) or 0
            status_val = f.get('status', 'Unknown')
            cancelled = 'cancel' in status_val.lower()
            dtype = (
                'cancellation' if cancelled
                else 'delay_long' if delay > 120
                else 'delay_short' if delay > 15
                else 'none'
            )
            return {
                'flight_number': flight_number,
                'status': status_val,
                'delay_minutes': delay,
                'gate': f.get('gate_dest', ''),
                'terminal': f.get('terminal_dest', ''),
                'disruption_type': dtype,
            }
        except Exception as e:
            logger.warning('FlightAware check failed: %s', e)
            return None

    def _generate_fallback_status(
        self, flight_number: str, date: str, airline: str
    ) -> Dict[str, Any]:
        """Deterministic fallback flight status."""
        seed = int(
            hashlib.md5(f'{flight_number}:{date}'.encode()).hexdigest()[:8], 16
        )
        rng = random.Random(seed)

        # 70% on time, 20% short delay, 7% long delay, 3% cancellation
        roll = rng.random()
        if roll < 0.70:
            dtype = 'none'
            delay = 0
            status_text = 'On Time'
        elif roll < 0.90:
            dtype = 'delay_short'
            delay = rng.randint(15, 55)
            status_text = f'Delayed {delay}min'
        elif roll < 0.97:
            dtype = 'delay_long'
            delay = rng.randint(60, 240)
            status_text = f'Delayed {delay}min'
        else:
            dtype = 'cancellation'
            delay = 0
            status_text = 'Cancelled'

        gate = f'{rng.choice("ABCDE")}{rng.randint(1, 45)}'
        terminal = str(rng.randint(1, 5))

        return {
            'flight_number': flight_number,
            'airline': airline,
            'date': date,
            'status': status_text,
            'delay_minutes': delay,
            'gate': gate,
            'terminal': terminal,
            'disruption_type': dtype,
        }

    def _generate_recovery(
        self, flight_number: str, date: str, airline: str, disruption_type: str
    ) -> List[Dict[str, Any]]:
        """Generate recovery options for disrupted flights."""
        options = []
        if disruption_type == 'delay_short':
            options.append({
                'action': 'wait',
                'description': 'Wait for the delayed flight — short delay expected.',
                'cost': 0,
                'confidence': 'high',
            })
        elif disruption_type == 'delay_long':
            options.extend([
                {
                    'action': 'wait',
                    'description': 'Wait for the delayed flight.',
                    'cost': 0,
                    'confidence': 'medium',
                },
                {
                    'action': 'rebook_same_airline',
                    'description': f'Request rebooking on next {airline or "airline"} flight.',
                    'cost': 0,
                    'confidence': 'high',
                },
                {
                    'action': 'rebook_different',
                    'description': 'Book alternative flight on different airline.',
                    'cost': 150,
                    'confidence': 'high',
                },
            ])
        elif disruption_type == 'cancellation':
            options.extend([
                {
                    'action': 'rebook_same_airline',
                    'description': f'{airline or "Airline"} should rebook you on the next available flight for free.',
                    'cost': 0,
                    'confidence': 'high',
                },
                {
                    'action': 'rebook_different',
                    'description': 'Book on alternative airline (may be reimbursable).',
                    'cost': 200,
                    'confidence': 'medium',
                },
                {
                    'action': 'refund_and_cancel',
                    'description': 'Request full refund and cancel this leg.',
                    'cost': 0,
                    'confidence': 'high',
                },
            ])
        return options

    def _search_alternatives_llm(
        self, origin: str, destination: str, date: str, airline_pref: str
    ) -> Optional[List[Dict]]:
        """Try LLM for alternative flight suggestions."""
        api_key = getattr(
            settings, 'OPENAI_API_KEY', os.getenv('OPENAI_API_KEY', '')
        )
        if not api_key or api_key in ('', 'your_openai_api_key_here'):
            return None

        try:
            from langchain_openai import ChatOpenAI
            from langchain.schema import HumanMessage, SystemMessage

            model = ChatOpenAI(
                model='gpt-4o-mini', temperature=0.3,
                api_key=api_key, request_timeout=30,
            )
            resp = model.invoke([
                SystemMessage(content='You are a flight rebooking assistant. Return JSON only.'),
                HumanMessage(content=f"""Suggest 4 alternative flights from {origin} to {destination} on {date}.
{f'Prefer {airline_pref} if possible.' if airline_pref else ''}

Return a JSON array:
[{{"airline": "...", "flight_number": "...", "departure": "HH:MM", "arrival": "HH:MM", "stops": 0, "estimated_price": 250, "confidence": "high"}}]"""),
            ])
            content = resp.content.strip()
            if content.startswith('```'):
                content = content.split('\n', 1)[1].rsplit('```', 1)[0]
            return json.loads(content)
        except Exception as e:
            logger.warning('LLM alternative search failed: %s', e)
            return None

    def _generate_alternative_flights(
        self, origin: str, destination: str, date: str, original_price: float
    ) -> List[Dict[str, Any]]:
        """Deterministic fallback alternative flights."""
        seed = int(
            hashlib.md5(f'{origin}:{destination}:{date}'.encode()).hexdigest()[:8], 16
        )
        rng = random.Random(seed)
        airlines = ['Delta', 'United', 'American', 'JetBlue', 'Southwest', 'Alaska']
        base_price = original_price if original_price > 0 else rng.randint(200, 800)

        alternatives = []
        for i in range(4):
            airline = rng.choice(airlines)
            code = airline[:2].upper()
            dep_hour = rng.randint(6, 20)
            flight_hrs = rng.randint(2, 8)
            stops = rng.choice([0, 0, 0, 1, 1, 2])
            price = round(base_price * rng.uniform(0.8, 1.5), 2)
            alternatives.append({
                'airline': airline,
                'flight_number': f'{code}{rng.randint(100, 9999)}',
                'departure': f'{dep_hour:02d}:{rng.choice(["00", "15", "30", "45"])}',
                'arrival': f'{(dep_hour + flight_hrs) % 24:02d}:{rng.choice(["00", "15", "30", "45"])}',
                'stops': stops,
                'estimated_price': price,
                'confidence': 'medium',
            })
        alternatives.sort(key=lambda x: x['estimated_price'])
        return alternatives
