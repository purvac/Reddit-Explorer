import praw
import csv
import sys
import logging

from datetime import datetime, timedelta
from common.write_csv import write_post_data


SUBMISSION_PULL_LIMIT = 50
SUBREDDIT_NAME = "dataengineering"


def main():

    # Configure PRAW with credentials from praw.ini file
    try:
        reddit = praw.Reddit(config_file='praw.ini')
    except (praw.exceptions.ClientException, FileNotFoundError) as e:
        logging.error(f"Error configuring PRAW: {e}")
        return 

    subreddit = reddit.subreddit(SUBREDDIT_NAME)

    yesterday_date = datetime.date(datetime.utcnow()) - timedelta(days=1)
    
    filename = "reddit-post-data-" + str(yesterday_date) + ".csv"

    try:
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header row only if file is empty
            if csvfile.tell() == 0:
                writer.writerow(['Post_ID', 'Title', 'Body', 'Date', 'Time', 'Score', 'Upvote Ratio', 'URL'])

            for submission in subreddit.new(limit=SUBMISSION_PULL_LIMIT):
                if datetime.date(datetime.utcfromtimestamp(submission.created_utc)) == yesterday_date:
                    write_post_data(writer, submission)

    except praw.exceptions.RedditAPIException as e:
        logging.error(f"API Error: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
    
    return 0
        

if __name__ == "__main__":
    sys.exit(main())