import asyncio
import os
from dotenv import load_dotenv
import logging
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, filters, ApplicationBuilder, ContextTypes
import uvicorn

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

# Load environment variables
load_dotenv()
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("No TOKEN provided. Please set the TOKEN environment variable.")

TELEGRAM_CHANNEL_ID = "@testbot00X00"
WEBHOOK_URL = "https://home-of-projects-backend.onrender.com/webhook"  # Replace with your actual webhook URL

# Initialize Telegram Application
application = ApplicationBuilder().token(TOKEN).build()

# Initialize FastAPI
app = FastAPI()

# Define handlers for different Telegram events
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    frontend_url = "https://your-frontend-url.com"  # Replace with your actual frontend URL
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"I'm a bot, please talk to me! Use this URL: {frontend_url}")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)

# Register handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

# FastAPI endpoint for Telegram webhook
@app.post("/webhook")
async def telegram_webhook(request: Request):
    try:
        # Ensure the application is initialized
        if not application.bot:
            logging.warning("Application was not initialized. Initializing now...")
            await application.initialize()
        
        update_dict = await request.json()
        logging.info(f"Webhook received: {update_dict}")  # Log the raw update
        update = Update.de_json(update_dict, application.bot)
        await application.process_update(update)
        return {"status": "success"}
    except Exception as e:
        logging.error(f"Error processing webhook update: {e}")
        return {"status": "error", "message": str(e)}

# Function to set the webhook
async def set_webhook():
    try:
        webhook_result = await application.bot.set_webhook(WEBHOOK_URL)
        if webhook_result:
            logging.info(f"Webhook set successfully to {WEBHOOK_URL}")
        else:
            logging.error("Failed to set webhook.")
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

# FastAPI root endpoint
@app.get("/")
async def read_root():
    return {"message": "Hello, Render!"}

# Function to run FastAPI
async def run_fastapi():
    port = int(os.getenv("PORT", 8000))
    config = uvicorn.Config(app, host="0.0.0.0", port=port)
    server = uvicorn.Server(config)
    await server.serve()

# Function to run both FastAPI and Telegram bot concurrently
async def main():
    await initialize_bot()
    await run_fastapi()

if __name__ == "__main__":
    asyncio.run(main())
