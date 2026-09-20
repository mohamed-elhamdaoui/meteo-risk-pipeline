-- ============================================================
-- Schema : Pipeline Meteo-Risque
-- 2 tables normalisees : cities (statique) / weather_forecasts (mise a jour)
-- ============================================================

-- Table des villes : une ligne par ville, jamais dupliquee
CREATE TABLE IF NOT EXISTS cities (
    city_id     SERIAL PRIMARY KEY,
    city_name   VARCHAR(100) NOT NULL UNIQUE,
    lat         FLOAT NOT NULL,
    lng         FLOAT NOT NULL
);

-- Table des previsions : une ligne par ville par jour
CREATE TABLE IF NOT EXISTS weather_forecasts (
    forecast_id                 SERIAL PRIMARY KEY,
    city_id                     INTEGER NOT NULL REFERENCES cities(city_id),
    forecast_date               DATE NOT NULL,

    temperature_max             FLOAT,
    temperature_min             FLOAT,
    precipitation               FLOAT,
    precipitation_probability   INTEGER,
    wind_speed_max               FLOAT,
    wind_gusts_max               FLOAT,
    weather_code                INTEGER,

    temp_category               VARCHAR(20),
    precip_category              VARCHAR(20),
    wind_category                VARCHAR(20),

    risk_score                   FLOAT,
    risk_category                 VARCHAR(20),

    UNIQUE (city_id, forecast_date)
);

-- Index pour accelerer les requetes frequentes (filtrage par date, tri par risque)
CREATE INDEX IF NOT EXISTS idx_forecasts_date ON weather_forecasts(forecast_date);
CREATE INDEX IF NOT EXISTS idx_forecasts_risk ON weather_forecasts(risk_score DESC);



SELECT current_database();

-- DROP TABLE cities;

SELECT * from cities

TRUNCATE TABLE weather_forecasts, cities RESTART IDENTITY CASCADE;


SELECT city_name FROM cities WHERE city_name LIKE 'F%s';


SELECT city_name FROM cities WHERE city_name LIKE 'F%s';


SELECT encode(city_name::bytea, 'hex') 
FROM cities 
WHERE city_name LIKE 'F%s' 
LIMIT 1;


SELECT city_name FROM cities WHERE city_name LIKE 'F%s';
SELECT COUNT(*) FROM cities;