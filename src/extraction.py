import json

import pandas as pd
import requests


df = pd.read_csv("data/Bronze/ma.csv")

latitudes = df["lat"].tolist()
longitudes = df["lng"].tolist()

params = {
    "latitude": ",".join(map(str, latitudes)),
    "longitude": ",".join(map(str, longitudes)),
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
        timeout=30,
    )
    response.raise_for_status()

    responses = response.json()
    weather_data = {}

    for i, city in df.iterrows():
        weather_data[city["city"]] = responses[i]

    with open("data/Bronze/weather_data.json", "w", encoding="utf-8") as file:
        json.dump(weather_data, file, ensure_ascii=False, indent=4)

    print(f"Weather data collected for {len(weather_data)} cities.")

except requests.exceptions.Timeout:
    print("Timeout: the API took too long to respond.")

except requests.exceptions.RequestException as error:
    print(f"API error: {error}")
