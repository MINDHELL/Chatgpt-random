import random
import logging
import asyncio
from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Message,
    CallbackQuery,
)
from config import (
    API_ID,
    API_HASH,
    BOT_TOKEN,
    DATABASE_CHANNEL,
    MONGO_DB_URI,
    SEND_IMAGES_AND_VIDEOS,
    OWNER_ID,
    FORCE_SUB_CHANNEL,
    PROTECT_CONTENT,
    AUTO_DELETE_TIME,
)
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
user_collection = db["users"]

# Store previously sent file IDs to avoid repetition
sent_files_cache = set()

# Initialize bot
bot = Client(
    "RandomFileSenderBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
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
        "file_type": "video" if message.video else "document" if message.document else "photo",
    }
    if not file_collection.find_one({"file_id": file_data["file_id"]}):  # Avoid duplicates
        file_collection.insert_one(file_data)
        logger.info(f"Stored file with ID: {file_data['file_id']}")

async def is_subscribed(client, user_id):
    """Check if a user is subscribed to the FORCE_SUB_CHANNEL."""
    try:
        member = await client.get_chat_member(FORCE_SUB_CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception:
        return False

async def send_protected_file(client, chat_id, file_id, file_type):
    """Send a file with optional content protection and auto-delete."""
    protect = PROTECT_CONTENT
    try:
        if file_type == "video":
            sent_message = await client.send_video(
                chat_id=chat_id, video=file_id, protect_content=protect
            )
        elif file_type == "photo":
            sent_message = await client.send_photo(
                chat_id=chat_id, photo=file_id, protect_content=protect
            )
        else:
            sent_message = await client.send_document(
                chat_id=chat_id, document=file_id, protect_content=protect
            )

        if AUTO_DELETE_TIME > 0:
            await asyncio.sleep(AUTO_DELETE_TIME)
            await sent_message.delete()
    except Exception as e:
        logger.error(f"Error sending file: {e}")

async def get_random_file(client, message):
    """Fetch a random file from MongoDB and send it to the user."""
    user_id = message.from_user.id

    if user_id != OWNER_ID:
        if not await is_subscribed(client, user_id):
            keyboard = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "Join Channel", url=f"https://t.me/{FORCE_SUB_CHANNEL}"
                        )
                    ]
                ]
            )
            await message.reply_text(
                f"Please join @{FORCE_SUB_CHANNEL} to access random files.",
                reply_markup=keyboard,
            )
            return

    query_filter = {"file_type": "video"} if not SEND_IMAGES_AND_VIDEOS else {}

    # Fetch eligible files excluding already sent ones
    available_files = list(
        file_collection.find(
            {"$and": [query_filter, {"file_id": {"$nin": list(sent_files_cache)}}]}
        )
    )

    if not available_files:
        await message.reply_text("No more unique files found in the database.")
        return

    # Select a random file
    random_file = random.choice(available_files)

    file_id = random_file.get("file_id")
    file_type = random_file.get("file_type")

    if not file_id or not file_type:
        await message.reply_text("Error fetching the file from the database.")
        return

    # Add the file to sent cache
    sent_files_cache.add(file_id)

    await send_protected_file(client, message.chat.id, file_id, file_type)

@bot.on_message(filters.command("start"))
async def start(client, message):
    """Start command handler."""
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🎥 Send Random File", callback_data="send_random_file")],
            [InlineKeyboardButton("About", callback_data="about")],
            [InlineKeyboardButton("Close", callback_data="close")],
        ]
    )
    await message.reply_photo(
        photo="file_id_of_welcome_image",
        caption="Welcome to the Random File Sender Bot!\nClick the buttons below to interact:",
        reply_markup=keyboard,
    )

@bot.on_callback_query()
async def callback_query_handler(client, callback_query):
    """Handle callback queries from inline buttons."""
    data = callback_query.data
    if data == "send_random_file":
        await get_random_file(client, callback_query.message)
    elif data == "about":
        about_text = (
            "Creator: This Person\n"
            "Language: Python3\n"
            "Library: Pyrogram asyncio 2.1.37\n"
            "Source Code: [Click here](#)\n"
            "Channel: xxxxx\n"
            "Support Group: @xxxx"
        )
        await callback_query.message.edit_text(
            about_text, disable_web_page_preview=True
        )
    elif data == "close":
        await callback_query.message.delete()

@bot.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
async def broadcast(client, message):
    """Broadcast a message to all users."""
    if len(message.command) < 2:
        await message.reply_text("Please provide a message to broadcast.")
        return

    broadcast_text = message.text.split(maxsplit=1)[1]
    users = user_collection.find()
    for user in users:
        try:
            await client.send_message(user["user_id"], broadcast_text)
        except Exception as e:
            logger.error(f"Error sending broadcast to {user['user_id']}: {e}")

@bot.on_message(filters.private)
async def track_users(client, message):
    """Track users who interact with the bot."""
    user_id = message.from_user.id
    if not user_collection.find_one({"user_id": user_id}):
        user_collection.insert_one({"user_id": user_id})
        logger.info(f"Added new user: {user_id}")

# Start the Flask server in a separate thread
threading.Thread(target=run_health_server).start()

0
