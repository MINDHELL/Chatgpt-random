import random
import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import API_ID, API_HASH, BOT_TOKEN, DATABASE_CHANNEL, MONGO_DB_URI
from pymongo import MongoClient
from flask import Flask
import threading

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MongoDB client
mongo_client = MongoClient(MONGO_DB_URI)
db = mongo_client["file_sharing_bot"]
file_collection = db["files"]

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

# Store file metadata on upload
@bot.on_message(filters.chat(DATABASE_CHANNEL) & (filters.document | filters.video))
async def store_file(client, message):
    """Store file metadata in MongoDB."""
    file_data = {
        "file_id": message.video.file_id if message.video else message.document.file_id,
        "file_type": "video" if message.video else "document"
    }
    file_collection.insert_one(file_data)
    logger.info(f"Stored file with ID: {file_data['file_id']}")

async def get_random_file(client, message):
    """Fetch a random file from MongoDB and send it to the user."""
    file_count = file_collection.count_documents({})
    if file_count == 0:
        await message.reply_text("No files found in the database.")
        return

    random_file = file_collection.aggregate([{"$sample": {"size": 1}}]).next()

    if random_file["file_type"] == "video":
        await client.send_video(
            chat_id=message.chat.id,
            video=random_file["file_id"]
        )
    else:
        await client.send_document(
            chat_id=message.chat.id,
            document=random_file["file_id"]
        )

@bot.on_message(filters.command("start"))
async def start(client, message):
    """Start command handler."""
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

# Start the Flask server in a separate thread
threading.Thread(target=run_health_server).start()

# Start the bot
bot.run()
