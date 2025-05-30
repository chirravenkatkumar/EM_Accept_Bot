import os
import json
from dotenv import load_dotenv
from telegram import Update, Message
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Load env variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
USER_DB = "users.json"
PENDING_BROADCAST = set()

# Ensure DB file
if not os.path.exists(USER_DB):
    with open(USER_DB, "w") as f:
        json.dump([], f)

# Save user ID
def save_user(user_id: int):
    with open(USER_DB, "r") as f:
        users = json.load(f)
    if user_id not in users:
        users.append(user_id)
        with open(USER_DB, "w") as f:
            json.dump(users, f)

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    save_user(user_id)
    await update.message.reply_text("👋 Welcome to EM Bot! You're subscribed!")

# /broadcast command
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return await update.message.reply_text("❌ You're not authorized.")

    PENDING_BROADCAST.add(user_id)
    await update.message.reply_text("📢 Please send the message you want to broadcast (text, image, etc).")

# Handle the next message for broadcast
async def handle_broadcast_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID or user_id not in PENDING_BROADCAST:
        return

    # Remove pending status
    PENDING_BROADCAST.remove(user_id)

    with open(USER_DB, "r") as f:
        users = json.load(f)

    count, failed = 0, 0
    for uid in users:
        try:
            await update.message.copy(chat_id=uid)
            count += 1
        except Exception as e:
            failed += 1
            print(f"Failed to send to {uid}: {e}")

    await update.message.reply_text(f"✅ Broadcast sent to {count} users.\n❌ Failed: {failed}")

# /stats command
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("❌ You're not authorized.")

    with open(USER_DB, "r") as f:
        users = json.load(f)
    await update.message.reply_text(f"📊 Total subscribers: {len(users)}")

# /check command
async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is running!")

# Run the bot
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("check", check))
    app.add_handler(MessageHandler(filters.ALL, handle_broadcast_content))

    print("🚀 Bot running with broadcast support...")
    app.run_polling()
