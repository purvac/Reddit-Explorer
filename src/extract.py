import praw
from datetime import datetime
#get client_id, client_secret, user_agent, username and password from praw.ini file
#More information on configuring praw.ini files given here - https://praw.readthedocs.io/en/stable/getting_started/configuration/prawini.html
reddit = praw.Reddit("DEFAULT") 

# if reddit credentials are put in, below statement will be false since your reddit instance is not read only
print(reddit.read_only)


subreddit_name = "dataengineering"
subreddit = reddit.subreddit(subreddit_name)

n_of_posts = 0
try: 
    new_posts = subreddit.new(limit=10)
    for post_id in new_posts: 
        #n_of_posts = n_of_posts + 1
        print(f"Post ID: {post_id}")
        submission = reddit.submission(id=post_id)
        print(f"# of comments: {submission.num_comments}")
        
        # Expand all comments and remove 'MoreComments' objects
        submission.comments.replace_more(limit=None)
        for comment in submission.comments.list(): 
            print(f"Comment ID: {comment.id} Comment time: {datetime.utcfromtimestamp(comment.created_utc)}")
        print("\n")
        
        #print(f"Title: {submission.title} | Score:{submission.score} | Created At: {datetime.utcfromtimestamp(submission.created_utc)} | Number of comments: {submission.num_comments} | Text: {submission.selftext}")
        # the most activity would be measured for new items which receive most number of comments
        # can we find the time a comment was posted to a post? 
        #That way we can find the time when most comments are posted
        #print(f"Post ID: {post_id} Created At: {datetime.utcfromtimestamp(submission.created_utc)} Number of comments: {submission.num_comments}")
except Exception as e: 
    print(f"An error occurred: {e}")
    print("Total number of posts: " + n_of_posts)