import asyncio
import os
from dotenv import load_dotenv
import logging
from typing import Optional
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import CommandHandler, MessageHandler, filters, ApplicationBuilder, ContextTypes
import uvicorn

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

# Load environment variables
load_dotenv()
# Replace with your actual Telegram Bot Token
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("No TOKEN provided. Please set the TOKEN environment variable.")

TELEGRAM_CHANNEL_ID = "@testbot00X00"
WEBHOOK_URL = "https://home-of-projects-backend.onrender.com/webhook"  # Replace with your actual webhook URL

# Initialize Telegram Application
application = ApplicationBuilder().token(TOKEN).build()

# Initialize FastAPI
app = FastAPI()

# Add CORS middleware
origins = [
    "https://home-of-projects-mini-app.vercel.app/project-form",
    "https://api.telegram.org",
    "http://localhost:3000/project-form"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define handlers for different Telegram events
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    description = (
        "Welcome to our bot! 🎉\n\n"
        "This bot provides useful functionality to connect with our platform.\n"
        "Click the button below to visit the frontend and explore more!"
    )
    frontend_url = "https://home-of-projects-mini-app.vercel.app/"
    keyboard = [
        [InlineKeyboardButton("Visit Frontend 🌐", web_app=WebAppInfo(url=frontend_url))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=description, reply_markup=reply_markup)

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)

# Register handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

# Function to handle received data
async def handle_data(data):
    """
    Handle submitted form data and send a formatted message to the Telegram channel.
    
    Args:
        data (dict): The form data submitted from the frontend.
    """
    try:
        # Access the bot and channel ID
        bot = application.bot
        channel_id = TELEGRAM_CHANNEL_ID

        # Extract data from the form submission
        project_name = data.get("projectName", "Unnamed Project")
        project_description = data.get("projectDescription", "No description provided.")
        telegram_link = data.get("telegramLink")
        linkedin_profile = data.get("linkedinProfile")
        twitter_account = data.get("twitterAccount")
        github_link = data.get("githubLink")
        live_link = data.get("liveLink")
        files = data.get("files", [])

        # Construct the message text with formatting
        message_text = (
    f"{'['+ project_name +']('+ github_link +')' if github_link else 'https://github.com/'}\n"
            f"{project_description}\n\n"
            f"{'🗨️[Telegram](' +  telegram_link + ')' if telegram_link else ''}"
            f"{'|🔗[LinkedIn](' + linkedin_profile + ')' if linkedin_profile else ''}"
            f"{'|🚀[Twitter](' + twitter_account + ')' if twitter_account else ''}"
        )

        # Build Inline Keyboard Buttons for available links
        buttons = []
        if github_link:
            buttons.append(InlineKeyboardButton("GitHub", url=github_link))
        if live_link:
            buttons.append(InlineKeyboardButton("Live Project", url=live_link))
        reply_markup = InlineKeyboardMarkup([buttons]) if buttons else None

        # Check if there's an image to send
        if files and len(files) > 0:
            # Assume the first file is an image URL
            image_url = files[0]
            message = await bot.send_photo(
                chat_id=channel_id,
                photo=image_url,
                caption=message_text,
                parse_mode="Markdown",
                reply_markup=reply_markup,
            )
        else:
            # Send the message without an image
            message = await bot.send_message(
                chat_id=channel_id,
                text=message_text,
                parse_mode="Markdown",
                reply_markup=reply_markup,
            )

        logging.info(f"Message sent successfully: {message.message_id}")
        return {"status": "success", "message_id": message.message_id}

    except Exception as e:
        logging.error(f"Error sending data to the channel: {e}")
        return {"status": "error", "message": str(e)}

# FastAPI endpoint for Telegram webhook
@app.post("/webhook")
async def telegram_webhook(request: Request):
    try:
        update_dict = await request.json()
        logging.info(f"Webhook received: {update_dict}")  # Log the raw update
        update = Update.de_json(update_dict, application.bot)
        logging.info(f"Update object created: {update}")
        await application.initialize()
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
        await application.initialize()  # Initialize the application
        await set_webhook()              # Set the webhook
        logging.info("Bot initialized successfully")
    except Exception as e:
        logging.error(f"Error initializing bot: {e}")
        
# FastAPI root endpoint
@app.get("/")
async def read_root():
    return {"message": "Hello, Render!"}

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
    await initialize_bot()  # Ensure the bot is initialized first
    await run_fastapi()      # Then run the FastAPI server

if __name__ == "__main__":
    asyncio.run(main())
