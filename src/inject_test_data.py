"""
Script de TEST uniquement - injecte des previsions synthetiques a risque
eleve/critique pour verifier que le dashboard Streamlit affiche bien tous
les cas (Faible/Modere/Eleve/Critique).

Ne touche PAS aux fichiers Bronze/Silver/Gold (qui doivent rester intacts).
Insere directement dans PostgreSQL, sur des villes EXISTANTES, a des dates
qui n'entrent pas en conflit avec les vraies previsions (on utilise le 8eme
jour, hors de la fenetre normale de 7 jours d'Open-Meteo).

A SUPPRIMER avant le rendu final du projet (voir clean_test_data() en bas).
"""

import os
from datetime import UTC, datetime, timedelta

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

# Date fictive, hors de la fenetre reelle des 7 jours, pour ne jamais entrer
# en conflit avec une vraie prevision lors des prochains runs du pipeline
TEST_DATE = datetime.now(tz=UTC).date() + timedelta(days=99)

# Scenarios synthetiques : (ville existante, temp_max, precip, vent_rafales)
TEST_SCENARIOS = [
    ("Agadir", 46.0, 55.0, 85.0),       # combinaison extreme -> risque Critique
    ("Essaouira", 32.0, 60.0, 95.0),    # pluie + vent extremes -> risque Critique
    ("Marrakech", 44.0, 20.0, 40.0),    # chaleur dominante -> risque Modere/Eleve
    ("Tangier", 26.0, 45.0, 70.0),      # pluie + vent forts -> risque Eleve
    ("Rabat", 28.0, 8.0, 25.0),         # tout normal -> risque Faible (temoin)
]


def linear_score(value, low, high):
    if value <= low:
        return 0
    if value >= high:
        return 100
    return (value - low) / (high - low) * 100


def compute_risk(temp_max, precip, wind_gusts):
    temp_score = linear_score(temp_max, low=30, high=45)
    precip_score = linear_score(precip, low=1, high=50)
    wind_score = linear_score(wind_gusts, low=30, high=90)
    score = precip_score * 0.40 + wind_score * 0.35 + temp_score * 0.25
    return round(score, 1)


def categorize_risk(score):
    if score < 30:
        return "Faible"
    elif score < 60:
        return "Modere"
    elif score < 80:
        return "Eleve"
    else:
        return "Critique"


def inject_test_data():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.set_client_encoding("UTF8")

    with conn.cursor() as cur:
        for city_name, temp_max, precip, wind_gusts in TEST_SCENARIOS:
            cur.execute("SELECT city_id FROM cities WHERE city_name = %s;", (city_name,))
            result = cur.fetchone()

            if result is None:
                print(f"Ville '{city_name}' introuvable, scenario ignore.")
                continue

            city_id = result[0]
            risk_score = compute_risk(temp_max, precip, wind_gusts)
            risk_category = categorize_risk(risk_score)

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
                    precipitation = EXCLUDED.precipitation,
                    wind_gusts_max = EXCLUDED.wind_gusts_max,
                    risk_score = EXCLUDED.risk_score,
                    risk_category = EXCLUDED.risk_category;
                """,
                (
                    city_id, TEST_DATE,
                    temp_max, temp_max - 8,
                    precip, 80,
                    wind_gusts * 0.7, wind_gusts, 3,
                    "TEST", "TEST", "TEST",
                    risk_score, risk_category,
                ),
            )
            print(f"{city_name} : risk_score={risk_score} -> {risk_category}")

    conn.commit()
    conn.close()
    print(f"\nDonnees de test injectees a la date fictive {TEST_DATE}.")


def clean_test_data():
    """Supprime les donnees de test avant le rendu final du projet."""
    conn = psycopg2.connect(**DB_CONFIG)
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM weather_forecasts WHERE forecast_date = %s;",
            (TEST_DATE,),
        )
    conn.commit()
    conn.close()
    print("Donnees de test supprimees.")


if __name__ == "__main__":
    inject_test_data()
    # Pour nettoyer plus tard, commente la ligne au-dessus et decommente celle-ci :
    # clean_test_data()
