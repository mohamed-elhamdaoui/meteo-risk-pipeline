from pprint import pprint

import pandas as pd
import requests


df = pd.read_csv("data/Bronze/ma.csv")

city = df.iloc[0]
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

response = requests.get("https://api.open-meteo.com/v1/forecast", params=params)

print(city["city"])
print(response.status_code)
pprint(response.json())
