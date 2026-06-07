import os
import json
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# ================= CONFIG =================
TOKEN = os.getenv('TOKEN')
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

# ================= PRICE =================
PRICES = {
    "Facebook": {"Follow sale": 28, "Follow clone": 26.2},
    "TikTok": {"Follow clone": 47.8, "S4 Follow": 48.9, "S6 Follow": 34.9},
    "Instagram": {"S1 Follow": 45, "Follow Tây": 33.63}
}

menu = ReplyKeyboardMarkup(
    [["📦 Dịch vụ"], ["💰 Nạp tiền", "👤 Tài khoản"], ["📊 Đơn hàng", "📞 Liên hệ Admin"]], 
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

    if query.data in ["fb", "tt", "ig"]:
        platform = {"fb": "Facebook", "tt": "TikTok", "ig": "Instagram"}[query.data]
        STATE[uid] = {"step": "service", "platform": platform}
        keyboard = [[InlineKeyboardButton(f"{k} - {v}đ", callback_data=f"svc|{k}")] for k, v in PRICES[platform].items()]
        await query.message.reply_text(f"📦 CHỌN DỊCH VỤ: {platform}", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("svc|"):
        service = query.data.split("|")[1]
        STATE[uid]["service"] = service
        STATE[uid]["step"] = "qty"
        await query.message.reply_text("🔢 Vui lòng nhập SỐ LƯỢNG bạn cần tăng:")

    elif query.data == "confirm_order":
        # Khi xác nhận, chuyển qua bước nhập link
        STATE[uid]["step"] = "link"
        await query.message.edit_text("🔗 Đã xác nhận! Hãy gửi LINK (profile/bài viết) cần tăng:")

    elif query.data == "cancel_order":
        STATE.pop(uid, None)
        await query.message.edit_text("❌ Giao dịch đã được hủy.")

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.message.chat_id)
    text = update.message.text
    data = load()
    init_user(data, uid)

    if text == "📦 Dịch vụ":
        STATE[uid] = {"step": "platform"}
        await update.message.reply_text("🌐 CHỌN NỀN TẢNG:", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📘 Facebook", callback_data="fb")],
            [InlineKeyboardButton("🎵 TikTok", callback_data="tt")],
            [InlineKeyboardButton("📸 Instagram", callback_data="ig")]
        ]))

    elif text == "💰 Nạp tiền":
        await update.message.reply_text(
            "┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
            "┃        💰 NẠP TIỀN           ┃\n"
            "┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫\n"
            "┃ 🏦 Ngân hàng: ACB           ┃\n"
            "┃ 🔢 STK: 26084821            ┃\n"
            "┃ 👤 CTK: DINH HOANG VIET ANH ┃\n"
            "┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫\n"
            "┃ 📌 Nhập số tiền tối thiểu   ┃\n"
            "┃    50.000 VNĐ để nạp        ┃\n"
            "┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛"
        )
        STATE[uid] = {"step": "deposit_amount"}

    elif uid in STATE and STATE[uid].get("step") == "qty":
        try:
            qty = int(text)
            platform = STATE[uid]["platform"]
            service = STATE[uid]["service"]
            total = PRICES[platform][service] * qty
            STATE[uid].update({"qty": qty, "total": total, "step": "confirm_order"})
            
            await update.message.reply_text(
                f"╭────────────────────────────╮\n"
                f"│      📋 XÁC NHẬN ĐƠN        │\n"
                f"├────────────────────────────┤\n"
                f"│ 🔢 SL: {qty}                │\n"
                f"│ 💰 Tổng: {total:,.1f} VNĐ         │\n"
                f"╰────────────────────────────╯\n"
                "📌 Bạn có muốn đặt đơn này không?",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ XÁC NHẬN", callback_data="confirm_order"),
                     InlineKeyboardButton("❌ HỦY", callback_data="cancel_order")]
                ])
            )
        except:
            await update.message.reply_text("❌ Vui lòng nhập số lượng bằng số!")

    # ... (Giữ nguyên các xử lý link, account, orders của bạn ở đây)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    print("VIET ANH AUTO IS RUNNING...")
    app.run_polling()

if __name__ == "__main__":
    main()
