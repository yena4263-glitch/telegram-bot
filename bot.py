import os
import json
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# ================= CONFIG =================
TOKEN = os.getenv('TOKEN')
ADMIN_ID = 8348914397  # Thay bằng ID Admin thật của cậu
ADMIN = "@Vietanhenter"  # Username admin thật

DATA_FILE = "data.json"

STATE = {}
DEPOSITS = {}

# ================= DATA =================
def load():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"users": {}, "orders": {}}
    except Exception:
        return {"users": {}, "orders": {}}

def save(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def init_user(data, uid):
    if uid not in data["users"]:
        data["users"][uid] = {"balance": 0}

# ================= PRICE =================
PRICES = {
    "Facebook": {
        "Follow sale": 28,
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

    # Hiển thị thông báo chào mừng và Menu chính
    await update.message.reply_text(
        "🚀 **VIET ANH AUTO BOT XIN CHAO**\n━━━━━❤━━━━━\nChọn dịch vụ bên dưới:",
        reply_markup=menu,
        parse_mode='Markdown'
    )

# ================= CALLBACK (Dã sửa lỗi dư ký tự) =================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Dã xóa hai ký tự 'nc' thừa ở dây

    query = update.callback_query
    await query.answer()

    uid = str(query.message.chat_id)
    data = load()
    init_user(data, uid)

    # 1. Chọn Nền tảng (fb, tt, ig)
    if query.data in ["fb", "tt", "ig"]:

        platform = {"fb": "Facebook", "tt": "TikTok", "ig": "Instagram"}[query.data]
        STATE[uid] = {"step": "service", "platform": platform}

        keyboard = [
            [InlineKeyboardButton(f"{k} - {v}đ", callback_data=f"svc|{k}")]
            for k, v in PRICES[platform].items()
        ]

        await query.message.edit_text(
            f"📦 **CHỌN LOẠI DỊCH VỤ: {platform}**",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )

    # 2. Chọn Gói Dịch vụ
    elif query.data.startswith("svc|"):

        service = query.data.split("|")[1]
        STATE[uid]["service"] = service
        STATE[uid]["step"] = "qty"  # Chuyển sang bước chờ nhập số lượng

        await query.message.reply_text(f"🔢 Đã chọn: {service}\nVui lòng **NHẬP SỐ LƯỢNG** bạn cần:", parse_mode='Markdown')

    # 3. Quản lý Đơn hàng (Admin)
    elif query.data.startswith("stt|"):

        _, status, order_id = query.data.split("|")
        order = data["orders"].get(order_id)
        if not order: return

        old_status = order["status"]
        order["status"] = status

        if status == "cancel" and old_status != "cancel":
            user_id = order["user"]
            amount = order["total"]
            data["users"][user_id]["balance"] += amount

            await context.bot.send_message(
                int(user_id),
                f"🔴 **ĐƠN HÀNG BỊ HỦY**\n🆔 {order_id}\n💰 Hoàn tiền: +{amount} VNĐ\n📌 Lý do: Vui lòng liên hệ admin.",
                parse_mode='Markdown'
            )

        save(data)
        await query.message.edit_text(f"📌 CẬP NHẬT TRẠNG THÁI: {status.upper()}")

    # 4. Quản lý Nạp tiền (Admin)
    elif query.data.startswith("dep|"):

        _, action, code = query.data.split("|")
        dep = DEPOSITS.get(code)
        if not dep: return

        user_id = dep["user"]
        amount = dep["amount"]
        
        data_nạp = load()
        init_user(data_nạp, user_id)

        if action == "ok":
            data_nạp["users"][user_id]["balance"] += amount
            save(data_nạp)

            await context.bot.send_message(
                int(user_id),
                f"✅ **NẠP TIỀN THÀNH CÔNG**\n🧾 CODE: {code}\n💰 Số tiền: +{amount} VNĐ",
                parse_mode='Markdown'
            )
            await query.message.edit_text("✅ ĐÃ DUYỆT NẠP TIỀN")
            del DEPOSITS[code]

        elif action == "no":
            await context.bot.send_message(
                int(user_id),
                f"❌ **YÊU CẦU NẠP TIỀN BỊ HỦY**\n🧾 CODE: {code}\n💰 Số tiền: {amount} VNĐ\n📌 Lý do: Admin hủy hoặc chưa nhận dược tiền.",
                parse_mode='Markdown'
            )
            await query.message.edit_text("❌ ĐÃ HỦY YÊU CẦU")
            del DEPOSITS[code]

    # 5. Xác nhận nạp tiền (Khách hàng)
    elif query.data.startswith("paid_confirm|"):
        _, code = query.data.split("|")
        dep = DEPOSITS.get(code)
        if not dep: return

        await query.message.reply_text("📩 **ĐÃ GỬI XÁC NHẬN CHO ADMIN**\nVui lòng chờ admin kiểm tra ví.", parse_mode='Markdown')

        await context.bot.send_message(
            ADMIN_ID,
            f"⚠️ **KHÁCH XÁC NHẬN ĐÃ CHUYỂN TIỀN**\n🧾 CODE: {code}\n👤 USER ID: `{dep['user']}`\n💰 SỐ TIỀN: {dep['amount']} VNĐ",
            parse_mode='Markdown'
        )

# ================= TEXT =================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = str(update.message.chat_id)
    text = update.message.text
    data = load()
    init_user(data, uid)

    # ================= CÁC LỆNH MENU GỐC =================
    if text == "📦 Dịch vụ":
        STATE.pop(uid, None) # Xóa trạng thái cũ
        await update.message.reply_text("🌐 **CHỌN NỀN TẢNG ĐỂ TĂNG**", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📘 Facebook", callback_data="fb")],
            [InlineKeyboardButton("🎵 TikTok", callback_data="tt")],
            [InlineKeyboardButton("📸 Instagram", callback_data="ig")]
        ]), parse_mode='Markdown')

    elif text == "💰 Nạp tiền":
        STATE.pop(uid, None)
        STATE[uid] = {"step": "deposit_amount"}
        await update.message.reply_text(
            "┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
            "┃        💰 NẠP TIỀN           ┃\n"
            "┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫\n"
            "┃ 🏦 Ngân hàng: ACB           ┃\n"
            "┃ 🔢 STK: `26084821`            ┃\n"
            "┃ 👤 CTK: DINH HOANG VIET ANH ┃\n"
            "┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫\n"
            "┃ 📌 **NHẬP SỐ TIỀN** tối thiểu   ┃\n"
            "┃    **50.000 VNĐ** để nạp        ┃\n"
            "┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛",
            parse_mode='Markdown'
        )

    elif text == "👤 Tài khoản":
        balance = data["users"].get(uid, {}).get("balance", 0)
        await update.message.reply_text(f"👤 **THÔNG TIN TÀI KHOẢN**\n🆔 ID: `{uid}`\n💰 Số dư: **{balance} VNĐ**", parse_mode='Markdown')

    elif text == "📊 Đơn hàng":
        found = False
        msg = "📊 **DANH SÁCH ĐƠN HÀNG CỦA BẠN**\n━━━━━━━━━━━━━━\n\n"
        
        for order_id, o in data.get("orders", {}).items():
            if o["user"] == uid:
                found = True
                status_icon = {"pending": "🟡 CHỜ", "running": "🔵 ĐANG CHẠY", "done": "🟢 HOÀN THÀNH", "cancel": "🔴 HỦY"}.get(o["status"], "⚪ CHỜ")
                msg += (
                    f"🆔 `{order_id}`\n"
                    f"📱 {o['platform']} | {o['service']}\n"
                    f"🔢 Số lượng: {o['qty']}\n"
                    f"🔗 {o['link']}\n"
                    f"💰 Tổng tiền: {o['total']} VNĐ\n"
                    f"📌 Trạng thái: **{status_icon}**\n"
                    f"━━━━━━━━━━━━━━\n"
                )

        if not found: msg = "📊 **BẠN CHƯA CÓ ĐƠN HÀNG NÀO**"
        await update.message.reply_text(msg, parse_mode='Markdown')

    elif text == "☎ Liên hệ admin":
        await update.message.reply_text(f"☎ **LIÊN HỆ ADMIN ĐỂ ĐƯỢC HỖ TRỢ**\n📌 Liên hệ: {ADMIN}", parse_mode='Markdown')

    # ================= CÁC LỆNH NHẬP TRẠNG THÁI =================

    # 1. Nhập Số lượng (Khi step='qty')
    elif uid in STATE and STATE[uid].get("step") == "qty":
        try:
            qty = int(text)
            plat = STATE[uid]["platform"]
            svc = STATE[uid]["service"]
            
            unit_price = PRICES[plat][svc]
            total = unit_price * qty
            
            # Cập nhật thông tin và chuyển sang step 'link'
            STATE[uid].update({"qty": qty, "total": total, "step": "link"})
            
            await update.message.reply_text(
                f"╭────────────────────────────╮\n"
                f"│      📊 **BẢNG TÍNH GIÁ ĐƠN** │\n"
                f"├────────────────────────────┤\n"
                f"│ 📱 Gói: {svc}\n"
                f"│ 🔢 Số lượng: {qty}\n"
                f"│ 💰 Tổng tiền: **{total} VNĐ**\n"
                f"╰────────────────────────────╯\n"
                f"📌 Vui lòng **GỬI LINK** (profile/bài viết) cần tăng:",
                parse_mode='Markdown'
            )
        except ValueError:
            await update.message.reply_text("❌ **LỖI:** Vui lòng nhập số lượng bằng số nguyên!")

    # 2. Nhập Link (Khi step='link')
    elif uid in STATE and STATE[uid].get("step") == "link":
        
        # ... [Phần xử lý tạo đơn hàng mà cậu đã viết trước dây] ...
        await update.message.reply_text("✅ **TẠO ĐƠN THÀNH CÔNG!** Đơn hàng của bạn sẽ được admin xử lý sớm nhất.", parse_mode='Markdown')
        STATE.pop(uid) # Xóa trạng thái

    # 3. Nhập Số tiền Nạp (Khi step='deposit_amount')
    elif uid in STATE and STATE[uid].get("step") == "deposit_amount":
        try:
            amount = float(text)
            if amount < 50000:
                await update.message.reply_text("❌ **LỖI:** Số tiền nạp tối thiểu là 50.000 VNĐ!")
                return
            
            # Tạo mã nạp tiền unique
            code = f"DEP{int(time.time())}"
            DEPOSITS[code] = {"user": uid, "amount": amount}
            STATE.pop(uid)

            await update.message.reply_text(
                f"╭────────────────────────────╮\n"
                f"│      💰 **YÊU CẦU NẠP TIỀN** │\n"
                f"├────────────────────────────┤\n"
                f"│ 🧾 MÃ CODE: `{code}`\n"
                f"│ 💰 Số tiền: **{amount} VNĐ**\n"
                f"├────────────────────────────┤\n"
                f"│ 📌 Nội dung: **{code} + Số tiền**\n"
                f"╰────────────────────────────╯\n"
                f"✅ **BẤM NÚT** khi đã chuyển khoản xong:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💸 ĐÃ CHUYỂN KHOẢN", callback_data=f"paid_confirm|{code}")]
                ]),
                parse_mode='Markdown'
            )

            await context.bot.send_message(
                ADMIN_ID,
                f"💰 **YÊU CẦU NẠP TIỀN MỚI**\n🧾 CODE: {code}\n👤 USER ID: `{uid}`\n💰 SỐ TIỀN: {amount} VNĐ",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("✅ DUYỆT", callback_data=f"dep|ok|{code}"),
                        InlineKeyboardButton("❌ HỦY", callback_data=f"dep|no|{code}")
                    ]
                ]),
                parse_mode='Markdown'
            )
        except ValueError:
            await update.message.reply_text("❌ **LỖI:** Vui lòng nhập số tiền là số!")

# ================= MAIN =================
def main():
    if not TOKEN:
        print("❌ LỖI: Chưa cấu hình TOKEN cho bot!")
        return
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    
    print("VIET ANH AUTO IS RUNNING...")
    app.run_polling()

if __name__ == "__main__":
    main()
