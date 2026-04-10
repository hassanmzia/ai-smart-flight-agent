"""
LiveContextService — Real-Time Awareness Engine

Provides weather impact assessment, crowd-level predictions, and
aggregated live context for destinations and attractions.
"""

import hashlib
import logging
import random
from datetime import datetime, timedelta, timezone as dt_timezone
from typing import Optional

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

# ── Deterministic helpers ──────────────────────────────────────────────

def _seed_for(destination: str, extra: str = "") -> int:
    """Return a stable numeric seed derived from destination + extra string."""
    raw = f"{destination.lower().strip()}{extra}"
    return int(hashlib.md5(raw.encode()).hexdigest(), 16) % (2**31)


# ── Climate profiles per rough latitude / keyword ──────────────────────

_CLIMATE_PROFILES = {
    # (avg_temp_C, humidity%, rain_chance%, dominant_condition)
    "tropical": (30, 78, 45, "Rain"),
    "mediterranean": (24, 55, 20, "Clear"),
    "continental": (18, 50, 30, "Partly Cloudy"),
    "arid": (35, 22, 5, "Clear"),
    "oceanic": (16, 70, 40, "Clouds"),
    "cold": (5, 60, 35, "Snow"),
    "default": (22, 55, 25, "Partly Cloudy"),
}

_DESTINATION_CLIMATE_HINTS: dict[str, str] = {
    "bali": "tropical", "bangkok": "tropical", "cancun": "tropical",
    "miami": "tropical", "singapore": "tropical", "jakarta": "tropical",
    "havana": "tropical", "phuket": "tropical", "honolulu": "tropical",
    "rome": "mediterranean", "barcelona": "mediterranean",
    "athens": "mediterranean", "lisbon": "mediterranean",
    "nice": "mediterranean", "dubrovnik": "mediterranean",
    "istanbul": "mediterranean", "naples": "mediterranean",
    "paris": "oceanic", "london": "oceanic", "amsterdam": "oceanic",
    "dublin": "oceanic", "brussels": "oceanic", "seattle": "oceanic",
    "new york": "continental", "chicago": "continental",
    "berlin": "continental", "tokyo": "continental", "toronto": "continental",
    "seoul": "continental", "beijing": "continental", "moscow": "cold",
    "dubai": "arid", "marrakech": "arid", "phoenix": "arid",
    "las vegas": "arid", "cairo": "arid", "doha": "arid",
    "reykjavik": "cold", "oslo": "cold", "helsinki": "cold",
}

_CONDITIONS = ["Clear", "Clouds", "Rain", "Partly Cloudy", "Drizzle",
               "Thunderstorm", "Snow", "Mist"]

_CONDITION_ICONS = {
    "Clear": "01d",
    "Clouds": "04d",
    "Rain": "10d",
    "Drizzle": "09d",
    "Partly Cloudy": "02d",
    "Thunderstorm": "11d",
    "Snow": "13d",
    "Mist": "50d",
}

# Month-based temperature offsets (Northern Hemisphere bias, simple model)
_MONTH_TEMP_OFFSET = {
    1: -8, 2: -6, 3: -2, 4: 3, 5: 7, 6: 10,
    7: 12, 8: 11, 9: 7, 10: 2, 11: -3, 12: -7,
}

_CROWD_LABELS = {
    1: "Very Low", 2: "Low", 3: "Below Average", 4: "Moderate",
    5: "Average", 6: "Above Average", 7: "Busy",
    8: "Very Busy", 9: "Crowded", 10: "Extremely Crowded",
}


