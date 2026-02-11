"""
AI Agent Tools for Travel Planning
Includes all tools from the notebook: flight search, hotel search, goal checker, utility checkers
"""
from typing import Dict, Any, List, Optional
import requests
import json
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

            # Normalize airport codes to uppercase (SerpAPI requirement)
            origin = origin.upper().strip()
            destination = destination.upper().strip()

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
                "airline_logo": flight.get('airline_logo', ''),
                "flight_number": flight.get('flight_number', ''),
                "departure_airport": flight.get('departure_airport', {}).get('name', ''),
                "departure_airport_code": flight.get('departure_airport', {}).get('id', ''),
                "departure_time": flight.get('departure_airport', {}).get('time', ''),
                "arrival_airport": flight.get('arrival_airport', {}).get('name', ''),
                "arrival_airport_code": flight.get('arrival_airport', {}).get('id', ''),
                "arrival_time": flight.get('arrival_airport', {}).get('time', ''),
                "duration": flight_data.get('total_duration', 0),
                "stops": len(flights) - 1,
                "layovers": flight_data.get('layovers', []),
                "aircraft": flight.get('airplane', 'Unknown'),
                "travel_class": flight.get('travel_class', 'Economy'),
                "legroom": flight.get('legroom', 'Standard'),
                "extensions": flight.get('extensions', []),
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

            # Parse images - SerpAPI returns array of objects with 'thumbnail' and 'original_image'
            images = []
            raw_images = hotel_data.get('images', [])
            if raw_images:
                for img in raw_images:
                    try:
                        if isinstance(img, dict):
                            # Prefer original_image for better quality, fallback to thumbnail
                            image_url = img.get('original_image') or img.get('thumbnail')
                            if image_url and isinstance(image_url, str) and image_url.startswith('http'):
                                images.append(image_url)
                        elif isinstance(img, str) and img.startswith('http'):
                            # Handle case where images might already be strings
                            images.append(img)
                    except Exception as e:
                        # Skip invalid images
                        logger.warning(f"Failed to parse image: {e}")
                        continue

            # Parse link - might be a string or object
            link = hotel_data.get('link', '')
            if isinstance(link, dict):
                # If link is an object, try to extract URL from common properties
                link = link.get('url') or link.get('href') or link.get('link') or ''

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
                "images": images,  # Now properly extracted URLs
                "link": link,  # Now properly extracted string URL
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
            Dict with individual scores and combined utility score,
            preserving all original hotel data
        """
        price_eval = UtilityBasedEvaluator.evaluate_price_utility(
            hotel.get('price_per_night', hotel.get('price', 0))
        )
        rating_eval = UtilityBasedEvaluator.evaluate_rating_utility(hotel)

        combined_score = price_eval['price_utility_score'] + rating_eval['rating_utility_score']

        # Start with all original hotel data to preserve images, amenities, etc.
        evaluated_hotel = dict(hotel)

        # Add/override with evaluation fields
        evaluated_hotel.update({
            # Use field names that match frontend expectations
            "name": hotel.get('hotel_name', hotel.get('name', 'Unknown')),
            "hotel_name": hotel.get('hotel_name', hotel.get('name', 'Unknown')),  # Keep for backward compatibility
            "price": price_eval['price'],
            "price_per_night": price_eval['price'],  # Ensure this is set
            "price_utility_score": price_eval['price_utility_score'],
            "stars": rating_eval['star_rating'],
            "star_rating": rating_eval['star_rating'],  # Keep for backward compatibility
            "rating_utility_score": rating_eval['rating_utility_score'],
            "utility_score": combined_score,  # Frontend expects this name
            "combined_utility_score": combined_score,  # Keep for backward compatibility
            "recommendation": UtilityBasedEvaluator._get_recommendation(combined_score)
        })

        return evaluated_hotel

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

        Filters out hotels with $0 prices (no pricing data available from API)

        Returns:
            List of hotels sorted by utility score (highest first)
        """
        # Filter out hotels with no pricing data ($0 price)
        # SerpAPI sometimes doesn't provide pricing for certain hotels/dates
        hotels_with_prices = [
            hotel for hotel in hotels
            if hotel.get('price_per_night', 0) > 0 or hotel.get('price', 0) > 0
        ]

        # If no hotels have prices, return empty list rather than showing $0 hotels
        if not hotels_with_prices:
            print("⚠️ Warning: No hotels with pricing data available")
            return []

        evaluated_hotels = [
            UtilityBasedEvaluator.evaluate_hotel_comprehensive(hotel)
            for hotel in hotels_with_prices
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


class CarRentalSearchTool:
    """
    Tool for searching car rentals using SerpAPI Google Car Rental
    """

    name = "car_rental_search"
    description = "Search for car rentals at a specific location and dates"

    def _run(self, pickup_location: str, pickup_date: str, dropoff_date: str,
             car_type: Optional[str] = None) -> str:
        """
        Search for car rentals

        Args:
            pickup_location: City, airport code, or location
            pickup_date: Pickup date (YYYY-MM-DD)
            dropoff_date: Drop-off date (YYYY-MM-DD)
            car_type: Optional filter (economy, compact, suv, etc.)

        Returns:
            JSON string with car rental results
        """
        try:
            # Convert airport codes to city names for Google Local search
            # Use broader city names (not airport-specific) for better search results
            airport_to_city = {
                'LAX': 'Los Angeles, CA',
                'JFK': 'New York, NY',
                'LGA': 'New York, NY',
                'EWR': 'Newark, NJ',
                'ORD': 'Chicago, IL',
                'SFO': 'San Francisco, CA',
                'MIA': 'Miami, FL',
                'DFW': 'Dallas, TX',
                'SEA': 'Seattle, WA',
                'BOS': 'Boston, MA',
                'ATL': 'Atlanta, GA',
                'DEN': 'Denver, CO',
                'IAD': 'Washington, DC',
                'DCA': 'Washington, DC',
                'LAS': 'Las Vegas, NV',
                'PHX': 'Phoenix, AZ',
                'IAH': 'Houston, TX',
                'MCO': 'Orlando, FL',
                'CDG': 'Paris, France',
                'LHR': 'London, UK',
                'BER': 'Berlin, Germany',
                'FCO': 'Rome, Italy',
                'NRT': 'Tokyo, Japan',
            }

            # Convert location if it's an airport code
            search_location = airport_to_city.get(pickup_location.upper(), pickup_location)
            logger.info(f"Searching car rentals: {pickup_location} -> {search_location}, {pickup_date} to {dropoff_date}")

            # Build SerpAPI parameters
            # Use more specific search terms to get better results
            search_query = f"car rental companies {search_location}"
            params = {
                "engine": "google_local",
                "q": search_query,
                "location": search_location,
                "api_key": settings.SERP_API_KEY
            }

            logger.info(f"Car rental search query: {search_query}")

            # Make API request
            response = requests.get("https://serpapi.com/search", params=params, timeout=30)
            raw_results = response.json()

            logger.info(f"Car rental API response keys: {raw_results.keys()}")

            # Check for errors in API response
            if 'error' in raw_results:
                logger.error(f"SERP API error for car rentals: {raw_results.get('error')}")
                return json.dumps({"success": False, "error": raw_results.get('error'), "cars": []})

            # Log if local_results is missing or empty
            local_results = raw_results.get('local_results', [])
            if not local_results:
                logger.warning(f"No local_results in car rental response. Keys: {raw_results.keys()}")
                logger.warning(f"Search parameters: q={search_query}, location={search_location}")

            # Format results (will return empty cars array if no results)
            formatted_results = self._format_car_rental_results(
                raw_results, pickup_date, dropoff_date, car_type
            )

            logger.info(f"Formatted {len(formatted_results.get('cars', []))} car rental options")
            return json.dumps(formatted_results)

        except Exception as e:
            logger.error(f"Error searching car rentals: {str(e)}", exc_info=True)
            return json.dumps({"success": False, "error": str(e), "cars": []})

    @staticmethod
    def _format_car_rental_results(raw_results: Dict, pickup_date: str,
                                   dropoff_date: str, car_type: Optional[str] = None) -> Dict[str, Any]:
        """Format car rental search results"""
        try:
            cars = []
            local_results = raw_results.get('local_results', [])

            for result in local_results[:15]:  # Limit to 15 results
                # Parse car rental data
                parsed_car = CarRentalSearchTool._parse_car_rental(result, pickup_date, dropoff_date)

                # Apply car type filter if specified
                if car_type and parsed_car.get('car_type', '').lower() != car_type.lower():
                    continue

                cars.append(parsed_car)

            return {
                "success": True,
                "cars": cars,
                "search_parameters": {
                    "pickup_location": raw_results.get('search_parameters', {}).get('q', ''),
                    "pickup_date": pickup_date,
                    "dropoff_date": dropoff_date
                }
            }
        except Exception as e:
            logger.error(f"Error formatting car rental results: {str(e)}")
            return {"success": False, "error": str(e), "cars": []}

    @staticmethod
    def _parse_car_rental(car_data: Dict, pickup_date: str, dropoff_date: str) -> Dict[str, Any]:
        """Parse individual car rental data"""
        try:
            # Calculate rental days
            from datetime import datetime
            pickup = datetime.strptime(pickup_date, '%Y-%m-%d')
            dropoff = datetime.strptime(dropoff_date, '%Y-%m-%d')
            days = max(1, (dropoff - pickup).days)

            # Extract price (simulated for car rentals)
            price_per_day = 50  # Default price
            if 'price' in car_data:
                try:
                    price_str = car_data['price'].replace('$', '').replace(',', '')
                    price_per_day = float(price_str)
                except:
                    pass

            # Infer car type from title
            title = car_data.get('title', '').lower()
            car_type = 'economy'  # default
            if any(word in title for word in ['suv', 'jeep', 'explorer']):
                car_type = 'suv'
            elif any(word in title for word in ['luxury', 'mercedes', 'bmw', 'audi']):
                car_type = 'luxury'
            elif any(word in title for word in ['van', 'minivan']):
                car_type = 'van'
            elif any(word in title for word in ['compact', 'small']):
                car_type = 'compact'
            elif any(word in title for word in ['full', 'large']):
                car_type = 'fullsize'

            return {
                "rental_company": car_data.get('title', 'Unknown'),
                "car_type": car_type,
                "vehicle": "Standard Vehicle",  # Would come from detailed API
                "price_per_day": price_per_day,
                "total_price": price_per_day * days,
                "currency": "USD",
                "pickup_location": car_data.get('address', ''),
                "rating": car_data.get('rating', 0),
                "reviews": car_data.get('reviews', 0),
                "features": [
                    "Air Conditioning",
                    "Automatic Transmission",
                    "4 Passengers",
                    "2 Large Bags"
                ],
                "phone": car_data.get('phone', ''),
                "website": car_data.get('website', ''),
                "thumbnail": car_data.get('thumbnail', ''),
                "rental_days": days,
                "pickup_date": pickup_date,
                "dropoff_date": dropoff_date,
                "mileage": "Unlimited",
                "deposit": 200,  # Default deposit
                "insurance_available": True
            }
        except Exception as e:
            logger.error(f"Error parsing car rental: {str(e)}", exc_info=True)
            return {}

class CarRentalEvaluator:
    """
    Utility-based evaluator for car rentals
    Evaluates cars based on price, rating, and car type
    """

    @staticmethod
    def evaluate_price_utility(price: float) -> Dict[str, Any]:
        """
        Evaluate car rental price utility

        Score ranges (per day):
        - < $30: +40 (excellent value)
        - $30-49: +20 (good value)
        - $50-69: 0 (moderate)
        - $70-99: -20 (expensive)
        - >= $100: -40 (very expensive)
        """
        try:
            if isinstance(price, str):
                price = float(price.replace('$', '').replace(',', '').strip())
            else:
                price = float(price)
        except:
            price = 9999  # Fail-safe large price

        if price < 30:
            price_score = 40
        elif price < 50:
            price_score = 20
        elif price < 70:
            price_score = 0
        elif price < 100:
            price_score = -20
        else:  # price >= 100
            price_score = -40

        return {
            "price": price,
            "price_utility_score": price_score
        }

    @staticmethod
    def evaluate_car_type_utility(car_type: str) -> Dict[str, Any]:
        """
        Evaluate car type utility

        Score ranges:
        - Economy/Compact: +20 (fuel efficient, affordable)
        - Midsize: +10 (balanced)
        - SUV/Fullsize: 0 (spacious but less efficient)
        - Luxury: -10 (expensive)
        - Van: -20 (less demand)
        """
        car_type = car_type.lower() if car_type else 'economy'

        if car_type in ['economy', 'compact']:
            type_score = 20
        elif car_type in ['midsize']:
            type_score = 10
        elif car_type in ['suv', 'fullsize']:
            type_score = 0
        elif car_type in ['luxury']:
            type_score = -10
        else:  # van, convertible, etc.
            type_score = -20

        return {
            "car_type": car_type,
            "type_utility_score": type_score
        }

    @staticmethod
    def evaluate_rating_utility(rating: float, reviews: int = 0) -> Dict[str, Any]:
        """
        Evaluate car rental company rating utility

        Score ranges:
        - 4.5-5.0: +20 (excellent)
        - 4.0-4.4: +10 (good)
        - 3.5-3.9: 0 (average)
        - 3.0-3.4: -10 (below average)
        - < 3.0: -20 (poor)

        Bonus: +5 if reviews > 100 (well-established)
        """
        try:
            rating = float(rating)
        except:
            rating = 0

        if rating >= 4.5:
            rating_score = 20
        elif rating >= 4.0:
            rating_score = 10
        elif rating >= 3.5:
            rating_score = 0
        elif rating >= 3.0:
            rating_score = -10
        else:
            rating_score = -20

        # Bonus for many reviews (indicates reliability)
        if reviews > 100:
            rating_score += 5

        return {
            "rating": rating,
            "reviews": reviews,
            "rating_utility_score": rating_score
        }

    @staticmethod
    def evaluate_car_comprehensive(car: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive car rental evaluation combining price, type, and rating utilities

        Returns:
            Dict with individual scores and combined utility score,
            preserving all original car data
        """
        price_eval = CarRentalEvaluator.evaluate_price_utility(
            car.get('price_per_day', car.get('price', 0))
        )
        type_eval = CarRentalEvaluator.evaluate_car_type_utility(
            car.get('car_type', 'economy')
        )
        rating_eval = CarRentalEvaluator.evaluate_rating_utility(
            car.get('rating', 0),
            car.get('reviews', 0)
        )

        # Combined score
        combined_score = (
            price_eval['price_utility_score'] +
            type_eval['type_utility_score'] +
            rating_eval['rating_utility_score']
        )

        # Start with all original car data
        evaluated_car = dict(car)

        # Add/override with evaluation fields
        evaluated_car.update({
            "price": price_eval['price'],
            "price_per_day": price_eval['price'],
            "price_utility_score": price_eval['price_utility_score'],
            "car_type": type_eval['car_type'],
            "type_utility_score": type_eval['type_utility_score'],
            "rating": rating_eval['rating'],
            "rating_utility_score": rating_eval['rating_utility_score'],
            "utility_score": combined_score,
            "combined_utility_score": combined_score,
            "recommendation": CarRentalEvaluator._get_recommendation(combined_score)
        })

        return evaluated_car

    @staticmethod
    def _get_recommendation(score: int) -> str:
        """Get recommendation based on utility score"""
        if score >= 40:
            return "Excellent choice - great value and quality"
        elif score >= 15:
            return "Good option - reasonable value"
        elif score >= -15:
            return "Fair option - acceptable"
        else:
            return "Consider other options - poor value or quality"

    @staticmethod
    def rank_cars(cars: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Rank car rentals by combined utility score

        Filters out cars with $0 prices (no pricing data available)

        Returns:
            List of cars sorted by utility score (highest first)
        """
        # Filter out cars with no pricing data
        cars_with_prices = [
            car for car in cars
            if car.get('price_per_day', 0) > 0 or car.get('price', 0) > 0
        ]

        if not cars_with_prices:
            print("⚠️ Warning: No car rentals with pricing data available")
            return []

        evaluated_cars = [
            CarRentalEvaluator.evaluate_car_comprehensive(car)
            for car in cars_with_prices
        ]

        return sorted(
            evaluated_cars,
            key=lambda x: x['combined_utility_score'],
            reverse=True
        )


class RestaurantSearchTool:
    """
    Tool for searching restaurants using SerpAPI Google Local
    """

    name = "restaurant_search"
    description = "Search for restaurants at a specific location"

    def _run(self, city: str, cuisine: Optional[str] = None) -> str:
        """
        Search for restaurants

        Args:
            city: City or location to search
            cuisine: Optional cuisine type filter

        Returns:
            JSON string with restaurant results
        """
        try:
            logger.info(f"Searching restaurants: {city}, cuisine: {cuisine or 'any'}")

            # Convert airport codes to city names
            airport_to_city = {
                'LAX': 'Los Angeles, CA',
                'JFK': 'New York, NY',
                'LGA': 'New York, NY',
                'EWR': 'Newark, NJ',
                'ORD': 'Chicago, IL',
                'SFO': 'San Francisco, CA',
                'MIA': 'Miami, FL',
                'DFW': 'Dallas, TX',
                'SEA': 'Seattle, WA',
                'BOS': 'Boston, MA',
                'ATL': 'Atlanta, GA',
                'DEN': 'Denver, CO',
                'IAD': 'Washington, DC',
                'DCA': 'Washington, DC',
                'LAS': 'Las Vegas, NV',
                'PHX': 'Phoenix, AZ',
                'IAH': 'Houston, TX',
                'MCO': 'Orlando, FL',
                'CDG': 'Paris, France',
                'LHR': 'London, UK',
                'BER': 'Berlin, Germany',
                'FCO': 'Rome, Italy',
                'NRT': 'Tokyo, Japan',
            }

            search_city = airport_to_city.get(city.upper(), city)

            # Build search query
            search_query = f"restaurants {search_city}"
            if cuisine:
                search_query = f"{cuisine} restaurants {search_city}"

            # Build SerpAPI parameters
            params = {
                "engine": "google_local",
                "q": search_query,
                "location": search_city,
                "api_key": settings.SERP_API_KEY
            }

            # Make API request
            response = requests.get("https://serpapi.com/search", params=params, timeout=30)
            raw_results = response.json()

            # Format results
            return json.dumps(self._format_restaurant_results(raw_results, search_city, cuisine))

        except Exception as e:
            logger.error(f"Error searching restaurants: {str(e)}")
            return json.dumps({"success": False, "error": str(e), "restaurants": []})

    @staticmethod
    def _format_restaurant_results(raw_results: Dict, city: str, cuisine: Optional[str] = None) -> Dict[str, Any]:
        """Format restaurant search results"""
        try:
            restaurants = []
            local_results = raw_results.get('local_results', [])

            for result in local_results[:15]:  # Limit to 15 results
                # Parse restaurant data
                parsed_restaurant = RestaurantSearchTool._parse_restaurant(result, city)

                # Apply cuisine filter if specified
                if cuisine and cuisine.lower() not in parsed_restaurant.get('cuisine_type', '').lower():
                    continue

                restaurants.append(parsed_restaurant)

            return {
                "success": True,
                "restaurants": restaurants,
                "search_parameters": {
                    "city": city,
                    "cuisine": cuisine
                }
            }
        except Exception as e:
            logger.error(f"Error formatting restaurant results: {str(e)}")
            return {"success": False, "error": str(e), "restaurants": []}

    @staticmethod
    def _parse_restaurant(restaurant_data: Dict, city: str) -> Dict[str, Any]:
        """Parse individual restaurant data"""
        try:
            # Extract price level
            price_info = restaurant_data.get('price', '')
            if isinstance(price_info, str):
                price_level = len([c for c in price_info if c == '$'])
            else:
                price_level = 2  # Default to $$

            # Determine cuisine type
            restaurant_type = restaurant_data.get('type', '')
            cuisine_type = 'Other'
            common_cuisines = ['American', 'Italian', 'Mexican', 'Chinese', 'Japanese',
                             'Indian', 'Thai', 'French', 'Mediterranean', 'Seafood']
            for c in common_cuisines:
                if c.lower() in restaurant_type.lower():
                    cuisine_type = c
                    break

            # Estimate average cost
            cost_map = {1: 15, 2: 30, 3: 50, 4: 100}
            avg_cost = cost_map.get(price_level, 30)

            return {
                "name": restaurant_data.get('title', 'Unknown Restaurant'),
                "cuisine_type": cuisine_type,
                "city": city,
                "address": restaurant_data.get('address', ''),
                "rating": float(restaurant_data.get('rating', 0)),
                "review_count": restaurant_data.get('reviews', 0),
                "price_level": price_level,
                "price_range": '$' * price_level,
                "average_cost_per_person": avg_cost,
                "currency": "USD",
                "phone": restaurant_data.get('phone', ''),
                "website": restaurant_data.get('website', ''),
                "thumbnail": restaurant_data.get('thumbnail', ''),
                "has_delivery": 'delivery' in restaurant_type.lower(),
                "has_takeout": 'takeout' in restaurant_type.lower(),
                "hours": restaurant_data.get('hours', ''),
            }
        except Exception as e:
            logger.error(f"Error parsing restaurant: {str(e)}", exc_info=True)
            return {}


class RestaurantEvaluator:
    """
    Utility-based evaluator for restaurants
    Scores based on rating, price, and reviews
    """

    @staticmethod
    def evaluate_rating_utility(rating: float, reviews: int = 0) -> Dict[str, Any]:
        """
        Evaluate restaurant rating utility

        Score ranges:
        - 4.5-5★: +40 (excellent)
        - 4.0-4.4★: +20 (very good)
        - 3.5-3.9★: 0 (good)
        - 3.0-3.4★: -20 (fair)
        - < 3.0★: -40 (poor)

        Bonus: +5 for > 100 reviews (well-established)
        """
        try:
            rating = float(rating)
        except:
            rating = 0

        if rating >= 4.5:
            rating_score = 40
        elif rating >= 4.0:
            rating_score = 20
        elif rating >= 3.5:
            rating_score = 0
        elif rating >= 3.0:
            rating_score = -20
        else:
            rating_score = -40

        # Bonus for well-reviewed restaurants
        review_bonus = 5 if reviews > 100 else 0

        return {
            "rating": rating,
            "review_count": reviews,
            "rating_utility_score": rating_score + review_bonus
        }

    @staticmethod
    def evaluate_price_utility(price_level: int, avg_cost: float = 0) -> Dict[str, Any]:
        """
        Evaluate restaurant price utility

        Score ranges:
        - $ (budget): +30 (excellent value)
        - $$ (moderate): +10 (good value)
        - $$$ (upscale): -10 (expensive)
        - $$$$ (fine dining): -30 (very expensive)
        """
        try:
            price_level = int(price_level)
        except:
            price_level = 2

        if price_level == 1:
            price_score = 30
        elif price_level == 2:
            price_score = 10
        elif price_level == 3:
            price_score = -10
        else:  # 4
            price_score = -30

        return {
            "price_level": price_level,
            "price_range": '$' * price_level,
            "average_cost_per_person": avg_cost,
            "price_utility_score": price_score
        }

    @staticmethod
    def evaluate_restaurant_comprehensive(restaurant: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive restaurant evaluation combining rating and price utilities
        """
        rating_eval = RestaurantEvaluator.evaluate_rating_utility(
            restaurant.get('rating', 0),
            restaurant.get('review_count', 0)
        )
        price_eval = RestaurantEvaluator.evaluate_price_utility(
            restaurant.get('price_level', 2),
            restaurant.get('average_cost_per_person', 0)
        )

        combined_score = rating_eval['rating_utility_score'] + price_eval['price_utility_score']

        # Start with all original restaurant data
        evaluated_restaurant = dict(restaurant)

        # Add/override with evaluation fields
        evaluated_restaurant.update({
            "rating": rating_eval['rating'],
            "review_count": rating_eval['review_count'],
            "rating_utility_score": rating_eval['rating_utility_score'],
            "price_level": price_eval['price_level'],
            "price_range": price_eval['price_range'],
            "average_cost_per_person": price_eval['average_cost_per_person'],
            "price_utility_score": price_eval['price_utility_score'],
            "utility_score": combined_score,
            "combined_utility_score": combined_score,
            "recommendation": RestaurantEvaluator._get_recommendation(combined_score)
        })

        return evaluated_restaurant

    @staticmethod
    def _get_recommendation(score: int) -> str:
        """Get recommendation based on utility score"""
        if score >= 40:
            return "Highly recommended - excellent rating and value"
        elif score >= 20:
            return "Great choice - good balance of quality and price"
        elif score >= 0:
            return "Good option - decent quality"
        elif score >= -20:
            return "Consider alternatives - may be overpriced"
        else:
            return "Not recommended - poor value or quality"

    @staticmethod
    def rank_restaurants(restaurants: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank restaurants by utility score"""
        if not restaurants:
            return []

        evaluated_restaurants = [
            RestaurantEvaluator.evaluate_restaurant_comprehensive(restaurant)
            for restaurant in restaurants
        ]

        return sorted(
            evaluated_restaurants,
            key=lambda x: x['combined_utility_score'],
            reverse=True
        )
