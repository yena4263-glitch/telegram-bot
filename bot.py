import os
import json
import time
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = "8832222333:AAGbnhv8hkfmlXEHrcDEYih8jEzLDRdZCak"
ADMIN_ID = 8348914397
DATA_FILE = "data.json"
STATE = {}
DEPOSITS = {}

PRICES = {
    "Facebook": {"Follow clone": 28, "Follow sale": 26.7},
    "TikTok": {"Follow clone": 47.8, "S4 Follow": 48.9, "S6 Follow": 34.9},
    "Instagram": {"S1 Follow": 45, "Follow Tây": 33.63},
}

def load():
    if not os.path.exists(DATA_FILE): return {"users": {}, "orders": {}}
    with open(DATA_FILE, "r") as f: return json.load(f)

def save(data):
    with open(DATA_FILE, "w") as f: json.dump(data, f, indent=2)

def init_user(data, uid):
    if uid not in data["users"]:
        data["users"][uid] = {"balance": 0}
        save(data)
    return data

app = Flask(__name__)
@app.route('/')
def home(): return "Bot is running!"

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load()
    
    # 1. DUYỆT NẠP TIỀN
    if query.data.startswith("dep|"):
        _, action, code = query.data.split("|")
        dep = DEPOSITS.get(code)
        if dep:
            uid_user = dep["user"]
            if action == "ok":
                data = init_user(data, uid_user)
                data["users"][uid_user]["balance"] += dep["amount"]
                save(data)
                await context.bot.send_message(int(uid_user), f"✅ Nạp {dep['amount']:,.0f}đ thành công!")
                await query.message.edit_text(f"✅ Đã duyệt nạp {dep['amount']:,.0f}đ cho user {uid_user}")
                del DEPOSITS[code]
    
    # 2. DUYỆT ĐƠN HÀNG
    elif query.data.startswith("stt|"):
        _, status, oid = query.data.split("|")
        if oid in data["orders"]:
            data["orders"][oid]["status"] = status
            save(data)
            await query.message.edit_text(f"📌 Đơn {oid} đã: {status.upper()}")
            await context.bot.send_message(data["orders"][oid]["user"], f"📌 Đơn hàng {oid} của bạn đã: {status.upper()}")

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.message.chat_id)
    text = update.message.text
    data = init_user(load(), uid)
    
    if text == "📦 Dịch vụ":
        STATE[uid] = {"step": "platform"}
        await update.message.reply_text("📦 Chọn nền tảng:", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📘 Facebook", callback_data="fb")],
            [InlineKeyboardButton("🎵 TikTok", callback_data="tt")],
            [InlineKeyboardButton("📸 Instagram", callback_data="ig")]
        ]))
    elif text == "💰 Nạp tiền":
        STATE[uid] = {"step": "deposit"}
        await update.message.reply_text("💰 NẠP TIỀN\n🏦 ACB: 26084821\n👤 DINH HOANG VIET ANH\n⚠️ NHẬP SỐ TIỀN (tối thiểu 50.000):")
    elif text == "📊 Đơn hàng":
        orders = [o for o in data["orders"].values() if o["user"] == uid]
        if not orders: await update.message.reply_text("📊 BẠN CHƯA CÓ ĐƠN HÀNG.")
        else:
            msg = "📋 CHI TIẾT 5 ĐƠN GẦN NHẤT:\n━━━━━━━━━━━━━━\n"
            for o in orders[-5:]:
                msg += (f"🆔 {o['id']}\n🔹 Dịch vụ: {o['platform']} - {o['service']}\n"
                        f"📌 Trạng thái: {o['status'].upper()}\n💰 Số tiền: {o['total']:,.0f}đ\n━━━━━━━━━━━━━━\n")
            await update.message.reply_text(msg)
    elif uid in STATE:
        step = STATE[uid].get("step")
        if step == "deposit":
            try:
                amt = float(text)
                if amt < 50000: raise ValueError
                code = f"DEP{int(time.time())}"
                DEPOSITS[code] = {"user": uid, "amount": amt}
                await update.message.reply_text(f"✅ MÃ NẠP: `{code}`\nSố tiền: {amt:,.0f}đ\nNhấn nút sau khi đã CK:", parse_mode='Markdown', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Đã chuyển khoản", callback_data=f"notify_admin|{code}")]]))
                await context.bot.send_message(ADMIN_ID, f"💰 Yêu cầu nạp: {amt:,.0f}đ\nUser: {uid}\nCode: {code}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Duyệt", callback_data=f"dep|ok|{code}")]]))
                STATE.pop(uid)
            except: await update.message.reply_text("❌ Nhập số tiền hợp lệ (>= 50.000)!")
        elif step == "link": # Logic tạo đơn và gửi thông báo Admin
            # ... (Phần logic link cũ của bạn đã ổn)
            pass

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=10000)).start()
    bot = Application.builder().token(TOKEN).build()
    bot.add_handler(CommandHandler("start", lambda u, c: None)) # Thêm start handler ở đây
    bot.add_handler(CallbackQueryHandler(button_handler))
    bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    bot.run_polling()
