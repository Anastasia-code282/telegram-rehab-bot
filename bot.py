import telebot
from telebot import types
from flask import Flask, request
from datetime import datetime, timedelta
import threading
import schedule
import time
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

surgery_date = datetime(2025, 7, 8)
user_ids = set()

# === Меню клавіатури ===
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("/status", "/питання")
    markup.row("ℹ️ Контакт з реабілітологом")
    return markup

# === Вправи та рекомендації ===
def get_rehab_info(day_number):
    if day_number <= 14:
        return [
            "*Фаза 1: Гостра (1–14 день після операції)*\n",
            "🧠 *Ціль:* зменшити біль, набряк, активувати м'язи",
            "❗ Без опори на прооперовану ногу",
            "\n🦵 *Вправи:*",
            "- Ізометрія квадріцепса",
            "- Піднімання прямої ноги",
            "- Згинання коліна до 30–40°",
            "- Пальцева помпа, відведення ноги, розгинання в стегні",
            "\n💊 *Препарати:*",
            "- Ксарелто 10 мг – до 28.07.2025",
            "- Вітамін D3+K2, Магній",
            "\n📌 *Рекомендації:*",
            "- Носити тутор до 14 дня",
            "- Без навантаження 1.5 міс"
        ]
    elif 15 <= day_number <= 30:
        return [
            "*Фаза 2: Рання функціональна (3–6 тиждень)*\n",
            "🧘‍♀️ *Вправи:* Heel Slides, підйом ноги, міст, баланс, гомілкостоп",
            "🧠 *Ціль:* рух до 90°, м’язовий тонус, контроль",
            "\n💊 *Підтримка:*",
            "- Глюкозамін, Колаген II, D3, Mg",
            "\n❗ *Застереження:*",
            "- Без бігу, скручувань, сидіння навпочіпки",
            "- Стоп при болю або нестабільності"
        ]
    else:
        return [
            "*🎉 Основна фаза завершена!*",
            "Поступово збільшуй навантаження під наглядом спеціаліста"
        ]

# === Команди Telegram ===
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_ids.add(message.chat.id)
    bot.send_message(
        message.chat.id,
        "Привіт! 🤖\nЯ допоможу тобі з реабілітацією після операції.\n"
        "Натисни /status, щоб отримати план на сьогодні.",
        reply_markup=main_menu()
    )

@bot.message_handler(commands=['status'])
def send_status(message):
    today = datetime.now()
    day_number = (today.date() - surgery_date.date()).days + 1
    response = f"📅 *Сьогодні {day_number}-й день після операції*\n\n"
    rehab_info = get_rehab_info(day_number)
    response += "\n\n".join(rehab_info)
    bot.send_message(message.chat.id, response, parse_mode="Markdown")

@bot.message_handler(commands=['питання'])
def ask_help(message):
    bot.send_message(message.chat.id, "Напиши своє запитання: наприклад, *«чи можна згинати ногу?»*",
                     parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    text = message.text.lower()
    day = (datetime.now().date() - surgery_date.date()).days + 1

    if "згинати" in text and "ногу" in text:
        if day <= 14:
            bot.reply_to(message, "🔒 Наразі дозволено згинати до 30–40°, пасивно. Не більше без дозволу!")
        else:
            bot.reply_to(message, "✅ Можна обережно згинати до 90°, якщо немає болю.")
    elif "ксарелто" in text:
        bot.reply_to(message, "💊 Ксарелто слід приймати 1 таб/день до 28.07.2025.")
    elif "навантаження" in text:
        bot.reply_to(message, "🚫 Осьове навантаження на ліву ногу заборонене до 1.5 місяця після операції.")
    elif "контакт" in text:
        bot.reply_to(message, "📞 Зв’язок з реабілітологом: +380672727910")
    else:
        bot.reply_to(message, "❓ Не впевнений у відповіді. Надішли /status або конкретне питання.")

# === Автоматичні нагадування (не працює у Flask без окремого сервісу Render Worker) ===
def send_daily_reminders():
    for user_id in user_ids:
        bot.send_message(user_id, "🕘 *Нагадування:* не забудь виконати вправи ЛФК сьогодні! Надішли /status 🦵", parse_mode="Markdown")

# === Flask routes ===
@app.route('/')
def home():
    return "✅ Telegram Rehab Bot працює!"

@app.route(f"/{TOKEN}", methods=["POST"])
def receive_update():
    json_string = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

# === Запуск Flask-сервера ===
if os.getenv("RENDER_EXTERNAL_URL"):
    # Якщо на сервері Render — запускаємо вебхук
    app_url = os.getenv("RENDER_EXTERNAL_URL")
    bot.remove_webhook()
    bot.set_webhook(url=f"{app_url}/{TOKEN}")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
else:
    # Якщо локально — запускаємо polling
    print("🔁 Локальний запуск: режим polling")
    bot.remove_webhook()
    bot.infinity_polling()


