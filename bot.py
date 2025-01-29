import random
import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import API_ID, API_HASH, BOT_TOKEN, DATABASE_CHANNEL, MONGO_DB_URI, SEND_IMAGES_AND_VIDEOS
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
@bot.on_message(filters.chat(DATABASE_CHANNEL) & (filters.document | filters.video | filters.photo))
async def store_file(client, message):
    """Store file metadata in MongoDB."""
    file_data = {
        "file_id": message.video.file_id if message.video else message.document.file_id if message.document else message.photo.file_id,
        "file_type": "video" if message.video else "document" if message.document else "photo"
    }
    if not file_collection.find_one({"file_id": file_data["file_id"]}):  # Avoid duplicates
        file_collection.insert_one(file_data)
        logger.info(f"Stored file with ID: {file_data['file_id']}")

async def get_random_file(client, message):
    """Fetch a random file from MongoDB and send it to the user."""
    query_filter = {"file_type": "video"} if not SEND_IMAGES_AND_VIDEOS else {}

    file_count = file_collection.count_documents(query_filter)
    if file_count == 0:
        await message.reply_text("No files found in the database.")
        return

    # Fetch a random file without cursor errors
    random_file = list(file_collection.aggregate([{"$match": query_filter}, {"$sample": {"size": 1}}]))

    if not random_file:
        await message.reply_text("Error fetching the file from the database.")
        return

    file = random_file[0]
    file_id = file.get("file_id")
    file_type = file.get("file_type")

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
