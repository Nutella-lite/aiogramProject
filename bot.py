import asyncio
import random
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import ReplyKeyboardBuilder
import aiosqlite
import aiohttp
import os
from config import TOKEN, EXCHANGE_API_KEY

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Кнопки и клавиатуры
button_register = KeyboardButton(text="Регистрация")
button_exchange_rates = KeyboardButton(text="Курсы валют")
button_tips = KeyboardButton(text="Советы по экономии")
button_finances = KeyboardButton(text="Личные финансы")

keyboard_unregistered = ReplyKeyboardMarkup(
    keyboard=[
        [button_register, button_exchange_rates],
        [button_tips, button_finances]
    ],
    resize_keyboard=True
)

keyboard_registered = ReplyKeyboardMarkup(
    keyboard=[
        [button_exchange_rates, button_tips, button_finances]
    ],
    resize_keyboard=True
)

# FSM для личных финансов
class FinancesForm(StatesGroup):
    category = State()
    expenses = State()
    counter = State()

# Создание таблицы пользователей
async def init_db():
    async with aiosqlite.connect('user.db') as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE,
                name TEXT,
                categories TEXT,
                expenses TEXT
            )
        ''')
        await db.commit()

# Обработчик команды /start
@dp.message(CommandStart())
async def send_start(message: Message):
    telegram_id = message.from_user.id
    async with aiosqlite.connect('user.db') as db:
        async with db.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,)) as cursor:
            user = await cursor.fetchone()
        if user:
            await message.answer("Привет! Выберите действие в меню:", reply_markup=keyboard_registered)
        else:
            await message.answer("Привет! Я финансовый помощник. Выберите действие в меню:", reply_markup=keyboard_unregistered)

# Обработчик регистрации
@dp.message(F.text == "Регистрация")
async def registration(message: Message):
    telegram_id = message.from_user.id
    name = message.from_user.full_name
    async with aiosqlite.connect('user.db') as db:
        async with db.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,)) as cursor:
            user = await cursor.fetchone()
        if user:
            await message.answer("Вы уже зарегистрированы!")
        else:
            await db.execute('INSERT INTO users (telegram_id, name) VALUES (?, ?)', (telegram_id, name))
            await db.commit()
            await message.answer("Вы успешно зарегистрированы!", reply_markup=keyboard_registered)

# Обработчик курсов валют
@dp.message(F.text == "Курсы валют")
async def exchange_rates(message: Message):
    url = f"https://v6.exchangerate-api.com/v6/{EXCHANGE_API_KEY}/latest/USD"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    await message.answer("Не удалось получить данные, попробуйте снова")
                    return
                data = await response.json()
        usd_to_rub = data['conversion_rates']['RUB']
        usd_to_eur = data['conversion_rates']['EUR']
        eur_to_rub = usd_to_rub / usd_to_eur
        await message.answer(
            f"1 USD - {usd_to_rub:.2f} RUB\n"
            f"1 EUR - {eur_to_rub:.2f} RUB"
        )
    except Exception as e:
        logging.error(f"Ошибка при получении курсов валют: {e}")
        await message.answer("Произошла ошибка, попробуйте снова")

# Обработчик советов по экономии
@dp.message(F.text == "Советы по экономии")
async def send_tips(message: Message):
    tips = [
        "Совет 1: Ведите бюджет и следите за своими расходами.",
        "Совет 2: Откладывайте часть доходов на сбережения.",
        "Совет 3: Покупайте товары по скидкам и распродажам.",
        "Совет 4: Избегайте импульсивных покупок.",
        "Совет 5: Планируйте крупные расходы заранее."
    ]
    tip = random.choice(tips)
    await message.answer(tip)

# Обработчик личных финансов
@dp.message(F.text == "Личные финансы")
async def finances_start(message: Message, state: FSMContext):
    await state.update_data(categories=[], expenses=[], counter=1)
    await state.set_state(FinancesForm.category)
    await message.reply("Введите название категории расхода №1:")

# Универсальный обработчик для состояний FinancesForm
@dp.message(F.state.in_([FinancesForm.category, FinancesForm.expenses]))
async def finances_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    counter = data.get('counter', 1)
    categories = data.get('categories', [])
    expenses = data.get('expenses', [])

    current_state = await state.get_state()
    if current_state == FinancesForm.category.state:
        categories.append(message.text)
        await state.update_data(categories=categories)
        await state.set_state(FinancesForm.expenses)
        await message.reply(f"Введите сумму расходов для категории '{message.text}':")
    elif current_state == FinancesForm.expenses.state:
        try:
            expense = float(message.text.replace(',', '.'))
            expenses.append(expense)
            await state.update_data(expenses=expenses)
            counter += 1
            await state.update_data(counter=counter)
            if counter <= 3:
                await state.set_state(FinancesForm.category)
                await message.reply(f"Введите название категории расхода №{counter}:")
            else:
                # Сохранение данных в БД
                telegram_id = message.from_user.id
                categories_str = ';'.join(data['categories'])
                expenses_str = ';'.join(map(str, data['expenses']))
                async with aiosqlite.connect('user.db') as db:
                    await db.execute(
                        '''UPDATE users SET categories = ?, expenses = ? WHERE telegram_id = ?''',
                        (categories_str, expenses_str, telegram_id)
                    )
                    await db.commit()
                await state.clear()
                await message.answer("Категории и расходы сохранены!")
        except ValueError:
            await message.reply("Пожалуйста, введите числовое значение для расходов.")

async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
