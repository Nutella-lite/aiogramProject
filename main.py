import asyncio
import requests
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from googletrans import Translator
from config import TG_TOKEN, WEATHER_API_KEY, GIPHY_API_KEY

bot = Bot(token=TG_TOKEN)
dp = Dispatcher()
translator = Translator()

@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("Привет, я бот, который сообщает погоду в любом городе.")

@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer("Я умею выполнять команды: \n/start - запуск \n/help - помощь \n/city - поиск погоды в городе \nНазвание города нужно вводить после команды /city")


@dp.message(Command("city"))
async def cmd_city(message: Message):
    city = message.text.split(' ', 1)[1] if len(message.text.split()) > 1 else None

    if city:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
        response = requests.get(url)
        data = response.json()
        if response.status_code == 200:
            weather_description = data['weather'][0]['description']
            try:
                translated_description = translator.translate(weather_description, dest='ru').text
            except Exception as e:
                translated_description = weather_description
                print(f"Ошибка перевода: {e}")
            await message.answer(
                f"Температура в городе {city} {data['main']['temp']}°C, {translated_description}")
        else:
            await message.answer(
                f"Извините, не удалось получить данные о погоде для города {city}.\nВот Вам за это случайная гифка: \n{get_random_gif()}")
    else:
        await message.answer("Пожалуйста, укажите название города после команды /city.")


def get_random_gif():
    url = f'http://api.giphy.com/v1/gifs/random?api_key={GIPHY_API_KEY}'
    response = requests.get(url)
    data = response.json()
    gif_url = data['data']['images']['original']['url']
    return gif_url

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())