import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ChatJoinRequestHandler,
    CommandHandler,
    ContextTypes,
)
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g. https://your-app-name.up.railway.app
PORT = int(os.getenv("PORT", 8000))     # Railway provides this env variable automatically

WELCOME_LINK = os.getenv("WELCOME_LINK", "https://your-link.com")

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def auto_accept(update: Update, context: ContextTypes.DEFAULT_TYPE):
    join_request = update.chat_join_request
    user = join_request.from_user
    chat_id = join_request.chat.id
    user_id = user.id

    await context.bot.approve_chat_join_request(chat_id=chat_id, user_id=user_id)
    logging.info(f"Approved join request from {user.full_name}")

    welcome_text = f"👋 Welcome, {user.full_name}!\nClick below to get started:"
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🚀 Open Link", url=WELCOME_LINK)]])

    try:
        await context.bot.send_message(chat_id=user_id, text=welcome_text, reply_markup=keyboard)
    except Exception as e:
        logging.warning(f"Couldn't send message to user {user_id}: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to EM Files Bot!\n\n"
        "📢 Add me to your channel or group as an *Admin*.\n"
        "✅ I will auto-accept join requests for you.",
        parse_mode="Markdown"
    )

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is alive!")

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(ChatJoinRequestHandler(auto_accept))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("check", check))

    # Run webhook on Railway
    await app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_path=f"/webhook/{BOT_TOKEN}",
        webhook_url=f"{WEBHOOK_URL}/webhook/{BOT_TOKEN}"
    )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
