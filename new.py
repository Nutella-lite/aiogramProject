import sqlite3
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import logging
from config import TG_TOKEN, WEATHER_API_KEY, GIPHY_API_KEY

logging.basicConfig(level=logging.INFO)

"""
Создайте новую базу данных school_data.db. 
В этой базе данных создайте таблицу students с колонками: 
id (INTEGER, PRIMARY KEY, AUTOINCREMENT) name (TEXT) age (INTEGER) grade (TEXT)
Создайте Телеграм-бота, который запрашивает у пользователя 
имя, возраст и класс (grade), в котором он учится. 
Сделайте так чтоб бот сохранял введенные данные в таблицу students 
базы данных school_data.db.
"""
class Form(StatesGroup):
    name = State()
    age = State()
    grade = State()
def init_db():
    conn = sqlite3.connect('school_data.db')
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    age INTEGER,
    grade TEXT)''')
    conn.commit()
    conn.close()

init_db()

bot = Bot(token=TG_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await message.answer('Привет! Как тебя зовут?')
    await state.set_state(Form.name)

@dp.message(Form.name)
async def name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer('Сколько тебе лет?')
    await state.set_state(Form.age)

@dp.message(Form.age)
async def age(message: Message, state: FSMContext):
    await state.update_data(age=message.text)
    await message.answer('В каком ты классе?')
    await state.set_state(Form.grade)

@dp.message(Form.grade)
async def grade(message: Message, state: FSMContext):
    await state.update_data(grade=message.text)
    data = await state.get_data()
    conn = sqlite3.connect('school_data.db')
    cur = conn.cursor()
    cur.execute('''
    INSERT INTO students (name, age, grade) VALUES (?, ?, ?)''', (data['name'], data['age'], data['grade']))
    conn.commit()
    conn.close()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())