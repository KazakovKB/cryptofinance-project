from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

default_args = {
    'owner': 'cryptofinance',
    'depends_on_past': False,
    'start_date': datetime(2024, 4, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 0
}

dag = DAG('delete', default_args=default_args, schedule_interval='0 0 * * *', catchup=False)

run_delete_trades = BashOperator(
    task_id='delete_trades',
    bash_command='python3 /opt/airflow/scripts/delete_trades.py',
    dag=dag
)