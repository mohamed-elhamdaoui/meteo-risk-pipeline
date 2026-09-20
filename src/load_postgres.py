import os

import pandas as pd
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}


def get_connection():
    """Ouvre une connexion PostgreSQL, en forcant l'encodage UTF-8."""
    conn = psycopg2.connect(**DB_CONFIG)
    print(f"Encodage AVANT set_client_encoding : {conn.encoding}")
    conn.set_client_encoding("UTF8")
    print(f"Encodage APRES set_client_encoding : {conn.encoding}")
    return conn


def load_gold_data(path="data/gold/weather_risk.csv"):
    """Charge le CSV Gold final."""
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    return df


def upsert_cities(df, conn):
    """
    Insere les villes uniques dans la table cities.
    ON CONFLICT DO NOTHING : si la ville existe deja (meme city_name), on l'ignore
    plutot que de planter ou dupliquer.
    """
    cities = df[["city", "lat", "lng"]].drop_duplicates(subset=["city"])

    with conn.cursor() as cur:
        for _, row in cities.iterrows():
            cur.execute(
                """
                INSERT INTO cities (city_name, lat, lng)
                VALUES (%s, %s, %s)
                ON CONFLICT (city_name) DO NOTHING;
                """,
                (row["city"], row["lat"], row["lng"]),
            )
    conn.commit()
    print(f"{len(cities)} villes traitees (inserees ou deja existantes).")


def get_city_id_map(conn):
    """Recupere le mapping city_name -> city_id depuis la base."""
    with conn.cursor() as cur:
        cur.execute("SELECT city_id, city_name FROM cities;")
        rows = cur.fetchall()
    return {city_name: city_id for city_id, city_name in rows}


def upsert_forecasts(df, conn, city_id_map):
    """
    Insere ou met a jour les previsions.
    ON CONFLICT (city_id, forecast_date) DO UPDATE : si une prevision existe deja
    pour cette ville a cette date, on ecrase avec les nouvelles valeurs
    (les previsions sont mises a jour au fil du temps, comme demande dans le sujet).
    """
    with conn.cursor() as cur:
        for _, row in df.iterrows():
            city_id = city_id_map[row["city"]]

            cur.execute(
                """
                INSERT INTO weather_forecasts (
                    city_id, forecast_date,
                    temperature_max, temperature_min,
                    precipitation, precipitation_probability,
                    wind_speed_max, wind_gusts_max, weather_code,
                    temp_category, precip_category, wind_category,
                    risk_score, risk_category
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (city_id, forecast_date) DO UPDATE SET
                    temperature_max = EXCLUDED.temperature_max,
                    temperature_min = EXCLUDED.temperature_min,
                    precipitation = EXCLUDED.precipitation,
                    precipitation_probability = EXCLUDED.precipitation_probability,
                    wind_speed_max = EXCLUDED.wind_speed_max,
                    wind_gusts_max = EXCLUDED.wind_gusts_max,
                    weather_code = EXCLUDED.weather_code,
                    temp_category = EXCLUDED.temp_category,
                    precip_category = EXCLUDED.precip_category,
                    wind_category = EXCLUDED.wind_category,
                    risk_score = EXCLUDED.risk_score,
                    risk_category = EXCLUDED.risk_category;
                """,
                (
                    city_id,
                    row["date"].date(),
                    row["temperature_max"],
                    row["temperature_min"],
                    row["precipitation"],
                    row["precipitation_probability"],
                    row["wind_speed_max"],
                    row["wind_gusts_max"],
                    row["weather_code"],
                    row["temp_category"],
                    row["precip_category"],
                    row["wind_category"],
                    row["risk_score"],
                    row["risk_category"],
                ),
            )
    conn.commit()
    print(f"{len(df)} previsions inserees/mises a jour.")


def run_load():
    """Pipeline complet Gold -> PostgreSQL."""
    df = load_gold_data()
    conn = get_connection()

    try:
        upsert_cities(df, conn)
        city_id_map = get_city_id_map(conn)
        upsert_forecasts(df, conn, city_id_map)
    finally:
        conn.close()

    print("Chargement PostgreSQL termine.")


if __name__ == "__main__":
    run_load()