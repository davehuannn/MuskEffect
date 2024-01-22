import os
import json
from requests_oauthlib import OAuth1Session
import requests
import logging
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Create a timestamp for the log file name
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file_name = f"log_{timestamp}.log"

# Specify the directory where you want to save the log file
log_directory = 'filepath' # eg. /user/kenneth/documents/logs

# Specify the full path for the log file
log_file_path = os.path.join(log_directory, log_file_name)

# Configure the logging system
logging.basicConfig(filename=log_file_path, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Twitter OAuth 1.0a credentials
# Set up your Twitter API credentials
consumer_key = 'xxxxxxx'
consumer_secret = 'xxxxxxx'
access_token = 'xxxxxx'
access_token_secret = 'xxxxxx'

# CoinMarketCap API
api_key = 'xxxxxx-xxxxxx-xxxxxx-xxxxxx'  # Replace with your actual API key
url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/map'

def create_url():
    # Replace with user ID below
    # Elon Musk USER ID
    user_id = 44196397
    return "https://api.twitter.com/2/users/{}/tweets".format(user_id)

def get_params():
    # Tweet fields are adjustable.
    # Options include:
    # attachments, author_id, context_annotations,
    # conversation_id, created_at, entities, geo, id,
    # in_reply_to_user_id, lang, non_public_metrics, organic_metrics,
    # possibly_sensitive, promoted_metrics, public_metrics, referenced_tweets,
    # source, text, and withheld
    return {"tweet.fields": "created_at"}

def oauth1_authorization():
    return OAuth1Session(
        client_key=consumer_key,
        client_secret=consumer_secret,
        resource_owner_key=access_token,
        resource_owner_secret=access_token_secret,
    )

def connect_to_endpoint(url, params, auth):
    response = auth.get(url, params=params)
    print(response.status_code)
    # logging.debug(response.status_code)
    if response.status_code != 200:
        try:
            error_message = response.json()["detail"]
        except (KeyError, IndexError):
            error_message = response.text
        raise Exception(
            "Request returned an error: {} {}".format(
                response.status_code, error_message
            )
        )
    return response.json()

# CoinMarketCap 
# ------------------------------------------------------------------------------------------------
headers = {
    'Accepts': 'application/json',
    'X-CMC_PRO_API_KEY': api_key,
}

response = requests.get(url, headers=headers)
data = response.json()

# Extract names and store in a list
# crypto_names = [crypto['name'] for crypto in data['data']]
crypto_list = [{'id': crypto['id'], 'name': crypto['name']} for crypto in data['data']]
# ------------------------------------------------------------------------------------------------

# Email 
# ------------------------------------------------------------------------------------------------
def send_email(subject, body, to_address, attachment_path):
    # Set up the email server
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    smtp_username = 'xxxxx@gmail.com'  # Replace with your Gmail email address
    smtp_password = 'xxxxx xxxxx xxxxx'   # Replace with your Gmail app password

    # Set up the email message
    msg = MIMEMultipart()
    msg['From'] = smtp_username
    msg['To'] = to_address
    msg['Subject'] = subject

    # Attach the log file
    with open(attachment_path, 'r') as attachment:  # Open the file in text mode ('r')
        attachment_part = MIMEText(attachment.read(), _subtype='plain')
        attachment_part.add_header('Content-Disposition', 'attachment', filename=os.path.basename(attachment_path))
        msg.attach(attachment_part)

    # Add the email body
    msg.attach(MIMEText(body, 'plain'))

    # Connect to the SMTP server and send the email
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(smtp_username, to_address, msg.as_string())
# ------------------------------------------------------------------------------------------------

def main():
    url = create_url()
    params = get_params()
    auth = oauth1_authorization()
    json_response = connect_to_endpoint(url, params, auth)

    # List for Individual Words + Original Text + Create Timestamp
    # ----------------------------------------------------------------------------------
    # Create a dictionary to map words to their original tweets and timestamps
    words_to_tweets = {}
    for tweet in json_response.get("data", []):
        tweet_text = tweet.get("text", "")
        created_at = tweet.get("created_at", "")
        words = tweet_text.lower().split()  # Convert to lowercase before splitting

        # Update the dictionary with words, their associated tweets, and timestamps
        for word in words:
            lowercase_word = word.lower()  # Convert word to lowercase
            if lowercase_word not in words_to_tweets:
                words_to_tweets[lowercase_word] = {"tweets": [], "timestamps": []}
            words_to_tweets[lowercase_word]["tweets"].append(tweet_text)
            words_to_tweets[lowercase_word]["timestamps"].append(created_at)
    # ----------------------------------------------------------------------------------

    # Create a list to store information for words in the dictionary
    matching_words_info = []

    # Comparing the two list
    # ------------------------------------------------------------------------------------------------
    # Compare each word in the dictionary with the comparison list (case-insensitive)
    for word in crypto_list:
        lowercase_word = word["name"].lower()  # Convert comparison word to lowercase
        if lowercase_word in words_to_tweets:
            word_info = {
                "word": lowercase_word,
                "tweets": words_to_tweets[lowercase_word]['tweets'],
                "timestamps": words_to_tweets[lowercase_word]['timestamps']
            }
            matching_words_info.append(word_info)
    # ------------------------------------------------------------------------------------------------

    # Logging
    # ------------------------------------------------------------------------------------------------
    # Print the information for words that are in the dictionary
    logging.info("Information for Words in the Dictionary:")
    for word_info in matching_words_info:
        logging.info(f"{word_info['word']}:")
        for tweet, timestamp in zip(word_info['tweets'], word_info['timestamps']):
            #logging.info(f"  - Tweet: {tweet}, Timestamp: {timestamp}")
            logging.info(f"  - Tweet: {tweet}")
            logging.info(f"  - Timestamp: {timestamp}")
    # ------------------------------------------------------------------------------------------------
            
    # Logging
    # ------------------------------------------------------------------------------------------------ 
    # Send the log file via email
    email_subject = 'Elon Musk Effect'
    email_body = 'Please find the log file attached.'
    to_email_address = 'xxxxx@gmail.com'  # Replace with your email address

    send_email(email_subject, email_body, to_email_address, log_file_path)
    # ------------------------------------------------------------------------------------------------ 

    # print(json.dumps(json_response, indent=4, sort_keys=True))

if __name__ == "__main__":
    main()