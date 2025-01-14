import asyncio
import os
from dotenv import load_dotenv
import logging
from typing import Optional
from fastapi import FastAPI, Request, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import CommandHandler, MessageHandler, filters, ApplicationBuilder, ContextTypes
import uvicorn
import base64
from io import BytesIO

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

TELEGRAM_CHANNEL_ID = "@homeofprojects"
WEBHOOK_URL = "https://home-of-projects-backend.onrender.com/webhook"  # Replace with your actual webhook URL

# Initialize Telegram Application
application = ApplicationBuilder().token(TOKEN).build()

# Initialize FastAPI
app = FastAPI()

# Add CORS middleware
origins = [
    "https://home-of-projects-mini-app.vercel.app",
    "https://api.telegram.org",
    "http://localhost:3000/"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_link = f"tg://user?id={user.id}"
    description = (
    "🚀 **Turn Your Ideas into a Spotlight!** 🚀\n\n"
    "Welcome to the [Home of Projects](https://t.me/homeofprojects)🌟\n"
    "✨ Why Upload?\n\n"
    "- 🗣️ **Valuable Feedback**: Gain insights from a vibrant tech community.\n"
    "- 🌍 **Community Exposure**: Share your work with the community.\n"
    "- 🔄 **Connect & Collaborate**: Connect with like-minded innovators\n\n"
    "💻 Use the mini-app to upload your projects!📖\n\n"
    "🎯 Ready to Shine? Post your project and take center stage today!\n"
    "[🌐Explore Projects by the community](https://t.me/homeofprojects)"
)

    frontend_url = "https://home-of-projects-mini-app.vercel.app/"
    keyboard = [
        [InlineKeyboardButton("Upload Project🌐", web_app=WebAppInfo(url=frontend_url))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    image_path = "image.png"  # Path to the image file
    with open(image_path, 'rb') as image_file:
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=image_file, caption=description, reply_markup=reply_markup, parse_mode="Markdown")
    # await context.bot.send_message(chat_id=update.effective_chat.id, photo= text=description, reply_markup=reply_markup, parse_mode="Markdown")
    
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)

# Register handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

# Function to handle received data
async def handle_data(data, files: Optional[list[UploadFile]] = None):
    """
    Handle submitted form data and send a formatted message to the Telegram channel.
    
    Args:
        data (dict): The form data submitted from the frontend.
        files (list[UploadFile], optional): List of uploaded files.
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
        username = data.get("telegramUsername") 
        # Prepend the appropriate URLs to the usernames
        twitter_url = f"https://twitter.com/{twitter_account}" if twitter_account else None
        tg_link = f"http://t.me/{username}"
        # Construct the message text with formatting
        message_text = (
            f"{'[' + project_name + '](' + github_link + ')' if github_link else project_name}\n"
            f"{project_description}\n\n"
            f"{'[Telegram](' + tg_link + ')' if username else ''}"
            f"{'[LinkedIn ](' + linkedin_profile + ')' if linkedin_profile else ''}"
            f"{'| [Twitter](' + twitter_url + ')' if twitter_account else ''} \\n"
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
            logging.info("Base64 image file found in the submission.")
            # Decode the base64 string
            base64_data = files[0].split(",")[1]  # Remove the data URI prefix
            image_bytes = base64.b64decode(base64_data)

            # Send the image file directly
            message = await bot.send_photo(
                chat_id=channel_id,
                photo=BytesIO(image_bytes),
                caption=message_text,
                parse_mode="Markdown",
                reply_markup=reply_markup,
            )
        else:
            logging.info("No base64 image file found in the submission.")
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
    """
    Endpoint to handle data from the frontend.
    """
    logging.info("Data endpoint called")
    try:
        # Extract JSON data from the request
        data = await request.json()

        # Check for base64-encoded file in the "files" field
        files = data.get("files", [])
        await handle_data(data, files)
        return {"status": "success", "data": data}
    except Exception as e:
        logging.error(f"Error processing request: {e}")
        return {"status": "error", "message": str(e)}
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
