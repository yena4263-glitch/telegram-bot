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
    "Follow clone": 26.2
    },
    "TikTok": {
        "Follow clone": 47.8,
        "S4 Follow": 48.9,
        "S6 Follow": 34.9
    },
    "Instagram": {
        "S1 Follow": 45,
        "Follow Tây": 33.63
    }
}

# ================= MENU =================
menu = ReplyKeyboardMarkup(
    [
        ["📦 Dịch vụ"],
        ["💰 Nạp tiền", "👤 Tài khoản"],
        ["📊 Đơn hàng", "☎ Liên hệ admin"]
    ],
    resize_keyboard=True
)

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = str(update.message.chat_id)
    data = load()
    init_user(data, uid)
    save(data)

    await update.message.reply_text(
        "🚀 BOT SMM PRO MAX\n━━━━━━━━━━━━━━",
        reply_markup=menu
    )

# ================= CALLBACK =================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    uid = str(query.message.chat_id)
    data = load()
    init_user(data, uid)

    # ================= PLATFORM =================
    if query.data in ["fb", "tt", "ig"]:

        platform = {"fb": "Facebook", "tt": "TikTok", "ig": "Instagram"}[query.data]

        STATE[uid] = {"step": "service", "platform": platform}

        keyboard = [
            [InlineKeyboardButton(f"{k} - {v}đ", callback_data=f"svc|{k}")]
            for k, v in PRICES[platform].items()
        ]

        await query.message.reply_text(
            f"📦 {platform}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # ================= SERVICE =================
    elif query.data.startswith("svc|"):

        service = query.data.split("|")[1]

        STATE[uid]["service"] = service
        STATE[uid]["step"] = "qty"

        await query.message.reply_text("🔢 NHẬP SỐ LƯỢNG:")

    # ================= ORDER STATUS =================
    elif query.data.startswith("stt|"):

        _, status, order_id = query.data.split("|")

        order = data["orders"].get(order_id)
        if not order:
            return

        old = order["status"]
        order["status"] = status

        if status == "cancel" and old != "cancel":
            user = order["user"]
            amount = order["total"]
            data["users"][user]["balance"] += amount

            await context.bot.send_message(
                int(user),
                f"🔴 ĐƠN HÀNG BỊ HỦY\n💰 Hoàn tiền: {amount} VNĐ"
            )

        save(data)

        await query.message.edit_text(
            f"📌 CẬP NHẬT TRẠNG THÁI: {status.upper()}"
        )

    # ================= DEPOSIT =================
    elif query.data.startswith("dep|"):

        _, action, code = query.data.split("|")

        dep = DEPOSITS.get(code)
        if not dep:
            return

        user = dep["user"]
        amount = dep["amount"]

        data = load()
        init_user(data, user)

        if action == "ok":

            data["users"][user]["balance"] += amount
            save(data)

            await context.bot.send_message(
                int(user),
                f"✅ NẠP TIỀN THÀNH CÔNG\n💰 +{amount} VNĐ"
            )

            await query.message.edit_text("✅ ĐÃ DUYỆT NẠP TIỀN")

        elif action == "no":

            await context.bot.send_message(
                int(user),
                f"❌ NẠP TIỀN BỊ HỦY\n💰 {amount} VNĐ"
            )

            await query.message.edit_text("❌ ĐÃ HỦY NẠP TIỀN")

    # ================= USER CONFIRM =================
    elif query.data.startswith("paid_confirm|"):

        _, code = query.data.split("|")

        dep = DEPOSITS.get(code)
        if not dep:
            return

        await query.message.reply_text("📩 ĐÃ GỬI XÁC NHẬN CHO ADMIN")

        await context.bot.send_message(
            ADMIN_ID,
            f"⚠️ XÁC NHẬN CHUYỂN KHOẢN\n"
            f"🧾 CODE: {code}\n"
            f"👤 USER: {dep['user']}\n"
            f"💰 SỐ TIỀN: {dep['amount']} VNĐ"
        )

# ================= TEXT =================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = str(update.message.chat_id)
    text = update.message.text

    data = load()
    init_user(data, uid)

    # ================= SERVICES =================
    if text == "📦 Dịch vụ":

        STATE.pop(uid, None)
        STATE[uid] = {"step": "platform"}

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📘 Facebook", callback_data="fb")],
            [InlineKeyboardButton("🎵 TikTok", callback_data="tt")],
            [InlineKeyboardButton("📸 Instagram", callback_data="ig")]
        ])

        await update.message.reply_text("📦 CHỌN NỀN TẢNG", reply_markup=keyboard)

    # ================= DEPOSIT =================
    elif text == "💰 Nạp tiền":

        STATE.pop(uid, None)
        STATE[uid] = {"step": "deposit_amount"}

        await update.message.reply_text(
            "💰 NẠP TIỀN\n━━━━━━━━━━━━━━\n"
            "🏦 ACB: 26084821\n"
            "👤 DINH HOANG VIET ANH\n"
            "📌 NHẬP SỐ TIỀN (TỐI THIỂU 50.000 VNĐ)"
        )

    # ================= DEPOSIT INPUT =================
    elif uid in STATE and STATE[uid].get("step") == "deposit_amount":

        try:
            amount = float(text)
        except:
            await update.message.reply_text("❌ VUI LÒNG NHẬP SỐ")
            return

        if amount < 50000:
            await update.message.reply_text("❌ TỐI THIỂU 50.000 VNĐ")
            return

        code = f"DEP{int(time.time())}"

        DEPOSITS[code] = {"user": uid, "amount": amount}

        STATE.pop(uid)

        await update.message.reply_text(
            f"🧾 MÃ NẠP: {code}\n"
            f"💰 {amount} VNĐ\n"
            f"📌 NỘI DUNG: {code} + {amount}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💸 ĐÃ CHUYỂN TIỀN", callback_data=f"paid_confirm|{code}")]
            ])
        )

        await context.bot.send_message(
            ADMIN_ID,
            f"💰 YÊU CẦU NẠP TIỀN\n"
            f"🧾 CODE: {code}\n"
            f"👤 USER: {uid}\n"
            f"💰 SỐ TIỀN: {amount}",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ DUYỆT", callback_data=f"dep|ok|{code}"),
                    InlineKeyboardButton("❌ HỦY", callback_data=f"dep|no|{code}")
                ]
            ])
        )

    # ================= QTY =================
    elif uid in STATE and STATE[uid].get("step") == "qty":

        STATE[uid]["qty"] = int(text)
        STATE[uid]["step"] = "link"

        await update.message.reply_text("🔗 GỬI LINK CẦN TĂNG:")

    # ================= LINK =================
    elif uid in STATE and STATE[uid].get("step") == "link":

        platform = STATE[uid]["platform"]
        service = STATE[uid]["service"]
        qty = STATE[uid]["qty"]
        link = text

        price = PRICES[platform][service]
        total = price * qty

        if data["users"][uid]["balance"] < total:
            await update.message.reply_text("❌ KHÔNG ĐỦ TIỀN")
            STATE.pop(uid)
            return

        data["users"][uid]["balance"] -= total

        order_id = f"ORD{int(time.time())}"

        data["orders"][order_id] = {
            "id": order_id,
            "user": uid,
            "platform": platform,
            "service": service,
            "qty": qty,
            "link": link,
            "total": total,
            "status": "pending"
        }

        save(data)
        STATE.pop(uid)

        await update.message.reply_text(
            f"✅ TẠO ĐƠN THÀNH CÔNG\n🆔 {order_id}"
        )

        await context.bot.send_message(
            ADMIN_ID,
            f"📦 ĐƠN HÀNG MỚI\n"
            f"━━━━━━━━━━━━━━\n"
            f"🆔 {order_id}\n"
            f"📱 {platform}\n"
            f"⚡ {service}\n"
            f"🔢 {qty}\n"
            f"🔗 {link}\n"
            f"💰 {total} VNĐ\n"
            f"📌 CHỜ XỬ LÝ",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🟡 CHỜ", callback_data=f"stt|pending|{order_id}")
                ],
                [
                    InlineKeyboardButton("🔵 ĐANG CHẠY", callback_data=f"stt|running|{order_id}")
                ],
                [
                    InlineKeyboardButton("🟢 HOÀN THÀNH", callback_data=f"stt|done|{order_id}"),
                    InlineKeyboardButton("🔴 HỦY", callback_data=f"stt|cancel|{order_id}")
                ]
            ])
        )

    # ================= ACCOUNT =================
    elif text == "👤 Tài khoản":
        await update.message.reply_text(f"💰 SỐ DƯ: {data['users'][uid]['balance']} VNĐ")

    # ================= ORDERS =================
    elif text == "📊 Đơn hàng":

        msg = "📊 ĐƠN HÀNG CỦA BẠN\n━━━━━━━━━━━━━━\n\n"
        found = False

        for o in data["orders"].values():
            if o["user"] == uid:
                found = True
                msg += (
                    f"🆔 {o['id']}\n"
                    f"📱 {o['platform']}\n"
                    f"⚡ {o['service']}\n"
                    f"📌 {o['status']}\n"
                    f"💰 {o['total']} VNĐ\n"
                    f"━━━━━━━━━━━━━━\n"
                )

        if not found:
            msg = "📊 CHƯA CÓ ĐƠN HÀNG"

        await update.message.reply_text(msg)

    # ================= ADMIN =================
    elif text == "☎ Liên hệ admin":
        await update.message.reply_text(ADMIN)

# ================= RUN =================
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    print("BOT RUNNING...")
    app.run_polling()

if __name__ == "__main__":
    main()
