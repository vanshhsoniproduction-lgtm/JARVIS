"""
Weather & Geolocation Tool Integration using Open-Meteo API with Direct IP Coordinate Geolocation & Real-Time Hourly Forecast Breakdown
"""

import re
import time
from datetime import datetime
from typing import Optional, Dict, Any

try:
    import requests
except ImportError:
    requests = None

# Cache auto location to avoid repeated API calls
_CACHED_GEO = None
_CACHED_GEO_TIME = 0

# WMO Weather Interpretation Codes (WW)
WMO_CODES = {
    0: "Clear Sky (Saaf Aasmaan)",
    1: "Mainly Clear (Halki Dhoop)",
    2: "Partly Cloudy (Halke Baadal)",
    3: "Overcast (Ghane Baadal)",
    45: "Foggy (Kohrra)",
    48: "Dense Fog (Ghana Kohrra)",
    51: "Light Drizzle (Boondabaandi)",
    53: "Moderate Drizzle",
    55: "Dense Drizzle",
    61: "Light Rain (Halki Baarish)",
    63: "Moderate Rain (Baarish)",
    65: "Heavy Rain (Tez Baarish)",
    80: "Light Rain Showers",
    81: "Rain Showers",
    82: "Heavy Rain Showers",
    95: "Thunderstorm (Bijli aur Toofan)",
    96: "Thunderstorm with Hail",
    99: "Heavy Thunderstorm with Hail",
}


def get_user_ip_geo() -> Dict[str, Any]:
    """Detect real physical city, region, country, lat, lon of the user via IP geolocation (cached 1h)."""
    global _CACHED_GEO, _CACHED_GEO_TIME
    now = time.time()
    if _CACHED_GEO and (now - _CACHED_GEO_TIME) < 3600:
        return _CACHED_GEO

    if requests is not None:
        try:
            res = requests.get("http://ip-api.com/json/", timeout=3).json()
            if res.get("status") == "success":
                geo_info = {
                    "city": res.get("city", "Amritsar"),
                    "region": res.get("regionName", "Punjab"),
                    "country": res.get("country", "India"),
                    "lat": res.get("lat", 31.6340),
                    "lon": res.get("lon", 74.8723),
                }
                _CACHED_GEO = geo_info
                _CACHED_GEO_TIME = now
                return geo_info
        except Exception:
            pass

    return {
        "city": "Amritsar",
        "region": "Punjab",
        "country": "India",
        "lat": 31.6340,
        "lon": 74.8723,
    }


def get_auto_location() -> str:
    """Returns city name string."""
    return get_user_ip_geo()["city"]


