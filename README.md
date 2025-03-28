# Auto Tweet Bot

This script automatically posts tweets from an Excel file to Twitter at optimal times throughout the day.

## Important Update: New Twitter API v2 Version

Due to changes in Twitter's API, we've created a new version of the script (`autotweets_v2.py`) that directly uses the Twitter API v2 instead of the Tweepy library. If you're experiencing 403 Forbidden errors with the original script, please use this new version.

**Key differences:**
- Uses direct API calls instead of Tweepy
- Better compatibility with Twitter's latest API changes
- More detailed error handling and diagnostics
- Requires the additional `requests-toolbelt` package (auto-installed by the script)

## Setup Instructions

### 1. Install Required Packages

You can install the required packages using the requirements.txt file:

```bash
pip install -r requirements.txt
```

Or install them individually:

```bash
pip install tweepy pandas openpyxl schedule python-dotenv pyTelegramBotAPI
```

### 2. Create Environment Variables

Create a `.env` file in the same directory as the script with the following variables:

```
# Twitter API Credentials
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_SECRET=your_access_secret

# Telegram Bot Credentials (Optional)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
```

Note: The updated script no longer requires the TWITTER_BEARER_TOKEN.

### 3. Create the Tweet List

Create an Excel file named `tweetlist.xlsx` in the same directory as the script with the following structure:

- Column header: `Tweet`
- Each row contains one tweet
- Leave a blank row to indicate the end of the tweet list

See `tweetlist_template.txt` for example content.

### 4. Add Media Files

Add at least 4 media files (images or videos) to the `media` folder. Supported formats:
- Images: .jpg, .png
- Videos: .mp4, .mov

### 5. Configure Posting Frequency

In the script, you can adjust the `POSTS_PER_DAY` variable (between 4-10) to control how many tweets are posted each day.

The script uses UTC time for scheduling posts, with times optimized for USA audiences. This ensures that the system's local time zone doesn't affect the posting schedule. The posting times are:
- 13:30, 14:30 UTC (Morning in Eastern US)
- 17:00, 18:00 UTC (Lunch time in Eastern US)
- 23:00, 00:00 UTC (Evening in Eastern US)
- 02:00, 03:00 UTC (Evening in Pacific US)
- 19:30, 04:30 UTC (Additional times covering multiple US time zones)

## Running the Bot

### Original Version (Tweepy-based)
```bash
python autotweets.py
```

### New Version (Twitter API v2)
```bash
python autotweets_v2.py
```

The bot will:
1. Load tweets from the Excel file
2. Schedule posts at optimal times throughout the day (in UTC time zone)
3. Post tweets with media and influencer tags
4. Send updates to Telegram (if configured)
5. Continue posting until it reaches a blank row in the Excel file

## Telegram Integration

To receive updates via Telegram:
1. Create a Telegram bot using BotFather (https://t.me/botfather)
2. Get your chat ID (you can use @userinfobot)
3. Add the bot token and chat ID to your .env file

## Troubleshooting

- If you see "No tweets found" error, check that your Excel file exists and has the correct column header
- If media uploads fail, ensure your media files are in supported formats and not too large
- For Telegram errors, verify your bot token and chat ID are correct

### 403 Forbidden Error

If you encounter a "403 Forbidden" error when posting tweets, this usually indicates an authentication or permission issue:

1. **API Key Issues**:
   - Verify your API keys in the .env file are correct and up-to-date
   - Ensure you've copied the keys exactly as shown in the Twitter Developer Portal

2. **Permission Issues**:
   - Check your Twitter Developer Portal to ensure your app has Write permissions enabled
   - Make sure your app has the correct OAuth settings (Read and Write)

3. **Content Issues**:
   - Twitter doesn't allow posting duplicate content - try modifying your tweets
   - Ensure your content doesn't violate Twitter's policies

4. **Account Issues**:
   - Check if your Twitter account has any posting restrictions
   - Verify your account is in good standing

5. **Authentication Method Issues**:
   - The script has been updated to use only OAuth 1.0a User Context authentication (no bearer token)
   - This authentication method is more compatible with Twitter's API requirements

The script includes enhanced error diagnostics that will help identify the specific cause of 403 errors.

## Recent Updates

The script has been updated to use a more reliable authentication method based on community feedback:

1. **Authentication Changes**:
   - Removed bearer token authentication
   - Now using only OAuth 1.0a User Context authentication
   - Created separate functions for Twitter API v1 and v2 connections

2. **Verification Improvements**:
   - Added verification for both API v1 and v2 credentials
   - Better error handling and diagnostics

These changes should help resolve the 403 Forbidden errors that some users were experiencing.
