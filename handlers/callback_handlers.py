import asyncio
import logging
import datetime

from aiogram import F
from aiogram import Router, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice
from chess import Piece
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select

from database.orm_query import add_diamonds_to_user
from market.market import buy_options,PAYMENTS_PROVIDER_TOKEN
from config import bot
from database.db import User, ClanMember, Clan, ShopItem, Purchase, Statistic
from database.db import session_maker
from gameLogic.game import Lobby
from kbds.State import FeedbackState, ProfileState, ClanState, PublicState,PrivateState
from kbds.inline import clan_actions, stat_keyboard, main_menu_keyboard, keyboards, event_board, claim_gift_board, \
    menu_button, leaders_keyboard
from utils.game_relation import get_game, board_update, send_board, games, lobbies

callback_router = Router()
# Глобальная переменная для хранения текущего item_id
current_item_id = 0



#Обработчик нажатия "Мой профиль"
@callback_router.callback_query(F.data == 'profile')
async def profile(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    async with session_maker() as session:  # Используем асинхронную сессию
        try:
            # Использование SQLAlchemy для получения пользователя
            result = await session.execute(select(User).filter(User.user_id == user_id))
            user = result.scalars().first()  # Получаем пользователя

            if user.username !='new':
                await callback_query.message.answer(
                    f"Ваш профиль:\n"
                    f"Имя пользователя: {user.username}\n"
                    f"Количество побед: {user.wins} 🏆\n"
                    f"Количество поражений: {user.losses} 😔\n"
                    f"Количество ничьих: {user.draws} ☯️\n"
                    f"Количество проведенных партий: {user.total_games} 🎮\n"
                    f"Процент побед: {user.win_percentage}% 🎯\n"
                    f"Баланс: {user.diamonds} 💎\n"
                    f"Рейтинг: {user.rating}🎖\n"
                    f"Место в ТОПе по рейтингу: {user.rang}👑\n"
                )
            else:
                # Если профиля нет, предлагаем его создать
                await callback_query.message.answer(
                    "Похоже, у вас еще нет профиля. Давайте создадим его!\nВведите ваш username:"
                )
                await state.set_state(ProfileState.waiting_for_username)
        except Exception as e:
            await callback_query.message.answer(f"Произошла ошибка: {str(e)}")

# @callback_router.callback_query(F.data == 'white')
# async def white_stat(callback_query: types.CallbackQuery):
#     user_id = callback_query.from_user.id
#     async with session_maker() as session:  # Используем асинхронную сессию
#         try:
#             # Использование SQLAlchemy для получения статистики
#             result = await session.execute(select(Statistic).filter(Statistic.user_id == user_id))
#             user_stats = result.scalars().first()  # Получаем статистику пользователя
#
#             # Получаем информацию о пользователе
#             result2 = await session.execute(select(User).filter(User.user_id == user_id))
#             user_info = result2.scalars().first()
#
#             if user_stats and user_info:
#                 await callback_query.message.answer(
#                     f"Ваша статистика игры за белых:\n"
#                     f"Количество побед: {user_stats.white_wins} 🏆\n"
#                     f"Количество поражений: {user_stats.white_losses} 😔\n"
#                     f"Количество ничьих: {user_stats.white_draws} ☯️\n"
#                     f"Количество проведенных партий: {user_info.total_games / 2} 🎮\n"
#                     f"Процент побед: {user_stats.win_percentage_white}% 🎯\n"
#                 )
#             else:
#                 # Если профиля нет, предлагаем его создать
#                 await callback_query.message.answer(
#                     "Похоже, у вас еще нет профиля."
#                 )
#         except Exception as e:
#             await callback_query.message.answer(f"Произошла ошибка: {str(e)}")


# @callback_router.callback_query(F.data == 'black')
# async def black_stat(callback_query: types.CallbackQuery, state: FSMContext):
#     user_id = callback_query.from_user.id
#     async with session_maker() as session:
#         try:
#             # Получаем данные о пользователе
#             result = await session.execute(select(Statistic).filter(Statistic.user_id == user_id))
#             user_stats = result.scalars().first()
#             result2 = await session.execute(select(User).filter(User.user_id == user_id))
#             user_info = result2.scalars().first()
#
#             if user_stats and user_info:
#                 # Вычисляем статистику за черных
#                 black_wins = user_stats.white_losses  # Поражения за белых равны победам за черных
#                 black_losses = user_stats.white_wins   # Победы за белых равны поражениям за черных
#                 total_games_black = user_info.total_games / 2  # Общее количество игр делим на 2
#                 black_draws = total_games_black - black_losses - black_wins
#
#                 # Процент побед за черных
#                 win_percentage_black = (
#                     (black_wins / total_games_black * 100) if total_games_black > 0 else 0
#                 )
#
#                 await callback_query.message.answer(
#                     f"Ваша статистика игры за черных:\n"
#                     f"Количество побед: {black_wins} 🏆\n"
#                     f"Количество поражений: {black_losses} 😔\n"
#                     f"Количество ничьих: {black_draws} ☯️\n"
#                     f"Количество проведенных партий: {total_games_black} 🎮\n"
#                     f"Процент побед: {win_percentage_black:.2f}% 🎯\n"
#                 )
#             else:
#                 await callback_query.message.answer("Похоже, у вас еще нет профиля.")
#         except Exception as e:
#             await callback_query.message.answer(f"Произошла ошибка: {str(e)}")

#Обработчик callback_query для кнопки Оставить отзыв
@callback_router.callback_query(F.data == 'feedback')
async def handle_feedback(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.answer("Пожалуйста, оставьте свой отзыв:")
    await state.set_state(FeedbackState.waiting_for_feedback)


# Обработчик кнопки "Кланы"
@callback_router.callback_query(F.data == "clan")
async def handle_clan_button(callback: types.CallbackQuery):
    await callback.message.answer("Выберите действие:", reply_markup=clan_actions)


# Обработчик создания клана
@callback_router.callback_query(F.data == "create_clan")
async def process_create_clan(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id

    async with session_maker() as session:
        try:
            # Использование SQLAlchemy для получения пользователя
            result = await session.execute(select(User).filter(User.user_id == user_id))
            user = result.scalars().first()  # Получаем пользователя

            if not user:
                await callback.message.answer("Пользователь не найден в базе данных.")
                return
            result2 = await session.execute(select(ClanMember).filter(ClanMember.user_id==user_id))
            clan_m = result2.scalars().first()
            if clan_m:
                await callback.message.answer(
                     'Невозможно создать клан пока вы состоите в клане, сначала покиньте клан'
                )
                return


            if user.diamonds < 200:
                await callback.message.answer(
                    "Недостаточно средств для создания клана. Требуется 200 алмазов. \n"
                    "Пополнить алмазы можно на вкладке Мой баланс"
                )
                return

            # Подтверждение оплаты
            await callback.message.answer(
                "Создание клана стоит 200 алмазиков. Подтвердите оплату, чтобы продолжить.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="Подтвердить", callback_data="confirm_payment")],
                        [InlineKeyboardButton(text="Отмена", callback_data="cancel_payment")]
                    ]
                )
            )
        except SQLAlchemyError as e:
            logging.error(f"Database error: {e}")
            await callback.message.answer("Произошла ошибка при обработке запроса.")

    await state.clear()


#Обработчик оплаты создания клана
@callback_router.callback_query(F.data == "confirm_payment")
async def confirm_payment(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id

    async with session_maker() as session:
        try:
            # Получение пользователя из БД
            user = await session.scalar(select(User).where(User.user_id == user_id))

            if not user:
                await callback_query.message.answer("Пользователь не найден в базе данных.")
                return

            if user.diamonds < 200:
                await callback_query.message.answer("Недостаточно средств для создания клана.")
                return

            # Списание средств
            user.diamonds -= 200
            await session.commit()

            await callback_query.message.answer(
                "Оплата успешна. Теперь введите название для вашего клана:"
            )

            # Переход к логике создания клана — устанавливаем состояние
            await state.set_state(ClanState.enter_name)

        except SQLAlchemyError as e:
            logging.error(f"Database error: {e}")
            await callback_query.message.answer("Произошла ошибка при обработке запроса.")


@callback_router.message(ClanState.enter_name)
async def process_clan_name(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    clan_name = message.text

    async with session_maker() as session:
        try:
            # Проверяем уникальность имени клана
            result = await session.execute(select(Clan).where(Clan.name == clan_name))
            if result.scalars().first():
                await message.answer("Клан с таким названием уже существует. Попробуйте другое.")
                return

            # Создаем новый клан
            new_clan = Clan(name=clan_name, leader_id=user_id)
            session.add(new_clan)
            await session.flush()  # Применить изменения, чтобы получить id нового клана

            # Получаем id нового клана
            clan_id = new_clan.clan_id

            # Добавляем пользователя в члены клана
            new_member = ClanMember(clan_id=clan_id, user_id=user_id)
            session.add(new_member)
            await session.commit()

            await message.answer(f"Клан '{clan_name}' успешно создан!")
        except Exception as e:
            await message.answer(f"Произошла ошибка при создании клана: {str(e)}")

    await state.clear()



#Обработчик отмены создания клана
@callback_router.callback_query(F.data == "cancel_payment")
async def cancel_payment(callback_query: types.CallbackQuery):
    await callback_query.message.answer("Создание клана отменено.")


#Обработчик присоединения в клан
@callback_router.callback_query(F.data == "join_clan")
async def process_list_clans(callback: types.CallbackQuery):
    user_id = callback.from_user.id  # ID пользователя

    async with session_maker() as session:
        try:
            # Проверяем, состоит ли пользователь уже в каком-либо клане
            existing_member = await session.execute(
                select(ClanMember).filter(ClanMember.user_id == user_id)
            )
            if existing_member.scalars().first():
                await callback.message.answer("Вы уже состоите в клане. Сначала покиньте текущий клан, чтобы вступить в другой.")
                return

            # Получаем список доступных кланов
            result = await session.execute(select(Clan))
            clans = result.scalars().all()

            if not clans:
                await callback.message.answer("Нет доступных кланов для вступления.")
                return

            # Создаем клавиатуру с доступными кланами
            clan_buttons = [
                [InlineKeyboardButton(text=clan.name, callback_data=f"join_{clan.clan_id}")]
                for clan in clans
            ]
            clan_list_kb = InlineKeyboardMarkup(inline_keyboard=clan_buttons)

            await callback.message.answer("Выберите клан для вступления:", reply_markup=clan_list_kb)
        except Exception as e:
            await callback.message.answer(f"Произошла ошибка: {str(e)}")
# присоединение в клан
@callback_router.callback_query(F.data.startswith("join_"))
async def join_clan(callback: types.CallbackQuery):
    clan_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id

    async with session_maker() as session:
        try:
            logging.info(f"User {user_id} attempting to join clan {clan_id}")

            # Проверяем, существует ли клан
            clan_result = await session.execute(
                select(Clan).where(Clan.clan_id == clan_id)
            )
            clan = clan_result.scalars().first()
            if not clan:
                await callback.message.answer("Клан не найден.")
                return

            # Добавляем пользователя в клан
            new_member = ClanMember(clan_id=clan_id, user_id=user_id)
            session.add(new_member)
            await session.commit()

            await callback.message.answer(f"Вы успешно вступили в клан '{clan.name}'!")
        except Exception as e:
            logging.exception(f"Error: {e}")
            await callback.message.answer(f"Произошла ошибка: {str(e)}")


#Обработчик управлением кланами
@callback_router.callback_query(F.data == 'manage_clan')
async def manage_clan(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    async with session_maker() as session:
        try:
            # Проверяем, существует ли клан
            clan_result = await session.execute(
                select(ClanMember).where(ClanMember.user_id == user_id)
            )
            clan = clan_result.scalars().first()

            if not clan:
                await callback.message.answer("Клан не найден.")
                return
            cur_clan_id = clan.clan_id
            clan_info = await session.execute(
                select(Clan).where(Clan.clan_id == cur_clan_id)
            )
            clan_obj = clan_info.scalars().first()
            leader_id = clan_obj.leader_id

            # Получаем всех членов клана
            members_result = await session.execute(
                select(User)
                .join(ClanMember, User.user_id == ClanMember.user_id)
                .filter(ClanMember.clan_id == cur_clan_id)
            )
            members = members_result.scalars().all()

            # Формируем список участников клана
            member_list = []
            for member in members:

                text = f"{member.username} - рейтинг{member.rating}🎖️ {'(Лидер)' if member.user_id == leader_id else ''}"
                member_list.append(text)
            # Отправляем сообщение с участниками клана
            await callback.message.answer(
                f"Участники клана: {clan_obj.name}\n\n{chr(10).join(member_list)}",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[[
                        InlineKeyboardButton(text=f"Назад", callback_data="back_to_main_menu")
                    ]]
                ),
                parse_mode='HTML'
            )

        except SQLAlchemyError as e:
            logging.error(f"Database error: {e}")
            await callback.message.answer("Произошла ошибка при получении информации о клане.")

# Обработчик кнопки "Кланы"
@callback_router.callback_query(F.data == "leadersTable")
async def handle_leaderstable_button(callback: types.CallbackQuery):
    await callback.message.answer("Выберите действие:", reply_markup=leaders_keyboard)


# Обработчик нажатия "Топ 100 игроков"
@callback_router.callback_query(F.data == 'top100')
async def handle_top100(callback_query: types.CallbackQuery):
    try:
        async with session_maker() as session:
            result = await session.execute(select(User).order_by(User.win_percentage.desc()).limit(100))
            top_users = result.scalars().all()
            global current_item_id
            if top_users:
                response = "🏆 Топ 100 игроков по соотношению побед:\n"
                for i, user in enumerate(top_users, start=1):
                    result2 = await session.execute(
                        select(Purchase).filter(
                            Purchase.user_id == user.user_id,
                            Purchase.item_id == user.item_id  # Добавляем фильтр по item_id
                        )
                    )

                    user2 = result2.scalars().first()
                    if user2 and (user2.item_id > 0):
                        response += f"{i}. {user.username}{user2.description} - {user.win_percentage}% побед\n"
                    else:
                        response += f"{i}. {user.username} - {user.win_percentage}% побед\n"
            else:
                response = "Пока нет данных для отображения Топ 100."

        await callback_query.message.answer(response)
    except Exception as e:
        await callback_query.message.answer(f"Произошла ошибка при получении Топ 100: {str(e)}")

# Обработчик нажатия "Топ 100 игроков"
@callback_router.callback_query(F.data == 'top100rang')
async def handle_top100rang(callback_query: types.CallbackQuery):
    try:
        async with session_maker() as session:
            result = await session.execute(select(User).order_by(User.rating.desc()).limit(100))
            top_users = result.scalars().all()

            if top_users:
                response = "🏆 Топ 100 игроков по рейтингу:\n"
                for i, user in enumerate(top_users, start=1):
                    result2 = await session.execute(
                        select(Purchase).filter(
                            Purchase.user_id == user.user_id,
                            Purchase.item_id == user.item_id  # Добавляем фильтр по item_id
                        )
                    )

                    user2 = result2.scalars().first()
                    if user2 and (user2.item_id > 0):
                        response += f"{i}. {user.username}{user2.description} - {user.rating}🎖️\n"
                    else:
                        response += f"{i}. {user.username} - {user.rating}🎖️\n"
            else:
                response = "Пока нет данных для отображения Топ 100."

        await callback_query.message.answer(response)
    except Exception as e:
        await callback_query.message.answer(f"Произошла ошибка при получении Топ 100: {str(e)}")


# Обработчик нажатия "Топ 100 кланов"
@callback_router.callback_query(F.data == 'top100clans')
async def handle_top100clans(callback_query: types.CallbackQuery):
    try:
        async with session_maker() as session:
            # Запрос для получения топ 100 кланов по сумме рейтинга участников
            result = await session.execute(
                select(Clan)
                .join(ClanMember, Clan.clan_id == ClanMember.clan_id)
                .join(User, ClanMember.user_id == User.user_id)  # Предполагается, что у вас есть модель User
                .group_by(Clan.clan_id)
                .order_by(func.sum(User.rating).desc())
                .limit(100)
            )
            top_clans = result.scalars().all()

            if top_clans:
                response = "🏆 Топ 100 кланов:\n"
                for i, clan in enumerate(top_clans, start=1):
                    # Получаем сумму рейтинга участников клана
                    total_rating = await session.execute(
                        select(func.sum(User.rating))
                        .join(ClanMember, ClanMember.user_id == User.user_id)
                        .where(ClanMember.clan_id == clan.clan_id)
                    )
                    total_rating_value = total_rating.scalar() or 0  # Если нет участников, сумма будет 0
                    response += f"{i}. {clan.name} -  {total_rating_value}🎖️\n"
            else:
                response = "Пока нет данных для отображения Топ 100."

        await callback_query.message.answer(response)
    except Exception as e:
        await callback_query.message.answer(f"Произошла ошибка при получении Топ 100 кланов: {str(e)}")



# Обработчик кнопки "Магазин"
@callback_router.callback_query(F.data == 'shop')
async def handle_shop(callback_query: types.CallbackQuery):
    try:
        async with session_maker() as session:
            # Запрос для получения всех товаров
            result = await session.execute(select(ShopItem))
            items = result.scalars().all()  # Получаем все товары

            if items:
                # Если товары есть, формируем список и отправляем
                response = "🛍️ Список товаров:\n"

                # Формируем клавиатуру с кнопками
                keyboard = InlineKeyboardMarkup(inline_keyboard=[], row_width=1)

                for item in items:
                    response += f"🛒 {item.name}\nОписание: {item.description}\nЦена: {item.price} 💎\n\n"

                    # Создаем кнопку для покупки товара
                    buy_button = InlineKeyboardButton(
                        text=f"💵Купить товар {item.name} {item.description}",
                        callback_data=f"buy_{item.item_id}"
                    )

                    # Добавляем кнопку в клавиатуру
                    keyboard.inline_keyboard.append([buy_button])
                    f =[InlineKeyboardButton(text="Назад", callback_data="back_to_main_menu")]
                keyboard.inline_keyboard.append(f)
                # Отправляем сообщение с кнопками
                await callback_query.message.answer(response, reply_markup=keyboard)
            else:
                # Если товаров нет, сообщаем об этом
                response = "Список товаров пуст."
                await callback_query.message.answer(response)

    except Exception as e:
        await callback_query.message.answer(f"Произошла ошибка при получении товаров: {str(e)}")


# Обработчик нажатия кнопки "Купить"
@callback_router.callback_query(F.data.startswith('buy_'))
async def handle_buy(callback_query: types.CallbackQuery):
    try:
        item_id = int(callback_query.data.split('_')[1])
        user_id = callback_query.from_user.id  # Получаем ID пользователя

        async with session_maker() as session:
            # Получаем товар и пользователя по ID
            item = await session.get(ShopItem, item_id)
            user = await session.get(User, user_id)

            if not item:
                await callback_query.message.answer("Товар не найден.")
                return

            if not user:
                await callback_query.message.answer("Пользователь не найден.")
                return

            # Проверяем, достаточно ли средств на балансе
            if user.diamonds < item.price:
                await callback_query.message.answer(f"У вас недостаточно 💎 для покупки {item.name}.")
                return

            # Проверяем, была ли уже покупка этого товара пользователем
            existing_purchase = await session.execute(
                select(Purchase).where(Purchase.user_id == user_id, Purchase.item_id == item_id)
            )
            if existing_purchase.scalars().first():
                await callback_query.message.answer(f"Вы уже купили {item.name} {item.description}")
                return

            # Если средств хватает и товар еще не куплен, обновляем баланс
            user.diamonds -= item.price

            # Добавляем запись в таблицу покупок
            new_purchase = Purchase(user_id=user_id, item_id=item_id, name=item.name, description=item.description)
            session.add(new_purchase)

            # Сохраняем изменения
            await session.commit()

            # Отправляем сообщение о покупке
            await callback_query.message.answer(f"Вы купили {item.name} {item.description} за {item.price} 💎!")

    except Exception as e:
        await callback_query.message.answer(f"Произошла ошибка при обработке покупки: {str(e)}")





# Обработчик кнопки "Покупки"
@callback_router.callback_query(F.data == 'setting')
async def handle_purchases(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    try:
        async with session_maker() as session:
            # Запрос для получения всех покупок, принадлежащих пользователю
            result = await session.execute(
                select(Purchase).where(Purchase.user_id == user_id)
            )
            purchases = result.scalars().all()

            if purchases:
                # Если покупки есть, формируем список и отправляем
                response = "🛒 Ваши покупки:\n Нажмите на кнопку, чтобы установить скин"

                # Используем множество для хранения уникальных покупок
                unique_purchases = {}

                for purchase in purchases:
                    # Проверяем, если название уже есть в словаре
                    if purchase.name not in unique_purchases:
                        unique_purchases[purchase.name] = purchase.description

                    # Формируем клавиатуру с кнопками
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[], row_width=1)

                    # Добавляем кнопки для каждой уникальной покупки
                    for name, description in unique_purchases.items():
                        button = InlineKeyboardButton(
                            text=f'{name}{description}',
                            callback_data=f"purchase_{name}"  # Замените на нужный вам callback_data
                        )
                        keyboard.inline_keyboard.append([button])
                    back_button = [InlineKeyboardButton(
                        text="Перейти в магазин",
                        callback_data="shop"
                    )]
                    keyboard.inline_keyboard.append(back_button)

                # # Формируем ответ на основе уникальных покупок
                # for name, description in unique_purchases.items():
                #     response += f"📦 {name}\nОписание: {description}\n"

                # Отправляем сообщение с покупками и кнопками
                await callback_query.message.answer(response, reply_markup=keyboard)
            else:
                # Если покупок нет
                await callback_query.message.answer("У вас еще нет покупок.")

    except Exception as e:
        await callback_query.message.answer(f"Произошла ошибка при получении покупок: {str(e)}")

# Обработчик нажатий на кнопки с покупками
@callback_router.callback_query(F.data.startswith('purchase_'))
async def handle_item_selection(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    item_name = (callback_query.data.split('_')[1])  # Извлекаем item_id из callback_data
    async with session_maker() as session:
        try:
            result = await session.execute(select(User).filter(User.user_id == user_id))
            user = result.scalars().first()
            result2 = await session.execute(select(Purchase).filter(Purchase.user_id == user_id, Purchase.name == item_name))
            user2 = result2.scalars().first()

            if user2:
                user.item_id = user2.item_id  # Предполагается, что у модели User есть поле username
                await session.commit()
                await session.refresh(user)
                await callback_query.message.answer(f"Скин - {user2.name}{user2.description} установлен")
            else:
                return


        except Exception as e:
            # Обработка ошибок, например, если произошла ошибка подключения к базе данных
            return f"Ошибка при получении имени пользователя: {str(e)}"






# @callback_router.callback_query(ProfileState.waiting_for_username)
# async def callback_handler(callback_query: types.CallbackQuery):
#     data = callback_query.data.split(':')
#     user_id: int = callback_query.from_user.id
#     game_id = int(data[0])
#     cell_id = data[1]
#
#     game = await get_game(callback_query, game_id)
#     if game is None:
#         return
#
#     if cell_id in ('4', '3', '5', '2'):
#         last_move = game.board.pop()
#         last_move.promotion = int(cell_id)
#         game.board.push(last_move)
#
#         async with asyncio.TaskGroup() as tg:
#             tg.create_task(bot.delete_message(user_id, callback_query.message.message_id))
#             tg.create_task(board_update(game))
#
#         game.choosing_shape = -1
#         return
#
#     if game.choosing_shape != -1:
#         await callback_query.answer()
#         return
#
#     mess, update_board = game.click(cell_id, user_id)
#     outcome_message = await game.get_outcome_message()
#     if outcome_message is not None:
#         await board_update(game, True)
#         games.remove(game)
#         return
#
#     if mess is not None:
#         if mess == 'Превращение':
#             await bot.send_message(chat_id=user_id,
#                                    text='Выберите фигуру:',
#                                    reply_markup=InlineKeyboardMarkup(
#                                        inline_keyboard=[
#                                            [InlineKeyboardButton(
#                                                text=Piece(i, game.board.turn).unicode_symbol(invert_color=True),
#                                                callback_data=f'{game_id}:{i}')
#                                                for i in (4, 3, 5, 2)]]))
#         else:
#             await callback_query.answer(text=mess)
#     if update_board:
#         try:
#             await board_update(game)  # Убедитесь, что это асинхронно
#         except TelegramBadRequest:
#             print('ой')
#             await callback_query.answer()


@callback_router.callback_query(F.data == 'public_game')
async def public_game(callback_query: types.CallbackQuery,state: FSMContext):

    user_id: int = callback_query.from_user.id
    await callback_query.answer()
    current_state = await state.get_state()
    if current_state == PublicState.waiting_for_pub:
        await bot.send_message(user_id, "Вы уже находитесь в процессе поиска противника.")
        return

    lobby: Lobby = next(filter(lambda s_lobby: not s_lobby.private and
                                               not s_lobby.rank and
                                               s_lobby.first_player != user_id,
                               lobbies), None)
    if lobby is None:
        lobbies.append(Lobby(user_id))
        await state.set_state(PublicState.waiting_for_pub)
        await bot.send_message(user_id, 'Ищем для вас противника.')
        return
    else:

        game = lobby.start_game(user_id)
        lobbies.remove(lobby)
        games.append(game)
        await send_board(game)
        await state.clear()

# Обработчик игры с другом
@callback_router.callback_query(F.data == 'friendGame')
async def friend_game(callback_query: types.CallbackQuery):
    user_id: int = callback_query.from_user.id
    await callback_query.answer()

    lobby: Lobby = Lobby(user_id, private=True)
    lobbies.append(lobby)

    # Сообщение с кодом для подключения друга
    await bot.send_message(user_id,
                           f"Код для приглашения друга: {lobby.private_code}. Передайте его другу для подключения.")





#
# # Обработчик игры с другом
# @callback_router.callback_query(F.data == 'friendGame')
# async def friend_game(callback_query: types.CallbackQuery):
#     await callback_query.message.answer("Выберите :", reply_markup=private_board)
#     # await callback_query.answer()


# # Обработчик игры с другом
# @callback_router.callback_query(F.data == 'get')
# async def get_code(callback_query: types.CallbackQuery, state: FSMContext):
#     user_id: int = callback_query.from_user.id
#     await bot.send_message(user_id,f" Введите код подключения")
#     await state.set_state(PrivateState.waiting_for_code)
#
#
# # Обработчик игры с другом
# @callback_router.callback_query(F.data == 'create')
# async def create_code(callback_query: types.CallbackQuery,state: FSMContext):
#     user_id: int = callback_query.from_user.id
#     lobby: Lobby = Lobby(user_id, private=True)
#     lobbies.append(lobby)
#
#     # Сообщение с кодом для подключения друга
#     await bot.send_message(user_id,
#                            f"Код для приглашения друга: {lobby.private_code}. Передайте его другу для подключения.")
#     await state.set_state(PrivateState.waiting_for_friend_join)

# #обработчик обычной игры
# @callback_router.callback_query(PublicState.waiting_for_pub)
# async def callback_public_game(callback_query: types.CallbackQuery, state: FSMContext):
#     data = callback_query.data.split(':')
#     user_id: int = callback_query.from_user.id
#     game_id = int(data[0])
#     cell_id = data[1]
#
#     game = await get_game(callback_query, game_id)
#     if game is None:
#         return
#
#     if cell_id in ('4', '3', '5', '2'):
#         last_move = game.board.pop()
#         last_move.promotion = int(cell_id)
#         game.board.push(last_move)
#
#         async with asyncio.TaskGroup() as tg:
#             tg.create_task(bot.delete_message(user_id, callback_query.message.message_id))
#             tg.create_task(board_update(game))
#
#         game.choosing_shape = -1
#         return
#
#     if game.choosing_shape != -1:
#         await callback_query.answer()
#         return
#
#     mess, update_board = game.click(cell_id, user_id)
#     outcome_message = await game.get_outcome_message()
#
#     if outcome_message is not None:
#         await board_update(game, True)
#         games.remove(game)
#         return
#
#     if mess is not None:
#         if mess == 'Превращение':
#             await bot.send_message(
#                 chat_id=user_id,
#                 text='Выберите фигуру:',
#                 reply_markup=InlineKeyboardMarkup(
#                     inline_keyboard=[
#                         [InlineKeyboardButton(
#                             text=Piece(i, game.board.turn).unicode_symbol(invert_color=True),
#                             callback_data=f'{game_id}:{i}'
#                         ) for i in (4, 3, 5, 2)]
#                     ]
#                 )
#             )
#         else:
#             await callback_query.answer(text=mess)
#
#     if update_board:
#         try:
#             await board_update(game)  # Убедитесь, что это асинхронно
#         except TelegramBadRequest:
#             print('Ошибка при обновлении доски')
#             await callback_query.answer()
#
#     # Убедитесь, что состояние остаётся в waiting_for_pub_game
#     await state.set_state(PublicState.waiting_for_pub_game)
#
#
# @callback_router.callback_query(PublicState.waiting_for_pub_game)
# async def callback_click_public_game(callback_query: types.CallbackQuery, state: FSMContext):
#     data = callback_query.data.split(':')
#     user_id: int = callback_query.from_user.id
#     game_id = int(data[0])
#     cell_id = data[1]
#
#     game = await get_game(callback_query, game_id)
#     if game is None:
#         return
#
#     if cell_id in ('4', '3', '5', '2'):
#         last_move = game.board.pop()
#         last_move.promotion = int(cell_id)
#         game.board.push(last_move)
#
#         async with asyncio.TaskGroup() as tg:
#             tg.create_task(bot.delete_message(user_id, callback_query.message.message_id))
#             tg.create_task(board_update(game))
#
#         game.choosing_shape = -1
#         return
#
#     if game.choosing_shape != -1:
#         await callback_query.answer()
#         return
#
#     mess, update_board = game.click(cell_id, user_id)
#     outcome_message = await game.get_outcome_message()
#
#     if outcome_message is not None:
#         await board_update(game, True)
#         games.remove(game)
#         return
#
#     if mess is not None:
#         if mess == 'Превращение':
#             await bot.send_message(
#                 chat_id=user_id,
#                 text=f'Выберите фигуру:',
#                 reply_markup=InlineKeyboardMarkup(
#                     inline_keyboard=[
#                         [InlineKeyboardButton(
#                             text=Piece(i, game.board.turn).unicode_symbol(invert_color=True),
#                             callback_data=f'{game_id}:{i}'
#                         ) for i in (4, 3, 5, 2)]
#                     ]
#                 )
#             )
#         else:
#             await callback_query.answer(text=mess)
#
#     if update_board:
#         try:
#             await board_update(game)  # Убедитесь, что это асинхронно
#         except TelegramBadRequest:
#             print('Ошибка при обновлении доски')
#             await callback_query.answer()
#
#     # Убедитесь, что состояние остаётся в waiting_for_pub_game
#     await state.clear()
#     await state.set_state(PublicState.waiting_for_pub_game)


# #обработчик приватной игры
# @callback_router.callback_query(PrivateState.waiting_for_private)
# async def callback_private_game(callback_query: types.CallbackQuery, state: FSMContext):
#     data = callback_query.data.split(':')
#     user_id: int = callback_query.from_user.id
#     game_id = int(data[0])
#     cell_id = data[1]
#
#     game = await get_game(callback_query, game_id)
#     if game is None:
#         return
#
#     if cell_id in ('4', '3', '5', '2'):
#         last_move = game.board.pop()
#         last_move.promotion = int(cell_id)
#         game.board.push(last_move)
#
#         async with asyncio.TaskGroup() as tg:
#             tg.create_task(bot.delete_message(user_id, callback_query.message.message_id))
#             tg.create_task(board_update(game))
#
#         game.choosing_shape = -1
#         return
#
#     if game.choosing_shape != -1:
#         await callback_query.answer()
#         return
#
#     mess, update_board = game.click(cell_id, user_id)
#     outcome_message = await game.get_outcome_message()
#
#     if outcome_message is not None:
#         await board_update(game, True)
#         games.remove(game)
#         return
#
#     if mess is not None:
#         if mess == 'Превращение':
#             await bot.send_message(
#                 chat_id=user_id,
#                 text='Выберите фигуру:',
#                 reply_markup=InlineKeyboardMarkup(
#                     inline_keyboard=[
#                         [InlineKeyboardButton(
#                             text=Piece(i, game.board.turn).unicode_symbol(invert_color=True),
#                             callback_data=f'{game_id}:{i}'
#                         ) for i in (4, 3, 5, 2)]
#                     ]
#                 )
#             )
#         else:
#             await callback_query.answer(text=mess)
#
#     if update_board:
#         try:
#             await board_update(game)  # Убедитесь, что это асинхронно
#         except TelegramBadRequest:
#             print('Ошибка при обновлении доски')
#             await callback_query.answer()
#
#     # Убедитесь, что состояние остаётся в waiting_for_pub_game
#     await state.clear()
#     await state.set_state(PrivateState.waiting_for_private_game)


@callback_router.callback_query(PrivateState.waiting_for_private_game)
async def callback_click_private_game(callback_query: types.CallbackQuery, state: FSMContext):
    data = callback_query.data.split(':')
    user_id: int = callback_query.from_user.id
    game_id = int(data[0])
    cell_id = data[1]

    game = await get_game(callback_query, game_id)
    if game is None:
        return

    if cell_id in ('4', '3', '5', '2'):
        last_move = game.board.pop()
        last_move.promotion = int(cell_id)
        game.board.push(last_move)

        async with asyncio.TaskGroup() as tg:
            tg.create_task(bot.delete_message(user_id, callback_query.message.message_id))
            tg.create_task(board_update(game))

        game.choosing_shape = -1
        return

    if game.choosing_shape != -1:
        await callback_query.answer()
        return

    mess, update_board = game.click(cell_id, user_id)
    outcome_message = await game.get_outcome_message()

    if outcome_message is not None:
        await board_update(game, True)
        games.remove(game)
        return

    if mess is not None:
        if mess == 'Превращение':
            await bot.send_message(
                chat_id=user_id,
                text=f'Выберите фигуру:',
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(
                            text=Piece(i, game.board.turn).unicode_symbol(invert_color=True),
                            callback_data=f'{game_id}:{i}'
                        ) for i in (4, 3, 5, 2)]
                    ]
                )
            )
        else:
            await callback_query.answer(text=mess)

    if update_board:
        try:
            await board_update(game)  # Убедитесь, что это асинхронно
        except TelegramBadRequest:
            print('Ошибка при обновлении доски')
            await callback_query.answer()

    # Убедитесь, что состояние остаётся в waiting_for_pub_game
    await state.set_state(PublicState.waiting_for_pub_game)

@callback_router.callback_query(F.data == 'statistics')
async def show_statistics(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    async with session_maker() as session:  # Используем асинхронную сессию
        try:
            # Использование SQLAlchemy для получения пользователя
            result1 = await session.execute(select(Statistic).filter(Statistic.user_id == user_id))
            users = result1.scalars().first()  # Получаем пользователя

            if users:
                await callback_query.message.answer("Выберите тип статистики:", reply_markup=stat_keyboard)
        except Exception as e:
            await callback_query.message.answer(f"Произошла ошибка: {str(e)}")

@callback_router.callback_query(F.data == 'back_to_main_menu')
async def back_to_main_menu(callback_query: types.CallbackQuery):
    await callback_query.message.edit_text("Вы вернулись в главное меню.",reply_markup=main_menu_keyboard)  # Здесь можно добавить основное меню или другие кнопки


@callback_router.callback_query(
    lambda callback_query: callback_query.data in ['public_stat', 'ranked_stat', 'main_stat', 'private_stat'])
async def in_progres(callback_query: types.CallbackQuery):
    # Здесь вы можете обработать каждое значение data по своему
    if callback_query.data == 'public_stat':
        await callback_query.message.edit_text("Вы выбрали публичную статистику.")
    elif callback_query.data == 'ranked_stat':
        await callback_query.message.edit_text("Вы выбрали рейтинговую статистику.")
    elif callback_query.data == 'main_stat':
        await callback_query.message.edit_text("Вы выбрали основную статистику.")
    elif callback_query.data == 'private_stat':
        await callback_query.message.edit_text("Вы выбрали приватную статистику.")

    # Отправляем уведомление
    notification_message = await callback_query.message.answer("🛠 Уведомление: Функция в разработке...")

    # Ждем 3 секунды
    await asyncio.sleep(3)

    # Удаляем уведомление
    await notification_message.delete()

@callback_router.callback_query(F.data == 'rank_game')
async def rank_game(callback_query: types.CallbackQuery):
    user_id: int = callback_query.from_user.id
    await callback_query.answer()
    # rating = await get_user_rating(user_id)
    # # Определяем диапазон рейтинга
    # if rating < 50:
    #     rating_range = range(0, 51)
    # elif rating < 100:
    #     rating_range = range(51, 100)
    # elif rating < 150:
    #     rating_range = range(100, 1000)
    # else:
    #     await bot.send_message(user_id, 'Ваш рейтинг слишком высок для этой игры.')
    #     return

    lobby: Lobby = next(filter(lambda s_lobby: not s_lobby.private and
                                            s_lobby.rank and
                                               s_lobby.first_player != user_id,
                               lobbies), None)

    if lobby is None:
        lobbies.append(Lobby(user_id, rank=True))
        await bot.send_message(user_id, 'Ищем для вас противника.')
    else:
        game = lobby.start_game(user_id)
        lobbies.remove(lobby)
        games.append(game)
        await send_board(game)


# Обработчик кнопки "Магазин"
@callback_router.callback_query(F.data == 'myBalance')
async def handle_sh(callback_query: types.CallbackQuery):
    # Отправляем сообщение с кнопками
    await callback_query.message.answer("Выберите количество алмазов для покупки:", reply_markup=keyboards)

@callback_router.callback_query(F.data.startswith("Bbuy_"))
async def handle_buy(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    try:
        item_id = callback_query.data.split('_')[1]  # Получаем ID товара
        if item_id not in buy_options:
            await callback_query.message.answer("Неверный выбор.")
            return

        # Получаем данные о выбранном товаре
        item = buy_options[item_id]
        price_in_rub = item["price"]  # Цена в рублях
        diamonds = item["amount"]  # Количество алмазов

        # Устанавливаем цену в копейках (нужно для LabeledPrice)
        prices = [LabeledPrice(label=diamonds, amount=price_in_rub * 100)]

        # Отправляем инвойс
        await bot.send_invoice(
            chat_id=user_id,
            title=f"Покупка 💎",
            description=f"Оплат за {diamonds}.",
            payload=f"buy_{item_id}",  # Полезная нагрузка для проверки
            provider_token=PAYMENTS_PROVIDER_TOKEN,
            currency="RUB",
            prices=prices,
            start_parameter="purchase"
        )
    except Exception as e:
        await callback_query.message.answer(f"Произошла ошибка: {str(e)}")
gift_claim_times = {}
# Кнопки для текущих событий



# Обработчик кнопки "События"
@callback_router.callback_query(F.data == 'event')
async def handle_event(callback_query: types.CallbackQuery):

    await callback_query.message.answer(text='Доступные события', reply_markup=event_board)



# Обработчик кнопки события "Релиз проекта"
@callback_router.callback_query(F.data == 'release_event')
async def handle_release_event(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    now = datetime.datetime.now()

    # Проверяем, прошло ли 24 часа с момента последнего забора подарка
    if user_id in gift_claim_times and (now - gift_claim_times[user_id]).total_seconds() < 86400:
        time_left = 86400 - (now - gift_claim_times[user_id]).total_seconds()
        hours = int(time_left // 3600)
        minutes = int((time_left % 3600) // 60)
        seconds = int(time_left % 60)
        await callback_query.answer(f"Подарок можно забрать через {hours} часов, {minutes} минут и {seconds} секунд.")
    else:

        await callback_query.message.answer(text='ChessSuaiBot уже здесь!', reply_markup=claim_gift_board)


# Обработчик кнопки "Забрать подарок"
@callback_router.callback_query(F.data == 'claim_gift')
async def handle_claim_gift(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    gift_claim_times[user_id] = datetime.datetime.now()

    # Добавляем алмазы пользователю
    await add_diamonds_to_user(user_id, 5)

    await callback_query.message.edit_text("Вы получили 5 алмазов! Подарок можно будет забрать снова через 24 часа.",reply_markup=menu_button)









@callback_router.callback_query()
async def callback_handler(callback_query: types.CallbackQuery):
    data = callback_query.data.split(':')
    user_id: int = callback_query.from_user.id
    game_id = int(data[0])
    cell_id = data[1]

    game = await get_game(callback_query, game_id)
    if game is None:
        return

    if cell_id in ('4', '3', '5', '2'):
        last_move = game.board.pop()
        last_move.promotion = int(cell_id)
        game.board.push(last_move)

        async with asyncio.TaskGroup() as tg:
            tg.create_task(bot.delete_message(user_id, callback_query.message.message_id))
            tg.create_task(board_update(game))

        game.choosing_shape = -1
        return

    if game.choosing_shape != -1:
        await callback_query.answer()
        return

    mess, update_board = game.click(cell_id, user_id)
    outcome_message = await game.get_outcome_message()
    if outcome_message is not None:
        await board_update(game, True)
        games.remove(game)
        return

    if mess is not None:
        if mess == 'Превращение':
            await bot.send_message(chat_id=user_id,
                                   text='Выберите фигуру:',
                                   reply_markup=InlineKeyboardMarkup(
                                       inline_keyboard=[
                                           [InlineKeyboardButton(
                                               text=Piece(i, game.board.turn).unicode_symbol(invert_color=True),
                                               callback_data=f'{game_id}:{i}')
                                               for i in (4, 3, 5, 2)]]))
        else:
            await callback_query.answer(text=mess)
    if update_board:
        try:
            await board_update(game)  # Убедитесь, что это асинхронно
        except TelegramBadRequest:
            print('ой')
            await callback_query.answer()
