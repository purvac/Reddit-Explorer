import praw
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv
import sys
import logging
import csv
from common.write_csv import write_post_data

#get client_id, client_secret, user_agent, username and password. Can't use praw.ini file since facing issues accessing praw.ini file in airflow run on docker
"""       
reddit = praw.Reddit("DEFAULT")
 """

SUBMISSION_PULL_LIMIT = 50
SUBREDDIT_NAME = "dataengineering"

def main(): 

  try:
    load_dotenv()
    
    reddit = praw.Reddit(
        client_id=os.getenv("client_id"),
        client_secret=os.getenv("client_secret"),
        user_agent=os.getenv("user_agent"),
        password=os.getenv("password"),
        username=os.getenv("username"),
    )
    
  except (praw.exceptions.ClientException, FileNotFoundError) as e:
    logging.error(f"Error configuring PRAW: {e}")
    return 

  # if reddit credentials are put in, below statement will be false since your reddit instance is not read only
  print(reddit.read_only)

  subreddit = reddit.subreddit(SUBREDDIT_NAME)

  yesterday_date = datetime.now(timezone.utc).date() - timedelta(days=1)
    
  filename = "reddit-post-data-" + str(yesterday_date) + ".csv"
  # the path below is the local path for the src folder in the docker container. 
  destination = "/usr/local/airflow/src/" + filename

  try:
      with open(destination, 'w', newline='') as csvfile:
          writer = csv.writer(csvfile)

          # Write header row only if file is empty
          if csvfile.tell() == 0:
              writer.writerow(['Post_ID', 'Title', 'Body', 'Date', 'Time', 'Score', 'Upvote Ratio', 'URL'])

          for submission in subreddit.new(limit=SUBMISSION_PULL_LIMIT):
              if datetime.date(datetime.fromtimestamp(submission.created_utc, timezone.utc)) == yesterday_date:
                  write_post_data(writer, submission)        

  except praw.exceptions.RedditAPIException as e:
      logging.error(f"API Error: {e}")
  except Exception as e:
      logging.error(f"An unexpected error occurred: {e}")
    
  return 0


if __name__ == "__main__":
    sys.exit(main())
