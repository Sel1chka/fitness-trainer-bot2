import os
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes
)
from programs import TRAINING_PROGRAMS, get_program_by_goal

# Настройка логирования - ИСПРАВЛЕНО
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Состояния диалога
ASK_GOAL, ASK_LEVEL = range(2)

# Словари для соответствия русских названий ключам
GOALS = {
    "Сжигание жира": "weight_loss",
    "Набор массы": "muscle_gain", 
    "Сила": "strength",
    "Выносливость": "endurance"
}

LEVELS = {
    "Новичок": "beginner",
    "Средний": "intermediate", 
    "Продвинутый": "advanced"
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я помогу создать программу тренировок.\n\n"
        "Команды:\n"
        "/create - Создать программу\n"
        "/help - Помощь"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start - Начать\n"
        "/create - Создать программу\n"
        "/cancel - Отменить"
    )

async def create(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[goal] for goal in GOALS.keys()]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("🎯 Выберите цель:", reply_markup=reply_markup)
    return ASK_GOAL

async def handle_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    goal_text = update.message.text
    if goal_text in GOALS:
        context.user_data['goal'] = GOALS[goal_text]
        keyboard = [[level] for level in LEVELS.keys()]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text("📊 Ваш уровень:", reply_markup=reply_markup)
        return ASK_LEVEL
    else:
        await update.message.reply_text("Пожалуйста, выберите цель из списка.")
        return ASK_GOAL

async def handle_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    level_text = update.message.text
    if level_text in LEVELS:
        goal = context.user_data['goal']
        level = LEVELS[level_text]
        program = get_program_by_goal(goal, level)
        
        text = f"🎉 **Ваша программа:**\n\n"
        text += f"**{program['title']}**\n"
        text += f"{program['description']}\n\n"
        text += "✨ **Особенности:**\n"
        for f in program['features']:
            text += f"• {f}\n"
        text += "\n📅 **Расписание:**\n"
        for day, workout in program['weekly_schedule'].items():
            text += f"• {day}: {workout}\n"
        text += f"\n🥗 Питание: {program['nutrition']}\n"
        text += f"💧 Вода: {program['water']}\n"
        if 'tips' in program:
            text += f"💡 Совет: {program['tips']}\n"
        
        await update.message.reply_text(text, parse_mode='Markdown')
        await update.message.reply_text(
            "Удачных тренировок! 💪",
            reply_markup=ReplyKeyboardMarkup.remove_keyboard()
        )
        return ConversationHandler.END
    else:
        await update.message.reply_text("Пожалуйста, выберите уровень из списка.")
        return ASK_LEVEL

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❌ Отменено",
        reply_markup=ReplyKeyboardMarkup.remove_keyboard()
    )
    return ConversationHandler.END

def main():
    token = os.environ.get('BOT_TOKEN')
    if not token:
        print("ОШИБКА: токен не найден!")
        return
    
    app = Application.builder().token(token).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('create', create)],
        states={
            ASK_GOAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_goal)],
            ASK_LEVEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_level)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(conv_handler)
    
    print("✅ Бот запущен!")
    app.run_polling()

if name == '__main__':
    main()
