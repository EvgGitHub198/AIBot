import os
from dotenv import load_dotenv
import telebot
import openai

load_dotenv()
bot = telebot.TeleBot(os.getenv("TELEGRAM_BOT_TOKEN"))
openai.api_key = os.getenv("OPENAI_API_KEY")


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Добро пожаловать в открытый искусственный интеллект-бот. Введите любое сообщение, чтобы получить ответ от меня.")


@bot.message_handler(func=lambda message: True)
def generate_response(message):
    try:
        prompt_chunks = [message.text[i:i + 80] for i in range(0, len(message.text), 80)]
        response_chunks = []
        for chunk in prompt_chunks:
            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=chunk,
                max_tokens=1500,
                n=1,
                stop=None,
                temperature=0.7,
            )
            response_chunks.append(response.choices[0].text)
        full_response = "".join(response_chunks)

        if len(full_response) > 1500:
            full_response = full_response[:1500]


        bot.reply_to(message, full_response)

    except Exception as e:
        bot.reply_to(message, "При обработке вашего запроса произошла ошибка. Пожалуйста, попробуйте еще раз позже.")


bot.polling()
