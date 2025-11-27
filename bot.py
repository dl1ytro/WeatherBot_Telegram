"""
Простой Telegram-бот погоды с long polling.
Использует OpenWeather и читает токены из .env.
"""
from __future__ import annotations

import os
import sys
from typing import Optional

import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import CallbackContext, CommandHandler, Filters, MessageHandler, Updater

# Загружаем переменные окружения из .env
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
DEFAULT_CITY = "Odessa"
OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"


def ensure_tokens() -> None:
    """Проверяем наличие токенов перед стартом."""
    if not BOT_TOKEN:
        print("Ошибка: BOT_TOKEN не задан в .env")
        sys.exit(1)
    if not WEATHER_API_KEY:
        print("Предупреждение: WEATHER_API_KEY не задан, ответы о погоде будут недоступны.")


def fetch_weather(city: str) -> Optional[str]:
    """Запрашивает погоду для города и возвращает готовый текст ответа или сообщение об ошибке."""
    if not WEATHER_API_KEY:
        return "Не настроен WEATHER_API_KEY. Добавьте его в .env и перезапустите бота."

    params = {
        "q": city,
        "appid": WEATHER_API_KEY,
        "units": "metric",
        "lang": "ru",
    }
    try:
        response = requests.get(OPENWEATHER_URL, params=params, timeout=10)
        data = response.json()
    except requests.RequestException:
        return "Не удалось связаться с OpenWeather. Попробуйте позже."

    # OpenWeather может вернуть cod как int или строку
    cod = data.get("cod")
    if response.status_code != 200 or str(cod) != "200":
        return f"Не удалось найти погоду для города \"{city}\". Проверьте название."

    weather_list = data.get("weather") or []
    description = weather_list[0].get("description", "").capitalize() if weather_list else "Нет данных"
    main = data.get("main") or {}
    temp = main.get("temp")
    feels_like = main.get("feels_like")

    # Безопасные подстановки значений
    temp_text = f"{temp}°C" if temp is not None else "нет данных"
    feels_text = f"{feels_like}°C" if feels_like is not None else "нет данных"

    return (
        f"Погода в {city}:\n"
        f"{description}\n"
        f"🌡 Температура: {temp_text}\n"
        f"🤔 Ощущается как: {feels_text}"
    )


def start(update: Update, context: CallbackContext) -> None:
    """Приветствие и подсказка по использованию."""
    message = (
        "Привет! Я бот, который показывает текущую погоду.\n"
        "Примеры:\n"
        "/weather Одесса\n"
        "или просто отправьте название города, например: Кишинев"
    )
    update.message.reply_text(message)


def weather(update: Update, context: CallbackContext) -> None:
    """Обрабатываем команду /weather с городом или с городом по умолчанию."""
    city = " ".join(context.args).strip() if context.args else DEFAULT_CITY
    result = fetch_weather(city)
    update.message.reply_text(result)


def handle_text(update: Update, context: CallbackContext) -> None:
    """Любой текст считаем названием города и возвращаем погоду."""
    city = update.message.text.strip()
    if not city:
        update.message.reply_text("Отправьте название города, например: Одесса")
        return
    result = fetch_weather(city)
    update.message.reply_text(result)


def main() -> None:
    ensure_tokens()

    updater = Updater(token=BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("weather", weather))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))

    print("Бот запущен. Ожидаю сообщения...")
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
