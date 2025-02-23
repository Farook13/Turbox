import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import requests
import re
from telegram import Update
from telegram.ext import CallbackContext

# Configuration
BOT_TOKEN = "YOUR_BOT_TOKEN"  # Replace with your bot token from BotFather
CHANNELS = [
    "@ChannelOne",      # First use
    "@ChannelTwo",      # After 5 attempts
    "@ChannelThree",    # After 15 attempts
    "@ChannelFour"      # After 20 attempts
]
ADMIN_ID = YOUR_ADMIN_ID  # Replace with your Telegram user ID (integer)

# User tracking (in-memory, use a database for persistence)
user_attempts = {}
user_channel_progress = {}  # Tracks which channel the user must join next

# Check if user is subscribed to a specific channel
def check_subscription(update: Update, context: CallbackContext, channel: str) -> bool:
    user_id = update.message.from_user.id
    try:
        member = context.bot.get_chat_member(channel, user_id)
        return member.status in ["member", "administrator", "creator"]
    except telegram.error.BadRequest:
        return False

# Simulate TeraBox link processing (replace with actual API/logic if available)
def get_terabox_download_link(terabox_url):
    # Placeholder: In a real scenario, use TeraBox API or scrape the link
    try:
        if "terabox.com" not in terabox_url and "terabox.app" not in terabox_url:
            return None
        response = requests.get(terabox_url, allow_redirects=True)
        return response.url if response.status_code == 200 else None
    except Exception:
        return None

# Start command
def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id not in user_attempts:
        user_attempts[user_id] = 0
        user_channel_progress[user_id] = 0  # Start with first channel

    update.message.reply_text(
        "Welcome to the TeraBox Downloader Bot!\n"
        "Please subscribe to our first channel: " + CHANNELS[0] + "\n"
        "Then send a TeraBox link to download."
    )

# Handle TeraBox link
def handle_link(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    message_text = update.message.text

    # Initialize user data if not present
    if user_id not in user_attempts:
        user_attempts[user_id] = 0
        user_channel_progress[user_id] = 0

    attempts = user_attempts[user_id]
    channel_index = user_channel_progress[user_id]
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
        user_channel_progress[user_id] = channel_index  # Update required channel
        return

    # Validate and process TeraBox link
    if not re.match(r"https?://(www\.)?(terabox\.com|terabox\.app)/.*", message_text):
        update.message.reply_text("Please send a valid TeraBox link.")
        return

    update.message.reply_text("Processing your TeraBox link...")
    download_link = get_terabox_download_link(message_text)

    if download_link:
        update.message.reply_text(f"Here’s your download link:\n{download_link}")
    else:
        update.message.reply_text("Sorry, couldn’t generate a download link. Check the URL and try again.")

    # Increment attempts
    user_attempts[user_id] += 1

# Main function to run the bot
def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_link))

    # Start the bot
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
