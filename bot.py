import random
import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import API_ID, API_HASH, BOT_TOKEN, DATABASE_CHANNEL_1, DATABASE_CHANNEL_2, MONGO_DB_URI
from pymongo import MongoClient
from flask import Flask
import threading

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MongoDB client
mongo_client = MongoClient(MONGO_DB_URI)
db = mongo_client["file_sharing_bot"]
file_collection_1 = db["files_channel_1"]
file_collection_2 = db["files_channel_2"]

# Initialize bot
bot = Client(
    "RandomFileSenderBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Flask server for health checks
app = Flask(__name__)

@app.route("/health")
def health():
    return "OK", 200

def run_health_server():
    app.run(host="0.0.0.0", port=8000)

# Store existing files from both channels
async def fetch_existing_files(channel_id, collection):
    """Fetch files from a Telegram channel and store in MongoDB."""
    async for message in bot.get_chat_history(channel_id):
        if message.video or message.document or message.photo:
            file_data = {
                "file_id": message.video.file_id if message.video else message.document.file_id if message.document else message.photo.file_id,
                "file_type": "video" if message.video else "document" if message.document else "photo"
            }
            if not collection.find_one({"file_id": file_data["file_id"]}):  # Avoid duplicates
                collection.insert_one(file_data)
                logger.info(f"Stored file with ID: {file_data['file_id']} from {channel_id}")

# Fetch a random file from the database
async def get_random_file(client, message, collection):
    file_count = collection.count_documents({})
    if file_count == 0:
        await message.reply_text("No files found in the database.")
        return

    try:
        random_file = list(collection.aggregate([{"$sample": {"size": 1}}]))[0]
    except (IndexError, StopIteration):
        await message.reply_text("Error fetching the file from the database.")
        return

    file_id = random_file.get("file_id")
    file_type = random_file.get("file_type")

    if not file_id or not file_type:
        await message.reply_text("Error fetching the file from the database.")
        return

    try:
        if file_type == "video":
            await client.send_video(chat_id=message.chat.id, video=file_id)
        elif file_type == "photo":
            await client.send_photo(chat_id=message.chat.id, photo=file_id)
        else:
            await client.send_document(chat_id=message.chat.id, document=file_id)
    except Exception as e:
        logger.error(f"Error sending file: {e}")
        await message.reply_text("An error occurred while sending the file.")

@bot.on_message(filters.command("start"))
async def start(client, message):
    """Start command handler."""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎥 Send from Channel 1", callback_data="send_channel_1")],
        [InlineKeyboardButton("📁 Send from Channel 2", callback_data="send_channel_2")]
    ])
    await message.reply_text(
        "Welcome to the Random File Sender Bot!\nChoose a category to receive random content:",
        reply_markup=keyboard
    )

@bot.on_callback_query(filters.regex("send_channel_1"))
async def send_random_file_channel_1(client, callback_query):
    """Handles button click to send a random file from channel 1."""
    await get_random_file(client, callback_query.message, file_collection_1)

@bot.on_callback_query(filters.regex("send_channel_2"))
async def send_random_file_channel_2(client, callback_query):
    """Handles button click to send a random file from channel 2."""
    await get_random_file(client, callback_query.message, file_collection_2)

# Start the Flask server in a separate thread
threading.Thread(target=run_health_server).start()

# Fetch existing files from both channels
bot.start()
bot.loop.run_until_complete(fetch_existing_files(DATABASE_CHANNEL_1, file_collection_1))
bot.loop.run_until_complete(fetch_existing_files(DATABASE_CHANNEL_2, file_collection_2))
bot.stop()

# Start the bot
bot.run()
