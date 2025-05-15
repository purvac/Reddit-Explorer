from common.data_cleaning import remove_special_characters
from datetime import datetime

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