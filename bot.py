from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from database import update_user_phone

TOKEN = "8793984992:AAHWlGhbzKXKjazxSG05eQNtnjNfXFyrL-4"
WEBAPP_URL = "https://basement-brakes-glow-libraries.trycloudflare.com"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Mini App ochish", web_app=WebAppInfo(url=WEBAPP_URL))]
    ])
    await update.message.reply_text(
        "Assalomu alaykum! Mini App ni ochish uchun pastdagi tugmani bosing:",
        reply_markup=keyboard,
    )


async def contact_from_miniapp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mini App orqali requestContact yuborilganda contact shu yerga tushadi"""
    contact = update.message.contact
    if not contact:
        return

    phone = contact.phone_number
    if phone and not phone.startswith("+"):
        phone = "+" + phone

    telegram_id = update.effective_user.id
    first_name = contact.first_name or update.effective_user.first_name or ""
    username = update.effective_user.username or ""

    # Profil rasmni olish
    photo_url = ""
    try:
        photos = await update.effective_user.get_profile_photos(limit=1)
        if photos.total_count > 0:
            file = await photos.photos[0][0].get_file()
            photo_url = file.file_path
    except Exception:
        pass

    # Bazaga saqlash yoki yangilash
    update_user_phone(telegram_id, phone, first_name, username, photo_url)


def run_bot():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    # Mini App'dan kelgan contact'lar uchun handler
    app.add_handler(MessageHandler(filters.CONTACT, contact_from_miniapp))
    print("Bot ishga tushdi!")
    app.run_polling()


if __name__ == "__main__":
    run_bot()
