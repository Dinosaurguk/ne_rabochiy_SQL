import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes
)
REG_NAME, REG_SURNAME = range(2)
EDIT_NAME, EDIT_SURNAME = range(2, 4)

conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        first_name TEXT,
        last_name TEXT
    )
''')
conn.commit()

def add_user(user_id, first_name, last_name):
    cursor.execute('INSERT INTO users (user_id, first_name, last_name) VALUES (?, ?, ?)', (user_id, first_name, last_name))
    conn.commit()

def get_user(user_id):
    cursor.execute('SELECT first_name, last_name FROM users WHERE user_id = ?', (user_id,))
    return cursor.fetchone()

def update_user(user_id, first_name, last_name):
    cursor.execute('UPDATE users SET first_name = ?, last_name = ? WHERE user_id = ?', (first_name, last_name, user_id))
    conn.commit()

#  /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("Регистрация", callback_data='register')],
        [InlineKeyboardButton("Редактирование", callback_data='edit')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите опцию:", reply_markup=reply_markup)

# кнопки
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == 'register':
        # Проверка на вшивость
        user_data = get_user(user_id)
        if user_data:
            await query.edit_message_text("Вы уже зарегистрированы.")
            return ConversationHandler.END
        else:
            await query.edit_message_text("Введите ваше имя:")
            return REG_NAME

    elif query.data == 'edit':
        # Проверка зарегистрирован ли пользователь
        user_data = get_user(user_id)
        if not user_data:
            await query.edit_message_text("Вы не зарегистрированы. Сначала зарегистрируйтесь.")
            return ConversationHandler.END
        else:
            await query.edit_message_text("Введите ваше новое имя:")
            return EDIT_NAME
    return ConversationHandler.END

# ввод имени
async def register_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    first_name = update.message.text
    context.user_data['first_name'] = first_name
    await update.message.reply_text("Введите вашу фамилию:")
    return REG_SURNAME

# ввод фамилии и сохранение
async def register_surname(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    last_name = update.message.text
    first_name = context.user_data['first_name']

    # Добавляем пользователя в БД 
    add_user(user_id, first_name, last_name)
    await update.message.reply_text(f"Регистрация комплит имя: {first_name}, фамилия: {last_name}")
    return ConversationHandler.END

# редактировании ввод имени
async def edit_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    first_name = update.message.text
    context.user_data['first_name'] = first_name
    await update.message.reply_text("Введите вашу новую фамилию:")
    return EDIT_SURNAME

# херня для редактирования ввод фамилии и обновление
async def edit_surname(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    last_name = update.message.text
    first_name = context.user_data['first_name']# Обновляем данные пользователя
    update_user(user_id, first_name, last_name)
    await update.message.reply_text(f"обновление: новое имя: {first_name}, фамилия: {last_name}")
    return ConversationHandler.END

def main() -> None:




    TOKEN = ''

    application = Application.builder().token(TOKEN).build()


    registration_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern='register')],
        states={
            REG_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_name)],
            REG_SURNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_surname)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    edit_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern='edit')],
        states={
            EDIT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_name)],
            EDIT_SURNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_surname)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(registration_handler)
    application.add_handler(edit_handler)
    application.add_handler(CallbackQueryHandler(button_handler))  # Для обработки кнопок меню, если они не пойманы выше

    # Запускаем бота
    application.run_polling()

if __name__ == 'main':
    __main__()