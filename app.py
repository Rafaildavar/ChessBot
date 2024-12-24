import asyncio
import logging
from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import bot

from handlers.callback_handlers import callback_router
from handlers.message_handlers import message_router
from handlers.pre_checkout_query import checkout_router

storage = MemoryStorage()
dp = Dispatcher(storage=storage)


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("bot_errors.log"),  # Логи записываются в файл
        logging.StreamHandler()  # Логи выводятся в консоль
    ]
)
dp.include_router(callback_router)
dp.include_router(message_router)
dp.include_router(checkout_router)



# Запуск бота
async def main():
    print('Бот запущен')
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот завершил работу")

