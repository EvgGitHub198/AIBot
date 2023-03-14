import os
from dotenv import load_dotenv
import telebot
import openai
import sqlite3
from datetime import datetime, timedelta

load_dotenv()
bot = telebot.TeleBot(os.getenv("TELEGRAM_BOT_TOKEN"))
openai.api_key = os.getenv("OPENAI_API_KEY")

conn = sqlite3.connect("bot.db", check_same_thread=False)

with conn:
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS context (user_id TEXT, message TEXT, timestamp TEXT)")

CONTEXT_CACHE_INTERVAL = timedelta(minutes=20)

context_cache = {}


@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Добро пожаловать в открытый искусственный интеллект-бот. Введите любое сообщение, чтобы получить ответ от меня.")


@bot.message_handler(commands=['help'])
def help(message):
    bot.reply_to(message,
                 "Вы можете отправлять запросы через меня. Просто напишите мне свой запрос и я отправлю его на обработку.")


@bot.message_handler(func=lambda message: True)
def echo(message):
    if message.chat.id in context_cache and datetime.now() - context_cache[message.chat.id]['timestamp'] <= CONTEXT_CACHE_INTERVAL:
        context = context_cache[message.chat.id]['message']
    else:
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT message FROM context WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1", (str(message.chat.id),))
            row = cur.fetchone()
            context = row[0] if row else ""

    bot.reply_to(message, "Запрос принят в работу.")
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=context + message.text,
            max_tokens=3500
        )
        bot.reply_to(message, response.choices[0].text)

        with conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO context (user_id, message, timestamp) VALUES (?, ?, ?)", (str(message.chat.id), context + message.text, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
        context_cache[message.chat.id] = {'message': context + message.text, 'timestamp': datetime.now()}

    except Exception as e:
        bot.reply_to(message, f"Произошла ошибка при обработке вашего запроса: {str(e)}")


bot.polling()