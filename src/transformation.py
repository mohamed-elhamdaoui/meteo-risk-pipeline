import json

import pandas as pd


def load_weather_json(path="data/bronze/weather_data.json"):
    """Charge les donnees meteo brutes (Bronze)."""
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def flatten_weather_data(weather_data):
    """Transforme le dict {ville: {daily: {...}}} en DataFrame une ligne par jour."""
    rows = []
    for city in weather_data:
        daily = weather_data[city]["daily"]

        for i in range(len(daily["time"])):
            rows.append(
                {
                    "city": city,
                    "date": daily["time"][i],
                    "temperature_max": daily["temperature_2m_max"][i],
                    "temperature_min": daily["temperature_2m_min"][i],
                    "precipitation": daily["precipitation_sum"][i],
                    "precipitation_probability": daily["precipitation_probability_max"][
                        i
                    ],
                    "wind_speed_max": daily["wind_speed_10m_max"][i],
                    "wind_gusts_max": daily["wind_gusts_10m_max"][i],
                    "weather_code": daily["weather_code"][i],
                }
            )

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    return df


def join_city_info(df, path="data/bronze/ma.csv"):
    """Ajoute lat/lng a partir du fichier des villes, et signale les non-matchees."""
    df_cities = pd.read_csv(path, encoding="cp1252", usecols=["city", "lat", "lng"])
    df = df.merge(df_cities, on="city", how="left")

    unmatched = df[df["lat"].isnull()]["city"].unique()
    if len(unmatched) > 0:
        print(f"Villes sans correspondance ({len(unmatched)}) :")
        print(unmatched)

    return df


def clean_data(df):
    """Supprime doublons et lignes incompletes."""
    before = len(df)
    df = df.drop_duplicates(subset=["city", "date"])
    df = df.dropna(subset=["temperature_max", "temperature_min"])
    after = len(df)

    print(f"{before - after} lignes supprimees lors du nettoyage.")
    return df


def reorder_columns(df):
    """Place city/lat/lng/date en premier pour la lisibilite."""
    return df[
        [
            "city",
            "lat",
            "lng",
            "date",
            "temperature_max",
            "temperature_min",
            "precipitation",
            "precipitation_probability",
            "wind_speed_max",
            "wind_gusts_max",
            "weather_code",
        ]
    ]


def run_transformation():
    """Pipeline complet Bronze -> Silver. Renvoie le DataFrame final."""
    weather_data = load_weather_json()
    df = flatten_weather_data(weather_data)
    df = join_city_info(df)
    df = clean_data(df)
    df = reorder_columns(df)

    df.to_csv("data/silver/weather_clean.csv", index=False)
    print(f"Silver terminee : {len(df)} lignes, {df['city'].nunique()} villes.")

    return df


if __name__ == "__main__":
    df = run_transformation()
    print(df.info())
    print(df.head(2))
