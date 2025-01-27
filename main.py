import asyncio
import os
from dotenv import load_dotenv
import logging
from typing import Optional
from fastapi import FastAPI, Request, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, InputMedia, InputFile, InputMediaPhoto, InputMediaVideo
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
origins = "https://home-of-projects-mini-app.vercel.app/"

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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
        if github_link:
            project_link = github_link
        else:
            project_link = live_link
        if username and username.startswith("@"):
            username = username[1:] 
        # Prepend the appropriate URLs to the usernames
        twitter_url = f"https://twitter.com/{twitter_account}" if twitter_account else None
        tg_link = f"http://t.me/{username}"
        
        message_text = (
            f"[{project_name}]({project_link})\n"
            f"{project_description}\n\n"
            f"{'[Github](' + github_link + ')' if github_link else ''}"
            f"{' | [Website](' + live_link + ')' if live_link else ''}\n"
            f"{'[Telegram](' + tg_link + ')' if tg_link else ''}"
            f"{' | [LinkedIn](' + linkedin_profile + ')' if linkedin_profile else ''}"
            f"{' | [Twitter](' + twitter_url + ')' if twitter_account else ''}"
        )


        
        if files and len(files) > 0:
            media_group = []
            for i, file in enumerate(files):
                base64_data = file.split(",")[1]
                file_bytes = base64.b64decode(base64_data)
                file_extension = file.split(";")[0].split("/")[1]

                # Determine the media type
                if file_extension in ["jpg", "jpeg", "png"]:
                    media = InputMediaPhoto(
                        media=BytesIO(file_bytes),
                        caption=message_text if i == 0 else None,  # Captions can only be set for the first media..!
                        parse_mode="Markdown" if i == 0 else None
                    )
                elif file_extension in ["mp4", "mov"]:
                    media = InputMediaVideo(
                        media=BytesIO(file_bytes),
                        caption=message_text if i == 0 else None,  # Captions can only be set for the first media..!
                        parse_mode="Markdown" if i == 0 else None
                    )
                else:
                    continue  # Skip unsupported file types

                media_group.append(media)

            if media_group:
                logging.info("Sending media group...")
                await bot.send_media_group(
                    chat_id=channel_id,
                    media=media_group
                )
        else:
            logging.info("No base64 image/video file found in the submission.")
            await bot.send_message(
                chat_id=channel_id,
                text=message_text,
                parse_mode="Markdown"
            )
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
