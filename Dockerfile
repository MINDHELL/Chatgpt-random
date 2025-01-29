FROM python:3.9

WORKDIR /app

# Copy project files
COPY . .

# Install dependencies
RUN pip install -r requirements.txt

# Start the bot
CMD ["python", "bot.py"]
