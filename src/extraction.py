import json

import pandas as pd
import requests


def load_cities(path="data/bronze/ma.csv"):
    """Charge le fichier des villes marocaines (lat/lng)."""
    return pd.read_csv(path, encoding="cp1252")


def build_params(df_cities):
    """Construit les parametres de la requete Open-Meteo a partir des villes."""
    latitudes = df_cities["lat"].tolist()
    longitudes = df_cities["lng"].tolist()

    return {
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


def fetch_weather(params):
    """Appelle l'API Open-Meteo et renvoie la liste des reponses (une par ville)."""
    response = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params=params,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def build_weather_dict(df_cities, responses):
    """Associe chaque reponse API a son nom de ville."""
    if len(responses) != len(df_cities):
        raise ValueError(
            f"Nombre de reponses ({len(responses)}) different du nombre "
            f"de villes ({len(df_cities)}) : donnees incoherentes."
        )

    weather_data = {}
    for i, city in df_cities.iterrows():
        weather_data[city["city"]] = responses[i]

    return weather_data


def save_weather_json(weather_data, path="data/bronze/weather_data.json"):
    """Sauvegarde les donnees meteo brutes en JSON."""
    with open(path, "w", encoding="utf-8") as file:
        json.dump(weather_data, file, ensure_ascii=False, indent=4)


def run_extraction():
    """Pipeline complet d'extraction Bronze. Renvoie le dict weather_data."""
    df_cities = load_cities()
    params = build_params(df_cities)

    try:
        responses = fetch_weather(params)
        weather_data = build_weather_dict(df_cities, responses)
        save_weather_json(weather_data)

        print(f"Weather data collected for {len(weather_data)} cities.")
        return weather_data

    except requests.exceptions.Timeout:
        print("Timeout: the API took too long to respond.")

    except requests.exceptions.RequestException as error:
        print(f"API error: {error}")

    except ValueError as error:
        print(f"Data error: {error}")


if __name__ == "__main__":
    run_extraction()
