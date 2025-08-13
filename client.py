from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
import requests
import logging

# Логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация
TOKEN = "8469169912:AAHcbKkHOgLR6HPwvpaEeYUTaN8bmjFOF2o"
SERVER_URL = "http://localhost:8000"

# Состояния
REGISTER_BUSINESS, BUSINESS_NAME, BUSINESS_DESC, BUSINESS_MEMBERS, BUSINESS_CONTACTS = range(5)
ADVERTISE_BUSINESS, ADVERTISE_KEY, ADVERTISE_TEXT = range(3)
SUPPORT_MESSAGE = range(1)

# --- /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Зарегистрировать бизнес", callback_data="register_business")],
        [InlineKeyboardButton("Найти работу", callback_data="find_job")],
        [InlineKeyboardButton("Прорекламировать бизнес", callback_data="advertise")],
        [InlineKeyboardButton("Помощь", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Добро пожаловать на биржу фриланса!", reply_markup=reply_markup)

# --- Поиск работы ---
async def find_job(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        response = requests.get(f"{SERVER_URL}/get_businesses", timeout=5)
        businesses = response.json().get("businesses", [])
    except Exception as e:
        logger.error(f"Ошибка при получении вакансий: {e}")
        businesses = []

    if not businesses:
        await query.edit_message_text("Пока нет доступных вакансий.")
        return

    keyboard = []
    for business in businesses:
        keyboard.append([InlineKeyboardButton(business["name"], callback_data=f"job_detail_{business['name']}")])
    keyboard.append([InlineKeyboardButton("Назад", callback_data="back_to_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Доступные вакансии:", reply_markup=reply_markup)

# --- Помощь ---
async def help_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("Связь с разработчиком", callback_data="contact_dev")],
        [InlineKeyboardButton("FAQ", callback_data="faq")],
        [InlineKeyboardButton("Назад", callback_data="back_to_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Чем помочь?", reply_markup=reply_markup)

async def contact_developer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📩 Напишите ваше сообщение разработчику:")
    return SUPPORT_MESSAGE

async def faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    faq_text = """
    ❓ **FAQ** ❓

    *1. Как зарегистрировать бизнес?*  
    → Используйте кнопку «Зарегистрировать бизнес» и следуйте инструкциям.  

    *2. Как повысить приоритет моего бизнеса?*  
    → Размещайте рекламу через бота.  

    *3. Как связаться с поддержкой?*  
    → Нажмите «Помощь» → «Связь с разработчиком».  
    """
    keyboard = [[InlineKeyboardButton("Назад", callback_data="help")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(faq_text, reply_markup=reply_markup, parse_mode="Markdown")

# --- Назад в меню ---
async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("Зарегистрировать бизнес", callback_data="register_business")],
        [InlineKeyboardButton("Найти работу", callback_data="find_job")],
        [InlineKeyboardButton("Прорекламировать бизнес", callback_data="advertise")],
        [InlineKeyboardButton("Помощь", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Главное меню:", reply_markup=reply_markup)

# --- Регистрация бизнеса ---
async def start_register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("🔑 Введите ключ активации для регистрации бизнеса:")
    return REGISTER_BUSINESS

async def register_business(update: Update, context: ContextTypes.DEFAULT_TYPE):
    key = update.message.text.strip()
    if key != "TESTKEY123":
        await update.message.reply_text("❌ Неверный ключ. Попробуйте снова:")
        return REGISTER_BUSINESS
    await update.message.reply_text("✅ Ключ принят! Введите название бизнеса:")
    return BUSINESS_NAME

async def business_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text.strip()
    await update.message.reply_text("📝 Описание бизнеса:")
    return BUSINESS_DESC

async def business_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["desc"] = update.message.text.strip()
    await update.message.reply_text("👥 Участники (через запятую):")
    return BUSINESS_MEMBERS

async def business_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["members"] = [m.strip() for m in update.message.text.split(",") if m.strip()]
    await update.message.reply_text("📞 Контакты:")
    return BUSINESS_CONTACTS

async def business_contacts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = {
        "user_id": str(update.message.from_user.id),
        "business_name": context.user_data["name"],
        "description": context.user_data["desc"],
        "members": context.user_data["members"],
        "contacts": update.message.text.strip()
    }
    try:
        resp = requests.post(f"{SERVER_URL}/register_business", json=data, timeout=5)
        if resp.status_code == 200:
            await update.message.reply_text("🎉 Бизнес зарегистрирован!")
        else:
            await update.message.reply_text("❌ Ошибка регистрации.")
    except:
        await update.message.reply_text("❌ Не удалось подключиться к серверу.")
    return ConversationHandler.END

# --- Реклама ---
async def start_advertise(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("🔑 Введите ключ активации для рекламы:")
    return ADVERTISE_KEY

async def advertise_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["adv_key"] = update.message.text.strip()
    await update.message.reply_text("📢 Введите текст рекламы:")
    return ADVERTISE_TEXT

async def advertise_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = {
        "user_id": str(update.message.from_user.id),
        "business_name": "Мой бизнес",
        "activation_key": context.user_data["adv_key"],
        "advertisement_text": update.message.text.strip()
    }
    try:
        resp = requests.post(f"{SERVER_URL}/advertise", json=data, timeout=5)
        if resp.status_code == 200:
            await update.message.reply_text("✅ Реклама отправлена!")
        else:
            await update.message.reply_text("❌ Ошибка: неверный ключ.")
    except:
        await update.message.reply_text("❌ Ошибка подключения.")
    return ConversationHandler.END

# --- Поддержка ---
async def send_support_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text
    user_id = update.message.from_user.id
    try:
        requests.post(f"{SERVER_URL}/send_support_message", json={"user_id": user_id, "message": msg}, timeout=5)
        await update.message.reply_text("✅ Сообщение отправлено!")
    except:
        await update.message.reply_text("❌ Не удалось отправить.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отменено.")
    return ConversationHandler.END


# --- Главная ---
def main():
    app = Application.builder().token(TOKEN).build()

    # 1. Конверсации
    reg_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_register, pattern="^register_business$")],
        states={
            REGISTER_BUSINESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_business)],
            BUSINESS_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, business_name)],
            BUSINESS_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, business_desc)],
            BUSINESS_MEMBERS: [MessageHandler(filters.TEXT & ~filters.COMMAND, business_members)],
            BUSINESS_CONTACTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, business_contacts)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    )

    adv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_advertise, pattern="^advertise$")],
        states={
            ADVERTISE_KEY: [MessageHandler(filters.TEXT & ~filters.COMMAND, advertise_key)],
            ADVERTISE_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, advertise_text)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    )

    # 2. Обработчики
    app.add_handler(CommandHandler("start", start))

    # Конверсации — первыми
    app.add_handler(reg_handler)
    app.add_handler(adv_handler)

    # Конкретные callback'и
    app.add_handler(CallbackQueryHandler(find_job, pattern="^find_job$"))
    app.add_handler(CallbackQueryHandler(help_menu, pattern="^help$"))
    app.add_handler(CallbackQueryHandler(contact_developer, pattern="^contact_dev$"))
    app.add_handler(CallbackQueryHandler(faq, pattern="^faq$"))
    app.add_handler(CallbackQueryHandler(back_to_menu, pattern="^back_to_menu$"))

    # Общий обработчик в конце
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, send_support_message))

    logger.info("Бот запущен.")
    app.run_polling()

if __name__ == "__main__":
    main()