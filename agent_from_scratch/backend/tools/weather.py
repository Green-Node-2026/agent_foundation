"""
Weather tools using Open-Meteo API.
Provides geocoding and weather retrieval functions.
"""

import openmeteo_requests
import requests
import requests_cache
from retry_requests import retry


def geocode(city: str) -> dict:
    """
    Convert city name to coordinates using Open-Meteo Geocoding API.
    Returns: {"name": str, "latitude": float, "longitude": float, "country": str}
    or {"error": str} if not found
    """
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": city, "count": 1}

    try:
        res = requests.get(url, params=params, timeout=5).json()

        if "results" not in res or not res["results"]:
            return {"error": f"Location '{city}' not found"}

        loc = res["results"][0]
        return {
            "name": loc["name"],
            "latitude": loc["latitude"],
            "longitude": loc["longitude"],
            "country": loc.get("country", "Unknown")
        }
    except Exception as e:
        return {"error": f"Geocoding failed: {str(e)}"}


def get_weather(latitude: float, longitude: float) -> dict:
    """
    Get current weather for coordinates using Open-Meteo API.
    Returns: {"temperature": float, "windspeed": float}
    or {"error": str} if failed
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current_weather": True
    }

    try:
        # Use cached session with retry logic
        session = requests_cache.CachedSession(
            cache_name='weather_cache',
            expire_after=300  # Cache for 5 minutes
        )
        retry_session = retry(session, retries=2, backoff_factor=0.5)

        res = retry_session.get(url, params=params, timeout=10)
        data = res.json()

        if "current_weather" not in data:
            return {"error": "No weather data available"}

        return {
            "temperature": data["current_weather"]["temperature"],
            "windspeed": data["current_weather"]["windspeed"]
        }
    except Exception as e:
        return {"error": f"Weather fetch failed: {str(e)}"}


def get_weather_by_city(location: str) -> dict:
    """
    High-level function: geocode city then fetch weather.
    Returns combined result or error.
    """
    geo = geocode(location)
    if "error" in geo:
        return geo

    weather = get_weather(geo["latitude"], geo["longitude"])
    if "error" in weather:
        return weather

    return {
        "location": geo["name"],
        "country": geo["country"],
        "temperature": weather["temperature"],
        "windspeed": weather["windspeed"]
    }


# Remove CLI code - keep module clean for imports
if __name__ == "__main__":
    city = input("Enter city: ")
    result = get_weather_by_city(city)
    print(result)