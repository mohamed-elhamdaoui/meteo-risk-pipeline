-- 1. Villes avec les temperatures les plus elevees
SELECT c.city_name, wf.forecast_date, wf.temperature_max
FROM weather_forecasts wf
JOIN cities c ON c.city_id = wf.city_id
ORDER BY wf.temperature_max DESC
LIMIT 10;


-- 2. Villes avec les plus fortes precipitations
SELECT c.city_name, wf.forecast_date, wf.precipitation
FROM weather_forecasts wf
JOIN cities c ON c.city_id = wf.city_id
ORDER BY wf.precipitation DESC
LIMIT 10;


-- 3. Villes avec le risque moyen le plus eleve (sur les 7 jours)
SELECT c.city_name, ROUND(AVG(wf.risk_score)::numeric, 1) AS avg_risk
FROM weather_forecasts wf
JOIN cities c ON c.city_id = wf.city_id
GROUP BY c.city_name
ORDER BY avg_risk DESC
LIMIT 10;


-- 4. Periodes (dates) avec le risque maximal, toutes villes confondues
SELECT wf.forecast_date, ROUND(AVG(wf.risk_score)::numeric, 1) AS avg_risk_ce_jour
FROM weather_forecasts wf
GROUP BY wf.forecast_date
ORDER BY avg_risk_ce_jour DESC;


-- 5. Pour chaque ville, quelle periode presente le plus grand risque
--    (bonus : fonction de fenetrage RANK())
SELECT city_name, forecast_date, risk_score
FROM (
    SELECT
        c.city_name,
        wf.forecast_date,
        wf.risk_score,
        RANK() OVER (PARTITION BY c.city_name ORDER BY wf.risk_score DESC) AS rang
    FROM weather_forecasts wf
    JOIN cities c ON c.city_id = wf.city_id
) sous_requete
WHERE rang = 1
ORDER BY risk_score DESC;