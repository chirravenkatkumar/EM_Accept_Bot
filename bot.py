import os
from dotenv import load_dotenv
from pymongo import MongoClient
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from telegram.ext import (
    ApplicationBuilder,
    ChatJoinRequestHandler,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# Load env variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
WELCOME_LINK = os.getenv("WELCOME_LINK", "https://your-link.com")
MONGO_URI = os.getenv("MONGO_URI")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# MongoDB setup
client = MongoClient(MONGO_URI)
db = client["em_bot"]
users_collection = db["users"]

def save_user(user_id, name):
    if not users_collection.find_one({"_id": user_id}):
        users_collection.insert_one({"_id": user_id, "name": name})

def get_all_user_ids():
    return [user["_id"] for user in users_collection.find()]

def get_user_count():
    return users_collection.count_documents({})

# Auto-approve join request
async def auto_accept(update: Update, context: ContextTypes.DEFAULT_TYPE):
    request = update.chat_join_request
    user = request.from_user
    chat_id = request.chat.id
    user_id = user.id

    await context.bot.approve_chat_join_request(chat_id=chat_id, user_id=user_id)
    save_user(user_id, user.full_name)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Open Link", url=WELCOME_LINK)]
    ])
    welcome_msg = f"👋 Welcome, {user.full_name}!\nClick below to get started:"
    try:
        await context.bot.send_message(chat_id=user_id, text=welcome_msg, reply_markup=keyboard)
    except Exception as e:
        print(f"⚠️ Couldn't send message to {user_id}: {e}")

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    save_user(user.id, user.full_name)
    await update.message.reply_text(
        "👋 Welcome to EM Bot!\n\n"
        "📢 Add me as admin in your group to auto-approve join requests.",
        parse_mode="Markdown"
    )

# /check
async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is alive!")

# /stats (admin only)
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("❌ You are not authorized.")
    total = get_user_count()
    await update.message.reply_text(f"📊 Total Users: {total}")

# /broadcast
broadcast_mode = {}

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("❌ You are not authorized.")
    await update.message.reply_text("📢 Please send the message (text/photo/forward) to broadcast.")
    broadcast_mode["active"] = True

async def handle_broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not broadcast_mode.get("active") or update.effective_user.id != ADMIN_ID:
        return

    broadcast_mode["active"] = False
    message: Message = update.message
    user_ids = get_all_user_ids()

    sent, failed = 0, 0
    for uid in user_ids:
        try:
            if message.text:
                await context.bot.send_message(chat_id=uid, text=message.text)
            elif message.photo:
                await context.bot.send_photo(chat_id=uid, photo=message.photo[-1].file_id, caption=message.caption)
            else:
                await context.bot.forward_message(chat_id=uid, from_chat_id=message.chat_id, message_id=message.message_id)
            sent += 1
        except Exception as e:
            print(f"❌ Failed to send to {uid}: {e}")
            failed += 1

    await update.message.reply_text(f"✅ Broadcast sent to {sent} users.\n❌ Failed: {failed}")

# Run bot
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(ChatJoinRequestHandler(auto_accept))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("check", check))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(MessageHandler(filters.ALL, handle_broadcast_message))

    print("🚀 Bot is running with MongoDB + Admin Broadcast...")
    app.run_polling()
