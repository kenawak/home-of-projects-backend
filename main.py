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
WEBHOOK_URL = "https://home-of-projects-backend.onrender.com/webhook"  # Replace with your actual webhook URL

# Initialize Telegram Application
application = ApplicationBuilder().token(TOKEN).build()

# Define handlers for different Telegram events
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")

# Register handlers
application.add_handler(CommandHandler("start", start))

# Function to set the webhook
async def set_webhook():
    await application.bot.set_webhook(WEBHOOK_URL)

# Function to initialize the bot
async def initialize_bot():
    await application.initialize()
    await set_webhook()

# Initialize FastAPI
app = FastAPI()

# FastAPI root endpoint
@app.get("/")
async def read_root():
    return {"message": "Hello, World!"}

# FastAPI endpoint for Telegram webhook
@app.post("/webhook")
async def telegram_webhook(update: dict):
    update = Update.de_json(update, application.bot)
    await application.process_update(update)
    return {"status": "success"}

# Function to run FastAPI
async def run_fastapi():
    config = uvicorn.Config(app, host="0.0.0.0", port=8000)
    server = uvicorn.Server(config)
    await server.serve()

# Function to run both FastAPI and Telegram bot concurrently
async def main():
    bot_task = asyncio.create_task(initialize_bot())
    fastapi_task = asyncio.create_task(run_fastapi())
    await asyncio.gather(bot_task, fastapi_task)

if __name__ == "__main__":
    asyncio.run(main())