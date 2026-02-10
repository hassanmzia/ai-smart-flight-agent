"""
AI Agent Tools for Travel Planning
Includes all tools from the notebook: flight search, hotel search, goal checker, utility checkers
"""
from typing import Dict, Any, List, Optional
import requests
from datetime import datetime
from django.conf import settings
from serpapi import GoogleSearch
import logging

logger = logging.getLogger(__name__)


class FlightSearchTool:
    """
    Tool for searching flights using SerpAPI Google Flights
    Based on the notebook implementation
    """

    @staticmethod
    def search_flights(
        origin: str,
        destination: str,
        date: str,
        trip_type: int = 2,
        return_date: Optional[str] = None,
        passengers: int = 1,
        travel_class: int = 1
    ) -> Dict[str, Any]:
        """
        Search for flights between origin and destination

        Args:
            origin: Airport code (e.g., 'CDG')
            destination: Airport code (e.g., 'BER')
            date: Departure date (YYYY-MM-DD)
            trip_type: 1=Round trip, 2=One way, 3=Multi-city
            return_date: Return date for round trips
            passengers: Number of passengers
            travel_class: 1=Economy (default), 2=Premium economy, 3=Business, 4=First

        Returns:
            Dict containing flight results
        """
        try:
            # Validate and normalize travel_class (SerpAPI expects integer 1-4)
            # Map string inputs to integers if needed
            if isinstance(travel_class, str):
                class_map = {
                    'economy': 1,
                    'premium_economy': 2,
                    'premium economy': 2,
                    'business': 3,
                    'first': 4
                }
                travel_class = class_map.get(travel_class.lower().strip(), 1)

            # Ensure it's a valid integer between 1-4
            if not isinstance(travel_class, int) or travel_class not in [1, 2, 3, 4]:
                logger.warning(f"Invalid travel_class '{travel_class}', defaulting to 1 (Economy)")
                travel_class = 1

            params = {
                "api_key": settings.SERP_API_KEY,
                "engine": "google_flights",
                "hl": "en",
                "gl": "us",
                "departure_id": origin,
                "arrival_id": destination,
                "outbound_date": date,
                "type": trip_type,
                "currency": "USD",
                "adults": passengers,
                "travel_class": travel_class  # Now correctly using integer 1-4
            }

            if trip_type == 1 and return_date:
                params["return_date"] = return_date

            logger.info(f"Flight search params: {params}")
            results = GoogleSearch(params).get_dict()

            # Log raw response for debugging
            logger.info(f"SerpAPI raw response keys: {results.keys()}")
            if 'error' in results:
                logger.error(f"SerpAPI returned error: {results.get('error')}")
                return {
                    "success": False,
                    "error": results.get('error'),
                    "message": "SerpAPI error",
                    "flights": []
                }

            # Log what we got
            best_count = len(results.get('best_flights', []))
            other_count = len(results.get('other_flights', []))
            logger.info(f"Found {best_count} best flights, {other_count} other flights")

            # Parse and format results
            formatted_results = FlightSearchTool._format_flight_results(results)

            logger.info(f"Flight search completed: {origin} -> {destination} on {date}")
            return formatted_results

        except Exception as e:
            logger.error(f"Flight search exception: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to search flights",
                "flights": []
            }

    @staticmethod
    def _format_flight_results(raw_results: Dict) -> Dict[str, Any]:
        """Format raw SerpAPI results into structured flight data"""
        try:
            flights = []

            # Extract best flights
            if 'best_flights' in raw_results:
                for flight_data in raw_results.get('best_flights', []):
                    parsed = FlightSearchTool._parse_flight(flight_data)
                    if parsed:  # Only add if parse was successful
                        flights.append(parsed)

            # Extract other flights
            if 'other_flights' in raw_results:
                for flight_data in raw_results.get('other_flights', [])[:10]:  # Limit to 10
                    parsed = FlightSearchTool._parse_flight(flight_data)
                    if parsed:  # Only add if parse was successful
                        flights.append(parsed)

            # Check if no flights were found
            if not flights:
                logger.warning(f"No flights found in SerpAPI response. Available keys: {list(raw_results.keys())}")

            return {
                "success": True,
                "flights": flights,
                "total_found": len(flights),
                "search_metadata": raw_results.get('search_metadata', {}),
                "search_parameters": raw_results.get('search_parameters', {}),
                "raw_keys": list(raw_results.keys())  # For debugging
            }
        except Exception as e:
            logger.error(f"Error formatting flight results: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e), "flights": []}

    @staticmethod
    def _parse_flight(flight_data: Dict) -> Optional[Dict[str, Any]]:
        """Parse individual flight data"""
        try:
            if not flight_data:
                return None

            flights = flight_data.get('flights', [{}])
            if not flights:
                return None

            flight = flights[0]

            # Extract price - this is critical
            price = flight_data.get('price', 0)
            if not price:
                logger.warning(f"Flight missing price: {flight_data.get('airline', 'Unknown')}")
                return None

            return {
                "airline": flight.get('airline', 'Unknown'),
                "flight_number": flight.get('flight_number', ''),
                "departure_airport": flight.get('departure_airport', {}).get('name', ''),
                "departure_airport_code": flight.get('departure_airport', {}).get('id', ''),
                "departure_time": flight.get('departure_airport', {}).get('time', ''),
                "arrival_airport": flight.get('arrival_airport', {}).get('name', ''),
                "arrival_airport_code": flight.get('arrival_airport', {}).get('id', ''),
                "arrival_time": flight.get('arrival_airport', {}).get('time', ''),
                "duration": flight_data.get('total_duration', 0),
                "stops": len(flights) - 1,
                "aircraft": flight.get('airplane', 'Unknown'),
                "travel_class": flight.get('travel_class', 'Economy'),
                "legroom": flight.get('legroom', 'Standard'),
                "price": price,
                "currency": "USD",
                "carbon_emissions": flight_data.get('carbon_emissions', {}),
                "booking_token": flight_data.get('booking_token', ''),
            }
        except Exception as e:
            logger.error(f"Error parsing flight: {str(e)}", exc_info=True)
            return None


class HotelSearchTool:
    """
    Tool for searching hotels using SerpAPI Google Hotels
    Based on the notebook implementation
    """

    @staticmethod
    def search_hotels(
        location: str,
        check_in_date: str,
        check_out_date: str,
        adults: int = 2,
        children: int = 0,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        star_rating: Optional[int] = None,
        sort_by: str = "13"  # 13 = highest rated
    ) -> Dict[str, Any]:
        """
        Search for hotels in a location

        Args:
            location: City or location name
            check_in_date: Check-in date (YYYY-MM-DD)
            check_out_date: Check-out date (YYYY-MM-DD)
            adults: Number of adults
            children: Number of children
            min_price: Minimum price filter
            max_price: Maximum price filter
            star_rating: Filter by star rating (1-5)
            sort_by: Sort option (13=highest rated, 3=price low to high)

        Returns:
            Dict containing hotel results
        """
        try:
            params = {
                "api_key": settings.SERP_API_KEY,
                "engine": "google_hotels",
                "q": location,
                "check_in_date": check_in_date,
                "check_out_date": check_out_date,
                "adults": adults,
                "children": children,
                "currency": "USD",
                "gl": "us",
                "hl": "en",
                "sort_by": sort_by
            }

            if min_price:
                params["min_price"] = min_price
            if max_price:
                params["max_price"] = max_price

            hotel_results = GoogleSearch(params).get_dict()

            # Format results
            formatted_results = HotelSearchTool._format_hotel_results(hotel_results, star_rating)

            logger.info(f"Hotel search completed: {location} ({check_in_date} - {check_out_date})")
            return formatted_results

        except Exception as e:
            logger.error(f"Hotel search error: {str(e)}")
            return {
                "error": str(e),
                "message": "Failed to search hotels"
            }

    @staticmethod
    def _format_hotel_results(raw_results: Dict, star_filter: Optional[int] = None) -> Dict[str, Any]:
        """Format raw SerpAPI hotel results"""
        try:
            hotels = []

            for hotel_data in raw_results.get('properties', []):
                parsed_hotel = HotelSearchTool._parse_hotel(hotel_data)

                # Apply star rating filter
                if star_filter and parsed_hotel.get('star_rating', 0) != star_filter:
                    continue

                hotels.append(parsed_hotel)

            return {
                "success": True,
                "hotels": hotels[:20],  # Limit to 20 results
                "search_metadata": raw_results.get('search_metadata', {}),
                "search_parameters": raw_results.get('search_parameters', {})
            }
        except Exception as e:
            logger.error(f"Error formatting hotel results: {str(e)}")
            return {"success": False, "error": str(e), "hotels": []}

    @staticmethod
    def _parse_hotel(hotel_data: Dict) -> Dict[str, Any]:
        """Parse individual hotel data"""
        try:
            # Extract price - SerpAPI provides clean integers in 'extracted_lowest'
            price_per_night = 0
            total_rate = 0

            # Get rate_per_night - prefer extracted_lowest (clean integer)
            if 'rate_per_night' in hotel_data and hotel_data['rate_per_night']:
                if isinstance(hotel_data['rate_per_night'], dict):
                    # Use extracted_lowest (integer) first, fallback to lowest (string with $)
                    price_per_night = hotel_data['rate_per_night'].get('extracted_lowest',
                                      hotel_data['rate_per_night'].get('extracted_before_taxes_fees', 0))
                else:
                    price_per_night = hotel_data['rate_per_night']

            # Get total_rate - prefer extracted_lowest (clean integer)
            if 'total_rate' in hotel_data and hotel_data['total_rate']:
                if isinstance(hotel_data['total_rate'], dict):
                    total_rate = hotel_data['total_rate'].get('extracted_lowest',
                                 hotel_data['total_rate'].get('extracted_before_taxes_fees', 0))
                else:
                    total_rate = hotel_data['total_rate']

            return {
                "hotel_name": hotel_data.get('name', 'Unknown'),
                "star_rating": hotel_data.get('overall_rating', 0),
                "guest_rating": hotel_data.get('reviews', 0),
                "price_per_night": price_per_night,  # Now a clean integer
                "total_rate": total_rate,  # Now a clean integer
                "currency": "USD",
                "address": hotel_data.get('description', ''),
                "distance_from_center": hotel_data.get('nearby_places', [{}])[0].get('distance', '') if hotel_data.get('nearby_places') else '',
                "amenities": hotel_data.get('amenities', []),
                "images": hotel_data.get('images', []),
                "link": hotel_data.get('link', ''),
                "hotel_id": hotel_data.get('property_token', ''),
                "check_in_time": hotel_data.get('check_in_time', ''),
                "check_out_time": hotel_data.get('check_out_time', ''),
            }
        except Exception as e:
            logger.error(f"Error parsing hotel: {str(e)}", exc_info=True)
            return {}


class GoalBasedEvaluator:
    """
    Goal-based agent for evaluating flights based on budget goals
    Implements penalty/reward scoring from the notebook
    """

    @staticmethod
    def evaluate_flight(
        flight: Dict[str, Any],
        budget_goal: float,
        penalty_factor: float = 0.1
    ) -> Dict[str, Any]:
        """
        Evaluate flight against budget goal with penalty scoring

        Args:
            flight: Flight data dict with 'price' field
            budget_goal: Target budget in USD
            penalty_factor: Penalty multiplier for over-budget (default 0.1)

        Returns:
            Dict with price, score, and status
        """
        try:
            # Extract price
            if isinstance(flight.get('price'), str):
                price = float(flight['price'].replace('$', '').replace(',', '').strip())
            else:
                price = float(flight.get('price', 0))

            # Calculate score
            if price <= budget_goal:
                # Within budget - positive score based on savings
                savings = budget_goal - price
                score = round(savings * (1.0 - penalty_factor), 2)
                status = "within budget"
                return {
                    "price": price,
                    "score": score,
                    "savings": round(savings, 2),
                    "status": status
                }
            else:
                # Over budget - negative penalty score
                excess = price - budget_goal
                score = round(-excess * penalty_factor, 2)
                status = "over budget"
                return {
                    "price": price,
                    "score": score,
                    "difference": round(excess, 2),
                    "status": status
                }

        except Exception as e:
            logger.error(f"Error evaluating flight goal: {str(e)}")
            return {
                "error": str(e),
                "price": 0,
                "score": 0,
                "status": "error"
            }

    @staticmethod
    def find_best_and_worst(
        flights: List[Dict[str, Any]],
        budget_goal: float,
        penalty_factor: float = 0.1
    ) -> Dict[str, Any]:
        """
        Find cheapest and most expensive flights and evaluate them

        Returns:
            Dict with 'cheapest flight' and 'most expensive flight' evaluations
        """
        if not flights:
            return {
                "error": "No flights provided",
                "cheapest flight": None,
                "most expensive flight": None
            }

        # Sort by price
        sorted_flights = sorted(flights, key=lambda x: float(str(x.get('price', 0)).replace('$', '').replace(',', '')))

        cheapest = sorted_flights[0]
        most_expensive = sorted_flights[-1]

        return {
            "cheapest flight": {
                "flight": cheapest,
                **GoalBasedEvaluator.evaluate_flight(cheapest, budget_goal, penalty_factor)
            },
            "most expensive flight": {
                "flight": most_expensive,
                **GoalBasedEvaluator.evaluate_flight(most_expensive, budget_goal, penalty_factor)
            }
        }


class UtilityBasedEvaluator:
    """
    Utility-based agent for evaluating hotels based on price and star rating
    Implements utility scoring system from the notebook
    """

    @staticmethod
    def evaluate_price_utility(price_raw: Any) -> Dict[str, Any]:
        """
        Evaluate hotel price utility with scoring ranges

        Score ranges:
        - >= $250: -40 (very expensive)
        - $180-249: -20 (expensive)
        - $150-179: 0 (moderate)
        - $120-149: +20 (good value)
        - < $120: +40 (excellent value)
        """
        try:
            if isinstance(price_raw, str):
                price = float(price_raw.replace('$', '').replace(',', '').strip())
            else:
                price = float(price_raw)
        except:
            price = 9999  # Fail-safe large price

        if price >= 250:
            price_score = -40
        elif price >= 180:
            price_score = -20
        elif price >= 150:
            price_score = 0
        elif price >= 120:
            price_score = 20
        else:  # price < 120
            price_score = 40

        return {
            "price": price,
            "price_utility_score": price_score
        }

    @staticmethod
    def evaluate_rating_utility(hotel: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate hotel star rating utility

        Score ranges:
        - 5 stars: +40 (luxury)
        - 4 stars: +20 (upscale)
        - 3 stars: 0 (standard)
        - 2 stars: -20 (budget)
        - 1 star or less: -40 (very basic)
        """
        stars_raw = hotel.get('rating', 0) or hotel.get('star rating', 0) or hotel.get('star_rating', 0)

        try:
            # Extract first digit in case it's like "5 stars"
            stars = float(str(stars_raw).strip()[0])
        except:
            stars = 0

        if stars == 5:
            star_score = 40
        elif stars == 4:
            star_score = 20
        elif stars == 3:
            star_score = 0
        elif stars == 2:
            star_score = -20
        else:
            star_score = -40

        return {
            "star_rating": stars,
            "rating_utility_score": star_score
        }

    @staticmethod
    def evaluate_hotel_comprehensive(hotel: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive hotel evaluation combining price and rating utilities

        Returns:
            Dict with individual scores and combined utility score
        """
        price_eval = UtilityBasedEvaluator.evaluate_price_utility(
            hotel.get('price_per_night', hotel.get('price', 0))
        )
        rating_eval = UtilityBasedEvaluator.evaluate_rating_utility(hotel)

        combined_score = price_eval['price_utility_score'] + rating_eval['rating_utility_score']

        return {
            # Use field names that match frontend expectations
            "name": hotel.get('hotel_name', hotel.get('name', 'Unknown')),
            "hotel_name": hotel.get('hotel_name', hotel.get('name', 'Unknown')),  # Keep for backward compatibility
            "price": price_eval['price'],
            "price_utility_score": price_eval['price_utility_score'],
            "stars": rating_eval['star_rating'],
            "star_rating": rating_eval['star_rating'],  # Keep for backward compatibility
            "rating_utility_score": rating_eval['rating_utility_score'],
            "utility_score": combined_score,  # Frontend expects this name
            "combined_utility_score": combined_score,  # Keep for backward compatibility
            "recommendation": UtilityBasedEvaluator._get_recommendation(combined_score)
        }

    @staticmethod
    def _get_recommendation(score: int) -> str:
        """Get recommendation based on utility score"""
        if score >= 60:
            return "Excellent choice - great value and quality"
        elif score >= 20:
            return "Good option - reasonable value"
        elif score >= -20:
            return "Fair option - acceptable"
        else:
            return "Consider other options - poor value or quality"

    @staticmethod
    def rank_hotels(hotels: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Rank hotels by combined utility score

        Returns:
            List of hotels sorted by utility score (highest first)
        """
        evaluated_hotels = [
            UtilityBasedEvaluator.evaluate_hotel_comprehensive(hotel)
            for hotel in hotels
        ]

        return sorted(
            evaluated_hotels,
            key=lambda x: x['combined_utility_score'],
            reverse=True
        )


class WeatherTool:
    """Tool for fetching weather information"""

    @staticmethod
    def get_weather(location: str, date: Optional[str] = None) -> Dict[str, Any]:
        """
        Get weather information for a location
        Uses OpenWeatherMap API or similar
        """
        # TODO: Implement weather API integration
        return {
            "location": location,
            "temperature": "22°C",
            "condition": "Partly Cloudy",
            "humidity": "65%",
            "wind_speed": "15 km/h"
        }
