"""
Enhanced Travel Agents with specialized integrations
- HealthSafetyAgent: WHO/CDC health alerts and safety info
- VisaRequirementsAgent: Visa and documentation requirements
- PackingListAgent: Weather-based packing recommendations
- EnhancedLocalExpertAgent: Restaurant and cuisine recommendations
"""

import os
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_openai import ChatOpenAI
from langchain.tools import Tool
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)


class HealthSafetyDataProvider:
    """Data provider for health and safety information"""

    @staticmethod
    def get_cdc_travel_health_notices(country: str) -> Dict[str, Any]:
        """
        Get CDC Travel Health Notices for a country.
        Note: This is a simplified implementation. Real CDC API requires proper authentication.
        """
        try:
            # CDC doesn't have a public API, so we'll simulate the structure
            # In production, you'd scrape their website or use a third-party service

            # For now, return structured placeholder data
            return {
                'country': country,
                'alert_level': 'Level 1',  # Level 1 (Low), Level 2 (Moderate), Level 3 (High)
                'notices': [
                    {
                        'title': 'Routine Vaccinations',
                        'description': 'Make sure you are up to date on routine vaccines before every trip.',
                        'severity': 'info'
                    }
                ],
                'vaccinations_required': ['Routine vaccines'],
                'vaccinations_recommended': [],
                'health_risks': [],
                'last_updated': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error fetching CDC data: {str(e)}")
            return {'error': str(e)}

    @staticmethod
    def get_who_disease_outbreaks(country: str) -> Dict[str, Any]:
        """
        Get WHO disease outbreak information.
        WHO provides some public APIs for disease outbreak news.
        """
        try:
            # WHO Disease Outbreak News
            # This is a simplified version - actual implementation would use WHO's API
            url = "https://www.who.int/api/outbreaks"  # Placeholder URL

            # Return structured data
            return {
                'country': country,
                'outbreaks': [],
                'alerts': [],
                'recommendations': [
                    'Practice good hygiene',
                    'Drink bottled water',
                    'Avoid street food if immunocompromised'
                ],
                'last_updated': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error fetching WHO data: {str(e)}")
            return {'error': str(e)}

    @staticmethod
    def get_travel_safety_score(country: str) -> Dict[str, Any]:
        """
        Get travel safety score from various sources.
        Could integrate with Travel State Gov, UK FCO, etc.
        """
        try:
            # Simulated safety score
            # In production, integrate with:
            # - travel.state.gov API (US State Department)
            # - UK Foreign Office travel advice
            # - Travel Risk Map

            return {
                'country': country,
                'overall_safety_score': 7.5,  # 0-10 scale
                'crime_level': 'moderate',
                'terrorism_threat': 'low',
                'political_stability': 'stable',
                'natural_disaster_risk': 'low',
                'health_infrastructure': 'good',
                'emergency_numbers': {
                    'police': '911 or local equivalent',
                    'ambulance': '911 or local equivalent',
                    'fire': '911 or local equivalent'
                },
                'embassy_contacts': [],
                'travel_advisories': [],
                'last_updated': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error fetching safety data: {str(e)}")
            return {'error': str(e)}

    @staticmethod
    def get_health_facilities(city: str, country: str) -> List[Dict[str, Any]]:
        """Get information about hospitals and medical facilities"""
        try:
            # In production, use Google Places API or similar
            return [
                {
                    'name': f'{city} General Hospital',
                    'type': 'hospital',
                    'address': f'{city}, {country}',
                    'phone': '+1-XXX-XXX-XXXX',
                    'accepts_international_insurance': True,
                    'english_speaking_staff': True
                }
            ]
        except Exception as e:
            logger.error(f"Error fetching health facilities: {str(e)}")
            return []


class VisaDataProvider:
    """Data provider for visa and documentation requirements"""

    @staticmethod
    def get_visa_requirements(
        origin_country: str,
        destination_country: str,
        citizenship: str = None
    ) -> Dict[str, Any]:
        """
        Get visa requirements using Sherpa API or similar.
        Note: Sherpa API requires paid subscription.
        """
        try:
            # Sherpa API endpoint (requires API key)
            # https://developers.sherpadoc.com/

            api_key = os.getenv('SHERPA_API_KEY')

            if not api_key:
                # Return generic information
                return {
                    'visa_required': 'Please check with embassy',
                    'visa_type': 'Tourist',
                    'max_stay_days': 90,
                    'processing_time_days': 14,
                    'cost_usd': 160,
                    'application_process': [
                        'Complete online application',
                        'Submit required documents',
                        'Attend interview if required',
                        'Wait for processing'
                    ],
                    'required_documents': [
                        'Valid passport (6+ months validity)',
                        'Completed visa application form',
                        'Recent passport photos',
                        'Proof of accommodation',
                        'Proof of funds',
                        'Return flight ticket'
                    ],
                    'vaccine_requirements': [],
                    'note': 'Verify requirements with official embassy sources'
                }

            # With API key, make real request
            # url = "https://api.joinsherpa.com/v2/travel-restrictions"
            # ... implementation with real API

            return {
                'visa_required': 'Check with embassy',
                'note': 'Use official sources for visa information'
            }

        except Exception as e:
            logger.error(f"Error fetching visa requirements: {str(e)}")
            return {'error': str(e)}


class WeatherBasedPackingHelper:
    """Generate packing lists based on weather forecast"""

    @staticmethod
    def generate_packing_list(
        destination: str,
        start_date: str,
        end_date: str,
        weather_data: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """Generate comprehensive packing list based on weather"""
        try:
            # Parse weather data
            temp_high = weather_data.get('temp_high', 75)
            temp_low = weather_data.get('temp_low', 60)
            precipitation = weather_data.get('precipitation_probability', 0)

            packing_list = {
                'clothing': [],
                'accessories': [],
                'toiletries': [],
                'electronics': [],
                'documents': [],
                'health_items': []
            }

            # Temperature-based clothing
            if temp_high > 80:
                packing_list['clothing'].extend([
                    'Light, breathable shirts',
                    'Shorts',
                    'Sundresses',
                    'Swimwear',
                    'Sun hat',
                    'Sunglasses'
                ])
            elif temp_high > 60:
                packing_list['clothing'].extend([
                    'T-shirts',
                    'Light pants/jeans',
                    'Light jacket',
                    'Comfortable walking shoes'
                ])
            else:
                packing_list['clothing'].extend([
                    'Warm jacket/coat',
                    'Sweaters',
                    'Long pants',
                    'Warm socks',
                    'Boots',
                    'Scarf and gloves'
                ])

            # Rain gear
            if precipitation > 30:
                packing_list['clothing'].extend([
                    'Rain jacket',
                    'Umbrella',
                    'Waterproof shoes'
                ])

            # Essential accessories
            packing_list['accessories'].extend([
                'Day backpack',
                'Reusable water bottle',
                'Travel pillow',
                'Eye mask',
                'Earplugs'
            ])

            # Toiletries
            packing_list['toiletries'].extend([
                'Toothbrush and toothpaste',
                'Shampoo and conditioner',
                'Body wash/soap',
                'Deodorant',
                'Sunscreen (SPF 30+)',
                'Moisturizer',
                'Hand sanitizer'
            ])

            # Electronics
            packing_list['electronics'].extend([
                'Phone charger',
                'Power bank',
                'Universal adapter',
                'Camera (optional)',
                'Headphones'
            ])

            # Important documents
            packing_list['documents'].extend([
                'Passport',
                'Travel insurance documents',
                'Flight tickets',
                'Hotel confirmations',
                'Emergency contact information',
                'Credit cards and some cash'
            ])

            # Health items
            packing_list['health_items'].extend([
                'Prescription medications',
                'Pain relievers',
                'Antihistamines',
                'Band-aids',
                'Antiseptic wipes',
                'Motion sickness medication'
            ])

            return packing_list

        except Exception as e:
            logger.error(f"Error generating packing list: {str(e)}")
            return {}


class RestaurantRecommendationProvider:
    """Provider for restaurant and dining recommendations"""

    @staticmethod
    def get_yelp_restaurants(
        city: str,
        cuisine: str = None,
        dietary: str = None,
        price_range: str = None
    ) -> List[Dict[str, Any]]:
        """
        Get restaurant recommendations from Yelp API.
        Requires YELP_API_KEY environment variable.
        """
        try:
            api_key = os.getenv('YELP_API_KEY')

            if not api_key:
                # Return placeholder data
                return [
                    {
                        'name': f'Popular Restaurant in {city}',
                        'cuisine': cuisine or 'International',
                        'rating': 4.5,
                        'price_level': '$$',
                        'address': f'{city} Downtown',
                        'phone': '+1-XXX-XXX-XXXX',
                        'popular_dishes': ['Signature dish', 'Local specialty'],
                        'dietary_options': ['Vegetarian', 'Gluten-free available']
                    }
                ]

            # Yelp Fusion API
            url = "https://api.yelp.com/v3/businesses/search"
            headers = {'Authorization': f'Bearer {api_key}'}
            params = {
                'location': city,
                'categories': 'restaurants',
                'limit': 10,
                'sort_by': 'rating'
            }

            if cuisine:
                params['categories'] = f'restaurants,{cuisine.lower()}'

            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            restaurants = []
            for business in data.get('businesses', []):
                restaurants.append({
                    'name': business.get('name'),
                    'cuisine': ', '.join([c.get('title', '') for c in business.get('categories', [])]),
                    'rating': business.get('rating'),
                    'price_level': business.get('price', '$$'),
                    'address': ', '.join(business.get('location', {}).get('display_address', [])),
                    'phone': business.get('phone'),
                    'url': business.get('url'),
                    'image_url': business.get('image_url')
                })

            return restaurants

        except Exception as e:
            logger.error(f"Error fetching Yelp data: {str(e)}")
            return []

    @staticmethod
    def get_local_cuisine_info(country: str, city: str) -> Dict[str, Any]:
        """Get information about local cuisine and food specialties"""
        try:
            # In production, this could pull from a curated database or API
            return {
                'country': country,
                'city': city,
                'signature_dishes': [
                    'Local dish 1',
                    'Local dish 2',
                    'Local dish 3'
                ],
                'food_customs': [
                    'Tipping customs',
                    'Dining etiquette',
                    'Meal times'
                ],
                'must_try_foods': [],
                'dietary_considerations': {
                    'vegetarian_friendly': True,
                    'vegan_friendly': True,
                    'halal_available': True,
                    'kosher_available': False,
                    'gluten_free_available': True
                },
                'price_expectations': {
                    'budget_meal': '$10-15',
                    'mid_range_meal': '$25-40',
                    'fine_dining': '$75+'
                }
            }
        except Exception as e:
            logger.error(f"Error fetching cuisine info: {str(e)}")
            return {}


class HealthSafetyAgent:
    """
    Agent for health, safety, and emergency information.
    Integrates with WHO, CDC, and travel advisory services.
    """

    def __init__(self, model_name: str = "gpt-4"):
        self.model = ChatOpenAI(model_name=model_name, temperature=0)
        self.data_provider = HealthSafetyDataProvider()

    def get_health_safety_report(
        self,
        destination: str,
        country: str,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """Generate comprehensive health and safety report"""
        try:
            # Gather data from multiple sources
            cdc_data = self.data_provider.get_cdc_travel_health_notices(country)
            who_data = self.data_provider.get_who_disease_outbreaks(country)
            safety_data = self.data_provider.get_travel_safety_score(country)
            health_facilities = self.data_provider.get_health_facilities(destination, country)

            # Compile report
            report = {
                'destination': destination,
                'country': country,
                'travel_dates': f'{start_date} to {end_date}',
                'health_information': {
                    'cdc_alert_level': cdc_data.get('alert_level', 'N/A'),
                    'required_vaccinations': cdc_data.get('vaccinations_required', []),
                    'recommended_vaccinations': cdc_data.get('vaccinations_recommended', []),
                    'health_risks': cdc_data.get('health_risks', []),
                    'disease_outbreaks': who_data.get('outbreaks', [])
                },
                'safety_information': {
                    'overall_safety_score': safety_data.get('overall_safety_score', 'N/A'),
                    'crime_level': safety_data.get('crime_level', 'N/A'),
                    'terrorism_threat': safety_data.get('terrorism_threat', 'N/A'),
                    'travel_advisories': safety_data.get('travel_advisories', [])
                },
                'emergency_contacts': {
                    'police': safety_data.get('emergency_numbers', {}).get('police', '911'),
                    'ambulance': safety_data.get('emergency_numbers', {}).get('ambulance', '911'),
                    'fire': safety_data.get('emergency_numbers', {}).get('fire', '911'),
                    'us_embassy': 'Contact local US Embassy'
                },
                'medical_facilities': health_facilities,
                'recommendations': who_data.get('recommendations', []),
                'last_updated': datetime.now().isoformat()
            }

            return report

        except Exception as e:
            logger.error(f"Error generating health safety report: {str(e)}")
            return {'error': str(e)}


class VisaRequirementsAgent:
    """Agent for visa and documentation requirements"""

    def __init__(self):
        self.data_provider = VisaDataProvider()

    def get_visa_requirements(
        self,
        origin_country: str,
        destination_country: str,
        citizenship: str = None,
        trip_purpose: str = "tourism"
    ) -> Dict[str, Any]:
        """Get visa requirements and documentation checklist"""
        try:
            visa_info = self.data_provider.get_visa_requirements(
                origin_country,
                destination_country,
                citizenship
            )

            return {
                'origin': origin_country,
                'destination': destination_country,
                'trip_purpose': trip_purpose,
                'visa_required': visa_info.get('visa_required', 'Unknown'),
                'visa_type': visa_info.get('visa_type', 'Tourist'),
                'max_stay': visa_info.get('max_stay_days', 'Varies'),
                'processing_time': visa_info.get('processing_time_days', 'Varies'),
                'estimated_cost': visa_info.get('cost_usd', 'Varies'),
                'application_process': visa_info.get('application_process', []),
                'required_documents': visa_info.get('required_documents', []),
                'vaccine_requirements': visa_info.get('vaccine_requirements', []),
                'important_notes': [
                    visa_info.get('note', ''),
                    'Always verify with official embassy sources',
                    'Apply well in advance of travel dates'
                ],
                'last_updated': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting visa requirements: {str(e)}")
            return {'error': str(e)}


class PackingListAgent:
    """Agent for generating weather-based packing lists"""

    def __init__(self):
        self.helper = WeatherBasedPackingHelper()

    def generate_packing_list(
        self,
        destination: str,
        start_date: str,
        end_date: str,
        weather_data: Dict[str, Any],
        trip_type: str = "leisure"
    ) -> Dict[str, Any]:
        """Generate comprehensive packing list"""
        try:
            base_list = self.helper.generate_packing_list(
                destination,
                start_date,
                end_date,
                weather_data
            )

            # Add trip-type specific items
            if trip_type == "business":
                base_list.setdefault('clothing', []).extend([
                    'Business attire',
                    'Dress shoes',
                    'Laptop bag'
                ])
                base_list.setdefault('electronics', []).append('Laptop')
            elif trip_type == "adventure":
                base_list.setdefault('clothing', []).extend([
                    'Hiking boots',
                    'Quick-dry clothing',
                    'Hat with sun protection'
                ])
                base_list.setdefault('accessories', []).extend([
                    'First aid kit',
                    'Multi-tool',
                    'Flashlight'
                ])

            return {
                'destination': destination,
                'travel_dates': f'{start_date} to {end_date}',
                'trip_type': trip_type,
                'packing_list': base_list,
                'packing_tips': [
                    'Roll clothes to save space',
                    'Pack essentials in carry-on',
                    'Leave room for souvenirs',
                    'Check airline baggage restrictions'
                ],
                'generated_at': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error generating packing list: {str(e)}")
            return {'error': str(e)}


class EnhancedLocalExpertAgent:
    """Enhanced local expert with restaurant and cuisine recommendations"""

    def __init__(self):
        self.restaurant_provider = RestaurantRecommendationProvider()

    def get_dining_recommendations(
        self,
        city: str,
        country: str,
        dietary_restrictions: List[str] = None,
        cuisine_preferences: List[str] = None,
        budget: str = "moderate"
    ) -> Dict[str, Any]:
        """Get comprehensive dining recommendations"""
        try:
            # Get local cuisine info
            cuisine_info = self.restaurant_provider.get_local_cuisine_info(country, city)

            # Get restaurant recommendations
            restaurants = []
            cuisines_to_try = cuisine_preferences or ['local', 'international']

            for cuisine in cuisines_to_try:
                restaurants.extend(
                    self.restaurant_provider.get_yelp_restaurants(
                        city=city,
                        cuisine=cuisine,
                        dietary=','.join(dietary_restrictions) if dietary_restrictions else None,
                        price_range=budget
                    )
                )

            return {
                'city': city,
                'country': country,
                'local_cuisine': cuisine_info,
                'restaurant_recommendations': restaurants[:10],  # Top 10
                'dietary_considerations': cuisine_info.get('dietary_considerations', {}),
                'food_customs': cuisine_info.get('food_customs', []),
                'must_try_dishes': cuisine_info.get('signature_dishes', []),
                'budget_guide': cuisine_info.get('price_expectations', {}),
                'tips': [
                    'Try local markets for authentic food',
                    'Ask locals for recommendations',
                    'Consider food tours for cultural immersion',
                    'Check restaurant reviews before visiting'
                ],
                'generated_at': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting dining recommendations: {str(e)}")
            return {'error': str(e)}
