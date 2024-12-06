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
        writer.writerow(['Post_ID', 'Title', 'Body', 'Title', 'Number of Upvotes', 'Upvote Ratio', 'URL'])
        for post_id in new_posts:
            print(f"Post ID: {post_id}")
            submission = reddit.submission(id=post_id)
            print(f"Title: {submission.title}")
            print(f"Selftext: {submission.selftext}")
            print(f"Time: {datetime.utcfromtimestamp(submission.created_utc)}")
            print(f"Upvotes: {submission.score}")
            print(f"Upvote Ratio: {submission.upvote_ratio}") 
            #submission upvote ratio - need to read more - https://www.reddit.com/r/redditdev/comments/6abuk3/how_can_i_use_praw_to_get_number_of_votes_and/
            print(f"url: {submission.url}")
            writer.writerow([post_id, submission.title, submission.selftext, datetime.utcfromtimestamp(submission.created_utc), submission.score, submission.upvote_ratio, submission.url])

except praw.exceptions.RedditAPIException as e:
    print(f"API Error: {e}")
except Exception as e:
    print(f"An error occurred: {e}")
    
#NOTES: 
#check if any other parameter needs to be pulled for the post
#divide time to date and time - maybe convert to CT or keep in UTC?
#filter post by previous date
#check what data structure can be used to also pull in all the comments for each of the posts