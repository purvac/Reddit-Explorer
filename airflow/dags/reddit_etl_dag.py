from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import PythonOperator
from airflow.utils.dates import days_ago
from datetime import timedelta, datetime

"""
DAG to run the python script src/extract.py
"""

# Output name of extracted file. This be passed to each
# DAG task so they know which file to process
output_name = datetime.now().strftime("%Y%m%d")

# Run our DAG daily and ensures DAG run will kick off
# once Airflow is started, as it will try to "catch up"
schedule_interval = "@daily"
start_date = days_ago(1)

default_args = {"owner": "airflow", "depends_on_past": False, "retries": 1, "start_date": days_ago(1), }

dag = DAG(
    dag_id="reddit_dag",
    description="Reddit DAG for ETL pipeline",
    schedule_interval=None,
    default_args=default_args,
    start_date=start_date,
    catchup=True,
    max_active_runs=1,
    tags=["RedditETL"],
)

run_script_task = BashOperator(
    task_id="run_extract_py_script", 
    bash_command=f"python /usr/local/airflow/src/extract.py",
    dag=dag,
    )

"""
Commands to run dag: 
1. docker compose up airflow-init
2. docker compose up --build 
    - The sequence docker-compose up airflow-init followed by docker-compose up -> explicitly ensure the initialization step happens first before the main Airflow components are started.
    - The first command ensures your database is set up.
    - The second command then brings up all the continuous Airflow services.

3. docker ps -> to check if containers are up
4. docker compose down --volumes --rmi all -> to stop and close all containers

"""
