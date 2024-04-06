from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

default_args = {
    'owner': 'cryptofinance',
    'depends_on_past': False,
    'start_date': datetime(2024, 3, 28),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 0
}

dag = DAG('news', default_args=default_args, schedule_interval='*/5 * * * *', catchup=False)

run_get_news = BashOperator(
    task_id='get_news',
    bash_command='python3 /opt/airflow/scripts/getNews.py',
    dag=dag,
)

run_news_letter = BashOperator(
    task_id='news_letter',
    bash_command='python3 /opt/airflow/scripts/newsLetter.py',
    dag=dag,
)

run_get_news >> run_news_letter

