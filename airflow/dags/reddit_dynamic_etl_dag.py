from airflow import DAG
from airflow.decorators import task
from datetime import date, datetime, timedelta
import logging
 

SUBMISSION_PULL_LIMIT = 100
BASE_OUTPUT_PATH = "/opt/airflow/output"

SUBREDDITS = [
        "dataengineering",
        "learndatascience",
        "powerbi",
        "tableau",
        "analytics",
        "dataisbeautiful",
        "dataanalysis",
        ]

default_args = {
    "owner": "airflow",
    "retries": 1,
}

with DAG(
    dag_id="reddit_dynamic_etl_dag",
    description="Dynamic Reddit ETL DAG using task mapping",
    default_args=default_args,
    schedule_interval=None,
    start_date=datetime(2024, 6, 1),
    catchup=False,
    max_active_runs=1,
    tags=["RedditETL"],
) as dag:

    @task
    def generate_extraction_params():
        """
        Generates a list of dictionaries.
        Each dict represents one mapped task input.
        """
        start_date = end_date = date.today() - timedelta(days=2)
        # start_date = date(2025, 10, 1)
        # end_date = date(2025, 10, 5)
        extraction_dates = []
        while start_date <= end_date:
            extraction_dates.append({
                    "extraction_date": start_date.isoformat(),
                })
            start_date += timedelta(days=1)

        return extraction_dates 
    
    @task
    def extract_reddit_posts(extraction_date: str):
        """
        Calls the extract_posts function from data_processing_functions.py, which returns the filename of the extracted data.
        This filename is then pushed to XCom for the next task to consume.
        """
        from scripts.data_processing_functions import extract_posts

        logging.getLogger("praw").setLevel(logging.DEBUG)
        logging.getLogger("prawcore").setLevel(logging.DEBUG)

        filename = extract_posts(BASE_OUTPUT_PATH, SUBMISSION_PULL_LIMIT, SUBREDDITS, extraction_date)
        return filename  
     
    @task
    def push_file_to_s3(filename: str):
        """
        Calls the upload_to_s3 function from data_processing_functions.py, which uploads the given file to S3.
        """
        from scripts.data_processing_functions import upload_to_s3
        upload_to_s3(BASE_OUTPUT_PATH, filename)

    extraction_params = generate_extraction_params()
    filenames = extract_reddit_posts.expand_kwargs(extraction_params)
    push_file_to_s3.expand(filename=filenames)


    """
    Improvements to consider:
    - Implement data validation checks post-extraction.
    """