import aiomysql
import asyncio

# Параметры подключения к базе данных
DB_HOST = '*****'  # адрес вашего хостинга
DB_PORT = ***** # порт по умолчанию 3306
DB_USER = '*****'  # имя пользователя
DB_PASSWORD = '*****'  # введите свой пароль
DB_NAME = 'chess_bot_db'  # название базы данных


# Функция для инициализации базы данных и таблиц
async def init_db():
    # Подключаемся к MySQL (для создания базы данных)
    async with aiomysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
    ) as conn:

        async with conn.cursor() as cursor:
            # Создаем базу данных, если её ещё нет
            await cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
            # Используем базу данных
            await cursor.execute(f"USE {DB_NAME}")

            # Создаем таблицу пользователей
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    username VARCHAR(255),
                    telegram_name VARCHAR(255),
                    wins INT DEFAULT 0,
                    losses INT DEFAULT 0,
                    draws INT DEFAULT 0,
                    total_games INT GENERATED ALWAYS AS (wins + losses + draws) VIRTUAL,
                    win_percentage DECIMAL(5, 2) GENERATED ALWAYS AS (wins / NULLIF(total_games, 0) * 100) VIRTUAL
                )
            """)

            # Создаем таблицу для сохранения игр
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS games (
                    game_id INT AUTO_INCREMENT PRIMARY KEY,
                    user1_id BIGINT,
                    user2_id BIGINT,
                    winner_id BIGINT,
                    game_type VARCHAR(255),  # Тип игры (например, "с другом", "с ботом")
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Создаем таблицу для хранения приглашений и участников игры
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS invites (
                    invite_id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id BIGINT,  -- ID пользователя, который создал приглашение
                    accepted_user_id BIGINT,  -- ID пользователя, который принял приглашение
                    invite_code VARCHAR(255),  -- Уникальный код приглашения
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP  -- Время создания приглашения
                )
            """)

            # Создаем таблицу для товаров магазина
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    product_id INT AUTO_INCREMENT PRIMARY KEY,  -- Уникальный идентификатор товара
                    product_name VARCHAR(255) NOT NULL,          -- Название товара
                    category VARCHAR(100),                       -- Категория товара, например, "шахматы"
                    price DECIMAL(10, 2) NOT NULL,               -- Стоимость товара, например, 15.99
                    description TEXT,                            -- Описание товара
                    stock INT DEFAULT 0,                         -- Количество доступного товара
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP  -- Дата и время добавления товара
                )
            """)

            # Создаем таблицу для отзывов пользователей
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id INT AUTO_INCREMENT PRIMARY KEY,  -- Уникальный идентификатор отзыва
                    user_id BIGINT,                     -- Идентификатор пользователя, оставившего отзыв
                    feedback TEXT,                      -- Текст отзыва или обратной связи
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP  -- Дата и время создания отзыва
                )
            """)


# Запуск функции инициализации базы данных
async def run_init():
    await init_db()


# Запускаем инициализацию
asyncio.run(run_init())

