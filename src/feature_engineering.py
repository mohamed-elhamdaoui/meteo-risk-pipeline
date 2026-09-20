import pandas as pd


def load_silver(path="data/silver/weather_clean.csv"):
    df = pd.read_csv(path, encoding="utf-8")
    df["date"] = pd.to_datetime(df["date"])
    return df


def linear_score(value, low, high):
    """
    Transforme une valeur en sous-score 0-100 par interpolation lineaire.
    - value <= low  -> 0   (aucun risque)
    - value >= high -> 100 (risque maximal)
    - entre les deux -> interpolation proportionnelle
    """
    if value <= low:
        return 0
    if value >= high:
        return 100
    return (value - low) / (high - low) * 100


def categorize_temperature(temp_max):
    """Categorise la temperature max en 4 niveaux."""
    if temp_max < 15:
        return "Froid"
    elif temp_max < 30:
        return "Normal"
    elif temp_max < 38:
        return "Chaud"
    else:
        return "Extreme"


def categorize_precipitation(precip_sum):
    """Categorise le cumul de precipitation en 4 niveaux."""
    if precip_sum < 1:
        return "Sec"
    elif precip_sum < 10:
        return "Faible"
    elif precip_sum < 30:
        return "Moderee"
    else:
        return "Forte"


def categorize_wind(wind_gusts):
    """Categorise les rafales de vent en 4 niveaux."""
    if wind_gusts < 20:
        return "Calme"
    elif wind_gusts < 40:
        return "Modere"
    elif wind_gusts < 60:
        return "Fort"
    else:
        return "Tempete"


def categorize_risk(score):
    """Categorise le score de risque final en 4 niveaux."""
    if score < 30:
        return "Faible"
    elif score < 60:
        return "Modere"
    elif score < 80:
        return "Eleve"
    else:
        return "Critique"


def compute_risk_score(row):
    """
    Calcule le score de risque meteo (0-100) pour une ligne, a partir de
    3 sous-scores ponderes : precipitation (40%), vent (35%), temperature (25%).

    Seuils utilises (justifies dans la documentation du projet) :
    - temperature_max : 0 en dessous de 30C, 100 a partir de 45C
    - precipitation   : 0 en dessous de 1mm, 100 a partir de 50mm
    - vent (rafales)  : 0 en dessous de 30km/h, 100 a partir de 90km/h
    """
    temp_score = linear_score(row["temperature_max"], low=30, high=45)
    precip_score = linear_score(row["precipitation"], low=1, high=50)
    wind_score = linear_score(row["wind_gusts_max"], low=30, high=90)

    final_score = precip_score * 0.40 + wind_score * 0.35 + temp_score * 0.25

    return round(final_score, 1)


def add_features(df):

    df["temp_category"] = df["temperature_max"].apply(categorize_temperature)
    df["precip_category"] = df["precipitation"].apply(categorize_precipitation)
    df["wind_category"] = df["wind_gusts_max"].apply(categorize_wind)

    df["risk_score"] = df.apply(compute_risk_score, axis=1)
    df["risk_category"] = df["risk_score"].apply(categorize_risk)

    return df


def run_gold():
    """Pipeline complet Silver -> Gold. Renvoie le DataFrame final."""
    df = load_silver()
    df = add_features(df)

    df.to_csv("data/gold/weather_risk.csv", index=False, encoding="utf-8")
    print(f"Gold terminee : {len(df)} lignes.")
    print(f"Repartition des niveaux de risque :\n{df['risk_category'].value_counts()}")

    return df


if __name__ == "__main__":
    df = run_gold()
    print(
        df[
            [
                "city",
                "date",
                "temperature_max",
                "precipitation",
                "wind_gusts_max",
                "risk_score",
                "risk_category",
            ]
        ].head(10)
    )
