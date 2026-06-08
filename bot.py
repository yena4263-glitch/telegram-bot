import os
import json
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# ================= CONFIG =================
TOKEN = os.getenv('TOKEN')
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

# ================= DATA =================
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

menu = ReplyKeyboardMarkup(
    [["📦 Dịch vụ"], ["💰 Nạp tiền", "👤 Tài khoản"], ["📊 Đơn hàng", "☎ Liên hệ admin"]],
    resize_keyboard=True
)

# ================= CALLBACK =================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = str(query.message.chat_id)
    
    # Kiểm tra quyền Admin
    if query.data.startswith(("dep|", "stt|")) and not is_admin(uid):
        await query.answer("❌ Bạn không có quyền!")
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
                init_user(data, user_id)
                data["users"][user_id]["balance"] += dep["amount"]
                save(data)
                await context.bot.send_message(int(user_id), khung("✅ NẠP TIỀN", f"Cộng {dep['amount']:,.0f}đ thành công!"))
                await query.edit_message_text(khung("✅ ĐÃ DUYỆT", f"Đã duyệt {dep['amount']:,.0f}đ cho user {user_id}"))
            else:
                await context.bot.send_message(int(user_id), khung("❌ NẠP TIỀN", "Yêu cầu đã bị hủy."))
                await query.edit_message_text(khung("❌ ĐÃ HỦY", f"Đã hủy nạp cho user {user_id}"))
            del DEPOSITS[code]

    elif query.data.startswith("stt|"):
        await query.answer()
        _, status, oid = query.data.split("|")
        if oid in data["orders"]:
            data["orders"][oid]["status"] = status
            save(data)
            await query.edit_message_text(khung("📌 CẬP NHẬT ĐƠN", f"Đơn {oid}: {status.upper()}"))
            await context.bot.send_message(int(data["orders"][oid]["user"]), khung("🔔 THÔNG BÁO", f"Đơn {oid}: {status.upper()}"))

# ================= HANDLE TEXT =================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.message.chat_id)
    text = update.message.text
    data = load()
    init_user(data, uid)

    if text == "📦 Dịch vụ":
        await update.message.reply_text(khung("📦 CHỌN DỊCH VỤ", "Chọn nền tảng:"), reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📘 Facebook", callback_data="fb")],
            [InlineKeyboardButton("🎵 TikTok", callback_data="tt")],
            [InlineKeyboardButton("📸 Instagram", callback_data="ig")]
        ]))
    elif text == "💰 Nạp tiền":
        STATE[uid] = {"step": "deposit_amount"}
        await update.message.reply_text(khung("💰 NẠP TIỀN", "🏦 ACB: 26084821\n👤 DINH HOANG VIET ANH\n📌 Nhập số tiền (>= 50k):"))
    elif text == "☎ Liên hệ admin":
        await update.message.reply_text(khung("☎ HỖ TRỢ", f"Mọi vấn đề vui lòng liên hệ:\nAdmin: {ADMIN_CONTACT}"))
    elif uid in STATE and STATE[uid].get("step") == "deposit_amount":
        try:
            amount = float(text)
            if amount < 50000: raise ValueError
            code = f"DEP{int(time.time())}"
            DEPOSITS[code] = {"user": uid, "amount": amount}
            STATE.pop(uid)
            await update.message.reply_text(khung("✅ YÊU CẦU NẠP", f"Mã ck: {code}"))
            await context.bot.send_message(ADMIN_ID, khung("💰 NẠP MỚI", f"User: {uid}\nTiền: {amount:,.0f}đ\nMã: {code}"),
                                         reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ DUYỆT", callback_data=f"dep|ok|{code}"), InlineKeyboardButton("❌ HỦY", callback_data=f"dep|no|{code}")]]))
        except: await update.message.reply_text("❌ Nhập số tiền hợp lệ (>= 50.000)")
    # ... (các phần khác giữ nguyên)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("🚀 CHÀO MỪNG BẠN", reply_markup=menu)))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    app.run_polling()

if __name__ == "__main__": main()
