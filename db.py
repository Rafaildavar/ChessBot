from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv
import os

from sqlalchemy import Column, Integer, BigInteger, String, Text, DECIMAL, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import ForeignKey
from datetime import datetime
import logging



# Создание базового класса путем наследования от declarative_base
Base = declarative_base()
load_dotenv()
database_url = os.getenv('DATABASE_URL')
# Создание асинхронного движка для подключения к базе данных
engine = create_async_engine(database_url, echo=True)

# Создание асинхронной сессии
session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

logger = logging.getLogger(__name__)


# Модель для таблицы пользователей
class User(Base):
    __tablename__ = 'users'

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str | None] = mapped_column(String(255))
    telegram_name: Mapped[str | None] = mapped_column(String(255))
    wins: Mapped[int] = mapped_column(Integer, default=0)
    losses: Mapped[int] = mapped_column(Integer, default=0)
    draws: Mapped[int] = mapped_column(Integer, default=0)
    total_games: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False,
        server_default="0"
    )
    win_percentage: Mapped[float] = mapped_column(
        DECIMAL(5, 2), nullable=False, server_default="0.00"
    )
    diamonds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

# Функция обновления win_percentage при изменении статистики игрока
async def update_user_stats(user_id, wins, losses, draws):
    try:
        # Валидация данных
        if wins < 0 or losses < 0 or draws < 0:
            raise ValueError("Количество побед, поражений и ничьих не может быть отрицательным.")

        # Обновление данных пользователя
        async with session_maker() as session:
            user = await session.get(User, user_id)
            if user:
                user.wins = wins
                user.losses = losses
                user.draws = draws
                user.total_games = wins + losses + draws
                user.win_percentage = (wins / user.total_games * 100) if user.total_games > 0 else 0
                await session.commit()
                await session.refresh(user)
            else:
                raise ValueError("Пользователь не найден.")
    except Exception as e:
        logger.error(f"Ошибка обновления статистики пользователя {user_id}: {e}")

# Модель для таблицы отзывов
class Feedback(Base):
    __tablename__ = 'feedback'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    feedback: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

# Модель для таблицы товаров
class ShopItem(Base):
    __tablename__ = 'shop_items'

    item_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    item_type: Mapped[str] = mapped_column(String(50), nullable=False)

# Модель для таблицы покупок
class Purchase(Base):
    __tablename__ = 'purchases'

    purchase_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    item_id: Mapped[int] = mapped_column(Integer, ForeignKey('shop_items.item_id'), nullable=False)
    purchase_date: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

# Модель для таблицы кланов
class Clan(Base):
    __tablename__ = 'clans'

    clan_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    leader_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


# Модель для таблицы участников кланов
class ClanMember(Base):
    __tablename__ = 'clan_members'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    clan_id: Mapped[int] = mapped_column(Integer, ForeignKey('clans.clan_id'), nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    join_date: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
