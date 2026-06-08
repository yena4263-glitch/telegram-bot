import os
import json
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# ================= CONFIG =================
TOKEN = os.getenv('TOKEN')
ADMIN_ID = 8348914397 # ID Telegram của bạn
ADMIN_CONTACT = "@TenCuaBan" # Thay bằng username Telegram của bạn
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
    if uid not in data["users"]: data["users"][uid] = {"balance": 0}

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
    await query.answer()
    uid = str(query.message.chat_id)
    data = load()

    # Kiểm tra quyền Admin cho các hành động duyệt
    if query.data.startswith(("dep|", "stt|")) and not is_admin(uid):
        await query.message.reply_text("❌ Bạn không có quyền duyệt!")
        return

    if query.data.startswith(("fb", "tt", "ig")):
        platform = {"fb": "Facebook", "tt": "TikTok", "ig": "Instagram"}[query.data]
        STATE[uid] = {"step": "service", "platform": platform}
        kb = [[InlineKeyboardButton(f"{k} - {v}đ", callback_data=f"svc|{k}")] for k, v in PRICES[platform].items()]
        await query.message.reply_text(khung("📦 NỀN TẢNG", platform), reply_markup=InlineKeyboardMarkup(kb))
    
    elif query.data.startswith("svc|"):
        service = query.data.split("|")[1]
        STATE[uid].update({"service": service, "step": "qty"})
        await query.message.reply_text(khung("🔢 NHẬP SỐ LƯỢNG", "Vui lòng nhập số lượng bạn cần:"))

    elif query.data.startswith("dep|"):
        _, action, code = query.data.split("|")
        if code in DEPOSITS:
            dep = DEPOSITS[code]
            if action == "ok":
                data["users"][dep["user"]]["balance"] += dep["amount"]
                save(data)
                await context.bot.send_message(int(dep["user"]), khung("✅ NẠP TIỀN", f"Cộng {dep['amount']:,.0f}đ thành công!"))
                await query.message.edit_text(khung("✅ ĐÃ DUYỆT", f"Đã duyệt {dep['amount']:,.0f}đ cho user {dep['user']}"))
            else:
                await context.bot.send_message(int(dep['user']), khung("❌ NẠP TIỀN", "Yêu cầu đã bị hủy."))
                await query.message.edit_text(khung("❌ ĐÃ HỦY", "Đã hủy yêu cầu."))
            del DEPOSITS[code]

    elif query.data.startswith("stt|"):
        _, status, oid = query.data.split("|")
        if oid in data["orders"]:
            data["orders"][oid]["status"] = status
            save(data)
            await query.message.edit_text(khung("📌 CẬP NHẬT ĐƠN", f"Đơn {oid}: {status.upper()}"))
            await context.bot.send_message(int(data["orders"][oid]["user"]), khung("🔔 THÔNG BÁO", f"Đơn {oid}: {status.upper()}"))

# ================= HANDLE TEXT =================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.message.chat_id)
    text = update.message.text
    data = load()
    init_user(data, uid)

    if text == "📦 Dịch vụ":
        STATE[uid] = {"step": "platform"}
        await update.message.reply_text(khung("📦 CHỌN DỊCH VỤ", "Chọn nền tảng:"), reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📘 Facebook", callback_data="fb")],
            [InlineKeyboardButton("🎵 TikTok", callback_data="tt")],
            [InlineKeyboardButton("📸 Instagram", callback_data="ig")]
        ]))

    elif text == "💰 Nạp tiền":
        STATE[uid] = {"step": "deposit_amount"}
        msg = "🏦 ACB: 26084821\n👤 DINH HOANG VIET ANH\n📌 Nhập số tiền đã chuyển (>= 50k):"
        await update.message.reply_text(khung("💰 NẠP TIỀN", msg))

    elif text == "☎ Liên hệ admin":
        await update.message.reply_text(khung("☎ HỖ TRỢ", f"Mọi vấn đề vui lòng liên hệ:\nAdmin: {ADMIN_CONTACT}"))

    elif uid in STATE and STATE[uid].get("step") == "deposit_amount":
        try:
            amount = float(text)
            if amount < 50000: raise ValueError
            code = f"DEP{int(time.time())}"
            DEPOSITS[code] = {"user": uid, "amount": amount}
            STATE.pop(uid)
            await update.message.reply_text(khung("✅ YÊU CẦU NẠP", f"Mã nội dung ck: {code}"))
            await context.bot.send_message(ADMIN_ID, khung("💰 NẠP TIỀN MỚI", f"User: {uid}\nTiền: {amount:,.0f}đ\nMã: {code}"),
                                         reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ DUYỆT", callback_data=f"dep|ok|{code}"), InlineKeyboardButton("❌ HỦY", callback_data=f"dep|no|{code}")]]))
        except: await update.message.reply_text("❌ Nhập số tiền hợp lệ (>= 50.000)")

    elif uid in STATE and STATE[uid].get("step") == "qty":
        try:
            qty = int(text)
            price = PRICES[STATE[uid]["platform"]][STATE[uid]["service"]]
            total = price * qty
            STATE[uid].update({"qty": qty, "total": total, "step": "link"})
            await update.message.reply_text(khung("💰 TỔNG CỘNG", f"{total:,.0f} VNĐ\n🔗 Gửi link cần tăng:"))
        except: await update.message.reply_text("❌ Số lượng sai!")

    elif uid in STATE and STATE[uid].get("step") == "link":
        total = STATE[uid]["total"]
        if data["users"][uid]["balance"] < total:
            await update.message.reply_text("❌ Không đủ số dư!")
        else:
            data["users"][uid]["balance"] -= total
            oid = f"ORD{int(time.time())}"
            data["orders"][oid] = {**STATE[uid], "id": oid, "user": uid, "link": text, "status": "pending"}
            save(data)
            await update.message.reply_text(khung("✅ TẠO ĐƠN", f"Mã: {oid}\nChờ Admin duyệt!"))
            await context.bot.send_message(ADMIN_ID, khung("📦 ĐƠN HÀNG MỚI", f"🆔 {oid}\n💰 {total:,.0f}đ\n🔗 {text}"),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔵 CHẠY", callback_data=f"stt|running|{oid}"), InlineKeyboardButton("🟢 XONG", callback_data=f"stt|done|{oid}")],
                    [InlineKeyboardButton("🔴 HỦY", callback_data=f"stt|cancel|{oid}")]
                ]))
        STATE.pop(uid)

    elif text == "👤 Tài khoản": 
        await update.message.reply_text(khung("👤 THÔNG TIN", f"💰 Số dư: {data['users'][uid]['balance']:,.0f} VNĐ"))
    elif text == "📊 Đơn hàng":
        msg = "\n".join([f"🆔 {o['id']} | {o['status']} | {o['total']:,.0f}đ" for o in data["orders"].values() if o["user"] == uid])
        await update.message.reply_text(khung("📊 ĐƠN HÀNG", msg or "Chưa có đơn nào."))

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("🚀 CHÀO MỪNG BẠN", reply_markup=menu)))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    app.run_polling()

if __name__ == "__main__": main()
