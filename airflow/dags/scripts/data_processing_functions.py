import pandas as pd
from airflow import DAG
from airflow.decorators import task
from airflow.utils.dates import days_ago
from datetime import date, datetime, timezone
import os
import csv
import logging
import praw
import re
import boto3
import prawcore
from dotenv import load_dotenv
from botocore.exceptions import ClientError

def extract_posts(base_output_path, submission_pull_limit, subreddits, extraction_date: str): 
    """
    Extracts Reddit posts for a single date.
    """
    from scripts.data_processing_functions import write_post_data
    
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
        reddit.user.me()
        logging.info("Reddit client authenticated successfully.")

    except prawcore.exceptions.Unauthorized as e:
        log_reddit_api_error(e)
        raise

    except Exception as e:
        logging.error(f"Failed to initialize Reddit client: {e}")
        raise

    filename = f"reddit-post-data-{extraction_date}.csv"
    destination = os.path.join(base_output_path, filename)

    try:
        with open(destination, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(
                [
                    "POST_ID",
                    "SUBREDDIT",
                    "POST_TITLE",
                    "POST_BODY",
                    "POST_AUTHOR", 
                    "POST_DATE",
                    "POST_TIME",
                    "POST_SCORE",
                    "POST_UPVOTE_RATIO",
                    "POST_NUMBER_OF_COMMENTS",
                    "POST_INDEXABLE",
                    "POST_URL"
                ]
            )
    
            for subreddit in subreddits:
                logging.info(f"Starting extraction for subreddit={subreddit}, date={extraction_date}")

                subreddit_obj = reddit.subreddit(subreddit)
                submission_count = 0
                
                for submission in subreddit_obj.new(limit=submission_pull_limit):
                    post_date = datetime.fromtimestamp(submission.created_utc, timezone.utc).date()

                    if post_date == extraction_date:
                        write_post_data(writer, submission)
                        submission_count += 1

                logging.info(f"Extracted posts for subreddit={subreddit}, date={extraction_date}, extracted_count={submission_count}")

        
    except prawcore.exceptions.TooManyRequests as e:
        log_reddit_api_error(e, subreddit)
        raise  # Fail fast so Airflow retries properly

    except prawcore.exceptions.Forbidden as e:
        log_reddit_api_error(e, subreddit)
        raise  # Skip this subreddit, continue others

    except prawcore.exceptions.PrawcoreException as e:
        log_reddit_api_error(e, subreddit)
        raise

    except Exception as e:
        logging.error(
            f"[UNEXPECTED ERROR] Extraction failed for subreddit={subreddit} date={extraction_date}: {e}"
        )
        raise
    logging.info(
        f"Extraction completed for date={extraction_date}"
    )

    os.chdir("..")
    os.chdir(base_output_path)
    df = pd.read_csv(filename)

    if df.empty:
        logging.warning(
            f"[EMPTY OUTPUT] No posts extracted for date={extraction_date}. "
            f"This may indicate API access issues or no matching posts."
        )

    df.to_parquet(filename.strip(".csv") + ".parquet", engine='pyarrow', index=False)
    
    filename = filename.strip(".csv") + ".parquet"

    logging.info(f"Parquet file created: {filename}")

    return filename

def remove_special_characters(text: str) -> str:
    """
    Removes special characters from the given text, leaving only alphanumeric characters and spaces.
    """
    pattern = r'[^a-zA-Z0-9\s]'
    return re.sub(pattern, '', text)

def write_post_data(writer: object, submission: object):
    """
    Writes a single post's data to the CSV file.
    """
    date_time = datetime.fromtimestamp(submission.created_utc, timezone.utc)
    
    # Extract body text, handling crossposts
    if "crosspost_parent" in vars(submission):
        body = submission.crosspost_parent_list[0]['selftext']

    writer.writerow([
        submission.id,
        submission.subreddit, 
        remove_special_characters(submission.title),
        remove_special_characters(submission.selftext), #body
        submission.author, 
        date_time.date(),
        date_time.time(),
        submission.score,
        submission.upvote_ratio,
        submission.num_comments,
        submission.is_robot_indexable,
        "https://reddit.com" + submission.permalink,
    ])
    return None

def upload_to_s3(base_output_path, filename: str):
    os.chdir(base_output_path)
    logging.info(f"Preparing to upload file to S3: {filename}, current_dir={os.getcwd()}")
    session = boto3.Session()
    logging.info(f"AWS Session initialized successfully.")
    s3_client = boto3.client('s3')
    try:
        response = s3_client.upload_file(str(filename), "reddit-explorer-bucket", filename)
    except ClientError as e:
        logging.error(e)
    logging.info("Upload Successful")
    return None

def log_reddit_api_error(error: Exception, subreddit: str | None = None):
    subreddit_info = f" subreddit={subreddit}" if subreddit else ""

    if isinstance(error, prawcore.exceptions.Forbidden):
        logging.error(
            f"[403 FORBIDDEN]{subreddit_info} – Access denied. "
            f"Likely causes: invalid credentials, bad user-agent, or restricted subreddit."
        )

    elif isinstance(error, prawcore.exceptions.TooManyRequests):
        logging.error(
            f"[429 RATE LIMITED]{subreddit_info} – Too many requests. "
            f"Backoff or reduce parallelism."
        )


    elif isinstance(error, prawcore.exceptions.NotFound):
        logging.error(
            f"[404 NOT FOUND]{subreddit_info} – Subreddit does not exist or is private."
        )

    elif isinstance(error, prawcore.exceptions.ResponseException):
        status = getattr(error.response, "status_code", "UNKNOWN")
        logging.error(
            f"[HTTP {status}]{subreddit_info} – Reddit API response error: {error}"
        )

    else:
        logging.error(
            f"[UNKNOWN REDDIT ERROR]{subreddit_info}: {error}"
        )
    return None

