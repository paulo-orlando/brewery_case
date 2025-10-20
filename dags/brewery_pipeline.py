from datetime import datetime, timedelta
import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
from airflow.operators.bash import BashOperator
from airflow.utils.task_group import TaskGroup

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
    schedule_interval='@daily',  # or '0 2 * * *' to run at 2am
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

# Task 2.5: Clean existing Silver data before transformation
clean_silver_task = BashOperator(
    task_id='clean_silver_layer',
    bash_command='rm -rf /opt/airflow/data/silver/breweries && mkdir -p /opt/airflow/data/silver/breweries',
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

# Task 4: Data Quality Check (Quality Gate before Gold)
quality_check = PythonOperator(
    task_id='data_quality_check',
    python_callable=check_data_quality,
    op_kwargs={
        'input_path': '/opt/airflow/data/silver/breweries',
        'layer': 'silver',
    },
    dag=dag,
)

# Task 5: Create Gold Aggregations
gold_task = PythonOperator(
    task_id='create_gold_aggregations',
    python_callable=create_gold_aggregations,
    op_kwargs={
        'input_path': '/opt/airflow/data/silver/breweries',
        'output_path': '/opt/airflow/data/gold/breweries_by_type_location',
    },
    dag=dag,
)

# Define dependencies (Quality Check acts as a gate between Silver and Gold)
extract_task >> bronze_task >> clean_silver_task >> silver_task >> quality_check >> gold_task