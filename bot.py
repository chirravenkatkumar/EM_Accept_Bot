from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ChatJoinRequestHandler,
    CommandHandler,
    ContextTypes,
)
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WELCOME_LINK = os.getenv("WELCOME_LINK", "https://your-link.com")
APP_URL = os.getenv("APP_URL")  # e.g., https://your-railway-app.up.railway.app

# ✅ Auto-approve join requests
async def auto_accept(update: Update, context: ContextTypes.DEFAULT_TYPE):
    join_request = update.chat_join_request
    user = join_request.from_user
    chat_id = join_request.chat.id
    user_id = user.id

    await context.bot.approve_chat_join_request(chat_id=chat_id, user_id=user_id)
    print(f"✅ Approved: {user.full_name}")

    welcome_text = f"👋 Welcome, {user.full_name}!\nClick the button below to get started:"
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("🚀 Open Link", url=WELCOME_LINK)]]
    )

    try:
        await context.bot.send_message(chat_id=user_id, text=welcome_text, reply_markup=keyboard)
    except Exception as e:
        print(f"⚠️ Couldn't send message: {e}")

# ✅ /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to EM Files Bot!\n\n"
        "📢 Add me to your channel or group as an *Admin*.\n"
        "✅ I will auto-accept join requests for you.",
        parse_mode="Markdown"
    )

# ✅ /check command
async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is alive!")

# ✅ Webhook-based run
if __name__ == '__main__':
    import asyncio

    async def main():
        app = ApplicationBuilder().token(BOT_TOKEN).build()

        app.add_handler(ChatJoinRequestHandler(auto_accept))
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("check", check))

        print("🚀 Starting bot with webhook...")

        PORT = int(os.environ.get("PORT", "8443"))
        WEBHOOK_PATH = f"/{BOT_TOKEN}"
        WEBHOOK_URL = f"{APP_URL}{WEBHOOK_PATH}"  # Make sure APP_URL is set in Railway

        await app.bot.delete_webhook(drop_pending_updates=True)  # Avoid Conflict error
        await app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_path=WEBHOOK_PATH,
            webhook_url=WEBHOOK_URL
        )

    asyncio.run(main())
