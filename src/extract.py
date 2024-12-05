import praw
from datetime import datetime
import csv

SUBMISSION_PULL_LIMIT = 10

# Configure PRAW with credentials from praw.ini file
reddit = praw.Reddit(config_file='praw.ini')

# Subreddit name
subreddit_name = "dataengineering"
subreddit = reddit.subreddit(subreddit_name)

try:
    new_posts = subreddit.new(limit=SUBMISSION_PULL_LIMIT)
    with open('reddit_posts.csv', 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Post_ID', 'Title', 'Body', 'Title'])
        for post_id in new_posts:
            print(f"Post ID: {post_id}")
            submission = reddit.submission(id=post_id)
            print(f"Title: {submission.title}")
            print(f"Selftext: {submission.selftext}")
            print(f"Time: {datetime.utcfromtimestamp(submission.created_utc)}")
            writer.writerow([post_id, submission.title, submission.selftext, datetime.utcfromtimestamp(submission.created_utc)])

except praw.exceptions.RedditAPIException as e:
    print(f"API Error: {e}")
except Exception as e:
    print(f"An error occurred: {e}")