def fetch_weather(city: Optional[str] = None, lat: Optional[float] = None, lon: Optional[float] = None) -> Optional[str]:
    if requests is None:
        return None

    geo_info = get_user_ip_geo()
    is_custom_city = False

    if lat is not None and lon is not None:
        target_lat = lat
        target_lon = lon
        city_name = city
        if not city_name:
            try:
                rev_res = requests.get(
                    "https://api.bigdatacloud.net/data/reverse-geocode-client",
                    params={"latitude": lat, "longitude": lon, "localityLanguage": "en"},
                    timeout=3
                ).json()
                city_name = rev_res.get("city") or rev_res.get("locality") or rev_res.get("principalSubdivision") or geo_info["city"]
                region_name = rev_res.get("principalSubdivision") or geo_info["region"]
                location_label = f"Live GPS Location ({city_name}, {region_name})"
            except Exception:
                location_label = f"Live GPS Location ({geo_info['city']}, {geo_info['region']})"
        else:
            location_label = f"Live GPS Location ({city_name})"
    elif city and city.strip():
        target_city = city.strip()
        if target_city.lower() != geo_info["city"].lower():
            is_custom_city = True
            location_label = f"City of {target_city}"
        else:
            location_label = f"City of {geo_info['city']}, {geo_info['region']}"
        target_lat = geo_info["lat"]
        target_lon = geo_info["lon"]
    else:
        target_lat = geo_info["lat"]
        target_lon = geo_info["lon"]
        location_label = f"IP Location Estimate ({geo_info['city']}, {geo_info['region']})"

    try:
        if is_custom_city:
            geo_res = requests.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": target_city, "count": 1},
                timeout=5,
            ).json()
            if geo_res.get("results"):
                target_lat = geo_res["results"][0]["latitude"]
                target_lon = geo_res["results"][0]["longitude"]

        lat = target_lat
        lon = target_lon

        # Fetch current forecast + 12-hour hourly telemetry
        wx = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,precipitation,weather_code",
                "hourly": "temperature_2m,precipitation_probability,relative_humidity_2m,weather_code",
                "forecast_days": 2,
                "timezone": "auto",
            },
            timeout=5,
        ).json()

        cur = wx.get("current", {})
        if not cur:
            return None

        w_code = cur.get("weather_code", 0)
        condition = WMO_CODES.get(w_code, "Partly Cloudy")
        temp = cur.get("temperature_2m")
        humidity = cur.get("relative_humidity_2m")
        precip = cur.get("precipitation", 0.0)

        # Build 8-hour hourly breakdown starting from CURRENT HOUR
        hourly = wx.get("hourly", {})
        hourly_summary_items = []
        rain_max = 30

        if hourly and "time" in hourly and "precipitation_probability" in hourly:
            times = hourly.get("time", [])
            probs = hourly.get("precipitation_probability", [])
            temps = hourly.get("temperature_2m", [])
            hums = hourly.get("relative_humidity_2m", [])

            # Find index matching current hour (e.g. 13:00)
            cur_hour = datetime.now().hour
            start_idx = 0
            for idx, t in enumerate(times):
                if f"{cur_hour:02d}:00" in t:
                    start_idx = idx
                    break

            for i in range(start_idx, min(len(times), start_idx + 8)):
                t_str = times[i].split("T")[-1] if "T" in times[i] else str(times[i])
                p_val = probs[i] if i < len(probs) else 0
                t_val = temps[i] if i < len(temps) else temp
                h_val = hums[i] if i < len(hums) else humidity
                hourly_summary_items.append(f"[{t_str}: {t_val}°C, Rain {p_val}%, Humidity {h_val}%]")
                if p_val > rain_max:
                    rain_max = p_val

        hourly_block = " ".join(hourly_summary_items[:6])

        return (
            f"[LIVE DATA] User Location: {location_label} (GPS: {lat}°N, {lon}°E) | "
            f"Sky Condition: {condition} | Current Temperature: {temp}°C | "
            f"Rainfall Probability Today: {rain_max}% | Current Humidity: {humidity}% | Current Precipitation: {precip}mm | "
            f"Hourly Forecast Breakdown (Starting Current Hour): {hourly_block}. "
            f"MANDATORY RULE: Always state the CITY NAME ('{geo_info['city']}'), current temperature, and use the exact hourly metrics starting from current hour when asked about rain, humidity, or forecast."
        )
    except Exception as e:
        return None


def extract_city(user_input: str, default_city: Optional[str] = None) -> str:
    """Extract city name from user input, handling single-word cities, punctuation, and natural queries."""
    text = re.sub(r"[^\w\s]", "", user_input.strip())

    match = re.search(r"\b(?:in|at|of|for)\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)", text, re.IGNORECASE)
    if match:
        extracted = match.group(1).strip()
        words = extracted.split()
        filtered = [w for w in words if w.lower() not in ("right", "now", "today", "tomorrow", "please", "current", "currently", "the")]
        if filtered:
            res = " ".join(filtered).title()
            if res.lower() not in ("weather", "temp", "temperature", "sky", "cloud", "rain", "location", "city"):
                return res

    words = text.split()
    if len(words) == 1 and len(words[0]) >= 3:
        w = words[0].lower()
        if w not in ("check", "weather", "temp", "today", "sky", "cloud", "rain", "please", "yes", "sure", "where", "location"):
            return words[0].title()

    return default_city if default_city else get_auto_location()
