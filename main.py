import os
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, filters, Application

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

# Load environment variables
load_dotenv()
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("No TOKEN provided. Please set the TOKEN environment variable.")

WEBHOOK_URL = "https://home-of-projects-backend.onrender.com/webhook"  # Replace with your actual webhook URL

# Initialize FastAPI
app = FastAPI()

# Create the Telegram Application
application = Application.builder().token(TOKEN).build()

# Define handlers
async def start(update: Update, context):
    frontend_url = "https://your-frontend-url.com"  # Replace with your actual frontend URL
    await update.message.reply_text(f"I'm a bot, please talk to me! Use this URL: {frontend_url}")

async def echo(update: Update, context):
    await update.message.reply_text(update.message.text)

# Add handlers to the application
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

# FastAPI endpoint for Telegram webhook
@app.post("/webhook")
async def telegram_webhook(request: Request):
    try:
        update_dict = await request.json()
        update = Update.de_json(update_dict, application.bot)
        # Process the update
        await application.process_update(update)
        return {"status": "success"}
    except Exception as e:
        logging.error(f"Error processing webhook update: {e}")
        return {"status": "error", "message": str(e)}

# Endpoint to test server
@app.get("/")
async def read_root():
    return {"message": "Hello, Render!"}

# Set the webhook during startup
@app.on_event("startup")
async def on_startup():
    try:
        await application.bot.set_webhook(WEBHOOK_URL)
        logging.info(f"Webhook set successfully to {WEBHOOK_URL}")
    except Exception as e:
        logging.error(f"Error setting webhook: {e}")
