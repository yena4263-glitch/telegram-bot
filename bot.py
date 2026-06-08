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
    if not os.path.exists(DATA_FILE):
        return {"users": {}, "orders": {}}
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

PRICES = {
    "Facebook": {"Follow sale": 28, "Follow clone": 26.2},
    "TikTok": {"Follow clone": 47.8, "S4 Follow": 48.9, "S6 Follow": 34.9},
    "Instagram": {"S1 Follow": 45, "Follow Tây": 33.63}
}

menu = ReplyKeyboardMarkup(
    [["📦 Dịch vụ"], ["💰 Nạp tiền", "👤 Tài khoản"], ["📊 Đơn hàng", "☎ Liên hệ admin"]],
    resize_keyboard=True
)

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.message.chat_id)
    data = load()
    init_user(data, uid)
    save(data)
    await update.message.reply_text("🚀 VIỆT ANH AUTO BOT XIN CHÀO", reply_markup=menu)

# ================= CALLBACK =================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = str(query.message.chat_id)
    data = load()

    if query.data.startswith(("fb", "tt", "ig")):
        platform = {"fb": "Facebook", "tt": "TikTok", "ig": "Instagram"}[query.data]
        STATE[uid] = {"step": "service", "platform": platform}
        keyboard = [[InlineKeyboardButton(f"{k} - {v}đ", callback_data=f"svc|{k}")] for k, v in PRICES[platform].items()]
        await query.message.reply_text(f"📦 {platform}", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("svc|"):
        service = query.data.split("|")[1]
        STATE[uid].update({"service": service, "step": "qty"})
        await query.message.reply_text("🔢 NHẬP SỐ LƯỢNG:")

    elif query.data.startswith("dep|"):
        _, action, code = query.data.split("|")
        dep = DEPOSITS.get(code)
        if dep:
            if action == "ok":
                data["users"][dep["user"]]["balance"] += dep["amount"]
                save(data)
                await context.bot.send_message(int(dep["user"]), f"✅ Nạp {dep['amount']:,.0f}đ thành công!")
                await query.message.edit_text("✅ Đã duyệt nạp tiền")
            else:
                await context.bot.send_message(int(dep["user"]), "❌ Nạp tiền bị hủy")
                await query.message.edit_text("❌ Đã hủy nạp tiền")

    elif query.data.startswith("stt|"):
        _, status, order_id = query.data.split("|")
        if order_id in data["orders"]:
            data["orders"][order_id]["status"] = status
            save(data)
            await query.message.edit_text(f"📌 Đã cập nhật trạng thái đơn {order_id}: {status.upper()}")

# ================= TEXT HANDLER =================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.message.chat_id)
    text = update.message.text
    data = load()
    init_user(data, uid)

    if text == "📦 Dịch vụ":
        STATE[uid] = {"step": "platform"}
        await update.message.reply_text("📦 Chọn nền tảng:", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📘 Facebook", callback_data="fb")],
            [InlineKeyboardButton("🎵 TikTok", callback_data="tt")],
            [InlineKeyboardButton("📸 Instagram", callback_data="ig")]
        ]))

    elif text == "💰 Nạp tiền":
        STATE[uid] = {"step": "deposit_amount"}
        await update.message.reply_text("📌 NHẬP SỐ TIỀN (TỐI THIỂU 50.000 VNĐ):")

    elif uid in STATE and STATE[uid].get("step") == "deposit_amount":
        try:
            amount = float(text)
            if amount < 50000: raise ValueError
            code = f"DEP{int(time.time())}"
            DEPOSITS[code] = {"user": uid, "amount": amount}
            STATE.pop(uid)
            await update.message.reply_text(f"🧾 MÃ NẠP: {code}\n💰 {amount:,.0f} VNĐ\n📌 Nội dung: {code}")
            await context.bot.send_message(ADMIN_ID, f"💰 Yêu cầu nạp: {amount:,.0f}đ\n👤 User: {uid}\n🧾 Mã: {code}",
                                         reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ DUYỆT", callback_data=f"dep|ok|{code}")]]))
        except:
            await update.message.reply_text("❌ Nhập số tiền hợp lệ (>= 50.000)")

    elif uid in STATE and STATE[uid].get("step") == "qty":
        try:
            qty = int(text)
            p = STATE[uid]["platform"]
            s = STATE[uid]["service"]
            total = PRICES[p][s] * qty
            STATE[uid].update({"qty": qty, "total": total, "step": "link"})
            await update.message.reply_text(f"💰 Tổng: {total:,.0f} VNĐ\n🔗 Gửi link cần tăng:")
        except:
            await update.message.reply_text("❌ Nhập số lượng hợp lệ!")

    elif uid in STATE and STATE[uid].get("step") == "link":
        if data["users"][uid]["balance"] < STATE[uid]["total"]:
            await update.message.reply_text("❌ Không đủ tiền!")
        else:
            data["users"][uid]["balance"] -= STATE[uid]["total"]
            order_id = f"ORD{int(time.time())}"
            data["orders"][order_id] = {**STATE[uid], "id": order_id, "user": uid, "link": text, "status": "pending"}
            save(data)
            await update.message.reply_text(f"✅ Tạo đơn thành công! Mã: {order_id}")
        STATE.pop(uid)

    elif text == "👤 Tài khoản":
        await update.message.reply_text(f"💰 SỐ DƯ: {data['users'][uid]['balance']:,.0f} VNĐ")
    
    elif text == "📊 Đơn hàng":
        orders = [o for o in data["orders"].values() if o["user"] == uid]
        msg = "\n".join([f"🆔 {o['id']} | {o['status']} | {o['total']:,.0f}đ" for o in orders]) or "Chưa có đơn"
        await update.message.reply_text(f"📊 ĐƠN HÀNG:\n{msg}")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    app.run_polling()

if __name__ == "__main__":
    main()
