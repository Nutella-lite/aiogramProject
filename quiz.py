import asyncio
import requests
import random
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from googletrans import Translator
from config import TG_TOKEN
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

bot = Bot(token=TG_TOKEN)
dp = Dispatcher(bot=bot)
translator = Translator()


quiz_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Случайная', callback_data='random'),
     InlineKeyboardButton(text='Фильмы', callback_data='11'),
     InlineKeyboardButton(text='Книги', callback_data='10')],
    [InlineKeyboardButton(text='Музыка', callback_data='12'),
     InlineKeyboardButton(text='Природа', callback_data='17'),
     InlineKeyboardButton(text='ИТ', callback_data='18')],
    [InlineKeyboardButton(text='История', callback_data='23'),
     InlineKeyboardButton(text='Спорт', callback_data='21'),
     InlineKeyboardButton(text='Знаменитости', callback_data='26')],
    [InlineKeyboardButton(text='Животные', callback_data='27'),
     InlineKeyboardButton(text='География', callback_data='22'),
     InlineKeyboardButton(text='Искусство', callback_data='25')]
])

reply_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Ещё!'), KeyboardButton(text='Пожалуй, хватит')]
], resize_keyboard=True)
@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer('Привет! Хочешь проверить свою эрудицию? \nВыбери тему вопроса', reply_markup=quiz_kb)

def get_question(url):
    response = requests.get(url)
    data = response.json()
    topic = data['results'][0]['category']
    question = data['results'][0]['question']
    correct_answer = data['results'][0]['correct_answer']
    incorrect_answers = data['results'][0]['incorrect_answers']
    return topic, question, correct_answer, incorrect_answers


@dp.callback_query(F.data.in_({'random', '11', '10', '12', '17', '18', '23', '21', '26', '27', '22', '25'}))
async def choose_option(callback: CallbackQuery):
    category = callback.data
    difficulty = random.choice(['easy', 'medium', 'hard'])
    if category == 'random':
        url = f"https://opentdb.com/api.php?amount=1&difficulty={difficulty}"
    else:
        url = f"https://opentdb.com/api.php?amount=1&category={category}&difficulty={difficulty}"
    topic, question, correct_answer, incorrect_answers = get_question(url)
    all_answers = incorrect_answers + [correct_answer]
    random.shuffle(all_answers)
    buttons = [
        [InlineKeyboardButton(text=answer, callback_data=f"answer:{answer}:{correct_answer}")]
        for answer in all_answers
    ]
    kb_answers = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(f'Тема:  {topic} \nСложность:  {difficulty} \nВопрос:  {question}\n\nВыбери правильный ответ:', reply_markup=kb_answers)

@dp.callback_query(F.data.startswith('answer:'))
async def check_answer(callback: CallbackQuery):
    _, selected_answer, correct_answer = callback.data.split(':')
    if selected_answer == correct_answer:
        await callback.message.edit_text('Правильно!')
    else:
        await callback.message.edit_text(f'Мимо. Правильный ответ: {correct_answer}')
    await callback.message.answer('Продолжим?', reply_markup=reply_kb)

@dp.message(F.text.in_({"Пожалуй, хватит"}))
async def reply_bye(message: Message):
    await message.answer(f"Ok, {message.from_user.first_name}, заходи еще!")

@dp.message(F.text.in_({"Ещё!"}))
async def show_categories(message: Message):
    await message.answer('Выбери тему вопроса', reply_markup=quiz_kb)
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
