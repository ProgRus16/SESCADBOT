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
# Конфигурация
TOKEN = "8469169912:AAHcbKkHOgLR6HPwvpaEeYUTaN8bmjFOF2o"
SERVER_URL = "http://localhost:8000"

# Состояния для ConversationHandler
REGISTER_BUSINESS, BUSINESS_NAME, BUSINESS_DESC, BUSINESS_MEMBERS, BUSINESS_CONTACTS = range(5)
ADVERTISE_BUSINESS, ADVERTISE_KEY, ADVERTISE_TEXT = range(3)
SUPPORT_MESSAGE = range(1)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Зарегистрировать бизнес", callback_data="register_business")],
        [InlineKeyboardButton("Найти работу", callback_data="find_job")],
        [InlineKeyboardButton("Прорекламировать бизнес", callback_data="advertise")],
        [InlineKeyboardButton("Помощь", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Добро пожаловать на биржу фриланса!", reply_markup=reply_markup)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "register_business":
        await query.edit_message_text("Введите ключ активации для регистрации бизнеса:")
        return REGISTER_BUSINESS
    elif query.data == "find_job":
        await show_jobs(update, context)
    elif query.data == "advertise":
        await query.edit_message_text("Выберите бизнес для рекламы:")
        keyboard = [[InlineKeyboardButton("Мой бизнес", callback_data="advertise_my_business")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Выберите бизнес:", reply_markup=reply_markup)
        return ADVERTISE_BUSINESS
    elif query.data == "help":
        await show_help_menu(update, context)

async def show_jobs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = requests.get(f"{SERVER_URL}/get_businesses")
    businesses = response.json().get("businesses", [])

    if not businesses:
        await update.callback_query.edit_message_text("Пока нет доступных вакансий.")
        return

    keyboard = []
    for business in businesses:
        keyboard.append([InlineKeyboardButton(business["name"], callback_data=f"job_{business['name']}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text("Доступные вакансии:", reply_markup=reply_markup)

async def show_help_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Связь с разработчиком", callback_data="contact_dev")],
        [InlineKeyboardButton("FAQ", callback_data="faq")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text("Чем помочь?", reply_markup=reply_markup)

async def contact_developer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text("Напишите ваше сообщение разработчику:")
    return SUPPORT_MESSAGE

async def faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    faq_text = """
    ❓ **FAQ** ❓

    *1. Как зарегистрировать бизнес?*  
    → Используйте кнопку «Зарегистрировать бизнес» и следуйте инструкциям.  

    *2. Как повысить приоритет моего бизнеса?*  
    → Размещайте рекламу через бота.  

    *3. Как связаться с поддержкой?*  
    → Нажмите «Помощь» → «Связь с разработчиком».  
    """
    await update.callback_query.edit_message_text(faq_text, parse_mode="Markdown")

async def send_support_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    message = update.message.text
    requests.post(f"{SERVER_URL}/send_support_message", json={"user_id": user_id, "message": message})
    await update.message.reply_text("✅ Ваше сообщение отправлено разработчику!")
    return ConversationHandler.END

async def register_business(update: Update, context: ContextTypes.DEFAULT_TYPE):
    activation_key = update.message.text
    if activation_key != "TESTKEY123":
        await update.message.reply_text("❌ Неверный ключ активации. Попробуйте снова.")
        return REGISTER_BUSINESS
    await update.message.reply_text("✅ Ключ принят! Теперь введите название бизнеса:")
    return BUSINESS_NAME

async def business_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["business_name"] = update.message.text
    await update.message.reply_text("📝 Введите описание бизнеса:")
    return BUSINESS_DESC

async def business_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["description"] = update.message.text
    await update.message.reply_text("👥 Введите список участников (через запятую):")
    return BUSINESS_MEMBERS

async def business_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["members"] = update.message.text.split(",")
    await update.message.reply_text("📞 Введите контакты для связи:")
    return BUSINESS_CONTACTS

async def business_contacts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data
    user_id = update.message.from_user.id

    registration_data = {
        "user_id": str(user_id),
        "business_name": user_data["business_name"],
        "description": user_data["description"],
        "members": user_data["members"],
        "contacts": update.message.text
    }

    response = requests.post(f"{SERVER_URL}/register_business", json=registration_data)
    if response.status_code == 200:
        await update.message.reply_text("🎉 Бизнес успешно зарегистрирован!")
    else:
        await update.message.reply_text("❌ Ошибка при регистрации. Попробуйте позже.")
    return ConversationHandler.END

async def advertise_business(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🔑 Введите ключ активации для рекламы:")
    return ADVERTISE_KEY

async def advertise_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["activation_key"] = update.message.text
    await update.message.reply_text("📢 Введите текст рекламы:")
    return ADVERTISE_TEXT

async def advertise_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    advertise_data = {
        "user_id": str(user_id),
        "business_name": "Мой бизнес",
        "activation_key": context.user_data["activation_key"],
        "advertisement_text": update.message.text
    }
    response = requests.post(f"{SERVER_URL}/advertise", json=advertise_data)
    if response.status_code == 200:
        await update.message.reply_text("✅ Реклама успешно разослана!")
    else:
        await update.message.reply_text("❌ Ошибка: неверный ключ или бизнес не найден.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Действие отменено.")
    return ConversationHandler.END

def main():
    # Создаем Application вместо Updater
    application = Application.builder().token(TOKEN).build()

    # Обработчики команд и кнопок
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_click))

    # ConversationHandler для регистрации бизнеса
    reg_business_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_click, pattern="^register_business$")],
        states={
            REGISTER_BUSINESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_business)],
            BUSINESS_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, business_name)],
            BUSINESS_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, business_desc)],
            BUSINESS_MEMBERS: [MessageHandler(filters.TEXT & ~filters.COMMAND, business_members)],
            BUSINESS_CONTACTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, business_contacts)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    # ConversationHandler для рекламы
    advertise_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(advertise_business, pattern="^advertise_")],
        states={
            ADVERTISE_KEY: [MessageHandler(filters.TEXT & ~filters.COMMAND, advertise_key)],
            ADVERTISE_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, advertise_text)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    # Обработчик помощи
    application.add_handler(reg_business_handler)
    application.add_handler(advertise_handler)
    application.add_handler(CallbackQueryHandler(contact_developer, pattern="^contact_dev$"))
    application.add_handler(CallbackQueryHandler(faq, pattern="^faq$"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, send_support_message))

    application.run_polling()

if __name__ == "__main__":
    main()