import os
import requests
from flask import Flask, request
import telegram

TOKEN = os.getenv("BOT_TOKEN")
WEATHER_KEY = os.getenv("WEATHER_API_KEY")

bot = telegram.Bot(TOKEN)

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "Bot is running!", 200


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    update = telegram.Update.de_json(data, bot)

    if update.message and update.message.text:
        chat_id = update.message.chat.id
        text = update.message.text.strip().lower()

        if text.startswith("/start"):
            bot.send_message(
                chat_id,
                "Привет! Я бот погоды.\n"
                "Напиши: /weather Одесса\n"
                "или просто название города."
            )
            return "OK", 200

        if text.startswith("/weather"):
            city = text.replace("/weather", "").strip() or "Odessa"
        else:
            city = text

        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {"q": city, "appid": WEATHER_KEY, "units": "metric", "lang": "ru"}

        r = requests.get(url, params=params)
        if r.status_code != 200:
            bot.send_message(chat_id, "Город не найден.")
            return "OK", 200

        data_w = r.json()
        temp = data_w["main"]["temp"]
        feels = data_w["main"]["feels_like"]
        desc = data_w["weather"][0]["description"]

        bot.send_message(
            chat_id,
            f"Погода в {city}:\n"
            f"{desc.capitalize()}\n"
            f"🌡 Температура: {temp}°C\n"
            f"🤔 Ощущается как: {feels}°C"
        )

    return "OK", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
