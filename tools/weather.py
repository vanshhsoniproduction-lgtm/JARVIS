"""
Weather Tool Integration using Open-Meteo API with WMO Weather Codes
"""

import re
from typing import Optional

try:
    import requests
except ImportError:
    requests = None

# WMO Weather Interpretation Codes (WW)
WMO_CODES = {
    0: "Clear Sky (Saaf Aasmaan / Dhoop)",
    1: "Mainly Clear (Halki Dhoop)",
    2: "Partly Cloudy (Halke Baadal)",
    3: "Overcast (Ghane Baadal / Baarish Ka Mausam)",
    45: "Foggy (Kohrra)",
    48: "Depositing Rime Fog",
    51: "Light Drizzle (Halki Boondabaandi)",
    53: "Moderate Drizzle (Boondabaandi)",
    55: "Dense Drizzle",
    61: "Slight Rain (Halki Baarish)",
    63: "Moderate Rain (Baarish)",
    65: "Heavy Rain (Tez Baarish)",
    80: "Slight Rain Showers",
    81: "Moderate Rain Showers",
    82: "Violent Rain Showers",
    95: "Thunderstorm (Toofan aur Bijli)",
}


def fetch_weather(city: str) -> Optional[str]:
    if requests is None:
        return None
    try:
        geo = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1},
            timeout=5,
        ).json()
        if not geo.get("results"):
            return None
        lat = geo["results"][0]["latitude"]
        lon = geo["results"][0]["longitude"]

        wx = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,precipitation,weather_code",
            },
            timeout=5,
        ).json()
        cur = wx.get("current", {})
        if not cur:
            return None

        w_code = cur.get("weather_code", 0)
        condition = WMO_CODES.get(w_code, "Partly Cloudy")

        return (
            f"[EXACT LIVE WEATHER DATA] City: {city} | Condition: {condition} | "
            f"Temp: {cur.get('temperature_2m')}°C | Humidity: {cur.get('relative_humidity_2m')}% | "
            f"Rainfall: {cur.get('precipitation')}mm"
        )
    except Exception:
        return None


def extract_city(user_input: str, default_city: str = "Jaipur") -> str:
    match = re.search(r"\b(?:in|at)\s+([A-Za-z\s]+)$", user_input.strip(), re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return default_city