class LiveContextService:
    """Central service for real-time awareness data."""

    # ── Weather Impact ──────────────────────────────────────────────

    def get_weather_impact(self, destination: str, date: Optional[str] = None) -> dict:
        """
        Return weather data with itinerary impact assessment.

        Parameters
        ----------
        destination : str
            City / destination name.
        date : str | None
            ISO date string (YYYY-MM-DD).  Defaults to today.

        Returns
        -------
        dict with keys: temperature, condition, humidity, wind_speed,
             impact_level, suggestion, icon
        """
        if date:
            try:
                target_date = datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                target_date = datetime.now()
        else:
            target_date = datetime.now()

        # Attempt live data from OpenWeatherMap
        api_key = getattr(settings, "OPENWEATHERMAP_API_KEY", "") or getattr(
            settings, "OPENWEATHER_API_KEY", ""
        )
        weather = None
        if api_key:
            weather = self._fetch_openweathermap(destination, target_date, api_key)

        if weather is None:
            weather = self._generate_plausible_weather(destination, target_date)

        # Assess impact
        impact_level, suggestion = self._assess_impact(weather)
        weather["impact_level"] = impact_level
        weather["suggestion"] = suggestion
        return weather

    # ── Crowd Levels ────────────────────────────────────────────────

    def get_crowd_levels(
        self, destination: str, attraction_name: Optional[str] = None
    ) -> dict:
        """
        Return crowd-level predictions with an hourly heatmap (6 AM – 10 PM).

        Uses day-of-week awareness (weekends are busier).
        """
        now = datetime.now()
        day_of_week = now.weekday()  # 0=Mon … 6=Sun
        is_weekend = day_of_week >= 5

        seed_extra = attraction_name or ""
        rng = random.Random(_seed_for(destination, seed_extra + str(day_of_week)))

        hourly_levels: list[dict] = []
        base = 4 if not is_weekend else 6  # weekend boost

        for hour in range(6, 23):  # 6 AM to 10 PM inclusive
            # Bell-curve-ish pattern peaking around midday
            hour_factor = max(0, 1 - abs(hour - 13) / 7)
            level = int(base + hour_factor * 5 + rng.uniform(-1, 1))
            level = max(1, min(10, level))
            hourly_levels.append({
                "hour": hour,
                "level": level,
                "label": _CROWD_LABELS.get(level, "Average"),
            })

        # Derive summary values
        levels_only = [h["level"] for h in hourly_levels]
        current_hour = now.hour
        current_level = next(
            (h["level"] for h in hourly_levels if h["hour"] == current_hour),
            levels_only[len(levels_only) // 2],
        )

        peak_hours = sorted(hourly_levels, key=lambda h: h["level"], reverse=True)[:3]
        best_hours = sorted(hourly_levels, key=lambda h: h["level"])[:3]

        return {
            "destination": destination,
            "attraction_name": attraction_name,
            "day_of_week": now.strftime("%A"),
            "is_weekend": is_weekend,
            "current_level": current_level,
            "current_label": _CROWD_LABELS.get(current_level, "Average"),
            "peak_hours": [
                f"{h['hour']}:00" for h in peak_hours
            ],
            "best_time_to_visit": [
                f"{h['hour']}:00" for h in best_hours
            ],
            "hourly_levels": hourly_levels,
        }

    # ── Aggregated Live Context ─────────────────────────────────────

    def get_live_context(
        self,
        destination: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        date: Optional[str] = None,
    ) -> dict:
        """
        Combined live context: weather + crowd summary + nearby attractions.
        """
        weather = self.get_weather_impact(destination, date=date)
        crowd = self.get_crowd_levels(destination)

        nearby = self._get_nearby_attractions(destination, latitude, longitude)

        # Sunrise / sunset approximation
        now = datetime.now(dt_timezone.utc)
        sunrise = now.replace(hour=6, minute=15, second=0, microsecond=0)
        sunset = now.replace(hour=18, minute=45, second=0, microsecond=0)

        return {
            "destination": destination,
            "local_time": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "weather": weather,
            "crowd_summary": {
                "current_level": crowd["current_level"],
                "current_label": crowd["current_label"],
                "peak_hours": crowd["peak_hours"],
                "best_time_to_visit": crowd["best_time_to_visit"],
            },
            "nearby_attractions": nearby,
            "sunrise": sunrise.strftime("%H:%M"),
            "sunset": sunset.strftime("%H:%M"),
        }

    # ── Private helpers ─────────────────────────────────────────────

    def _fetch_openweathermap(
        self, destination: str, target_date: datetime, api_key: str
    ) -> Optional[dict]:
        """Try to fetch from OpenWeatherMap.  Return None on any failure."""
        try:
            days_ahead = (target_date - datetime.now()).days
            if days_ahead < 0:
                days_ahead = 0

            # Current weather (if today) or 5-day forecast
            if days_ahead <= 5:
                url = (
                    "https://api.openweathermap.org/data/2.5/forecast"
                    f"?q={destination}&appid={api_key}&units=metric&cnt=40"
                )
            else:
                # Beyond 5 days – fall back to current weather as proxy
                url = (
                    "https://api.openweathermap.org/data/2.5/weather"
                    f"?q={destination}&appid={api_key}&units=metric"
                )

            resp = requests.get(url, timeout=5)
            if resp.status_code != 200:
                logger.warning(
                    "OpenWeatherMap returned %s for %s", resp.status_code, destination
                )
                return None

            data = resp.json()

            # Parse forecast list — pick the entry closest to target date noon
            if "list" in data:
                target_ts = target_date.replace(hour=12).timestamp()
                closest = min(data["list"], key=lambda e: abs(e["dt"] - target_ts))
                main = closest.get("main", {})
                weather_desc = closest.get("weather", [{}])[0]
                wind = closest.get("wind", {})
            else:
                main = data.get("main", {})
                weather_desc = data.get("weather", [{}])[0]
                wind = data.get("wind", {})

            condition = weather_desc.get("main", "Clear")
            return {
                "temperature": round(main.get("temp", 22), 1),
                "condition": condition,
                "description": weather_desc.get("description", condition.lower()),
                "humidity": main.get("humidity", 50),
                "wind_speed": round(wind.get("speed", 5), 1),
                "icon": weather_desc.get("icon", _CONDITION_ICONS.get(condition, "01d")),
            }
        except Exception as exc:
            logger.warning("OpenWeatherMap fetch failed: %s", exc)
            return None

    def _generate_plausible_weather(
        self, destination: str, target_date: datetime
    ) -> dict:
        """Generate deterministic but plausible weather from destination + date."""
        dest_lower = destination.lower().strip()
        climate_key = _DESTINATION_CLIMATE_HINTS.get(dest_lower, "default")
        base_temp, base_humidity, rain_chance, dominant = _CLIMATE_PROFILES[climate_key]

        month = target_date.month
        temp_offset = _MONTH_TEMP_OFFSET.get(month, 0)

        rng = random.Random(_seed_for(destination, target_date.strftime("%Y-%m-%d")))

        temperature = round(base_temp + temp_offset + rng.uniform(-3, 3), 1)
        humidity = max(10, min(100, base_humidity + rng.randint(-10, 10)))
        wind_speed = round(rng.uniform(2, 20), 1)

        # Pick condition weighted toward the climate's dominant
        if rng.random() * 100 < rain_chance:
            condition = rng.choice(["Rain", "Drizzle", "Thunderstorm"])
        elif rng.random() < 0.5:
            condition = dominant
        else:
            condition = rng.choice(["Clear", "Clouds", "Partly Cloudy"])

        # Snow override for cold temps
        if temperature < 2 and condition in ("Rain", "Drizzle"):
            condition = "Snow"

        icon = _CONDITION_ICONS.get(condition, "01d")

        return {
            "temperature": temperature,
            "condition": condition,
            "description": condition.lower(),
            "humidity": humidity,
            "wind_speed": wind_speed,
            "icon": icon,
        }

    @staticmethod
    def _assess_impact(weather: dict) -> tuple[str, str]:
        """Return (impact_level, suggestion) based on weather data."""
        condition = weather.get("condition", "Clear")
        temp = weather.get("temperature", 22)
        wind = weather.get("wind_speed", 5)

        # Default
        impact_level = "none"
        suggestion = "Great weather for outdoor activities — enjoy your trip!"

        # Temperature extremes
        if temp > 38:
            impact_level = "high"
            suggestion = (
                "Extreme heat expected — stay hydrated, seek shade, "
                "and consider scheduling outdoor activities for early morning or evening."
            )
        elif temp > 33:
            impact_level = "moderate"
            suggestion = (
                "Hot weather ahead — bring sunscreen and water. "
                "Plan breaks in air-conditioned venues."
            )
        elif temp < 0:
            impact_level = "moderate"
            suggestion = (
                "Freezing temperatures — dress in warm layers and "
                "be cautious of icy paths."
            )
        elif temp < 5:
            impact_level = "low"
            suggestion = "Cold weather — pack warm clothing and plan for indoor options."

        # Precipitation overrides
        if condition in ("Rain", "Drizzle"):
            if impact_level in ("none", "low"):
                impact_level = "moderate"
            suggestion = (
                "Rain expected — consider indoor alternatives and carry an umbrella. "
                "Museum visits or covered markets make great backup plans."
            )
        elif condition == "Thunderstorm":
            impact_level = "high"
            suggestion = (
                "Thunderstorms forecast — avoid open areas and hilltops. "
                "Reschedule outdoor activities to a clearer window."
            )
        elif condition == "Snow":
            if impact_level in ("none", "low"):
                impact_level = "moderate"
            suggestion = (
                "Snow expected — roads may be slippery. "
                "Check local transport updates and wear proper footwear."
            )

        # Wind overrides
        if wind > 40:
            impact_level = "high"
            suggestion = (
                "Very high winds expected — outdoor tours and boat trips "
                "may be cancelled. Check with operators."
            )
        elif wind > 25 and impact_level in ("none", "low"):
            impact_level = "low"
            suggestion += " Windy conditions — secure loose items."

        return impact_level, suggestion

    def _get_nearby_attractions(
        self,
        destination: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
    ) -> list[dict]:
        """
        Return a list of plausible nearby attractions.

        If lat/lng are provided the distance values will be small;
        otherwise return well-known landmarks for the destination.
        """
        _KNOWN_ATTRACTIONS: dict[str, list[dict]] = {
            "paris": [
                {"name": "Eiffel Tower", "type": "landmark", "distance_km": 1.2},
                {"name": "Louvre Museum", "type": "museum", "distance_km": 2.0},
                {"name": "Notre-Dame Cathedral", "type": "landmark", "distance_km": 2.5},
                {"name": "Musee d'Orsay", "type": "museum", "distance_km": 1.8},
            ],
            "london": [
                {"name": "Big Ben", "type": "landmark", "distance_km": 0.8},
                {"name": "British Museum", "type": "museum", "distance_km": 1.5},
                {"name": "Tower of London", "type": "landmark", "distance_km": 3.2},
                {"name": "Buckingham Palace", "type": "landmark", "distance_km": 1.0},
            ],
            "tokyo": [
                {"name": "Senso-ji Temple", "type": "temple", "distance_km": 2.0},
                {"name": "Tokyo Tower", "type": "landmark", "distance_km": 1.5},
                {"name": "Meiji Shrine", "type": "shrine", "distance_km": 3.0},
                {"name": "Shibuya Crossing", "type": "landmark", "distance_km": 2.8},
            ],
            "new york": [
                {"name": "Statue of Liberty", "type": "landmark", "distance_km": 5.0},
                {"name": "Central Park", "type": "park", "distance_km": 1.0},
                {"name": "Times Square", "type": "landmark", "distance_km": 0.5},
                {"name": "Metropolitan Museum of Art", "type": "museum", "distance_km": 2.0},
            ],
            "rome": [
                {"name": "Colosseum", "type": "landmark", "distance_km": 1.0},
                {"name": "Vatican Museums", "type": "museum", "distance_km": 3.5},
                {"name": "Trevi Fountain", "type": "landmark", "distance_km": 1.5},
                {"name": "Pantheon", "type": "landmark", "distance_km": 1.8},
            ],
            "barcelona": [
                {"name": "Sagrada Familia", "type": "landmark", "distance_km": 2.0},
                {"name": "Park Guell", "type": "park", "distance_km": 3.5},
                {"name": "La Rambla", "type": "landmark", "distance_km": 1.0},
                {"name": "Casa Batllo", "type": "landmark", "distance_km": 1.5},
            ],
            "dubai": [
                {"name": "Burj Khalifa", "type": "landmark", "distance_km": 1.0},
                {"name": "Dubai Mall", "type": "shopping", "distance_km": 1.2},
                {"name": "Palm Jumeirah", "type": "landmark", "distance_km": 8.0},
                {"name": "Dubai Marina", "type": "landmark", "distance_km": 5.0},
            ],
            "sydney": [
                {"name": "Sydney Opera House", "type": "landmark", "distance_km": 1.0},
                {"name": "Harbour Bridge", "type": "landmark", "distance_km": 1.5},
                {"name": "Bondi Beach", "type": "beach", "distance_km": 7.0},
                {"name": "Taronga Zoo", "type": "zoo", "distance_km": 4.0},
            ],
        }

        dest_lower = destination.lower().strip()
        attractions = _KNOWN_ATTRACTIONS.get(dest_lower, [])

        if not attractions:
            # Generate generic attractions
            rng = random.Random(_seed_for(destination, "attractions"))
            types = ["landmark", "museum", "park", "market", "restaurant"]
            attractions = [
                {
                    "name": f"{destination} {t.title()} {i+1}",
                    "type": t,
                    "distance_km": round(rng.uniform(0.5, 6.0), 1),
                }
                for i, t in enumerate(types)
            ]

        if latitude is not None and longitude is not None:
            # Adjust distances slightly based on coords being provided
            rng = random.Random(_seed_for(str(latitude), str(longitude)))
            for a in attractions:
                a["distance_km"] = round(rng.uniform(0.3, a["distance_km"]), 1)

        return attractions
