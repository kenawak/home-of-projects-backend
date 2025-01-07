import asyncio
import os
import logging
from typing import Optional
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import CommandHandler, ApplicationBuilder, ContextTypes
import uvicorn

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

# Replace with your actual Telegram Bot Token
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("No TOKEN provided. Please set the TOKEN environment variable.")

TELEGRAM_CHANNEL_ID = "@testbot00X00"
WEBHOOK_URL = "https://home-of-projects-backend.onrender.com/webhook"  # Replace with your actual webhook URL

# Initialize Telegram Application
application = ApplicationBuilder().token(TOKEN).build()

# Define handlers for different Telegram events
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(f"Received /start command from {update.effective_chat.id}")
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")

# Register handlers
application.add_handler(CommandHandler("start", start))

# Function to handle received data
async def handle_data(data):
    context = application.bot
    channel_id = TELEGRAM_CHANNEL_ID
    await context.send_message(chat_id=channel_id, text=f"Received data: {data}")

# Function to set the webhook
async def set_webhook():
    try:
        await application.bot.set_webhook(WEBHOOK_URL)
        logging.info(f"Webhook set to {WEBHOOK_URL}")
    except Exception as e:
        logging.error(f"Error setting webhook: {e}")

# Function to initialize the bot
async def initialize_bot():
    try:
        await application.initialize()
        await set_webhook()
        logging.info("Bot initialized successfully")
    except Exception as e:
        logging.error(f"Error initializing bot: {e}")

# Initialize FastAPI
app = FastAPI()

# FastAPI root endpoint
@app.get("/")
async def read_root():
    return {"message": "Hello, Render!"}

# FastAPI endpoint for Telegram webhook
@app.post("/webhook")
async def telegram_webhook(request: Request):
    update_dict = await request.json()
    update = Update.de_json(update_dict, application.bot)
    await application.process_update(update)
    return {"status": "success"}

# FastAPI endpoint to receive data
@app.post("/data")
async def receive_data(request: Request):
    data = await request.json()
    await handle_data(data)
    return {"status": "success", "data": data}

# Function to run FastAPI
async def run_fastapi():
    port = int(os.getenv("PORT", 8000))
    config = uvicorn.Config(app, host="0.0.0.0", port=port)
    server = uvicorn.Server(config)
    await server.serve()

# Function to run both FastAPI and Telegram bot concurrently
async def main():
    bot_task = asyncio.create_task(initialize_bot())
    fastapi_task = asyncio.create_task(run_fastapi())
    await asyncio.gather(bot_task, fastapi_task)

if __name__ == "__main__":
    asyncio.run(main())
