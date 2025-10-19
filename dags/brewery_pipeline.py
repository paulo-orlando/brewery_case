from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
from airflow.utils.task_group import TaskGroup

# Importar suas funções dos módulos src
from src.api.brewery_api import fetch_brewery_data
from src.bronze.bronze_layer import save_to_bronze
from src.silver.silver_layer import transform_to_silver
from src.gold.gold_layer import create_gold_aggregations
from src.common.data_quality import check_data_quality

default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(hours=1),
}

dag = DAG(
    'brewery_pipeline',
    default_args=default_args,
    description='Pipeline for brewery data - Medallion Architecture',
    schedule_interval='@daily',  # ou '0 2 * * *' para rodar às 2h da manhã
    catchup=False,
    tags=['brewery', 'medallion', 'data-lake'],
)

# Task 1: Extract data from API
extract_task = PythonOperator(
    task_id='extract_brewery_data',
    python_callable=fetch_brewery_data,
    op_kwargs={
        'base_url': 'https://api.openbrewerydb.org/v1/breweries',
        'output_path': '/opt/airflow/data/raw/{{ ds }}',
    },
    dag=dag,
)

# Task 2: Load to Bronze Layer
bronze_task = PythonOperator(
    task_id='load_to_bronze',
    python_callable=save_to_bronze,
    op_kwargs={
        'input_path': '/opt/airflow/data/raw/{{ ds }}',
        'output_path': '/opt/airflow/data/bronze/breweries/{{ ds }}',
    },
    dag=dag,
)

# Task 3: Transform to Silver Layer
silver_task = PythonOperator(
    task_id='transform_to_silver',
    python_callable=transform_to_silver,
    op_kwargs={
        'input_path': '/opt/airflow/data/bronze/breweries/{{ ds }}',
        'output_path': '/opt/airflow/data/silver/breweries',
        'partition_cols': ['country', 'state'],
    },
    dag=dag,
)

# Task 4: Create Gold Aggregations
gold_task = PythonOperator(
    task_id='create_gold_aggregations',
    python_callable=create_gold_aggregations,
    op_kwargs={
        'input_path': '/opt/airflow/data/silver/breweries',
        'output_path': '/opt/airflow/data/gold/breweries_by_type_location',
    },
    dag=dag,
)

# Task 5: Data Quality Checks
quality_check = PythonOperator(
    task_id='data_quality_check',
    python_callable=check_data_quality,
    op_kwargs={
        'input_path': '/opt/airflow/data/silver/breweries',
        'layer': 'silver',
    },
    dag=dag,
)

# Define dependencies
extract_task >> bronze_task >> silver_task >> gold_task >> quality_check