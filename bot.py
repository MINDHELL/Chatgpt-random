import random
import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import API_ID, API_HASH, BOT_TOKEN, DATABASE_CHANNEL

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize bot
bot = Client(
    "RandomFileSenderBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

async def get_random_file(client, message):
    """Fetch a random file/video from the database channel and send it to the user."""
    files_list = []
    
    # Fetch messages from the database channel
    async for msg in client.get_chat_history(DATABASE_CHANNEL, limit=100):
        if msg.video or msg.document:  # Ensure it's a file or video
            files_list.append(msg)
    
    if not files_list:
        await message.reply_text("No files found in the database channel.")
        return
    
    # Pick a random file from the list
    random_file = random.choice(files_list)
    
    # Forward the file to the user
    await client.forward_messages(
        chat_id=message.chat.id,
        from_chat_id=DATABASE_CHANNEL,
        message_ids=random_file.message_id
    )

@bot.on_message(filters.command("start"))
async def start(client, message):
    """Start command handler - sends a welcome message with a random file button."""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎥 Send Random File", callback_data="send_random_file")]
    ])
    
    await message.reply_text(
        "Welcome to the Random File Sender Bot!\nClick the button below to get a random file/video:",
        reply_markup=keyboard
    )

@bot.on_callback_query(filters.regex("send_random_file"))
async def send_random_file(client, callback_query):
    """Handles button click to send a random file."""
    await get_random_file(client, callback_query.message)

# Start the bot
bot.run()
