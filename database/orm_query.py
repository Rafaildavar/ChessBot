from collections import defaultdict
from typing import Optional

from sqlalchemy.future import select

# from database.db import Statistic
from database.db import logger
from database.db import session_maker, User

# Словарь для отслеживания количества обновлений статистики
update_counter = defaultdict(int)


async def get_user_name(user_id: int) -> str:
    """Получить имя пользователя из базы данных."""
    async with session_maker() as session:
        try:
            result = await session.execute(select(User).filter(User.user_id == user_id))
            user = result.scalars().first()
            if user:
                return user.username  # Предполагается, что у модели User есть поле username
            else:
                return "Неизвестный пользователь"
        except Exception as e:
            # Обработка ошибок, например, если произошла ошибка подключения к базе данных
            return f"Ошибка при получении имени пользователя: {str(e)}"


async def get_user_rating(user_id: int) -> Optional[int]:
    """Получить рейтинг пользователя из базы данных."""
    async with session_maker() as session:
        result = await session.execute(select(User.rating).where(User.user_id == user_id))
        return result.scalar()


async def update_user_attributes(user_id: int,user_result:str) -> str:
    """Обновить атрибуты пользователя в базе данных по заданным условиям."""
    async with session_maker() as session:
        try:
            # Получаем пользователя из базы данных
            result = await session.execute(select(User).filter(User.user_id == user_id))
            user = result.scalars().first()

            if user:
                if update_counter[user_id] <1:
                # Увеличиваем счетчик обновлений для данного пользователя
                    update_counter[user_id] += 1
                    if 'Победа' in user_result:
                        user.wins += 1
                    elif 'Поражение' in user_result:
                        user.losses += 1
                    elif user_result == 'Ничья!':
                        user.draws += 1
                    user.total_games+=1
                    await update_user_stats(user_id, user.wins, user.losses, user.draws)
                    update_counter[user_id]+=1
                # Обновляем атрибуты пользователя на основе переданного словаря updates


                # Сохраняем изменения в базе данных
                await session.commit()
                return 'статистика обновлена'
            else:
                return "Неизвестный пользователь"
        except Exception as e:
            # Обработка ошибок, например, если произошла ошибка подключения к базе данных
            return f"Ошибка при обновлении данных пользователя: {str(e)}"
# Функция обновления win_percentage при изменении статистики игрока
async def update_user_stats(user_id, wins, losses, draws):
    try:
        # Валидация данных
        if wins < 0 or losses < 0 or draws < 0:
            raise ValueError("Количество побед, поражений и ничьих не может быть отрицательным.")

        # Обновление данных пользователя
        async with session_maker() as session:
            # stats = await session.get(Statistic, user_id)
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
