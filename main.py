import asyncio
import requests
import random
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, FSInputFile
from googletrans import Translator
from gtts import gTTS
import os
from config import TG_TOKEN, WEATHER_API_KEY, GIPHY_API_KEY


bot = Bot(token=TG_TOKEN)
dp = Dispatcher()
translator = Translator()

@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(f"Привет, {message.from_user.first_name}, я не волшебник, я только учусь. \nВведи /help для подробностей.")

@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer("Я умею выполнять команды: "
                         "\n/start - поприветствую тебя "
                         "\n/help - расскажу, что к чему "
                         "\n/photo - оценю твою фотку "
                         "\n/english - переведу твою фразу на английский язык "
                         "\n/city - найду погоду в любом городе "
                         "\nНазвание города нужно вводить после команды /city")


@dp.message(F.photo)
async def cmd_photo(message: Message):
    list = ['Ого, какая фотка!', 'Что это?', 'Не отправляй мне такое больше', 'Это шедевр!']
    rand_answ = random.choice(list)
    tts = gTTS(text=rand_answ, lang='ru')
    tts.save('tts.mp3')
    audio = FSInputFile('tts.mp3')
    await bot.send_audio(message.chat.id, audio)
    os.remove('tts.mp3')
    await bot.download(message.photo[-1],destination=f'img/{message.photo[-1].file_id}.jpg')

@dp.message(Command("english"))
async def cmd_english(message: Message):
    ru_text = message.text.split(' ', 1)[1] if len(message.text.split()) > 1 else None
    if ru_text:
        try:
            translated = translator.translate(ru_text, dest='en')
            if translated and translated.text: 
                en_text = translated.text
                await message.answer(en_text)
            else:
                await message.answer("Не удалось выполнить перевод. Попробуй еще раз.")
        except Exception as e:
            await message.answer(f"Произошла ошибка при переводе: {e}")
    else:
        await message.answer("Сначала команда /english, после нее через пробел - фраза на русском.")

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
                f"Извини, не удалось получить данные о погоде для города {city}.\nЛови за это случайнкю гифку: \n{get_random_gif()}")
    else:
        await message.answer("Сначала команда /city, после нее через пробел - город.")

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