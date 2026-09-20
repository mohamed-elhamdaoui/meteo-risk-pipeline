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

    # ---- Filtres (barre laterale) ----
    st.sidebar.header("Filtres")

    villes = sorted(df["city_name"].unique())
    villes_selectionnees = st.sidebar.multiselect(
        "Ville(s)", options=villes, default=[]
    )

    date_min = df["forecast_date"].min()
    date_max = df["forecast_date"].max()
    plage_dates = st.sidebar.date_input(
        "Periode", value=(date_min, date_max), min_value=date_min, max_value=date_max
    )

    niveaux_risque = ["Faible", "Modere", "Eleve", "Critique"]
    niveaux_selectionnes = st.sidebar.multiselect(
        "Niveau de risque", options=niveaux_risque, default=niveaux_risque
    )

    # ---- Application des filtres ----
    df_filtre = df.copy()

    if villes_selectionnees:
        df_filtre = df_filtre[df_filtre["city_name"].isin(villes_selectionnees)]

    if isinstance(plage_dates, tuple) and len(plage_dates) == 2:
        df_filtre = df_filtre[
            (df_filtre["forecast_date"] >= pd.to_datetime(plage_dates[0]))
            & (df_filtre["forecast_date"] <= pd.to_datetime(plage_dates[1]))
        ]

    if niveaux_selectionnes:
        df_filtre = df_filtre[df_filtre["risk_category"].isin(niveaux_selectionnes)]

    if df_filtre.empty:
        st.warning("Aucune donnee ne correspond aux filtres selectionnes.")
        return

    # ---- KPI (calcules sur les donnees FILTREES) ----
    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Nombre de villes", df_filtre["city_name"].nunique())
    col2.metric("Temperature max", f"{df_filtre['temperature_max'].max():.1f} °C")
    col3.metric("Precipitation max", f"{df_filtre['precipitation'].max():.1f} mm")

    nb_risque = df_filtre[df_filtre["risk_category"].isin(["Eleve", "Critique"])].shape[0]
    col4.metric("Periodes a risque (Eleve/Critique)", nb_risque)

    ville_plus_risquee = df_filtre.loc[df_filtre["risk_score"].idxmax(), "city_name"]
    col5.metric("Ville la plus a risque", ville_plus_risquee)

    st.divider()

    # ---- Carte des villes, coloree par niveau de risque ----
    st.subheader("Carte du risque par ville")

    couleurs_risque = {
        "Faible": [46, 204, 113],
        "Modere": [241, 196, 15],
        "Eleve": [230, 126, 34],
        "Critique": [231, 76, 60],
    }
    df_carte = df_filtre.copy()
    df_carte["couleur"] = df_carte["risk_category"].map(couleurs_risque)

    st.map(
        df_carte.rename(columns={"lat": "latitude", "lng": "longitude"}),
        latitude="latitude",
        longitude="longitude",
        color="couleur",
        size=20000,
    )

    # ---- Graphique : evolution de la temperature par ville ----
    st.subheader("Evolution de la temperature max")

    if villes_selectionnees:
        df_temp = df_filtre.pivot_table(
            index="forecast_date", columns="city_name", values="temperature_max"
        )
        st.line_chart(df_temp)
    else:
        st.info("Selectionne une ou plusieurs villes dans les filtres pour voir le detail par ville.")

    # ---- Top villes les plus a risque ----
    st.subheader("Top 10 villes les plus a risque (score moyen)")
    top_risque = (
        df_filtre.groupby("city_name")["risk_score"]
        .mean()
        .sort_values(ascending=False)
        .head(10)
    )
    st.bar_chart(top_risque)

    st.divider()

    # ---- Tableau detaille ----
    st.subheader("Donnees detaillees")
    st.dataframe(
        df_filtre[
            [
                "city_name", "forecast_date", "temperature_max", "temperature_min",
                "precipitation", "wind_gusts_max", "risk_score", "risk_category",
            ]
        ].sort_values("risk_score", ascending=False)
    )


if __name__ == "__main__":
    main()