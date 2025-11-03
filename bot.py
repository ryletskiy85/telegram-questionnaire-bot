import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import csv
import json
from pathlib import Path

# Load environment variables
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')

QUESTIONS = [
    "1. Как зовут вашу дочь?",
    "2. Сколько ей лет?",
    "3. Какое любимое занятие у вашей дочери?",
    "4. Какое любимое блюдо у вашей дочери?",
    "5. Какие у вашей дочери мечты?",
    "6. Какое самое забавное воспоминание о ней?",
    "7. Какой любимый цвет у вашей дочери?",
    "8. Есть ли у вашей дочери любимый питомец? Если да, кто?",
    "9. Какая ёё самая сильная черта характера?",
    "10. Какое её любимое время года?",
    "11. Какую музыку она предпочитает?",
    "12. Какую сказку она любит?",
    "13. Какими героями она восхищается?",
    "14. Какое ваше самое тёплое совместное воспоминание?",
    "15. Какие качества вы восхищаетесь в ней?",
    "16. Какие игры она любит?",
    "17. Что делает её счастливой?",
    "18. Какие достижения вы особенно цените?",
    "19. Какие у неё любимые книги или фильмы?",
    "20. Чем она любит заниматься с семьёй?",
    "21. Какие традиции в вашей семье ей нравятся?",
    "22. Какие слова ей нравятся слышать от вас?",
    "23. Как вы видите её будущее?",
    "24. Как вы хотите, чтобы она чувствовала себя, слушая эту песню?"
]

# Ensure data directory exists
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

RESPONSES_FILE = DATA_DIR / "responses.csv"
SESSION_FILE = DATA_DIR / "session_store.json"

# Load or initialize session store
def load_sessions():
    if SESSION_FILE.exists():
        with SESSION_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_sessions(sessions):
    with SESSION_FILE.open("w", encoding="utf-8") as f:
        json.dump(sessions, f)

# Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    sessions = load_sessions()
    sessions[str(chat_id)] = {"answers": [], "index": 0}
    save_sessions(sessions)
    await update.message.reply_text(
        "\u0417\u0434\u0440\u0430\u0432\u0441\u0442\u0432\u0443\u0439\u0442\u0435! \u0414\u0430\u0432\u0430\u0439\u0442\u0435 \u0441\u043e\u0437\u0434\u0430\u0434\u0438\u043c \u043f\u0435\u0440\u0441\u043e\u043d\u0430\u043b\u044c\u043d\u0443\u044e \u043f\u0435\u0441\u043d\u044e. \u042f \u0431\u0443\u0434\u0443 \u0437\u0430\u0434\u0430\u0432\u0430\u0442\u044c \u0432\u0430\u043c 24 \u0432\u043e\u043f\u0440\u043e\u0441\u0430. "
        "\u0412\u044b \u043c\u043e\u0436\u0435\u0442\u0435 \u0432 \u043b\u044e\u0431\u043e\u0439 \u043c\u043e\u043c\u0435\u043d\u0442 \u043d\u0430\u043f\u0438\u0441\u0430\u0442\u044c /back, \u0447\u0442\u043e\u0431\u044b \u0432\u0435\u0440\u043d\u0443\u0442\u044c\u0441\u044f \u043a \u043f\u0440\u0435\u0434\u044b\u0434\u0443\u0449\u0435\u043c\u0443 \u0432\u043e\u043f\u0440\u043e\u0441\u0443, "
        "\u0438\u043b\u0438 /cancel, \u0447\u0442\u043e\u0431\u044b \u043e\u0442\u043c\u0435\u043d\u0438\u0442\u044c \u043e\u043f\u0440\u043e\u0441.\n\n" + QUESTIONS[0]
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    text = update.message.text.strip()
    sessions = load_sessions()
    session = sessions.get(str(chat_id))

    if not session:
        await update.message.reply_text("\u041d\u0430\u0447\u043d\u0438\u0442\u0435 \u043e\u043f\u0440\u043e\u0441 \u043a\u043e\u043c\u0430\u043d\u0434\u043e\u0439 /start.")
        return

    # handle commands typed as regular text
    if text.lower() in ['/back', 'back']:
        await back(update, context)
        return
    if text.lower() in ['/cancel', 'cancel']:
        await cancel(update, context)
        return

    index = session["index"]
    session["answers"].append(text)
    index += 1
    session["index"] = index

    if index < len(QUESTIONS):
        save_sessions(sessions)
        await update.message.reply_text(QUESTIONS[index])
    else:
        # Save responses to CSV
        fieldnames = [f"Q{i+1}" for i in range(len(QUESTIONS))]
        write_header = not RESPONSES_FILE.exists()
        with RESPONSES_FILE.open("a", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if write_header:
                writer.writeheader()
            writer.writerow({fieldnames[i]: ans for i, ans in enumerate(session["answers"])})
        # Notify user
        summary = "\n".join([f"{QUESTIONS[i]} {ans}" for i, ans in enumerate(session["answers"])])
        await update.message.reply_text("\u0421\u043f\u0430\u0441\u0438\u0431\u043e \u0437\u0430 \u0432\u0430\u0448\u0438 \u043e\u0442\u0432\u0435\u0442\u044b! \u0412\u043e\u0442 \u0447\u0442\u043e \u043f\u043e\u043b\u0443\u0447\u0438\u043b\u043e\u0441\u044c:\n\n" + summary)
        # Optionally notify admin
        if ADMIN_CHAT_ID:
            try:
                await context.bot.send_message(int(ADMIN_CHAT_ID), f"\u041d\u043e\u0432\u0430\u044f \u0430\u043d\u043a\u0435\u0442\u0430 \u043e\u0442 {chat_id}:\n\n{summary}")
            except Exception as e:
                logging.exception("Failed to send admin message")
        # Clear session
        sessions.pop(str(chat_id))
        save_sessions(sessions)

async def back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    sessions = load_sessions()
    session = sessions.get(str(chat_id))
    if not session:
        await update.message.reply_text("\u041d\u0430\u0447\u043d\u0438\u0442\u0435 \u043e\u043f\u0440\u043e\u0441 \u043a\u043e\u043c\u0430\u043d\u0434\u043e\u0439 /start.")
        return
    index = session["index"]
    if index > 0:
        index -= 1
        session["index"] = index
        session["answers"] = session["answers"][:-1]
        save_sessions(sessions)
        await update.message.reply_text("\u0425\u043e\u0440\u043e\u0448\u043e, \u0432\u0435\u0440\u043d\u0451\u043c\u0441\u044f \u043a \u043f\u0440\u0435\u0434\u044b\u0434\u0443\u0449\u0435\u043c\u0443 \u0432\u043e\u043f\u0440\u043e\u0441\u0443:\n\n" + QUESTIONS[index])
    else:
        await update.message.reply_text("\u0412\u044b \u0435\u0449\u0451 \u043d\u0435 \u043e\u0442\u0432\u0435\u0442\u0438\u043b\u0438 \u043d\u0438 на один вопрос.")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    sessions = load_sessions()
    if str(chat_id) in sessions:
        sessions.pop(str(chat_id))
        save_sessions(sessions)
    await update.message.reply_text("\u0410\u043d\u043a\u0435\u0442\u0430 \u043e\u0442\u043c\u0435\u043d\u0435\u043d\u0430. \u0415\u0441\u043b\u0438 \u0437\u0430\u0445\u043e\u0442\u0438\u0442\u0435 \u043d\u0430\u0447\u0430\u0442\u044c \u0441\u043d\u043e\u0432\u0430, \u043e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 /start.")

async def export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Export CSV to admin
    if str(update.message.chat_id) != ADMIN_CHAT_ID:
        await update.message.reply_text("\u042dта команда доступна только администратору.")
        return
    if RESPONSES_FILE.exists():
        await update.message.reply_document(document=RESPONSES_FILE.open("rb"), filename="responses.csv")
    else:
        await update.message.reply_text("\u0424\u0430\u0439\u043b с ответами ещё не созда\u043d.")

def main():
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("back", back))
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(CommandHandler("export", export))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

if __name__ == "__main__":
    main()
