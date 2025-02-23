import os
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import requests
import re
import sqlite3
import logging
from telegram import Update
from telegram.ext import CallbackContext

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration from environment variables
BOT_TOKEN = os.environ.get("BOT_TOKEN", "7864220829:AAEfS005GxgrvHsNLXoIB7U4X8rmPZyCtwg")
CHANNELS = os.environ.get("CHANNELS", "@subtounlock1,@subtounlock2,@subtounlock3,@subtounlock4").split(",")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "5032034594"))

# SQLite setup for persistent storage
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, attempts INTEGER, channel_index INTEGER)")
conn.commit()

# Check if user is subscribed to a specific channel
def check_subscription(update: Update, context: CallbackContext, channel: str) -> bool:
    user_id = update.message.from_user.id
    try:
        member = context.bot.get_chat_member(channel, user_id)
        return member.status in ["member", "administrator", "creator"]
    except telegram.error.BadRequest:
        logger.warning(f"User {user_id} not found in {channel}")
        return False

# Process TeraBox link (placeholder, replace with actual logic if available)
def get_terabox_download_link(terabox_url):
    try:
        if not ("terabox.com" in terabox_url or "terabox.app" in terabox_url):
            return None
        response = requests.get(terabox_url, allow_redirects=True, timeout=10)
        if response.status_code == 200:
            return response.url
        logger.error(f"Failed to fetch TeraBox URL: {response.status_code}")
        return None
    except Exception as e:
        logger.error(f"Error processing TeraBox link: {e}")
        return None

# Load or initialize user data from SQLite
def get_user_data(user_id):
    cursor.execute("SELECT attempts, channel_index FROM users WHERE id = ?", (user_id,))
    result = cursor.fetchone()
    if result:
        return result[0], result[1]  # attempts, channel_index
    else:
        cursor.execute("INSERT INTO users (id, attempts, channel_index) VALUES (?, 0, 0)", (user_id,))
        conn.commit()
        return 0, 0

# Update user data in SQLite
def update_user_data(user_id, attempts, channel_index):
    cursor.execute("UPDATE users SET attempts = ?, channel_index = ? WHERE id = ?", (attempts, channel_index, user_id))
    conn.commit()

# Start command
def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    attempts, channel_index = get_user_data(user_id)
    
    update.message.reply_text(
        "Welcome to the TeraBox Downloader Bot!\n"
        "Please subscribe to our first channel: " + CHANNELS[0] + "\n"
        "Then send a TeraBox link to download."
    )
    logger.info(f"User {user_id} started the bot")

# Handle TeraBox link
def handle_link(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    message_text = update.message.text

    # Load user data
    attempts, channel_index = get_user_data(user_id)
    required_channel = CHANNELS[channel_index]

    # Determine the next channel requirement based on attempts
    if attempts == 0 and channel_index == 0:
        required_channel = CHANNELS[0]
    elif attempts >= 5 and channel_index < 1:
        channel_index = 1
        required_channel = CHANNELS[1]
    elif attempts >= 15 and channel_index < 2:
        channel_index = 2
        required_channel = CHANNELS[2]
    elif attempts >= 20 and channel_index < 3:
        channel_index = 3
        required_channel = CHANNELS[3]

    # Check if user is subscribed to the required channel
    if not check_subscription(update, context, required_channel):
        update.message.reply_text(
            f"You need to join {required_channel} to continue.\n"
            f"Attempts: {attempts}. Join now and try again!"
        )
        update_user_data(user_id, attempts, channel_index)
        logger.info(f"User {user_id} needs to join {required_channel}, attempts: {attempts}")
        return

    # Validate and process TeraBox link
    if not re.match(r"https?://(www\.)?(terabox\.com|terabox\.app)/.*", message_text):
        update.message.reply_text("Please send a valid TeraBox link.")
        logger.warning(f"User {user_id} sent invalid link: {message_text}")
        return

    update.message.reply_text("Processing your TeraBox link...")
    download_link = get_terabox_download_link(message_text)

    if download_link:
        update.message.reply_text(f"Here’s your download link:\n{download_link}")
        logger.info(f"User {user_id} received download link: {download_link}")
    else:
        update.message.reply_text("Sorry, couldn’t generate a download link. Check the URL and try again.")
        logger.error(f"User {user_id} failed to get download link for: {message_text}")

    # Increment attempts and update database
    attempts += 1
    update_user_data(user_id, attempts, channel_index)

# Main function to run the bot
def main():
    logger.info("Starting bot...")
    try:
        updater = Updater(BOT_TOKEN, use_context=True)
        dp = updater.dispatcher

        # Handlers
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_link))

        # Start the bot
        updater.start_polling()
        updater.idle()
    except Exception as e:
        logger.error(f"Bot failed to start: {e}")

if __name__ == "__main__":
    main()