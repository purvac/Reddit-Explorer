#from fileinput import filename
import pandas as pd
from airflow import DAG
from airflow.decorators import task
from airflow.utils.dates import days_ago
from datetime import date, datetime, timedelta, timezone
import os
import csv
import logging
import praw
import re
import boto3
from dotenv import load_dotenv
from botocore.exceptions import ClientError


#from common.write_csv import write_post_data

SUBREDDITS = [
    "dataengineering",
    "learndatascience",
    "powerbi",
    "tableau",
    "analytics",
    "dataisbeautiful",
    "dataanalysis",
]

SUBMISSION_PULL_LIMIT = 50
BASE_OUTPUT_PATH = "/usr/local/airflow/src"

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

        start_date = date(2026, 1, 1)
        end_date = date(2026, 1, 3)
        extraction_dates = []
        while start_date <= end_date:
            extraction_dates.append(start_date.isoformat())
            start_date += timedelta(days=1)

        params = []
        for extraction_date in extraction_dates:
            params.append(
                {
                    "extraction_date": extraction_date,
                }
            )

        return params
    
    def remove_special_characters(text: str) -> str:
        pattern = r'[^a-zA-Z0-9\s]'
        return re.sub(pattern, '', text)

    def write_post_data(writer: object, submission: object):
        """
        Writes a single post's data to the CSV file.
        """
        date_time = datetime.fromtimestamp(submission.created_utc, timezone.utc)
        
        # Extract body text, handling crossposts
        body = remove_special_characters(submission.selftext)
        if "crosspost_parent" in vars(submission):
            body = submission.crosspost_parent_list[0]['selftext']

        writer.writerow([
            submission.id,
            submission.subreddit, 
            remove_special_characters(submission.title),
            body,
            submission.author, 
            date_time.date(),
            date_time.time(),
            submission.score,
            submission.upvote_ratio,
            submission.num_comments,
            "https://reddit.com" + submission.permalink,
        ])
        return None

    @task
    def extract_reddit_posts(extraction_date: str):
        """
        Extracts Reddit posts for a single date.
        """
        extraction_date = datetime.fromisoformat(extraction_date).date()

        # Load credentials
        load_dotenv()

        try:
            reddit = praw.Reddit(
                client_id=os.getenv("client_id"),
                client_secret=os.getenv("client_secret"),
                user_agent=os.getenv("user_agent"),
                password=os.getenv("password"),
                username=os.getenv("username"),
            )
        except Exception as e:
            logging.error(f"Failed to initialize Reddit client: {e}")
            raise
        logging.info("Reddit client initialized successfully.")

        filename = f"reddit-post-data-{extraction_date}.csv"
        destination = os.path.join(BASE_OUTPUT_PATH, filename)

        try:
            with open(destination, "w", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(
                    [
                        "Post_ID",
                        "Subreddit",
                        "Title",
                        "Body",
                        "Author", 
                        "Date",
                        "Time",
                        "Score",
                        "Upvote_Ratio",
                        "Number_of_Comments",
                        "URL",
                    ]
                )
                for subreddit in SUBREDDITS:
                    subreddit_obj = reddit.subreddit(subreddit)

                    for submission in subreddit_obj.new():
                        post_date = datetime.fromtimestamp(submission.created_utc, timezone.utc).date()

                        if post_date == extraction_date:
                            write_post_data(writer, submission)
                    logging.info(f"Extracted posts for subreddit={subreddit}, date={extraction_date}")

        except Exception as e:
            logging.error(
                f"Extraction failed for date={extraction_date}: {e}"
            )
            raise
        logging.info(
            f"Extraction completed for date={extraction_date}"
        )
        os.chdir("..")
        os.chdir(BASE_OUTPUT_PATH)
        df = pd.read_csv(filename)
        df.to_parquet(filename.strip(".csv") + ".parquet", engine='pyarrow', index=False)
        
        filename = filename.strip(".csv") + ".parquet"

        logging.info(f"Parquet file created: {filename}")

        #return filename

    #@task
    #def push_file_to_s3(filename: str):
        session = boto3.Session()
        logging.info(f"AWS Session initialized successfully.")

        s3_client = boto3.client('s3')
        
        try:
            response = s3_client.upload_file(filename, "reddit-explorer-bucket", filename)
        except ClientError as e:
            logging.error(e)
        logging.info("Upload Successful")
        return None

    extraction_params = generate_extraction_params()
    extract_reddit_posts.expand_kwargs(extraction_params)
    """
    filename = extract_reddit_posts.expand_kwargs(extraction_params)
    push_file_to_s3(filename)
    """