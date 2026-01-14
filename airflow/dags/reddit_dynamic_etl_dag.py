from airflow import DAG
from airflow.decorators import task
from airflow.utils.dates import days_ago
from datetime import datetime, timedelta, timezone
import os
import csv
import logging
import praw
import re
from dotenv import load_dotenv


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
EXTRACTION_DATE = "2026-01-13"

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
        extraction_date = EXTRACTION_DATE

        params = []
        for subreddit in SUBREDDITS:
            params.append(
                {
                    "subreddit": subreddit,
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
        date_time = datetime.utcfromtimestamp(submission.created_utc)
        writer.writerow([
            submission.id,
            remove_special_characters(submission.title),
            remove_special_characters(submission.selftext),
            date_time.date(),
            date_time.time(),
            submission.score,
            submission.upvote_ratio,
            submission.url,
        ])
        return None

    @task
    def extract_reddit_posts(subreddit: str, extraction_date: str):
        """
        Extracts Reddit posts for a single subreddit and date.
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
        subreddit_obj = reddit.subreddit(subreddit)

        filename = f"reddit-post-data-{subreddit}-{extraction_date}.csv"
        destination = os.path.join(BASE_OUTPUT_PATH, filename)

        try:
            with open(destination, "w", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(
                    [
                        "Post_ID",
                        "Title",
                        "Body",
                        "Date",
                        "Time",
                        "Score",
                        "Upvote_Ratio",
                        "URL",
                    ]
                )

                for submission in subreddit_obj.new():
                    post_date = datetime.fromtimestamp(
                        submission.created_utc, timezone.utc
                    ).date()

                    if post_date == extraction_date:
                        write_post_data(writer, submission)

        except Exception as e:
            logging.error(
                f"Extraction failed for subreddit={subreddit}, date={extraction_date}: {e}"
            )
            raise
        logging.info(
            f"Extraction completed for subreddit={subreddit}, date={extraction_date}"
        )

    extraction_params = generate_extraction_params()
    extract_reddit_posts.expand_kwargs(extraction_params)
