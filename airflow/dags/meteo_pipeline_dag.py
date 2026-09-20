from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

# Les fonctions du pipeline sont importees directement.
# __main__ de chaque script ne s'execute jamais ici : seules les fonctions
# run_xxx() sont appelees, dans l'ordre defini par le DAG.
from src.extraction import run_extraction
from src.transformation import run_transformation
from src.feature_engineering import run_gold
from src.load_postgres import run_load

default_args = {
    "owner": "mohamed",
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="meteo_risk_pipeline",
    description="Pipeline complet : extraction Open-Meteo -> nettoyage -> risque -> PostgreSQL",
    default_args=default_args,
    schedule="@daily",
    start_date=datetime(2026, 9, 1),
    catchup=False,
    tags=["meteo", "risque", "pipeline"],
) as dag:

    task_extraction = PythonOperator(
        task_id="extraction_bronze",
        python_callable=run_extraction,
    )

    task_transformation = PythonOperator(
        task_id="transformation_silver",
        python_callable=run_transformation,
    )

    task_gold = PythonOperator(
        task_id="feature_engineering_gold",
        python_callable=run_gold,
    )

    task_load = PythonOperator(
        task_id="load_postgres",
        python_callable=run_load,
    )

    # Ordre d'execution : chaque etape attend que la precedente reussisse
    task_extraction >> task_transformation >> task_gold >> task_load
