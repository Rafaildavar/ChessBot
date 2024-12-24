import logging
from datetime import datetime

from sqlalchemy import Integer, BigInteger, String, Text, DECIMAL, DateTime, ForeignKey
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy.sql import func

from config import database_url

Base = declarative_base()
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
    rating: Mapped[int] = mapped_column(Integer, default=0)
    rang: Mapped[int] = mapped_column(Integer, default=0)
    diamonds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    item_id: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # Связь с таблицей статистики
    statistics: Mapped['Statistic'] = relationship("Statistic", back_populates="user", uselist=False)


# Модель для таблицы отзывов
class Feedback(Base):
    __tablename__ = 'feedback'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    feedback: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


# Модель для таблицы пользователей
# Модель для таблицы статистики
class Statistic(Base):
    __tablename__ = 'statistic'

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.user_id'), primary_key=True)
    username: Mapped[str | None] = mapped_column(String(255))

    white_wins: Mapped[int] = mapped_column(Integer, default=0)
    white_losses: Mapped[int] = mapped_column(Integer, default=0)
    white_draws: Mapped[int] = mapped_column(Integer, default=0)

    total_games: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False,
        server_default="0"
    )

    win_percentage_white: Mapped[float] = mapped_column(
        DECIMAL(5, 2), nullable=False, server_default="0.00"
    )

    # Связь с пользователем
    user: Mapped[User] = relationship("User", back_populates="statistics")

    def __init__(self, user_id: int, username: str | None):
        self.user_id = user_id
        self.username = username


# Модель для таблицы товаров
class ShopItem(Base):
    __tablename__ = 'shop_items'

    item_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    item_type: Mapped[str] = mapped_column(String(50), nullable=False)

class Purchase(Base):
    __tablename__ = 'purchases'

    purchase_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    item_id: Mapped[int] = mapped_column(Integer, ForeignKey('shop_items.item_id'), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

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

