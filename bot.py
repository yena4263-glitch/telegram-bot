import os
import json
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# ================= CONFIG =================
TOKEN = os.getenv('TOKEN') # Đảm bảo bạn đã thêm biến TOKEN vào Settings của Render
ADMIN_ID = 8348914397
ADMIN = "@Vietanhenter"
DATA_FILE = "data.json"

STATE = {}
DEPOSITS = {}

# ================= DATA =================
def load():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {"users": {}, "orders": {}}

def save(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def init_user(data, uid):
    if uid not in data["users"]:
        data["users"][uid] = {"balance": 0}

# ================= PRICE & MENU =================
PRICES = {
    "Facebook": {"Follow sale": 28, "Follow clone": 26.2},
    "TikTok": {"Follow clone": 47.8, "S4 Follow": 48.9, "S6 Follow": 34.9},
    "Instagram": {"S1 Follow": 45, "Follow Tây": 33.63}
}

menu = ReplyKeyboardMarkup(
    [["📦 Dịch vụ"], ["💰 Nạp tiền", "👤 Tài khoản"], ["📊 Đơn hàng", "☎ Liên hệ Admin"]], 
    resize_keyboard=True
)

# ================= HANDLERS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.message.chat_id)
    data = load()
    init_user(data, uid)
    save(data)
    await update.message.reply_text(
        "╔════════════════════════════╗\n"
        "║     🚀 VIỆT ANH AUTO       ║\n"
        "╠════════════════════════════╣\n"
        "║ Dịch vụ SMM Uy tín - Chất  ║\n"
        "╚════════════════════════════╝",
        reply_markup=menu
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = str(query.message.chat_id)
    data = load()
    
    # Xử lý logic nút bấm tại đây (giữ nguyên logic cũ của bạn)
    # ... (Các phần if/elif query.data của bạn)

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.message.chat_id)
    text = update.message.text
    data = load()
    init_user(data, uid)
    
    # Xử lý logic tin nhắn tại đây (giữ nguyên logic cũ của bạn)
    # ... (Các phần if/elif text == ... của bạn)

# ================= RUN =================
def main():
    if not TOKEN:
        print("LỖI: Chưa cấu hình TOKEN!")
        return
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    print("VIET ANH AUTO IS RUNNING...")
    app.run_polling()

if __name__ == "__main__":
    main()
