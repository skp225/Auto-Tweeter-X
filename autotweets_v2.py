import os
import time
import random
import pandas as pd
import schedule
import requests
import base64
import json
from datetime import datetime
import telebot
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Twitter API credentials from .env file
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

# Telegram Bot credentials
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Configuration - easily change the number of posts per day (between 4-10)
POSTS_PER_DAY = 4  # Default: 4 posts per day

# Initialize Telegram bot
def init_telegram_bot():
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        return telebot.TeleBot(TELEGRAM_BOT_TOKEN)
    return None

bot = init_telegram_bot()

# Function to send message to Telegram
def send_telegram_message(message):
    try:
        if bot and TELEGRAM_CHAT_ID:
            bot.send_message(TELEGRAM_CHAT_ID, message)
            print(f"📱 Telegram message sent: {message}")
    except Exception as e:
        print(f"❌ Telegram error: {e}")

# Custom print function that also sends to Telegram
def log_message(message):
    print(message)
    send_telegram_message(message)

# Function to create OAuth 1.0a headers for Twitter API v2
def get_oauth_headers(method="GET", url="", params=None):
    import hmac
    import hashlib
    import urllib.parse
    import uuid
    import time
    
    # Generate OAuth parameters
    oauth_timestamp = str(int(time.time()))
    oauth_nonce = uuid.uuid4().hex
    
    # Base OAuth parameters
    oauth_params = {
        'oauth_consumer_key': TWITTER_API_KEY,
        'oauth_nonce': oauth_nonce,
        'oauth_signature_method': 'HMAC-SHA1',
        'oauth_timestamp': oauth_timestamp,
        'oauth_token': TWITTER_ACCESS_TOKEN,
        'oauth_version': '1.0'
    }
    
    # Combine OAuth parameters with any additional parameters
    all_params = {}
    all_params.update(oauth_params)
    if params:
        all_params.update(params)
    
    # Create signature base string
    base_string_params = '&'.join([f"{urllib.parse.quote(k)}={urllib.parse.quote(str(all_params[k]))}" for k in sorted(all_params.keys())])
    base_string = f"{method}&{urllib.parse.quote(url)}&{urllib.parse.quote(base_string_params)}"
    
    # Create signing key
    signing_key = f"{urllib.parse.quote(TWITTER_API_SECRET)}&{urllib.parse.quote(TWITTER_ACCESS_SECRET)}"
    
    # Create signature
    signature = base64.b64encode(hmac.new(signing_key.encode(), base_string.encode(), hashlib.sha1).digest()).decode()
    
    # Add signature to OAuth parameters
    oauth_params['oauth_signature'] = signature
    
    # Create Authorization header
    auth_header = 'OAuth ' + ', '.join([f'{urllib.parse.quote(k)}="{urllib.parse.quote(oauth_params[k])}"' for k in sorted(oauth_params.keys())])
    
    return {
        'Authorization': auth_header,
        'Content-Type': 'application/json'
    }

