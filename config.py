import os

API_ID = int(os.getenv("API_ID", "27788368"))  # Replace with your API ID
API_HASH = os.getenv("API_HASH", "9df7e9ef3d7e4145270045e5e43e1081")  # Replace with your API Hash
BOT_TOKEN = os.getenv("BOT_TOKEN", "7692429836:AAHyUFP6os1A3Hirisl5TV1O5kArGAlAEuQ")  # Replace with your Bot Token
DATABASE_CHANNEL = int(os.getenv("DATABASE_CHANNEL", "-1002465297334"))  # Replace with your channel ID
MONGO_DB_URI = "mongodb+srv://aarshhub:6L1PAPikOnAIHIRA@cluster0.6shiu.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
SEND_IMAGES_AND_VIDEOS = "True"
# Telegram IDs and Usernames
OWNER_ID = int(os.environ.get("OWNER_ID", 67890))  # Replace 67890 with your Telegram user ID
FORCE_SUB_CHANNEL = int(os.environ.get("FORCE_SUB_CHANNEL", -1001234567890))  # Replace with your private channel's Chat ID

# Feature toggles
SEND_IMAGES_AND_VIDEOS = os.environ.get("SEND_IMAGES_AND_VIDEOS", "True").lower() in ("true", "1", "t")
PROTECT_CONTENT = os.environ.get("PROTECT_CONTENT", "True").lower() in ("true", "1", "t")
AUTO_DELETE_TIME = int(os.environ.get("AUTO_DELETE_TIME", 20))  # Time in seconds; default is 1 hour

# Welcome message configuration
WELCOME_IMAGE_ID = os.environ.get("WELCOME_IMAGE_ID", "your_welcome_image_file_id")  # Replace with the file ID of your welcome image
ABOUT_TEXT = """
Creator: This Person
Language: Python3
Library: Pyrogram asyncio 2.1.37
Source Code: [Click here](https://github.com/your-repo)
Channel: xxxxx
Support Group: @xxxx
"""  # Customize with your details
