import tweepy
import os
import time
import random
import pandas as pd
import schedule
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

# Functions to get Twitter API connections (based on forum code)
def get_twitter_conn_v1(api_key, api_secret, access_token, access_token_secret):
    """Get Twitter API v1.1 connection"""
    auth = tweepy.OAuth1UserHandler(api_key, api_secret)
    auth.set_access_token(access_token, access_token_secret)
    return tweepy.API(auth)

def get_twitter_conn_v2(api_key, api_secret, access_token, access_token_secret):
    """Get Twitter API v2 connection"""
    client = tweepy.Client(
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_token_secret
    )
    return client

# Initialize API connections
api = get_twitter_conn_v1(TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET)
client = get_twitter_conn_v2(TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET)

# Log the authentication method
log_message("🔐 Using OAuth 1.0a User Context authentication (no bearer token)")

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
        media = api.media_upload(media_path)

        # Post tweet with media and tags
        response = client.create_tweet(text=final_tweet, media_ids=[media.media_id])
        
        log_message(f"✅ Tweet {current_tweet_index+1}/{total_tweets} posted: {final_tweet}")
        log_message(f"🔗 Tweet Link: https://twitter.com/user/status/{response.data['id']}")
        
        # Increment tweet index
        current_tweet_index += 1
        
        # Check if we've reached the end of the tweet list
        if current_tweet_index >= total_tweets:
            log_message("🎉 Reached the end of the tweet list! Will check for updates tomorrow.")
            
        return True

    except tweepy.TweepyException as e:
        error_message = str(e)
        log_message(f"❌ Tweeting error: {error_message}")
        
        # Provide more detailed diagnostics for common errors
        if "403" in error_message:
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
                v1_user = api.verify_credentials()
                log_message(f"✅ API v1 connection successful. Authenticated as: @{v1_user.screen_name}")
                
                v2_user = client.get_me()
                log_message(f"✅ API v2 connection successful. Authenticated as: @{v2_user.data.username}")
                
                log_message("❗ This suggests the issue is with the content or posting permissions, not the API keys")
            except Exception as verify_error:
                log_message(f"❌ API verification failed: {verify_error}")
                log_message("❗ This suggests your API keys may be invalid or expired")
        
        return False
    except Exception as e:
        log_message(f"❌ Unexpected error: {e}")
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
        # Try to verify API v1 credentials
        v1_user = api.verify_credentials()
        log_message(f"✅ Twitter API v1 credentials verified! Authenticated as: @{v1_user.screen_name}")
        
        # Try to verify API v2 credentials
        v2_user = client.get_me()
        log_message(f"✅ Twitter API v2 credentials verified! Authenticated as: @{v2_user.data.username}")
        
        return True
    except tweepy.TweepyException as e:
        log_message(f"❌ Twitter API credential verification failed: {e}")
        log_message("⚠️ Please check your API keys in the .env file")
        log_message("⚠️ Common issues:")
        log_message("  1. Incorrect API keys or tokens")
        log_message("  2. Expired credentials")
        log_message("  3. App not properly set up in Twitter Developer Portal")
        return False
    except Exception as e:
        log_message(f"❌ Unexpected error during verification: {e}")
        return False

# Main execution
if __name__ == "__main__":
    log_message("🚀 Auto Tweet Bot Started")
    log_message(f"⚙️ Configuration: {POSTS_PER_DAY} posts per day")
    
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
