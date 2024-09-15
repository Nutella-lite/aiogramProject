import asyncio
import random
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import aiosqlite
import aiohttp
from aiogram.fsm.state import State, StatesGroup
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

finish_button = KeyboardButton(text="Завершить ввод")
cancel_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(finish_button)

# FSM для личных финансов
class FinancesForm(StatesGroup):
    choose_category = State()
    new_category = State()
    enter_amount = State()

# Создание таблицы пользователей
# В функции init_db() добавьте создание таблицы expenses
async def init_db():
    async with aiosqlite.connect('user.db') as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE,
                name TEXT
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                category TEXT,
                amount REAL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        await db.commit()


# Обработчик команды /start
@dp.message(CommandStart())
async def cmd_start(message: Message):
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
    telegram_id = message.from_user.id
    async with aiosqlite.connect('user.db') as db:
        # Получаем ID пользователя из базы данных
        async with db.execute('SELECT id FROM users WHERE telegram_id = ?', (telegram_id,)) as cursor:
            user = await cursor.fetchone()
        if not user:
            await message.reply("Вы не зарегистрированы. Пожалуйста, используйте кнопку \"Регистрация\".")
            return
        user_id = user[0]
        # Получаем список категорий пользователя
        async with db.execute('SELECT DISTINCT category FROM expenses WHERE user_id = ?', (user_id,)) as cursor:
            categories = await cursor.fetchall()
    if categories:
        # Если есть сохраненные категории, предлагаем их выбрать или добавить новую
        category_buttons = [KeyboardButton(text=category[0]) for category in categories]
        category_buttons.append(KeyboardButton(text="Добавить новую категорию"))
        category_buttons.append(finish_button)
        categories_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        categories_keyboard.add(*category_buttons)
        await message.reply("Выберите категорию или добавьте новую:", reply_markup=categories_keyboard)
        await state.set_state(FinancesForm.choose_category)
    else:
        # Если нет сохраненных категорий, просим добавить новую
        await message.reply("Введите название категории расходов.", reply_markup=cancel_keyboard)
        await state.set_state(FinancesForm.new_category)


# Универсальный обработчик для состояний FinancesForm
@dp.message(F.state == FinancesForm.choose_category)
async def process_choose_category(message: Message, state: FSMContext):
    category = message.text
    if category == "Добавить новую категорию":
        await message.reply("Введите название новой категории расходов.", reply_markup=cancel_keyboard)
        await state.set_state(FinancesForm.new_category)
    elif category == "Завершить ввод":
        await message.reply("Ввод завершен.", reply_markup=keyboard_registered)
        await state.clear()
    else:
        # Пользователь выбрал существующую категорию
        await state.update_data(category=category)
        await message.reply(f"Введите сумму расходов для категории '{category}'.", reply_markup=cancel_keyboard)
        await state.set_state(FinancesForm.enter_amount)

@dp.message(F.state == FinancesForm.new_category)
async def process_new_category(message: Message, state: FSMContext):
    category = message.text
    if category == "Завершить ввод":
        await message.reply("Ввод завершен.", reply_markup=keyboard_registered)
        await state.clear()
    else:
        await state.update_data(category=category)
        await message.reply(f"Введите сумму расходов для категории '{category}'.", reply_markup=cancel_keyboard)
        await state.set_state(FinancesForm.enter_amount)

@dp.message(F.state == FinancesForm.enter_amount)
async def process_enter_amount(message: Message, state: FSMContext):
    if message.text == "Завершить ввод":
        await message.reply("Ввод завершен.", reply_markup=keyboard_registered)
        await state.clear()
        return
    try:
        amount = float(message.text.replace(',', '.'))
        data = await state.get_data()
        category = data['category']
        telegram_id = message.from_user.id
        async with aiosqlite.connect('user.db') as db:
            # Получаем ID пользователя
            async with db.execute('SELECT id FROM users WHERE telegram_id = ?', (telegram_id,)) as cursor:
                user = await cursor.fetchone()
            user_id = user[0]
            # Сохраняем расход в базе данных
            await db.execute('INSERT INTO expenses (user_id, category, amount) VALUES (?, ?, ?)', (user_id, category, amount))
            await db.commit()
        await message.reply(f"Расход в категории '{category}' на сумму {amount} сохранен.\nВы можете добавить еще расходы или нажать 'Завершить ввод' для выхода.", reply_markup=cancel_keyboard)
        # Возвращаемся к выбору категории
        await state.set_state(FinancesForm.choose_category)
    except ValueError:
        await message.reply("Пожалуйста, введите числовое значение для суммы расходов.", reply_markup=cancel_keyboard)

async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
