"""
Health Travel Service
Medical facilities, accessibility ratings, medication management, fatigue-aware itineraries,
and health insurance recommendations.
"""
import hashlib
import json
import logging
import os
import random
from typing import Any, Dict, List, Optional

from django.conf import settings

logger = logging.getLogger(__name__)


class HealthTravelService:
    """Health-aware travel features: medical facilities, accessibility, medications, insurance, fatigue planning."""

    # Simplified UTC offset map (same as HealthAgent)
    _TZ_OFFSETS = {
        'US/Eastern': -5, 'America/New_York': -5,
        'US/Central': -6, 'America/Chicago': -6,
        'US/Mountain': -7, 'America/Denver': -7,
        'US/Pacific': -8, 'America/Los_Angeles': -8,
        'Europe/London': 0, 'GMT': 0, 'UTC': 0,
        'Europe/Paris': 1, 'Europe/Berlin': 1, 'Europe/Rome': 1,
        'Europe/Istanbul': 3, 'Asia/Dubai': 4,
        'Asia/Kolkata': 5, 'Asia/Bangkok': 7,
        'Asia/Singapore': 8, 'Asia/Shanghai': 8,
        'Asia/Tokyo': 9, 'Australia/Sydney': 11,
        'Pacific/Auckland': 12,
    }

    @staticmethod
    def find_medical_facilities(destination: str, facility_type: Optional[str] = None,
                                 emergency_only: bool = False, limit: int = 10) -> Dict[str, Any]:
        """Find medical facilities near a destination."""
        try:
            from apps.agents.models import MedicalFacility
            qs = MedicalFacility.objects.filter(destination__iexact=destination)
            if facility_type:
                qs = qs.filter(facility_type=facility_type)
            if emergency_only:
                qs = qs.filter(emergency_24h=True)

            if not qs.exists():
                HealthTravelService._generate_facilities(destination)
                qs = MedicalFacility.objects.filter(destination__iexact=destination)
                if facility_type:
                    qs = qs.filter(facility_type=facility_type)
                if emergency_only:
                    qs = qs.filter(emergency_24h=True)

            facilities = list(qs[:limit])
            return {
                'success': True,
                'facilities': [HealthTravelService._facility_to_dict(f) for f in facilities],
                'total': qs.count(),
            }
        except Exception as e:
            logger.error("Medical facilities failed: %s", e)
            return {'success': False, 'error': str(e)}

    @staticmethod
    def _generate_facilities(destination: str):
        from apps.agents.models import MedicalFacility
        seed = int(hashlib.md5(f"medical:{destination}".encode()).hexdigest()[:8], 16)
        rng = random.Random(seed)

        templates = [
            ('hospital', f'{destination} General Hospital', True, True, True,
             ['emergency_medicine', 'surgery', 'internal_medicine', 'pediatrics']),
            ('hospital', f'{destination} International Medical Center', True, True, True,
             ['cardiology', 'orthopedics', 'neurology', 'oncology']),
            ('clinic', f'{destination} Walk-In Clinic', False, True, True,
             ['general_practice', 'minor_injuries']),
            ('pharmacy', f'{destination} Central Pharmacy', False, True, False,
             ['prescriptions', 'over_the_counter']),
            ('pharmacy', f'MedPlus Pharmacy {destination}', False, False, False,
             ['prescriptions', 'travel_medicine']),
            ('emergency', f'{destination} Emergency Care', True, True, True,
             ['trauma', 'cardiac', 'stroke']),
            ('dental', f'{destination} Dental Care', False, True, True,
             ['general_dentistry', 'emergency_dental']),
        ]

        for ftype, name, emergency, english, insurance, specs in templates:
            MedicalFacility.objects.create(
                destination=destination, name=name,
                facility_type=ftype,
                address=f"Medical District, {destination}",
                phone=f"+1-555-{rng.randint(100, 999)}-{rng.randint(1000, 9999)}",
                distance_km=round(rng.uniform(0.5, 8.0), 2),
                emergency_24h=emergency,
                english_speaking=english,
                accepts_travel_insurance=insurance,
                specialties=specs,
                rating=round(rng.uniform(3.5, 5.0), 1),
                wheelchair_accessible=rng.choice([True, True, True, False]),
            )

    @staticmethod
    def get_accessibility_info(destination: str, venue_type: Optional[str] = None) -> Dict[str, Any]:
        """Get accessibility ratings for a destination."""
        try:
            from apps.agents.models import AccessibilityRating
            qs = AccessibilityRating.objects.filter(destination__iexact=destination)
            if venue_type:
                qs = qs.filter(venue_type=venue_type)

            ratings = list(qs.order_by('-created_at')[:20])
            avg_rating = sum(r.mobility_rating for r in ratings) / len(ratings) if ratings else 0

            return {
                'success': True,
                'ratings': [HealthTravelService._rating_to_dict(r) for r in ratings],
                'average_mobility_rating': round(avg_rating, 1),
                'total_ratings': qs.count(),
            }
        except Exception as e:
            logger.error("Accessibility info failed: %s", e)
            return {'success': False, 'error': str(e)}

    @staticmethod
    def submit_accessibility_rating(user, data: Dict) -> Dict[str, Any]:
        """Create or update an accessibility rating."""
        try:
            from apps.agents.models import AccessibilityRating
            destination = data.get('destination')
            venue_name = data.get('venue_name')
            venue_type = data.get('venue_type')
            mobility_rating = data.get('mobility_rating')

            if not all([destination, venue_name, venue_type, mobility_rating]):
                return {'success': False, 'error': 'destination, venue_name, venue_type, and mobility_rating are required'}

            rating, created = AccessibilityRating.objects.update_or_create(
                user=user, destination=destination, venue_name=venue_name,
                defaults={
                    'venue_type': venue_type,
                    'mobility_rating': int(mobility_rating),
                    'wheelchair_accessible': data.get('wheelchair_accessible', False),
                    'elevator_available': data.get('elevator_available', False),
                    'accessible_restroom': data.get('accessible_restroom', False),
                    'braille_signage': data.get('braille_signage', False),
                    'hearing_loop': data.get('hearing_loop', False),
                    'notes': data.get('notes', ''),
                },
            )
            return {
                'success': True,
                'created': created,
                'rating': HealthTravelService._rating_to_dict(rating),
            }
        except Exception as e:
            logger.error("Submit accessibility rating failed: %s", e)
            return {'success': False, 'error': str(e)}

    @staticmethod
    def manage_medication_reminders(user, action: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """CRUD for medication reminders."""
        try:
            from apps.agents.models import MedicationReminder

            if action == 'list':
                reminders = MedicationReminder.objects.filter(user=user, is_active=True).order_by('home_time')
                return {
                    'success': True,
                    'reminders': [HealthTravelService._reminder_to_dict(r) for r in reminders],
                }

            if action == 'add':
                if not data or not data.get('medication_name'):
                    return {'success': False, 'error': 'medication_name is required'}
                reminder = MedicationReminder.objects.create(
                    user=user,
                    medication_name=data['medication_name'],
                    dosage=data.get('dosage', ''),
                    home_time=data.get('home_time', '08:00'),
                    home_timezone=data.get('home_timezone', 'America/New_York'),
                    frequency=data.get('frequency', 'daily'),
                    notes=data.get('notes', ''),
                )
                return {'success': True, 'reminder': HealthTravelService._reminder_to_dict(reminder)}

            if action == 'update' and data:
                reminder_id = data.get('id')
                if not reminder_id:
                    return {'success': False, 'error': 'id is required for update'}
                reminder = MedicationReminder.objects.get(id=reminder_id, user=user)
                for field in ('medication_name', 'dosage', 'home_time', 'home_timezone', 'frequency', 'notes'):
                    if field in data:
                        setattr(reminder, field, data[field])
                reminder.save()
                return {'success': True, 'reminder': HealthTravelService._reminder_to_dict(reminder)}

            if action == 'delete' and data:
                reminder_id = data.get('id')
                if not reminder_id:
                    return {'success': False, 'error': 'id is required for delete'}
                MedicationReminder.objects.filter(id=reminder_id, user=user).update(is_active=False)
                return {'success': True, 'message': 'Reminder deactivated'}

            return {'success': False, 'error': f'Unknown action: {action}'}
        except Exception as e:
            logger.error("Medication reminders failed: %s", e)
            return {'success': False, 'error': str(e)}

    @staticmethod
    def adjust_medications_for_trip(user, destination_timezone: str) -> Dict[str, Any]:
        """Adjust medication schedule for a destination timezone."""
        try:
            from apps.agents.models import MedicationReminder
            reminders = MedicationReminder.objects.filter(user=user, is_active=True)
            if not reminders.exists():
                return {'success': True, 'adjusted_medications': [], 'message': 'No active medications'}

            adjusted = []
            for r in reminders:
                origin_offset = HealthTravelService._TZ_OFFSETS.get(r.home_timezone, 0)
                dest_offset = HealthTravelService._TZ_OFFSETS.get(destination_timezone, 0)
                diff = dest_offset - origin_offset

                h, m = r.home_time.hour, r.home_time.minute
                new_h = (h + diff) % 24
                adjusted_time = f"{new_h:02d}:{m:02d}"

                abs_diff = abs(diff)
                if abs_diff == 0:
                    note = 'No timezone change. Continue normal schedule.'
                elif abs_diff <= 3:
                    note = f'Small shift ({diff:+d}h). Adjust by 1 hour per day.'
                elif abs_diff <= 6:
                    note = f'Moderate shift ({diff:+d}h). Adjust over 2-3 days. Set phone alarms.'
                else:
                    note = f'Large shift ({diff:+d}h). Consult your doctor about adjustment strategy.'

                adjusted.append({
                    'medication_name': r.medication_name,
                    'dosage': r.dosage,
                    'original_time': r.home_time.strftime('%H:%M'),
                    'adjusted_time': adjusted_time,
                    'timezone_diff': f'{diff:+d}h',
                    'note': note,
                })

            return {'success': True, 'adjusted_medications': adjusted, 'destination_timezone': destination_timezone}
        except Exception as e:
            logger.error("Medication adjustment failed: %s", e)
            return {'success': False, 'error': str(e)}

    @staticmethod
    def get_health_insurance_info(country: str) -> Dict[str, Any]:
        """Get health insurance recommendations for a country."""
        try:
            from apps.agents.models import HealthInsuranceInfo
            info = HealthInsuranceInfo.objects.filter(country__iexact=country).first()
            if not info:
                info = HealthTravelService._generate_insurance_info(country)

            return {
                'success': True,
                'insurance': {
                    'country': info.country,
                    'risk_level': info.risk_level,
                    'recommended_coverage': info.recommended_coverage or [],
                    'avg_hospital_cost_per_day_usd': float(info.avg_hospital_cost_per_day_usd),
                    'public_healthcare_available': info.public_healthcare_available,
                    'emergency_number': info.emergency_number,
                    'vaccination_requirements': info.vaccination_requirements or [],
                    'malaria_risk': info.malaria_risk,
                    'altitude_risk': info.altitude_risk,
                    'notes': info.notes,
                    'reciprocal_agreements': info.reciprocal_agreements or [],
                },
            }
        except Exception as e:
            logger.error("Health insurance info failed: %s", e)
            return {'success': False, 'error': str(e)}

    @staticmethod
    def _generate_insurance_info(country: str):
        from apps.agents.models import HealthInsuranceInfo
        seed = int(hashlib.md5(f"insurance:{country}".encode()).hexdigest()[:8], 16)
        rng = random.Random(seed)

        high_cost_countries = ['united states', 'switzerland', 'japan', 'australia', 'canada', 'singapore']
        tropical_countries = ['thailand', 'india', 'brazil', 'indonesia', 'vietnam', 'kenya', 'nigeria', 'tanzania']
        altitude_countries = ['peru', 'bolivia', 'nepal', 'tibet', 'colombia', 'ecuador', 'ethiopia']

        country_lower = country.lower()
        is_high_cost = any(c in country_lower for c in high_cost_countries)
        is_tropical = any(c in country_lower for c in tropical_countries)
        is_altitude = any(c in country_lower for c in altitude_countries)

        if is_high_cost:
            risk_level = 'moderate'
            avg_cost = rng.randint(800, 3000)
        elif is_tropical:
            risk_level = 'high'
            avg_cost = rng.randint(100, 500)
        else:
            risk_level = 'low'
            avg_cost = rng.randint(200, 800)

        coverage = ['emergency_evacuation', 'hospitalization', 'outpatient_care']
        if is_tropical:
            coverage.extend(['tropical_disease', 'repatriation'])
        if is_high_cost:
            coverage.extend(['dental_emergency', 'specialist_consultation'])

        vaccinations = ['COVID-19 (recommended)', 'Routine vaccinations up to date']
        if is_tropical:
            vaccinations.extend(['Hepatitis A', 'Typhoid', 'Yellow Fever (check requirements)'])

        info = HealthInsuranceInfo.objects.create(
            country=country,
            risk_level=risk_level,
            recommended_coverage=coverage,
            avg_hospital_cost_per_day_usd=avg_cost,
            public_healthcare_available=not is_high_cost,
            emergency_number='112' if not any(c in country_lower for c in ['united states', 'canada']) else '911',
            vaccination_requirements=vaccinations,
            malaria_risk=is_tropical and rng.random() > 0.3,
            altitude_risk=is_altitude,
            notes=f'Consult a travel clinic 4-6 weeks before visiting {country}. Carry copies of prescriptions.',
        )
        return info

    @staticmethod
    def get_fatigue_aware_itinerary(destination: str, user_conditions: Optional[List[str]] = None,
                                     max_walking_km: float = 10, pace: str = 'moderate',
                                     trip_days: int = 3) -> Dict[str, Any]:
        """Generate a fatigue-aware itinerary plan."""
        try:
            result = HealthTravelService._fatigue_ai(destination, user_conditions, max_walking_km, pace, trip_days)
            if result:
                return {'success': True, 'plan': result}
            return {'success': True, 'plan': HealthTravelService._fatigue_fallback(destination, max_walking_km, pace, trip_days)}
        except Exception as e:
            logger.error("Fatigue itinerary failed: %s", e)
            return {'success': False, 'error': str(e)}

    @staticmethod
    def _fatigue_ai(destination, conditions, max_km, pace, days) -> Optional[List[Dict]]:
        api_key = getattr(settings, 'OPENAI_API_KEY', os.getenv('OPENAI_API_KEY', ''))
        if not api_key or api_key in ('your_openai_api_key_here', ''):
            return None
        try:
            from langchain_openai import ChatOpenAI
            conds = ', '.join(conditions) if conditions else 'None'
            llm = ChatOpenAI(model='gpt-4o-mini', temperature=0.3, api_key=api_key, request_timeout=30)
            response = llm.invoke(
                f"Create a {days}-day fatigue-aware itinerary for {destination}. "
                f"Max walking: {max_km} km/day, pace: {pace}, conditions: {conds}. "
                f"Return JSON array only (no markdown): "
                f'[{{"day":1,"morning":"...","midday_rest":"...","afternoon":"...",'
                f'"evening":"...","total_walking_km":5.0,"rest_periods":3,"hydration_reminder":"..."}}]'
            )
            content = response.content.strip()
            if content.startswith('```'):
                content = content.split('\n', 1)[1].rsplit('```', 1)[0]
            data = json.loads(content)
            if isinstance(data, list):
                return data
            return None
        except Exception as e:
            logger.warning("AI fatigue itinerary failed: %s", e)
            return None

    @staticmethod
    def _fatigue_fallback(destination: str, max_km: float, pace: str, days: int) -> List[Dict]:
        seed = int(hashlib.md5(f"fatigue:{destination}:{pace}:{days}".encode()).hexdigest()[:8], 16)
        rng = random.Random(seed)

        pace_config = {
            'slow': {'walk_factor': 0.6, 'rest': 4, 'acts': 2},
            'moderate': {'walk_factor': 0.8, 'rest': 3, 'acts': 3},
            'packed': {'walk_factor': 1.0, 'rest': 2, 'acts': 4},
        }
        cfg = pace_config.get(pace, pace_config['moderate'])

        morning_activities = [
            f"Visit a local landmark in {destination}", "Morning walking tour of the old town",
            "Explore a museum or gallery", "Walk through the central park",
            "Visit a historic market", "Guided cultural tour",
        ]
        afternoon_activities = [
            "Leisurely cafe visit", "Light shopping in local boutiques",
            "Visit a viewpoint or garden", "Explore a neighborhood on foot",
            "Art gallery or exhibit", "Local food tasting tour",
        ]
        evening_activities = [
            "Dinner at a local restaurant", "Sunset walk along the waterfront",
            "Evening cultural performance", "Relaxing at the hotel spa",
            "Night market exploration", "Light stroll and dessert",
        ]

        plan = []
        for d in range(1, days + 1):
            daily_km = round(max_km * cfg['walk_factor'] * rng.uniform(0.8, 1.0), 1)
            energy_note = "Start slower" if d == 1 else ("Peak energy day" if d == 2 else "Conserve energy for travel")

            plan.append({
                'day': d,
                'morning': f"8:00-12:00: {rng.choice(morning_activities)}. Walk ~{round(daily_km * 0.4, 1)} km. {energy_note}.",
                'midday_rest': f"12:00-{'1' if pace == 'packed' else '2'}:00 PM: Lunch and rest ({60 if pace == 'packed' else 90} min). Rehydrate.",
                'afternoon': f"{'1' if pace == 'packed' else '2'}:00-5:00 PM: {rng.choice(afternoon_activities)}. Walk ~{round(daily_km * 0.35, 1)} km.",
                'evening': f"6:00-9:00 PM: {rng.choice(evening_activities)}. Walk ~{round(daily_km * 0.25, 1)} km.",
                'total_walking_km': daily_km,
                'rest_periods': cfg['rest'],
                'hydration_reminder': f"Drink at least {round(2.0 + daily_km * 0.1, 1)}L of water today.",
            })
        return plan

    @staticmethod
    def get_health_travel_summary(user, destination: str, country: str) -> Dict[str, Any]:
        """Comprehensive health travel summary."""
        try:
            facilities = HealthTravelService.find_medical_facilities(destination, limit=5)
            accessibility = HealthTravelService.get_accessibility_info(destination)
            meds = HealthTravelService.adjust_medications_for_trip(user, 'Europe/London')
            insurance = HealthTravelService.get_health_insurance_info(country)
            fatigue = HealthTravelService.get_fatigue_aware_itinerary(destination, trip_days=3)

            return {
                'success': True,
                'destination': destination,
                'country': country,
                'medical_facilities': facilities.get('facilities', [])[:3],
                'accessibility': {
                    'average_rating': accessibility.get('average_mobility_rating', 0),
                    'total_ratings': accessibility.get('total_ratings', 0),
                },
                'medication_adjustments': meds.get('adjusted_medications', []),
                'insurance': insurance.get('insurance'),
                'fatigue_plan_preview': fatigue.get('plan', [])[:1],
            }
        except Exception as e:
            logger.error("Health travel summary failed: %s", e)
            return {'success': False, 'error': str(e)}

    @staticmethod
    def _facility_to_dict(facility) -> Dict[str, Any]:
        return {
            'id': facility.id,
            'name': facility.name,
            'facility_type': facility.facility_type,
            'address': facility.address,
            'phone': facility.phone,
            'distance_km': float(facility.distance_km) if facility.distance_km else None,
            'emergency_24h': facility.emergency_24h,
            'english_speaking': facility.english_speaking,
            'accepts_travel_insurance': facility.accepts_travel_insurance,
            'wheelchair_accessible': facility.wheelchair_accessible,
            'specialties': facility.specialties or [],
            'rating': float(facility.rating),
        }

    @staticmethod
    def _rating_to_dict(rating) -> Dict[str, Any]:
        return {
            'id': rating.id,
            'venue_name': rating.venue_name,
            'venue_type': rating.venue_type,
            'destination': rating.destination,
            'mobility_rating': rating.mobility_rating,
            'wheelchair_accessible': rating.wheelchair_accessible,
            'elevator_available': rating.elevator_available,
            'accessible_restroom': rating.accessible_restroom,
            'braille_signage': rating.braille_signage,
            'hearing_loop': rating.hearing_loop,
            'notes': rating.notes,
            'created_at': rating.created_at.isoformat() if rating.created_at else None,
        }

    @staticmethod
    def _reminder_to_dict(reminder) -> Dict[str, Any]:
        return {
            'id': reminder.id,
            'medication_name': reminder.medication_name,
            'dosage': reminder.dosage,
            'home_time': reminder.home_time.strftime('%H:%M') if reminder.home_time else '',
            'home_timezone': reminder.home_timezone,
            'frequency': reminder.frequency,
            'notes': reminder.notes,
            'is_active': reminder.is_active,
        }
