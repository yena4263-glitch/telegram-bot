import os
import json
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# ================= CONFIG =================
TOKEN = " 8826457177:AAEdk9dN3PjDYQd-_5smTs-cH8ChqwSjTEw"
ADMIN_ID = 8348914397 
ADMIN_CONTACT = "@Vietanhenter" 
DATA_FILE = "data.json"

STATE = {}
DEPOSITS = {}

# ================= HÀM HỖ TRỢ =================
def khung(title, content):
    return f"╭─── {title} ───╮\n{content}\n╰──────────────╯"

def is_admin(uid):
    return str(uid) == str(ADMIN_ID)

def load():
    if not os.path.exists(DATA_FILE): return {"users": {}, "orders": {}}
    try:
        with open(DATA_FILE, "r") as f: return json.load(f)
    except: return {"users": {}, "orders": {}}

def save(data):
    with open(DATA_FILE, "w") as f: json.dump(data, f, indent=2)

def init_user(data, uid):
    if uid not in data["users"]: 
        data["users"][uid] = {"balance": 0}
        save(data)

PRICES = {
    "Facebook": {"Follow sale": 28, "Follow clone": 26.2},
    "TikTok": {"Follow clone": 47.8, "S4 Follow": 48.9, "S6 Follow": 34.9},
    "Instagram": {"S1 Follow": 45, "Follow Tây": 33.63}
}

# Menu đã thêm nút "🏠 Trang chủ"
menu = ReplyKeyboardMarkup(
    [["📦 Dịch vụ"], ["💰 Nạp tiền", "👤 Tài khoản"], ["📊 Đơn hàng", "☎ Liên hệ admin"], ["🏠 Trang chủ"]],
    resize_keyboard=True
)

# ================= CALLBACK =================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = str(query.message.chat_id)
    
    if query.data.startswith(("dep|", "stt|")) and not is_admin(uid):
        await query.answer("❌ Bạn không có quyền!")
        return

    if query.data.startswith("confirm_dep|"):
        _, code = query.data.split("|")
        dep = DEPOSITS.get(code)
        if dep:
            await query.edit_message_text(khung("✅ ĐÃ GỬI", "Vui lòng chờ Admin duyệt lệnh nạp!"))
            await context.bot.send_message(ADMIN_ID, khung("💰 NẠP TIỀN MỚI", f"👤 User: {uid}\n💵 Số tiền: {dep['amount']:,.0f}đ\n🔢 Mã: {code}"),
                                         reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ DUYỆT", callback_data=f"dep|ok|{code}"), InlineKeyboardButton("❌ HỦY", callback_data=f"dep|no|{code}")]]))
        return

    data = load()
    if query.data.startswith(("fb", "tt", "ig")):
        await query.answer()
        platform = {"fb": "Facebook", "tt": "TikTok", "ig": "Instagram"}[query.data]
        STATE[uid] = {"step": "service", "platform": platform}
        kb = [[InlineKeyboardButton(f"{k} - {v}đ", callback_data=f"svc|{k}")] for k, v in PRICES[platform].items()]
        await query.message.reply_text(khung("📦 NỀN TẢNG", platform), reply_markup=InlineKeyboardMarkup(kb))
    
    elif query.data.startswith("svc|"):
        await query.answer()
        service = query.data.split("|")[1]
        STATE[uid].update({"service": service, "step": "qty"})
        await query.message.reply_text(khung("🔢 NHẬP SỐ LƯỢNG", "Vui lòng nhập số lượng bạn cần:"))

    elif query.data.startswith("dep|"):
        await query.answer("Đang xử lý...")
        _, action, code = query.data.split("|")
        if code in DEPOSITS:
            dep = DEPOSITS[code]
            user_id = str(dep["user"])
            if action == "ok":
                data = load()
                if user_id not in data["users"]: data["users"][user_id] = {"balance": 0}
                data["users"][user_id]["balance"] += dep["amount"]
                save(data)
                await context.bot.send_message(int(user_id), khung("✅ NẠP TIỀN", f"Cộng {dep['amount']:,.0f}đ thành công!"))
                await query.edit_message_text(khung("✅ ĐÃ DUYỆT", f"Đã duyệt {dep['amount']:,.0f}đ cho {user_id}"))
            else:
                await context.bot.send_message(int(user_id), khung("❌ NẠP TIỀN", "Yêu cầu đã bị hủy."))
                await query.edit_message_text(khung("❌ ĐÃ HỦY", f"Đã hủy nạp cho {user_id}"))
            del DEPOSITS[code]

# ================= HANDLE TEXT =================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.message.chat_id)
    text = update.message.text
    data = load()
    init_user(data, uid)

    if text == "🏠 Trang chủ" or text == "/start":
        await update.message.reply_text(khung("🤖 VIET ANH AUTO BOT", "Chào mừng bạn đến với hệ thống dịch vụ tự động!"), reply_markup=menu)
    elif text == "📦 Dịch vụ":
        await update.message.reply_text(khung("📦 CHỌN DỊCH VỤ", "Chọn nền tảng:"), reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📘 Facebook", callback_data="fb")],
            [InlineKeyboardButton("🎵 TikTok", callback_data="tt")],
            [InlineKeyboardButton("📸 Instagram", callback_data="ig")]
        ]))
    elif text == "💰 Nạp tiền":
        STATE[uid] = {"step": "deposit_amount"}
        await update.message.reply_text(khung("💰 NẠP TIỀN", "🏦 ACB: 26084821\n👤 DINH HOANG VIET ANH\n📌 Nhập số tiền (>= 50k):"))
    elif text == "👤 Tài khoản":
        balance = data["users"].get(uid, {}).get("balance", 0)
        await update.message.reply_text(khung("👤 TÀI KHOẢN", f"💰 Số dư: {balance:,.0f} VNĐ"))
    elif text == "☎ Liên hệ admin":
        await update.message.reply_text(khung("☎ LIÊN HỆ ADMIN", f"Mọi vấn đề vui lòng liên hệ:\n👉 {ADMIN_CONTACT}"))
    elif uid in STATE and STATE[uid].get("step") == "deposit_amount":
        try:
            amount = float(text)
            if amount < 50000: raise ValueError
            code = f"DEP{int(time.time())}"
            DEPOSITS[code] = {"user": uid, "amount": amount}
            STATE.pop(uid)
            await update.message.reply_text(khung("📌 XÁC NHẬN", f"Số tiền: {amount:,.0f}đ\nMã ck: {code}\n\nẤn nút để báo Admin duyệt:"),
                                         reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ ĐÃ CHUYỂN TIỀN", callback_data=f"confirm_dep|{code}")]]))
        except: await update.message.reply_text("❌ Nhập số tiền hợp lệ (>= 50.000)")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", handle)) # Dùng hàm handle chung cho /start
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    app.run_polling()

if __name__ == "__main__": main()