# Function to upload media to Twitter
def upload_media(media_path):
    log_message(f"🔄 Uploading media: {media_path}")
    
    try:
        # Step 1: INIT - Initialize the upload
        with open(media_path, 'rb') as file:
            media_data = file.read()
        
        file_size = len(media_data)
        media_type = "image/jpeg" if media_path.endswith(('.jpg', '.jpeg')) else "image/png" if media_path.endswith('.png') else "video/mp4"
        
        # For Twitter API v1.1 media upload (still used for media)
        url = "https://upload.twitter.com/1.1/media/upload.json"
        
        # Create OAuth 1.0a signature
        import hmac
        import hashlib
        import urllib.parse
        import uuid
        import time
        
        # Generate OAuth parameters
        oauth_timestamp = str(int(time.time()))
        oauth_nonce = uuid.uuid4().hex
        
        # Base string parameters
        params = {
            'oauth_consumer_key': TWITTER_API_KEY,
            'oauth_nonce': oauth_nonce,
            'oauth_signature_method': 'HMAC-SHA1',
            'oauth_timestamp': oauth_timestamp,
            'oauth_token': TWITTER_ACCESS_TOKEN,
            'oauth_version': '1.0',
            'command': 'INIT',
            'total_bytes': str(file_size),
            'media_type': media_type
        }
        
        # Create signature base string
        base_string_params = '&'.join([f"{urllib.parse.quote(k)}={urllib.parse.quote(params[k])}" for k in sorted(params.keys())])
        base_string = f"POST&{urllib.parse.quote(url)}&{urllib.parse.quote(base_string_params)}"
        
        # Create signing key
        signing_key = f"{urllib.parse.quote(TWITTER_API_SECRET)}&{urllib.parse.quote(TWITTER_ACCESS_SECRET)}"
        
        # Create signature
        signature = base64.b64encode(hmac.new(signing_key.encode(), base_string.encode(), hashlib.sha1).digest()).decode()
        
        # Add signature to parameters
        params['oauth_signature'] = signature
        
        # Create Authorization header
        auth_header = 'OAuth ' + ', '.join([f'{urllib.parse.quote(k)}="{urllib.parse.quote(params[k])}"' for k in sorted(params.keys()) if k.startswith('oauth')])
        
        # Headers for the request
        headers = {
            'Authorization': auth_header,
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        # Data for INIT
        data = {
            'command': 'INIT',
            'total_bytes': str(file_size),
            'media_type': media_type
        }
        
        # Make INIT request
        response = requests.post(url, headers=headers, data=data)
        
        if response.status_code != 200:
            log_message(f"❌ Media upload INIT failed: {response.text}")
            return None
        
        media_id = response.json()['media_id_string']
        log_message(f"✅ Media upload INIT successful. Media ID: {media_id}")
        
        # Step 2: APPEND - Upload the media data in chunks
        chunk_size = 4 * 1024 * 1024  # 4MB chunks
        
        for i in range(0, file_size, chunk_size):
            chunk = media_data[i:i+chunk_size]
            
            # Update OAuth parameters for APPEND
            oauth_timestamp = str(int(time.time()))
            oauth_nonce = uuid.uuid4().hex
            
            params = {
                'oauth_consumer_key': TWITTER_API_KEY,
                'oauth_nonce': oauth_nonce,
                'oauth_signature_method': 'HMAC-SHA1',
                'oauth_timestamp': oauth_timestamp,
                'oauth_token': TWITTER_ACCESS_TOKEN,
                'oauth_version': '1.0',
                'command': 'APPEND',
                'media_id': media_id,
                'segment_index': str(i // chunk_size)
            }
            
            # Create signature base string for APPEND
            base_string_params = '&'.join([f"{urllib.parse.quote(k)}={urllib.parse.quote(params[k])}" for k in sorted(params.keys())])
            base_string = f"POST&{urllib.parse.quote(url)}&{urllib.parse.quote(base_string_params)}"
            
            # Create signature for APPEND
            signature = base64.b64encode(hmac.new(signing_key.encode(), base_string.encode(), hashlib.sha1).digest()).decode()
            
            # Add signature to parameters
            params['oauth_signature'] = signature
            
            # Create Authorization header for APPEND
            auth_header = 'OAuth ' + ', '.join([f'{urllib.parse.quote(k)}="{urllib.parse.quote(params[k])}"' for k in sorted(params.keys()) if k.startswith('oauth')])
            
            # Headers for APPEND
            headers = {
                'Authorization': auth_header
            }
            
            # Create multipart form data
            import io
            from requests_toolbelt.multipart.encoder import MultipartEncoder
            
            mp_encoder = MultipartEncoder(
                fields={
                    'command': 'APPEND',
                    'media_id': media_id,
                    'segment_index': str(i // chunk_size),
                    'media': ('media', io.BytesIO(chunk), media_type)
                }
            )
            
            headers['Content-Type'] = mp_encoder.content_type
            
            # Make APPEND request
            response = requests.post(url, headers=headers, data=mp_encoder)
            
            if response.status_code != 200:
                log_message(f"❌ Media upload APPEND failed for segment {i // chunk_size}: {response.text}")
                return None
            
            log_message(f"✅ Media upload APPEND successful for segment {i // chunk_size}")
        
        # Step 3: FINALIZE - Finalize the upload
        oauth_timestamp = str(int(time.time()))
        oauth_nonce = uuid.uuid4().hex
        
        params = {
            'oauth_consumer_key': TWITTER_API_KEY,
            'oauth_nonce': oauth_nonce,
            'oauth_signature_method': 'HMAC-SHA1',
            'oauth_timestamp': oauth_timestamp,
            'oauth_token': TWITTER_ACCESS_TOKEN,
            'oauth_version': '1.0',
            'command': 'FINALIZE',
            'media_id': media_id
        }
        
        # Create signature base string for FINALIZE
        base_string_params = '&'.join([f"{urllib.parse.quote(k)}={urllib.parse.quote(params[k])}" for k in sorted(params.keys())])
        base_string = f"POST&{urllib.parse.quote(url)}&{urllib.parse.quote(base_string_params)}"
        
        # Create signature for FINALIZE
        signature = base64.b64encode(hmac.new(signing_key.encode(), base_string.encode(), hashlib.sha1).digest()).decode()
        
        # Add signature to parameters
        params['oauth_signature'] = signature
        
        # Create Authorization header for FINALIZE
        auth_header = 'OAuth ' + ', '.join([f'{urllib.parse.quote(k)}="{urllib.parse.quote(params[k])}"' for k in sorted(params.keys()) if k.startswith('oauth')])
        
        # Headers for FINALIZE
        headers = {
            'Authorization': auth_header,
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        # Data for FINALIZE
        data = {
            'command': 'FINALIZE',
            'media_id': media_id
        }
        
        # Make FINALIZE request
        response = requests.post(url, headers=headers, data=data)
        
        if response.status_code != 200:
            log_message(f"❌ Media upload FINALIZE failed: {response.text}")
            return None
        
        log_message(f"✅ Media upload FINALIZE successful")
        
        # If it's a video, we need to check processing status
        if media_type.startswith('video'):
            processing_info = response.json().get('processing_info')
            if processing_info:
                state = processing_info.get('state')
                
                # If the video is still processing, we need to wait and check status
                while state == 'pending' or state == 'in_progress':
                    check_after_secs = processing_info.get('check_after_secs', 5)
                    log_message(f"🔄 Video processing in progress. Checking again in {check_after_secs} seconds...")
                    time.sleep(check_after_secs)
                    
                    # Update OAuth parameters for STATUS
                    oauth_timestamp = str(int(time.time()))
                    oauth_nonce = uuid.uuid4().hex
                    
                    params = {
                        'oauth_consumer_key': TWITTER_API_KEY,
                        'oauth_nonce': oauth_nonce,
                        'oauth_signature_method': 'HMAC-SHA1',
                        'oauth_timestamp': oauth_timestamp,
                        'oauth_token': TWITTER_ACCESS_TOKEN,
                        'oauth_version': '1.0',
                        'command': 'STATUS',
                        'media_id': media_id
                    }
                    
                    # Create signature base string for STATUS
                    base_string_params = '&'.join([f"{urllib.parse.quote(k)}={urllib.parse.quote(params[k])}" for k in sorted(params.keys())])
                    base_string = f"GET&{urllib.parse.quote(url)}&{urllib.parse.quote(base_string_params)}"
                    
                    # Create signature for STATUS
                    signature = base64.b64encode(hmac.new(signing_key.encode(), base_string.encode(), hashlib.sha1).digest()).decode()
                    
                    # Add signature to parameters
                    params['oauth_signature'] = signature
                    
                    # Create Authorization header for STATUS
                    auth_header = 'OAuth ' + ', '.join([f'{urllib.parse.quote(k)}="{urllib.parse.quote(params[k])}"' for k in sorted(params.keys()) if k.startswith('oauth')])
                    
                    # Headers for STATUS
                    headers = {
                        'Authorization': auth_header
                    }
                    
                    # Make STATUS request
                    response = requests.get(f"{url}?command=STATUS&media_id={media_id}", headers=headers)
                    
                    if response.status_code != 200:
                        log_message(f"❌ Media upload STATUS check failed: {response.text}")
                        return None
                    
                    processing_info = response.json().get('processing_info')
                    if not processing_info:
                        break
                    
                    state = processing_info.get('state')
                    
                    if state == 'failed':
                        error = processing_info.get('error')
                        log_message(f"❌ Video processing failed: {error}")
                        return None
                
                log_message("✅ Video processing completed successfully")
        
        return media_id
        
    except Exception as e:
        log_message(f"❌ Media upload error: {str(e)}")
        return None

# Function to post a tweet with the Twitter API v2
def post_tweet_v2(text, media_id=None):
    try:
        url = "https://api.twitter.com/2/tweets"
        
        payload = {"text": text}
        
        # Add media if provided
        if media_id:
            payload["media"] = {"media_ids": [media_id]}
        
        # Create OAuth 1.0a headers
        headers = get_oauth_headers("POST", url)
        
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code != 201:
            log_message(f"❌ Tweet posting failed: {response.status_code} - {response.text}")
            return None
        
        return response.json()
    
    except Exception as e:
        log_message(f"❌ Tweet posting error: {str(e)}")
        return None

# Function to load tweets from Excel file
def load_tweets_from_excel():
    try:
        # Check if the Excel file exists
        if not os.path.exists("tweetlist.xlsx"):
            log_message("⚠️ ERROR: 'tweetlist.xlsx' file not found. Please create it with your tweets.")
            return None, 0
        
        # Read the Excel file
        df = pd.read_excel("tweetlist.xlsx")
        
        # Check if the dataframe has the required column
        if 'Tweet' not in df.columns:
            log_message("⚠️ ERROR: 'tweetlist.xlsx' must have a 'Tweet' column.")
            return None, 0
        
        # Get tweets and find the first blank row
        tweets = df['Tweet'].tolist()
        
        # Find the first blank row (None or NaN)
        first_blank = None
        for i, tweet in enumerate(tweets):
            if pd.isna(tweet) or tweet == "":
                first_blank = i
                break
        
        if first_blank is None:
            first_blank = len(tweets)
            
        # Return only non-blank tweets
        return tweets[:first_blank], first_blank
        
    except Exception as e:
        log_message(f"❌ Error loading tweets from Excel: {e}")
        return None, 0

# Track current position in tweet list
current_tweet_index = 0
total_tweets = 0

# ✅ List of influencers (Twitter handles without '@')
influencers = [
    "Edutopia", "TeachThought", "ClassTechTips", "web20classroom", "ShakeUpLearning", "rmbyrne", "ShellTerrell", "gcouros", "coolcatteacher", "MsMagiera", "courosa", "tvanderark", "audreywatters", "lesliefisher", "mrkempnz", "DNLee5", "eveewing", "thesiswhisperer", "AmyJoMartin", "GRwabigwi", "BiscottiNicole", "cultofpedagogy", "Larryferlazzo", "cpappas", "lauraoverton", "DonaldHTaylor", "CatMoore", "Josh_Bersin", "emasie", "brewerhm", "burgessdave", "BethHouf", "JayBilly2", "drmaryhemphill", "ERobbPrincipal", "shfarnsworth", "joboaler", "EduColorMVMT", "douglemov", "Tcea", "EdSurge", "ISTE", "MindShiftKQED", "HollyClarkEdu", "alicekeeler", "tonyvincent", "mattmiller", "jmattmiller", "jeffudall", "curriki"

]

# ✅ Path to the folder containing images/videos
media_folder = "media"

# ✅ Ensure media folder exists
if not os.path.exists(media_folder):
    os.makedirs(media_folder)
    log_message("📂 'media' folder created. Add media files and rerun the script.")
    exit()

# ✅ Get list of media files
media_files = [f for f in os.listdir(media_folder) if f.endswith(('.jpg', '.png', '.mp4', '.mov'))]

# ✅ Ensure there are at least 4 media files
if len(media_files) < 4:
    log_message("⚠️ ERROR: Please add at least 4 media files to the 'media' folder before running the script.")
    exit()

# Function to post a single tweet
def post_tweet():
    global current_tweet_index, total_tweets
    
    # Reload tweets from Excel to check for updates
    if current_tweet_index == 0 or current_tweet_index >= total_tweets:
        tweets_list, tweet_count = load_tweets_from_excel()
        if not tweets_list or tweet_count == 0:
            log_message("⚠️ No tweets found in the Excel file or reached the end. Stopping.")
            return False
        total_tweets = tweet_count
        log_message(f"📊 Loaded {total_tweets} tweets from Excel file.")
    
    try:
        # Select tweet and media file based on the index
        tweet_content = tweets_list[current_tweet_index % total_tweets]
        media_index = current_tweet_index % len(media_files)
        media_path = os.path.join(media_folder, media_files[media_index])
        
        # Select 10 influencers and format as mentions
        start_index = (current_tweet_index * 10) % len(influencers)
        selected_influencers = influencers[start_index:start_index + 10]
        if len(selected_influencers) < 10:
            selected_influencers += influencers[:(10 - len(selected_influencers))]
        
        # Clean up any @ symbols that might be in the list
        selected_influencers = [user.replace('@', '') for user in selected_influencers]
        influencer_tags = " ".join([f"@{user}" for user in selected_influencers])

        # Ensure total tweet length does not exceed 280 characters
        final_tweet = f"{tweet_content}\n\n{influencer_tags}"
        if len(final_tweet) > 280:
            final_tweet = f"{tweet_content[:260]}...\n{influencer_tags}"  # Truncate tweet if needed

        # Upload media
        log_message(f"🔄 Preparing to post tweet {current_tweet_index+1}/{total_tweets}")
        media_id = upload_media(media_path)
        
        if not media_id:
            log_message("❌ Failed to upload media. Skipping this tweet.")
            current_tweet_index += 1
            return False
        
        # Post tweet with media
        response = post_tweet_v2(final_tweet, media_id)
        
        if not response:
            log_message("❌ Failed to post tweet. Skipping to next tweet.")
            current_tweet_index += 1
            return False
        
        tweet_id = response.get('data', {}).get('id')
        
        if tweet_id:
            log_message(f"✅ Tweet {current_tweet_index+1}/{total_tweets} posted: {final_tweet}")
            log_message(f"🔗 Tweet Link: https://twitter.com/user/status/{tweet_id}")
        else:
            log_message(f"⚠️ Tweet posted but couldn't get tweet ID. Response: {response}")
        
        # Increment tweet index
        current_tweet_index += 1
        
        # Check if we've reached the end of the tweet list
        if current_tweet_index >= total_tweets:
            log_message("🎉 Reached the end of the tweet list! Will check for updates tomorrow.")
            
        return True

    except Exception as e:
        log_message(f"❌ Unexpected error while posting tweet: {str(e)}")
        
        # Try to provide more detailed diagnostics
        if "403" in str(e):
            log_message("🔍 403 Forbidden Error Diagnostics:")
            log_message("  - This usually indicates an authentication or permission issue")
            log_message("  - Possible causes:")
            log_message("    1. Invalid or expired API keys/tokens")
            log_message("    2. Your app may not have Write permissions enabled")
            log_message("    3. You might be trying to post duplicate content")
            log_message("    4. Your account may have posting restrictions")
            log_message("  - Troubleshooting steps:")
            log_message("    1. Verify your API keys in the .env file")
            log_message("    2. Check your Twitter Developer Portal to ensure Write permissions are enabled")
            log_message("    3. Try posting with different content")
            
            # Try to verify API credentials
            try:
                log_message("🔄 Attempting to verify API credentials...")
                url = "https://api.twitter.com/2/users/me"
                headers = get_oauth_headers("GET", url)
                response = requests.get(url, headers=headers)
                
                if response.status_code == 200:
                    user_data = response.json().get('data', {})
                    log_message(f"✅ API connection successful. Authenticated as: @{user_data.get('username')}")
                    log_message("❗ This suggests the issue is with the content or posting permissions, not the API keys")
                else:
                    log_message(f"❌ API verification failed: {response.status_code} - {response.text}")
                    log_message("❗ This suggests your API keys may be invalid or expired")
            except Exception as verify_error:
                log_message(f"❌ API verification failed: {str(verify_error)}")
                log_message("❗ This suggests your API keys may be invalid or expired")
        
        return False

# Optimal posting times in UTC for USA audiences
optimal_times = [
    "13:30", "14:30",  # Morning in Eastern US (9:30-10:30 AM ET)
    "17:00", "18:00",  # Lunch time in Eastern US (1-2 PM ET)
    "23:00", "00:00",  # Evening in Eastern US (7-8 PM ET)
    "02:00", "03:00",  # Evening in Pacific US (7-8 PM PT)
    "19:30", "04:30"   # Additional times covering multiple US time zones
]

# Schedule posts at optimal times based on POSTS_PER_DAY setting
def schedule_posts():
    # Clear any existing jobs
    schedule.clear()
    
    # Select posting times based on POSTS_PER_DAY
    if POSTS_PER_DAY < 4:
        post_times = optimal_times[:4]  # Minimum 4 posts
    elif POSTS_PER_DAY > 10:
        post_times = optimal_times[:10]  # Maximum 10 posts
    else:
        post_times = optimal_times[:POSTS_PER_DAY]
    
    # Schedule each post using UTC times
    for time_str in post_times:
        schedule.every().day.at(time_str, "UTC").do(post_tweet)
        log_message(f"📅 Scheduled post at {time_str} UTC")
    
    log_message(f"🔄 Set up {len(post_times)} posts per day")

# Function to verify Twitter API credentials
def verify_twitter_credentials():
    log_message("🔄 Verifying Twitter API credentials...")
    try:
        url = "https://api.twitter.com/2/users/me"
        headers = get_oauth_headers("GET", url)
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            user_data = response.json().get('data', {})
            log_message(f"✅ Twitter API credentials verified! Authenticated as: @{user_data.get('username')}")
            return True
        else:
            log_message(f"❌ Twitter API credential verification failed: {response.status_code} - {response.text}")
            log_message("⚠️ Please check your API keys in the .env file")
            return False
            
    except Exception as e:
        log_message(f"❌ Twitter API credential verification failed: {str(e)}")
        log_message("⚠️ Please check your API keys in the .env file")
        log_message("⚠️ Common issues:")
        log_message("  1. Incorrect API keys or tokens")
        log_message("  2. Expired credentials")
        log_message("  3. App not properly set up in Twitter Developer Portal")
        return False

# Main execution
if __name__ == "__main__":
    log_message("🚀 Auto Tweet Bot Started (Twitter API v2)")
    log_message(f"⚙️ Configuration: {POSTS_PER_DAY} posts per day")
    
    # Install required packages if not already installed
    try:
        import requests_toolbelt
    except ImportError:
        log_message("📦 Installing required package: requests-toolbelt")
        import subprocess
        subprocess.check_call(["pip", "install", "requests-toolbelt"])
        log_message("✅ Package installed successfully")
        import requests_toolbelt
    
    # Verify Twitter API credentials before proceeding
    if not verify_twitter_credentials():
        log_message("⚠️ Twitter API credential verification failed. Please fix the issues before continuing.")
        log_message("👉 See the README.md file for troubleshooting the 403 Forbidden error.")
        exit()
    
    # Initial tweet loading
    tweets_list, tweet_count = load_tweets_from_excel()
    if not tweets_list or tweet_count == 0:
        log_message("⚠️ No tweets found in the Excel file. Please add tweets and restart.")
        exit()
    
    total_tweets = tweet_count
    log_message(f"📊 Loaded {total_tweets} tweets from Excel file")
    
    # Schedule posts
    schedule_posts()
    
    # Run the scheduler
    log_message("⏱️ Scheduler running. Press Ctrl+C to stop.")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        log_message("👋 Auto Tweet Bot stopped by user")
    except Exception as e:
        log_message(f"❌ Error in main loop: {e}")
