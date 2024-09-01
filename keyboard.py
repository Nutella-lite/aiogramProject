"""
Задание 1: Создание простого меню с кнопками
При отправке команды /start бот будет показывать меню с кнопками "Привет" и "Пока".
При нажатии на кнопку "Привет" бот должен отвечать "Привет, {имя пользователя}!",
а при нажатии на кнопку "Пока" бот должен отвечать "До свидания, {имя пользователя}!".

Задание 2: Кнопки с URL-ссылками
При отправке команды /links бот будет показывать инлайн-кнопки с URL-ссылками.
Создайте три кнопки с ссылками на новости/музыку/видео

Задание 3: Динамическое изменение клавиатуры
При отправке команды /dynamic бот будет показывать инлайн-кнопку "Показать больше".
При нажатии на эту кнопку бот должен заменять её на две новые кнопки "Опция 1" и "Опция 2".
При нажатии на любую из этих кнопок бот должен отправлять сообщение с текстом выбранной опции.
"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

reply_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Привет'), KeyboardButton(text='Пока')]
],resize_keyboard=True)

inline_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Новости', url='https://www.rbc.ru/'),
    InlineKeyboardButton(text='Музыка', url='https://radiopotok.ru/radio/542'),
    InlineKeyboardButton(text='Видео', url='https://www.youtube.com/playlist?list=PLAB20788A0621F97E')]
])

inline_kb2 = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Показать больше', callback_data='show_more')]
])

options = ['Опция 1', 'Опция 2', 'Опция 3', 'Опция 4']
async def options_kb():
    kb = InlineKeyboardBuilder()
    for option in options:
        kb.add(InlineKeyboardButton(text=option, callback_data=option))
    return kb.adjust(2).as_markup()
