import praw
from datetime import datetime
from datetime import timedelta
import csv
from common.data_cleaning import remove_special_characters

SUBMISSION_PULL_LIMIT = 50
SUBREDDIT_NAME = "dataengineering"

# Configure PRAW with credentials from praw.ini file
reddit = praw.Reddit(config_file='praw.ini')

subreddit = reddit.subreddit(SUBREDDIT_NAME)

try:
    new_posts = subreddit.new(limit=SUBMISSION_PULL_LIMIT)
    submission_counter = 0; 
    yesterday_date = datetime.date(datetime.utcnow()) - timedelta(days=1)
    with open('reddit_posts.csv', 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Post_ID', 'Title', 'Body', 'Date', 'Time', 'Score', 'Upvote Ratio', 'URL'])
        for post_id in new_posts:
            submission = reddit.submission(id=post_id)
            date_time = datetime.utcfromtimestamp(submission.created_utc)
            if( datetime.date(date_time) == yesterday_date): 
                writer.writerow([post_id, remove_special_characters(submission.title), remove_special_characters(submission.selftext), datetime.date(date_time), datetime.time(date_time), submission.score, submission.upvote_ratio, submission.url])
            
            #------------- PRINT STATEMENTS FOR ALL DATA -------------
            #print(f"Post ID: {post_id}")
            #print(f"Title: {submission.title}")
            #print(f"Selftext: {submission.selftext}")
            #print(f"Date: {datetime.date(date_time)}")
            #print(f"Time: {datetime.time(date_time)}")
            #print(f"Score: {submission.score}")
            #print(f"Upvote Ratio: {submission.upvote_ratio}") 
            #print(f"url: {submission.url}")
            #-----------------------------------------------------------------
            
            #Calculate number of upvotes and downvotes using this table - https://www.reddit.com/r/TheoryOfReddit/comments/dcz833/a_simple_way_to_estimate_up_and_down_votes/

                
except praw.exceptions.RedditAPIException as e:
    print(f"API Error: {e}")
except Exception as e:
    print(f"An error occurred: {e}")
    
#NOTES: 
#divide time to date and time - maybe convert to CT or keep in UTC?
#filter post by previous date
#check what data structure can be used to also pull in all the comments for each of the posts