import json

import pandas as pd
import requests


df = pd.read_csv("data/Bronze/ma.csv")

weather_data = {}

for _, city in df.iterrows():
    latitude = city["lat"]
    longitude = city["lng"]

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "precipitation_probability_max",
            "wind_speed_10m_max",
            "wind_gusts_10m_max",
            "weather_code",
        ],
        "forecast_days": 7,
        "timezone": "Africa/Casablanca",
    }

    try:
        response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params=params,
            timeout=10,
        )
        response.raise_for_status()

        weather_data[city["city"]] = response.json()

    except requests.exceptions.Timeout:
        print(f"Timeout for {city['city']}")

    except requests.exceptions.RequestException as error:
        print(f"API error for {city['city']}: {error}")

with open("data/Bronze/weather_data.json", "w", encoding="utf-8") as file:
    json.dump(weather_data, file, ensure_ascii=False, indent=4)

print(f"Weather data collected for {len(weather_data)} cities.")
