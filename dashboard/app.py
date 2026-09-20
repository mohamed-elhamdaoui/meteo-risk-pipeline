import os

import pandas as pd
import psycopg2
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}


@st.cache_data(ttl=300)
def load_data():
    """Charge toutes les previsions jointes aux villes depuis PostgreSQL."""
    conn = psycopg2.connect(**DB_CONFIG)
    conn.set_client_encoding("UTF8")

    query = """
        SELECT
            c.city_name,
            c.lat,
            c.lng,
            wf.forecast_date,
            wf.temperature_max,
            wf.temperature_min,
            wf.precipitation,
            wf.wind_gusts_max,
            wf.risk_score,
            wf.risk_category
        FROM weather_forecasts wf
        JOIN cities c ON c.city_id = wf.city_id;
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df


def main():
    st.set_page_config(page_title="Meteo Risk Dashboard", layout="wide")
    st.title("🌦️ Dashboard Risque Meteo - Maroc")

    df = load_data()

    # ---- KPI ----
    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Nombre de villes", df["city_name"].nunique())
    col2.metric("Temperature max", f"{df['temperature_max'].max():.1f} °C")
    col3.metric("Precipitation max", f"{df['precipitation'].max():.1f} mm")

    nb_risque = df[df["risk_category"].isin(["Eleve", "Critique"])].shape[0]
    col4.metric("Periodes a risque (Eleve/Critique)", nb_risque)

    ville_plus_risquee = df.loc[df["risk_score"].idxmax(), "city_name"]
    col5.metric("Ville la plus a risque", ville_plus_risquee)

    st.divider()

    # ---- Tableau brut (temporaire, pour verifier que ca marche) ----
    st.subheader("Donnees brutes")
    st.dataframe(df)


if __name__ == "__main__":
    main()