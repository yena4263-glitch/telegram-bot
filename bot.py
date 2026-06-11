import os
import json
import time
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# --- CẤU HÌNH ---
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

# --- HÀM XỬ LÝ DỮ LIỆU ---
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

# --- HÀM XỬ LÝ TELEGRAM ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.message.chat_id)
    init_user(load(), uid)
    menu = ReplyKeyboardMarkup([["📦 Dịch vụ"], ["💰 Nạp tiền", "👤 Tài khoản"], ["📊 Đơn hàng", "☎ Liên hệ admin"]], resize_keyboard=True)
    await update.message.reply_text("🚀 VIỆT ANH AUTO BOT XIN CHÀO!", reply_markup=menu)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load()
    uid = str(query.message.chat_id)

    if query.data in ["fb", "tt", "ig"]:
        platform = {"fb": "Facebook", "tt": "TikTok", "ig": "Instagram"}[query.data]
        STATE[uid] = {"step": "service", "platform": platform}
        keyboard = [[InlineKeyboardButton(f"{k} - {v}đ", callback_data=f"svc|{k}")] for k, v in PRICES[platform].items()]
        await query.message.reply_text(f"📦 Chọn dịch vụ {platform}", reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif query.data.startswith("svc|"):
        service = query.data.split("|")[1]
        STATE[uid].update({"service": service, "step": "qty"})
        await query.message.reply_text("🔢 Nhập số lượng cần tăng:")

    elif query.data.startswith("dep|"):
        _, action, code = query.data.split("|")
        if code in DEPOSITS:
            dep = DEPOSITS[code]
            if action == "ok":
                data = init_user(data, dep["user"])
                data["users"][dep["user"]]["balance"] += dep["amount"]
                save(data)
                await context.bot.send_message(int(dep["user"]), f"✅ Nạp {dep['amount']:,.0f}đ thành công!")
                await query.message.edit_text(f"✅ Đã duyệt nạp {dep['amount']:,.0f}đ cho user {dep['user']}")
                del DEPOSITS[code]

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
            [InlineKeyboardButton("📸 Instagram", callback_data="ig")]]))
    elif text == "💰 Nạp tiền":
        STATE[uid] = {"step": "deposit"}
        await update.message.reply_text("💰 NẠP TIỀN\n🏦 ACB: 26084821\n👤 DINH HOANG VIET ANH\n⚠️ NHẬP SỐ TIỀN (tối thiểu 50.000):")
    elif text == "👤 Tài khoản":
        await update.message.reply_text(f"👤 SỐ DƯ: {data['users'][uid]['balance']:,.0f} VNĐ")
    elif text == "📊 Đơn hàng":
        orders = [o for o in data["orders"].values() if o["user"] == uid]
        if not orders: await update.message.reply_text("📊 BẠN CHƯA CÓ ĐƠN HÀNG.")
        else:
            msg = "📋 CHI TIẾT 5 ĐƠN GẦN NHẤT:\n━━━━━━━━━━━━━━\n"
            for o in orders[-5:]:
                msg += (f"🆔 {o['id']}\n🔹 Dịch vụ: {o['platform']} - {o['service']}\n📌 Trạng thái: {o['status'].upper()}\n💰 Số tiền: {o['total']:,.0f}đ\n━━━━━━━━━━━━━━\n")
            await update.message.reply_text(msg)
    elif text == "☎ Liên hệ admin":
        await update.message.reply_text("☎ ADMIN: @Vietanhenter")
    elif uid in STATE:
        step = STATE[uid].get("step")
        if step == "deposit":
            try:
                amt = float(text)
                if amt < 50000: raise ValueError
                code = f"DEP{int(time.time())}"
                DEPOSITS[code] = {"user": uid, "amount": amt}
                await update.message.reply_text(f"✅ Gửi Admin mã: {code}\nSố tiền: {amt:,.0f}đ")
                await context.bot.send_message(ADMIN_ID, f"💰 User {uid} nạp: {amt:,.0f}đ\nCode: {code}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Duyệt", callback_data=f"dep|ok|{code}")]]))
                STATE.pop(uid)
            except: await update.message.reply_text("❌ Nhập số tiền hợp lệ (>= 50.000)!")
        elif step == "qty":
            try:
                qty = int(text)
                p, s = STATE[uid]["platform"], STATE[uid]["service"]
                total = PRICES[p][s] * qty
                STATE[uid].update({"qty": qty, "total": total, "step": "link"})
                await update.message.reply_text(f"💰 Tổng: {total:,.0f}đ. Gửi link cần tăng:")
            except: await update.message.reply_text("❌ Nhập số lượng hợp lệ!")
        elif step == "link":
            p, s, q, total = STATE[uid]["platform"], STATE[uid]["service"], STATE[uid]["qty"], STATE[uid]["total"]
            if data["users"][uid]["balance"] >= total:
                data["users"][uid]["balance"] -= total
                oid = f"ORD{int(time.time())}"
                data["orders"][oid] = {"id": oid, "user": uid, "platform": p, "service": s, "qty": q, "link": text, "total": total, "status": "pending"}
                save(data)
                await context.bot.send_message(ADMIN_ID, f"🔔 ĐƠN MỚI ID: {oid}\nUser: {uid}\nDịch vụ: {p} - {s}\nLink: {text}\nTổng: {total:,.0f}đ", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Duyệt", callback_data=f"stt|done|{oid}"), InlineKeyboardButton("❌ Hủy", callback_data=f"stt|cancel|{oid}")]]))
                await update.message.reply_text(f"✅ Đơn {oid} đã tạo! Admin đang duyệt.")
            else: await update.message.reply_text("❌ Không đủ tiền!")
            STATE.pop(uid)

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=10000)).start()
    bot = Application.builder().token(TOKEN).build()
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CallbackQueryHandler(button_handler))
    bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    bot.run_polling()
