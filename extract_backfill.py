"""
extract_backfill.py
Pulls historical daily weather + hourly air quality for a set of cities
from the Open-Meteo API and loads it into DuckDB bronze tables.
"""

import requests
import duckdb
from datetime import date, timedelta

# --- Config ---

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

START_DATE = "2024-01-01"
END_DATE = (date.today() - timedelta(days=1)).isoformat()  # yesterday

DB_PATH = "daily_meteorology.duckdb"

WEATHER_URL = "https://archive-api.open-meteo.com/v1/archive"
AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"


def fetch_weather(city):
    params = {
        "latitude": city["lat"],
        "longitude": city["lon"],
        "start_date": START_DATE,
        "end_date": END_DATE,
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
        "start_date": START_DATE,
        "end_date": END_DATE,
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

    con.execute("""
        CREATE TABLE IF NOT EXISTS bronze_weather_daily (
            city VARCHAR,
            date DATE,
            temp_max_c DOUBLE,
            temp_min_c DOUBLE,
            precipitation_mm DOUBLE
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS bronze_air_quality_hourly (
            city VARCHAR,
            timestamp TIMESTAMP,
            pm2_5 DOUBLE,
            pm10 DOUBLE,
            us_aqi DOUBLE
        )
    """)

    for city in CITIES:
        print(f"Pulling weather for {city['name']}...")
        weather_data = fetch_weather(city)
        weather_rows = weather_json_to_rows(city["name"], weather_data)
        con.executemany(
            "INSERT INTO bronze_weather_daily VALUES (?, ?, ?, ?, ?)",
            weather_rows,
        )

        print(f"Pulling air quality for {city['name']}...")
        aq_data = fetch_air_quality(city)
        aq_rows = air_quality_json_to_rows(city["name"], aq_data)
        con.executemany(
            "INSERT INTO bronze_air_quality_hourly VALUES (?, ?, ?, ?, ?)",
            aq_rows,
        )

    con.close()
    print("Backfill complete.")


if __name__ == "__main__":
    main()