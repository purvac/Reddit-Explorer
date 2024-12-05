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

t1 = BashOperator(
    task_id="checkpoint_task_execution",
    bash_command="echo 'First print task completed!'",
    dag=dag,
)


run_script_task = BashOperator(
    task_id="run_extract_py_script", 
    bash_command=f"python /opt/airflow/src/extract_reddit_etl.py",
    dag=dag,
    )

run_script_task.set_upstream(t1)


