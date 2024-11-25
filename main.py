from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler,filters, ContextTypes, MessageHandler
from database import Database
from scheduler import Scheduler
from dotenv import load_dotenv
import os
import datetime
load_dotenv()
# API token (BotFather'dan olingan tokenni kiriting)
API_TOKEN = os.getenv('BOT_API_TOKEN')


# Ma'lumotlar bazasi va rejalashtiruvchi obyektlarni yaratamiz
db = Database("events.db")
scheduler = Scheduler()

MAIN_MENU = ReplyKeyboardMarkup(
    [["/list", "/help"]],
    resize_keyboard=True,
    one_time_keyboard=False
)

def reminder_time_selection(update, context):
    keyboard = [
        [InlineKeyboardButton("60 daqiqa", callback_data="60")],
        [InlineKeyboardButton("45 daqiqa", callback_data="45")],
        [InlineKeyboardButton("30 daqiqa", callback_data="30")],
        [InlineKeyboardButton("15 daqiqa", callback_data="15")],
        [InlineKeyboardButton("5 daqiqa", callback_data="5")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Iltimos, eslatma yuborish uchun vaqtni tanlang:", reply_markup=reply_markup)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Boshlang'ich buyruq."""
    await update.message.reply_text(
         "Assalomu alaykum! Tadbirlaringizni rejalashtirishga yordam beraman.\n\n"
        "Quyidagi buyruqlar orqali ishlashingiz mumkin:\n"
        "- /add: Yangi tadbir qo'shish\n"
        "- /list: Rejalashtirilgan tadbirlarni ko'rish\n"
        "- /delete: Tadbirni o'chirish\n\n"
        "- /delete_all: Barcha tadbirlarni o'chirib tashlaydi"
        "Buyruqlardan foydalanish uchun tugmalardan foydalaning 👇",
        reply_markup=MAIN_MENU,
    )

async def help_handler(update:Update, context:ContextTypes.DEFAULT_TYPE):
    """help_text.txt faylidagi ma'lumotlarni o'qib foydalanuvchiga yuboradi."""
    help_file_path = "help_text.txt"

    if os.path.exists(help_file_path):
        with open(help_file_path, "r", encoding="utf-8") as file:
            help_text = file.read()
        await update.message.reply_text(help_text)
    else:
        await update.message.reply_text("❌ Xato: help_text.txt fayli topilmadi.")
# Tadbir qo'shish funksiyasi
async def add_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Yangi tadbir qo'shish."""
    try:
        # Foydalanuvchidan tadbir nomi va vaqti
        data = " ".join(context.args)
        name, date_time = data.split("|")
        date_time = datetime.datetime.strptime(date_time.strip(), "%Y-%m-%d %H:%M")
        user_id = update.message.chat_id
        # Vaqtni UTC ga aylantirish
        date_time = date_time.replace(tzinfo=datetime.timezone.utc)
        # Eslatma vaqtini tanlash uchun inline tugmalarni yaratish
        keyboard = [
            [InlineKeyboardButton("60 daqiqa", callback_data="60")],
            [InlineKeyboardButton("45 daqiqa", callback_data="45")],
            [InlineKeyboardButton("30 daqiqa", callback_data="30")],
            [InlineKeyboardButton("15 daqiqa", callback_data="15")],
            [InlineKeyboardButton("5 daqiqa", callback_data="5")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Foydalanuvchiga eslatma vaqti tanlashni so'rash
        await update.message.reply_text(
            f"Tadbirni qo'shish uchun eslatma vaqtini tanlang: {name.strip()} - {date_time}",
            reply_markup=reply_markup
        )

        # User'ning ma'lumotlarini context.user_data'da saqlash
        context.user_data['event_name'] = name.strip()
        context.user_data['event_time'] = date_time
        context.user_data['user_id'] = user_id

    except Exception as e:
        await update.message.reply_text("❌ Xato: Tadbirni qo'shish formati noto'g'ri.\n"
                                        "To'g'ri format: /add Tadbir nomi | YYYY-MM-DD HH:MM")


# Eslatma vaqti tanlanganda ishlovchi handler
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Foydalanuvchi eslatma vaqtini tanlaganida ishlaydi."""
    query = update.callback_query
    await query.answer()

    reminder_time = int(query.data)  # Tanlangan eslatma vaqti
    event_name = context.user_data['event_name']
    event_time = context.user_data['event_time']
    user_id = context.user_data['user_id']

    # Tadbirni database'ga qo'shish (ma'lumotlar bazasi funksiyasiga bog'liq)
    db.add_event(user_id, event_name, event_time)

    # Eslatma vaqtini rejalashtirish (scheduler)
    scheduler.schedule_event(user_id, event_name, event_time, context, reminder_time)

    # Foydalanuvchiga tasdiqlovchi xabar yuborish
    await query.edit_message_text(
        text=f"Siz {reminder_time} daqiqa oldin eslatma olishni tanladingiz.\n"
             f"Tadbir muvaffaqiyatli qo'shildi: {event_name} - {event_time}"
    )

    # Foydalanuvchining ma'lumotlarini tozalash
    context.user_data.clear()


async def list_events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Foydalanuvchining tadbirlar ro'yxatini ko'rsatish."""
    user_id = update.message.chat_id
    events = db.get_user_events(user_id)

    if not events:
        await update.message.reply_text("Sizda rejalashtirilgan tadbirlar yo'q.")
        return

    text = "📅 Sizning tadbirlaringiz:\n"
    for event in events:
        text += f"- {event[1]} ({event[2]})\n"

    await update.message.reply_text(text)

async def remove_all_event(update:Update, context:ContextTypes.DEFAULT_TYPE):
    """Barcha eventlarni databasedan o'chirish"""
    try:
        user_id = update.message.from_user.id
        db.delete_all_events(user_id)
        await update.message.reply_text("✅ Barcha tarbirlar muvofaqqiyatli o'chirildi.")
    except:
        await update.message.reply_text("❌ Xato: Tarbirlar o'chirilmadi.")

async def delete_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tadbirni o'chirish."""
    try:
        event_id = int(context.args[0])
        db.delete_event(event_id)
        await update.message.reply_text("✅ Tadbir muvaffaqiyatli o'chirildi.")
    except:
        await update.message.reply_text("❌ Xato: Tadbirni o'chirish uchun tadbir ID-ni kiriting.")

async def unknown_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Foydalanuvchi noto'g'ri ma'lumot kiritsa."""
    await update.message.reply_text(
        "Men faqat menyudagi buyruqlarni qabul qilaman 😊",
        reply_markup=MAIN_MENU,
    )

# Botni ishga tushiramiz
app = ApplicationBuilder().token(API_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("add", add_event))
app.add_handler(CommandHandler("list", list_events))
app.add_handler(CommandHandler("delete", delete_event))
app.add_handler(CommandHandler('delete_all', remove_all_event))
app.add_handler(CommandHandler('help', help_handler))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_message))
app.add_handler(CallbackQueryHandler(button))
if __name__ == "__main__":
    print("Bot ishga tushdi!")
    app.run_polling()