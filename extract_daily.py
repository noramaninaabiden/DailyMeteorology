"""
extract_daily.py
Pulls yesterday's weather + air quality for all cities and loads it
into the same DuckDB bronze tables as the backfill (idempotent).
"""

import requests
import duckdb
from datetime import date, timedelta

CITIES = [
    {"name": "Kuala Lumpur", "lat": 3.1390, "lon": 101.6869},
    {"name": "Penang", "lat": 5.4141, "lon": 100.3288},
    {"name": "Johor Bahru", "lat": 1.4927, "lon": 103.7414},
    {"name": "Kota Kinabalu", "lat": 5.9804, "lon": 116.0735},
    {"name": "London", "lat": 51.5074, "lon": -0.1278},
    {"name": "New York", "lat": 40.7128, "lon": -74.0060},
    {"name": "Tokyo", "lat": 35.6762, "lon": 139.6503},
    {"name": "Sydney", "lat": -33.8688, "lon": 151.2093},
]

TARGET_DATE = (date.today() - timedelta(days=1)).isoformat()  # yesterday

DB_PATH = "daily_meteorology.duckdb"

WEATHER_URL = "https://api.open-meteo.com/v1/forecast"       # forecast, not archive
AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"


def fetch_weather(city):
    params = {
        "latitude": city["lat"],
        "longitude": city["lon"],
        "start_date": TARGET_DATE,
        "end_date": TARGET_DATE,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "timezone": "auto",
    }
    response = requests.get(WEATHER_URL, params=params)
    response.raise_for_status()
    return response.json()


def fetch_air_quality(city):
    params = {
        "latitude": city["lat"],
        "longitude": city["lon"],
        "start_date": TARGET_DATE,
        "end_date": TARGET_DATE,
        "hourly": "pm2_5,pm10,us_aqi",
        "timezone": "auto",
    }
    response = requests.get(AIR_QUALITY_URL, params=params)
    response.raise_for_status()
    return response.json()


def weather_json_to_rows(city_name, data):
    daily = data["daily"]
    rows = []
    for i, day in enumerate(daily["time"]):
        rows.append((
            city_name,
            day,
            daily["temperature_2m_max"][i],
            daily["temperature_2m_min"][i],
            daily["precipitation_sum"][i],
        ))
    return rows


def air_quality_json_to_rows(city_name, data):
    hourly = data["hourly"]
    rows = []
    for i, ts in enumerate(hourly["time"]):
        rows.append((
            city_name,
            ts,
            hourly["pm2_5"][i],
            hourly["pm10"][i],
            hourly["us_aqi"][i],
        ))
    return rows


def main():
    con = duckdb.connect(DB_PATH)

    for city in CITIES:
        print(f"Pulling {TARGET_DATE} weather for {city['name']}...")
        weather_rows = weather_json_to_rows(city["name"], fetch_weather(city))

        # idempotent: clear any existing row(s) for this city+date first
        con.execute(
            "DELETE FROM bronze_weather_daily WHERE city = ? AND date = ?",
            [city["name"], TARGET_DATE],
        )
        con.executemany(
            "INSERT INTO bronze_weather_daily VALUES (?, ?, ?, ?, ?)",
            weather_rows,
        )

        print(f"Pulling {TARGET_DATE} air quality for {city['name']}...")
        aq_rows = air_quality_json_to_rows(city["name"], fetch_air_quality(city))

        con.execute(
            "DELETE FROM bronze_air_quality_hourly WHERE city = ? AND CAST(timestamp AS DATE) = ?",
            [city["name"], TARGET_DATE],
        )
        con.executemany(
            "INSERT INTO bronze_air_quality_hourly VALUES (?, ?, ?, ?, ?)",
            aq_rows,
        )

    con.close()
    print(f"Daily load for {TARGET_DATE} complete.")


if __name__ == "__main__":
    main()