import os, sys, json, threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ========= ENV CONFIG =========
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
DATA_FILE = "data.json"

if not BOT_TOKEN or not ADMIN_ID:
    print("❌ BOT_TOKEN বা ADMIN_ID সেট করা হয়নি")
    sys.exit(1)

ADMIN_ID = int(ADMIN_ID)
# ==============================


# ========= FLASK (KEEP ALIVE) =========
web = Flask(__name__)

@web.route("/")
def home():
    return "✅ Task Tracker Bot is alive!"

def run_web():
    web.run(host="0.0.0.0", port=10000)
# ====================================


# ---------- Data Utils ----------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def is_admin(update: Update):
    return update.effective_user.id == ADMIN_ID


# ---------- Commands ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Work & Reward Tracker Bot\n\n"
        "👀 সবাই /list ও /details দিয়ে হিসাব দেখতে পারবে\n"
        "🔐 শুধু Admin কাজ ও পেমেন্ট আপডেট করতে পারবে"
    )


# ➕ Add work
async def add_work(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return await update.message.reply_text("❌ এই কমান্ড শুধু Admin ব্যবহার করতে পারবে")

    try:
        name = context.args[0]
        amount = int(context.args[1])
    except:
        return await update.message.reply_text("ব্যবহার: /add নাম সংখ্যা")

    data = load_data()

    if name not in data:
        data[name] = {"total": 0, "today": 0, "due": 0, "paid_amount": 0}

    data[name]["total"] += amount
    data[name]["today"] += amount
    data[name]["due"] += amount

    save_data(data)
    await update.message.reply_text(f"✅ {name} আজকে {amount}টা কাজ করেছে")


# 💰 Payment
async def pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return await update.message.reply_text("❌ শুধু Admin")

    try:
        name = context.args[0]
        amount = int(context.args[1])
    except:
        return await update.message.reply_text("ব্যবহার: /pay নাম টাকা")

    data = load_data()
    if name not in data:
        return await update.message.reply_text("❌ এই নাম পাওয়া যায়নি")

    data[name]["paid_amount"] += amount
    save_data(data)

    await update.message.reply_text(f"💰 {name} কে {amount} টাকা দেওয়া হয়েছে")


# 🔄 Set due
async def set_due(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return await update.message.reply_text("❌ শুধু Admin")

    try:
        name = context.args[0]
        amount = int(context.args[1])
    except:
        return await update.message.reply_text("ব্যবহার: /setdue নাম সংখ্যা")

    data = load_data()
    if name not in data:
        return await update.message.reply_text("❌ এই নাম নেই")

    data[name]["due"] = amount
    save_data(data)

    await update.message.reply_text(f"⏳ {name} এর বাকি কাজ সেট করা হয়েছে: {amount}")


# 📋 Reset today
async def reset_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return await update.message.reply_text("❌ শুধু Admin")

    data = load_data()
    for u in data:
        data[u]["today"] = 0

    save_data(data)
    await update.message.reply_text("🔄 আজকের কাজ রিসেট করা হয়েছে")


# 📊 List
async def list_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    if not data:
        return await update.message.reply_text("এখনো কোনো ডাটা নেই")

    msg = "⏳ চলমান কাজের তালিকা\n\n"
    for name, u in sorted(data.items(), key=lambda x: x[1]["total"], reverse=True):
        msg += f"🔹 {name} — মোট: {u['total']} | আজ: {u['today']} | বাকি: {u['due']}\n"

    msg += "\n(কাউন্টডাউন চলছে ⏱️)"
    await update.message.reply_text(msg)


# 👤 Details
async def details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        name = context.args[0]
    except:
        return await update.message.reply_text("ব্যবহার: /details নাম")

    data = load_data()
    if name not in data:
        return await update.message.reply_text("❌ তথ্য পাওয়া যায়নি")

    u = data[name]
    text = (
        f"📊 কাজ ও পেমেন্ট হিসাব\n\n"
        f"👤 নাম: {name}\n"
        f"✅ মোট কাজ: {u['total']}\n"
        f"📅 আজকের কাজ: {u['today']}\n"
        f"⏳ পেমেন্ট বাকি কাজ: {u['due']}\n"
        f"💰 পরিশোধ করা টাকা: {u['paid_amount']}"
    )
    await update.message.reply_text(text)


# ---------- Telegram Bot ----------
def run_bot():
    bot = ApplicationBuilder().token(BOT_TOKEN).build()

    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CommandHandler("add", add_work))
    bot.add_handler(CommandHandler("pay", pay))
    bot.add_handler(CommandHandler("setdue", set_due))
    bot.add_handler(CommandHandler("reset_today", reset_today))
    bot.add_handler(CommandHandler("list", list_all))
    bot.add_handler(CommandHandler("details", details))

    print("🤖 Telegram Bot running...")
    bot.run_polling()


# ---------- Main ----------
if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    run_bot()
