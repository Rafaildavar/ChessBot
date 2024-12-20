import asyncio
import logging

from aiogram import F
from aiogram import Router, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from chess import Piece
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select

from config import bot
from database.db import User, ClanMember, Clan, ShopItem, Purchase, Statistic
from database.db import session_maker
from gameLogic.game import Lobby
from kbds.State import FeedbackState, ProfileState, ClanState, PublicState
from kbds.inline import clan_actions, stat_keyboard, main_menu_keyboard
from utils.game_relation import get_game, board_update, send_board, games, lobbies

callback_router = Router()



#Обработчик нажатия "Мой профиль"
@callback_router.callback_query(F.data == 'profile')
async def profile(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    async with session_maker() as session:  # Используем асинхронную сессию
        try:
            # Использование SQLAlchemy для получения пользователя
            result = await session.execute(select(User).filter(User.user_id == user_id))
            user = result.scalars().first()  # Получаем пользователя

            if user:
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

# @callback_router.callback_query(F.data.startswith("join_"))
# async def join_clan(callback: types.CallbackQuery):
#     clan_id = int(callback.data.split("_")[1])
#     user_id = callback.from_user.id
#
#     async with session_maker() as session:
#         try:
#             logging.info(f"User {user_id} attempting to join clan {clan_id}")
#
#             # Проверяем, существует ли клан
#             clan_result = await session.execute(
#                 select(Clan).where(Clan.clan_id == clan_id)
#             )
#             clan = clan_result.scalars().first()
#             if not clan:
#                 await callback.message.answer("Клан не найден.")
#                 return
#
#             # Добавляем пользователя в клан
#             new_member = ClanMember(clan_id=clan_id, user_id=user_id)
#             session.add(new_member)
#             await session.commit()
#
#             await callback.message.answer(f"Вы успешно вступили в клан '{clan.name}'!")
#         except Exception as e:
#             logging.exception(f"Error: {e}")
#             await callback.message.answer(f"Произошла ошибка: {str(e)}")


# Обработчик нажатия "Топ 100 игроков"
@callback_router.callback_query(F.data == 'top100')
async def handle_top100(callback_query: types.CallbackQuery):
    try:
        async with session_maker() as session:
            result = await session.execute(select(User).order_by(User.win_percentage.desc()).limit(100))
            top_users = result.scalars().all()

            if top_users:
                response = "🏆 Топ 100 игроков по соотношению побед:\n"
                for i, user in enumerate(top_users, start=1):
                    response += f"{i}. {user.username} - {user.win_percentage}% побед\n"
            else:
                response = "Пока нет данных для отображения Топ 100."

        await callback_query.message.answer(response)
    except Exception as e:
        await callback_query.message.answer(f"Произошла ошибка при получении Топ 100: {str(e)}")



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
                        text=f"Купить товар",
                        callback_data=f"buy_{item.item_id}"
                    )

                    # Добавляем кнопку в клавиатуру
                    keyboard.inline_keyboard.append([buy_button])

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

            # Если средств хватает, обновляем баланс
            user.diamonds -= item.price

            # Добавляем запись в таблицу покупок
            new_purchase = Purchase(user_id=user_id, item_id=item_id, name=item.name, description=item.description)
            session.add(new_purchase)

            # Сохраняем изменения
            await session.commit()

            # Отправляем сообщение о покупке
            await callback_query.message.answer(f"Вы купили {item.name} за {item.price} 💎!")


    except Exception as e:
        await callback_query.message.answer(f"Произошла ошибка при обработке покупки: {str(e)}")

# Обработчик кнопки "Покупки"
@callback_router.callback_query(F.data == 'purchases')
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
                response = "🛒 Ваши покупки:\n"

                # Формируем клавиатуру с кнопками
                keyboard = InlineKeyboardMarkup(inline_keyboard=[], row_width=1)

                back_button = InlineKeyboardButton(
                    text="Перейти в магазин",
                    callback_data="shop"
                )
                # Добавляем кнопку на клавиатуру
                keyboard.inline_keyboard.append([back_button])

                for purchase in purchases:
                    response += f"📦 {purchase.name}\nОписание: {purchase.description}\n"

                # Отправляем сообщение с покупками
                await callback_query.message.answer(response, reply_markup=keyboard)
            else:
                # Если покупок нет
                await callback_query.message.answer("У вас еще нет покупок.")

    except Exception as e:
        await callback_query.message.answer(f"Произошла ошибка при получении покупок: {str(e)}")


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
        await state.set_state(PublicState.waiting_for_pub_game)
# Обработчик игры с другом
@callback_router.callback_query(F.data == 'friend_game')
async def friend_game(callback_query: types.CallbackQuery):
    user_id: int = callback_query.from_user.id
    await callback_query.answer()

    lobby: Lobby = Lobby(user_id, private=True)
    lobbies.append(lobby)

    # Сообщение с кодом для подключения друга
    await bot.send_message(user_id,
                           f"Код для приглашения друга: {lobby.private_code}. Передайте его другу для подключения.")


@callback_router.callback_query(PublicState.waiting_for_pub)
async def callback_public_game(callback_query: types.CallbackQuery, state: FSMContext):
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
                text='Выберите фигуру:',
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


@callback_router.callback_query(PublicState.waiting_for_pub_game)
async def callback_click_public_game(callback_query: types.CallbackQuery, state: FSMContext):
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
    await state.clear()
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





# @callback_router.callback_query(F.data == 'rank_game')
# async def rank_game(callback_query: types.CallbackQuery):
#     user_id: int = callback_query.from_user.id
#     await callback_query.answer()
#
#     lobby: Lobby = next(filter(lambda s_lobby: s_lobby.rank and
#                                                abs(user_profiles[user_id]['rating'] - user_profiles[user_id]['rating']) <= 50 and
#                                                s_lobby.first_player != user_id,
#                                lobbies), None)
#     if lobby is None:
#         lobbies.append(Lobby(user_id, rank=True))
#         await bot.send_message(user_id, 'Ищем для вас противника.')
#         return
#     else:
#         game = lobby.start_game(user_id)
#         lobbies.remove(lobby)
#         games.append(game)
#         await send_board(game)
