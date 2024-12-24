from collections import defaultdict
from typing import Optional

from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError, OperationalError
# from database.db import Statistic
from database.db import logger, Purchase, ShopItem
from database.db import session_maker, User,Statistic

# Словарь для отслеживания количества обновлений статистики
update_counter = defaultdict(int)
update_counter2 = defaultdict(int)
# Пример использования
shop_items_data = [
    {
        'name': 'Ты клоун',
        'description': '🤡',
        'price': 100,
        'item_type': 'Эмодзи'
    },
    {
        'name': 'Типо звезда',
        'description': '🤩',
        'price': 100,
        'item_type': 'Эмодзи'
    },
    {
        'name': 'Праздник',
        'description': '🥳',
        'price': 100,
        'item_type': 'Эмодзи'
    },
    {
        'name': 'Непон',
        'description': '🥸',
        'price': 100,
        'item_type': 'Эмодзи'
    },
    {
        'name': 'Рот',
        'description': '🤐',
        'price': 100,
        'item_type': 'Эмодзи'
    }
]




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


async def update_user_attributes(user_id: int,user_result:str, isprivate: bool,israng: bool) -> str:
    """Обновить атрибуты пользователя в базе данных по заданным условиям."""
    async with session_maker() as session:
        try:
            # Получаем пользователя из базы данных
            result = await session.execute(select(User).filter(User.user_id == user_id))
            user = result.scalars().first()

            if user:
                if update_counter[user_id] <1:

                    if not isprivate:
                        if not israng:
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
                        else:
                            update_counter[user_id] += 1
                            if 'Победа' in user_result:
                                user.wins += 1
                                user.rating +=1
                            elif 'Поражение' in user_result:
                                user.losses += 1
                                user.rating -= 1
                                if user.rating < 0:
                                    user.rating = 0
                            elif user_result == 'Ничья!':
                                user.draws += 1
                            user.total_games += 1
                            await update_user_stats(user_id, user.wins, user.losses, user.draws)
                            update_counter[user_id] += 1

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
async def add_diamonds_to_user(user_id: int, count : int) -> None:
    try:
        # Обновление данных пользователя
        async with session_maker() as session:
            user = await session.get(User, user_id)
            if user:
                user.diamonds+=int(count)

                await session.commit()
                await session.refresh(user)
            else:
                raise ValueError("Пользователь не найден.")
    except(IntegrityError, OperationalError) as e :
        logger.error(f"Ошибка обновления статистики пользователя {user_id}: {e}")
async def insert_shop_items(items_data):
    async with session_maker() as session:
        try:
            for item_data in items_data:
                new_item = ShopItem(
                    name=item_data['name'],
                    description=item_data['description'],
                    price=item_data['price'],
                    item_type=item_data['item_type']
                )
                session.add(new_item)
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e
# Функция обновления win_percentage при изменении статистики игрока
# async def update_user_st(user_id, wins, losses, draws):
#     try:
#
#         # Обновление данных пользователя
#         async with session_maker() as session:
#             stats = await session.get(Statistic, user_id)
#             if stats:
#                 stats.white_wins = wins
#                 stats.white_losses = losses
#                 stats.white_draws = draws
#                 stats.total_games = wins + losses + draws
#                 stats.win_percentage_white = (wins / stats.total_games * 100) if stats.total_games > 0 else 0
#
#                 await session.commit()
#                 await session.refresh(stats)
#             else:
#                 raise ValueError("Пользователь не найден.")
#     except Exception as e:
#         logger.error(f"Ошибка обновления статистики пользователя {user_id}: {e}")
# async def update_user_statistic(user_id: int,user_result:str) -> str:
#     """Обновить атрибуты пользователя в базе данных по заданным условиям."""
#     async with session_maker() as session:
#         try:
#             # Получаем пользователя из базы данных
#             result = await session.execute(select(Statistic).filter(Statistic.user_id == user_id))
#             user = result.scalars().first()
#
#             if user:
#                 if update_counter2[user_id] <1:
#                     # Увеличиваем счетчик обновлений для данного пользователя
#                         update_counter2[user_id] += 1
#                         if 'Победа' in user_result:
#                             user.white_wins += 1
#                         elif 'Поражение' in user_result:
#                             user.white_losses += 1
#                         elif user_result == 'Ничья!':
#                             user.white_draws += 1
#                         user.total_games+=1
#                         await update_user_st(user_id, user.white_wins, user.white_losses, user.white_draws)
#                         update_counter[user_id]+=1
#             # Обновляем атрибуты пользователя на основе переданного словаря updates
#
#                     # Сохраняем изменения в базе данных
#                         await session.commit()
#                 return 'статистика обновлена'
#             else:
#                 return "Неизвестный пользователь"
#         except Exception as e:
#             # Обработка ошибок, например, если произошла ошибка подключения к базе данных
#             return f"Ошибка при обновлении данных пользователя: {str(e)}"

async def get_item_id(user_id: int) -> str:
    """Получить имя пользователя из базы данных."""
    async with session_maker() as session:
        try:
            result = await session.execute(select(User).filter(User.user_id == user_id))
            user = result.scalars().first()
            result2 = await session.execute(
                select(Purchase).filter(
                    Purchase.user_id == user.user_id,
                    Purchase.item_id == user.item_id  # Добавляем фильтр по item_id
                )
            )

            user2 = result2.scalars().first()
            if user:
                return user2.description  # Предполагается, что у модели User есть поле username
            else:
                return ""
        except Exception as e:
            # Обработка ошибок, например, если произошла ошибка подключения к базе данных
            return f"Ошибка при получении имени пользователя: {str(e)}"


# Функция обновления win_percentage при изменении статистики игрока
async def update_user_name(user_id: int,username:str):
    try:

        # Обновление данных пользователя
        async with session_maker() as session:

            user = await session.get(User, user_id)
            if user:
                user.username = username
                await session.commit()
                await session.refresh(user)
            else:
                raise ValueError("Пользователь не найден.")
    except Exception as e:
        logger.error(f"Ошибка обновления статистики пользователя {user_id}: {e}")