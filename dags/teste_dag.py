from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from src.fetch.api_client import fetch_breweries
from src.silver.transform import silver_upsert
from src.gold.aggregate import aggregate_gold


defaul_args = {
    'owner': 'data_eng',
    'depends_on_past': False,
    'retries': 3,
    'retry_delay': timedelta(seconds=30),
    'email_on_failure': True,
}


dag = DAG(
    'brewery_incremental',
    default_args=defaul_args,
    description='Incremental load Open Brewery DB to Delta Lake with Gold aggregation',
    schedule_interval='@daily',
    start_date=datetime(2025, 10, 19),
    catchup=False
)


fetch_task = PythonOperator(
    task_id='fetch_breweries',
    python_callable=fetch_breweries,
    dag=dag
)


silver_task = PythonOperator(
    task_id='silver_upsert',
    python_callable=silver_upsert,
    dag=dag
)


gold_task = PythonOperator(
    task_id='aggregate_gold',
    python_callable=aggregate_gold,
    dag=dag
)


fetch_task >> silver_task >> gold_task