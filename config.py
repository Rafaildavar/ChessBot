import os
from aiogram import Bot
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Получаем токен бота из переменных окружения
TOKEN = os.getenv('token')

# Инициализируем бота
bot = Bot(token=TOKEN)
# Создание базового класса путем наследования от declarative_base

database_url = os.getenv('DATABASE_URL')