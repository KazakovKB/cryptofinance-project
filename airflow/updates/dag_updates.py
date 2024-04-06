from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

default_args = {
    'owner': 'cryptofinance',
    'depends_on_past': False,
    'start_date': datetime(2024, 3, 30),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 0
}

dag = DAG('updates', default_args=default_args, schedule_interval='0 0 * * 1', catchup=False)

run_update_limit = BashOperator(
    task_id='update_limit',
    bash_command='python3 /opt/airflow/scripts/update_limit.py',
    dag=dag
)
