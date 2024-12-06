import dp
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from sqlalchemy.future import select
from db import session_maker, User, Feedback, ClanMember, Clan, ShopItem
from sqlalchemy.exc import SQLAlchemyError
from aiogram import F
from datetime import datetime, timedelta
from sqlalchemy import and_
from sqlalchemy import delete
from dotenv import load_dotenv
import os


from board import Figure, FigureType
from game import Game

load_dotenv()
# Состояния для FSM (машины состояний)
class ProfileState(StatesGroup):
    waiting_for_username = State()
    waiting_for_telegram_name = State()
TOKEN = os.getenv('token')

# Состояния для FSM
class ClanState(StatesGroup):
    enter_name = State()
    confirm_join = State()


bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)



# Инициализация состояния доски и выбранной фигуры для каждого пользователя
user_board_states = {}
games = []  # Список для хранения информации о созданных играх
async def get_game(callback, game_id: int) -> Game | None:
    print(games)
    game = next(filter(lambda g: g.id == game_id, games), None)
    if game is None:
        await callback.answer('Игра не существует')
        return
    return game
# Обработчик нажатия "Мой профиль"
@dp.callback_query(F.data == 'profile')
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
                    f"Количество побед: {user.wins}\n"
                    f"Количество поражений: {user.losses}\n"
                    f"Количество проведенных партий: {user.total_games}\n"
                    f"Соотношение побед: {user.win_percentage}%\n"
                    f"Баланс: {user.diamonds} 💎\n"
                )
            else:
                # Если профиля нет, предлагаем его создать
                await callback_query.message.answer(
                    "Похоже, у вас еще нет профиля. Давайте создадим его!\nВведите ваш username:"
                )
                await state.set_state(ProfileState.waiting_for_username)
        except Exception as e:
            await callback_query.message.answer(f"Произошла ошибка: {str(e)}")

# Обработчик ввода username
@dp.message(ProfileState.waiting_for_username)
async def process_username(message: types.Message, state: FSMContext):
    await state.update_data(username=message.text)
    await message.answer("Введите ваш username в Telegram:")
    await state.set_state(ProfileState.waiting_for_telegram_name)

# from sqlalchemy.future import select
#
#
# @dp.callback_query(F.data.startswith("members_"))
# async def list_clan_members(callback: types.CallbackQuery):
#     clan_id = int(callback.data.split("_")[1])  # Извлекаем ID клана
#
#     async with session_maker() as session:
#         try:
#             # Проверяем, существует ли клан
#             clan_result = await session.execute(
#                 select(Clan).where(Clan.clan_id == clan_id)
#             )
#             clan = clan_result.scalars().first()
#             if not clan:
#                 await callback.message.edit_text("Клан не найден.")
#                 return
#
#             # Получаем участников клана
#             members_result = await session.execute(
#                 select(ClanMember.user_id).where(ClanMember.clan_id == clan_id)
#             )
#             members = members_result.scalars().all()
#
#             # Если в клане нет участников
#             if not members:
#                 await callback.message.edit_text(f"В клане '{clan.name}' пока нет участников.")
#                 return
#
#             # Формируем список участников
#             members_list = "\n".join([f"- {member}" for member in members])
#
#             # Отправляем пользователю список участников
#             await callback.message.edit_text(
#                 f"Список участников клана '{clan.name}':\n{members_list}"
#             )
#         except Exception as e:
#             # Обрабатываем ошибки
#             logging.exception(f"Error fetching members for clan {clan_id}: {e}")
#             await callback.message.edit_text("Произошла ошибка при получении списка участников.")
# Обработчик ввода telegram имени
@dp.message(ProfileState.waiting_for_telegram_name)
async def process_telegram_name(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    username = user_data.get("username")
    telegram_name = message.text
    user_id = message.from_user.id

    async with session_maker() as session:
        try:
            # Сохраняем профиль в базу данных
            user = User(user_id=user_id, username=username, telegram_name=telegram_name)
            session.add(user)
            await session.commit()

            await message.answer(
                f"Ваш профиль создан!\n"
                f"Имя пользователя: {username}\n"
            )
        except Exception as e:
            await message.answer(f"Произошла ошибка: {str(e)}")

    await state.clear()


clan_actions = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Создать клан", callback_data="create_clan")],
    [InlineKeyboardButton(text="Вступить в клан", callback_data="join_clan")]
])

# Обработчик кнопки "Кланы"
@dp.callback_query(F.data == "clan")
async def handle_clan_button(callback: types.CallbackQuery):
    await callback.message.edit_text("Выберите действие:", reply_markup=clan_actions)


# Обработчик кнопки "Создать клан"
@dp.callback_query(F.data == "create_clan")
async def process_create_clan(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите название для вашего клана:")
    await state.set_state(ClanState.enter_name)

@dp.message(ClanState.enter_name)
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


@dp.callback_query(F.data == "join_clan")
async def process_list_clans(callback: types.CallbackQuery, state: FSMContext):
    async with session_maker() as session:
        try:
            # Получаем список доступных кланов
            result = await session.execute(select(Clan))
            clans = result.scalars().all()

            if not clans:
                await callback.message.edit_text("Нет доступных кланов для вступления.")
                return

            # Создаем клавиатуру с доступными кланами
            clan_buttons = [
                [InlineKeyboardButton(text=clan.name, callback_data=f"join_{clan.clan_id}")]
                for clan in clans
            ]
            clan_list_kb = InlineKeyboardMarkup(inline_keyboard=clan_buttons)

            await callback.message.edit_text("Выберите клан для вступления:", reply_markup=clan_list_kb)
        except Exception as e:
            await callback.message.edit_text(f"Произошла ошибка: {str(e)}")


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("bot_errors.log"),  # Логи записываются в файл
        logging.StreamHandler()  # Логи выводятся в консоль
    ]
)

@dp.callback_query(F.data.startswith("join_"))
async def join_clan(callback: types.CallbackQuery):
    clan_id = int(callback.data.split("_")[1])  # Извлекаем ID клана
    user_id = callback.from_user.id  # ID пользователя

    async with session_maker() as session:  # Создаём сессию
        try:
            logging.info(f"User {user_id} attempting to join clan {clan_id}")

            # Проверяем, состоит ли пользователь уже в каком-либо клане
            existing_member = await session.execute(
                select(ClanMember).where(ClanMember.user_id == user_id)
            )
            if existing_member.scalars().first():
                await callback.message.edit_text("Вы уже состоите в клане.")
                logging.warning(f"User {user_id} already in a clan")
                return

            # Проверяем, существует ли клан
            clan_result = await session.execute(
                select(Clan).where(Clan.clan_id == clan_id)
            )
            clan = clan_result.scalars().first()
            if not clan:
                await callback.message.edit_text("Клан не найден.")
                logging.error(f"Clan with ID {clan_id} not found")
                return

            # Добавляем пользователя в клан
            new_member = ClanMember(clan_id=clan_id, user_id=user_id)
            session.add(new_member)
            await session.commit()
            logging.info(f"User {user_id} successfully joined clan {clan.name}")

            # Уведомляем пользователя о вступлении
            await callback.message.edit_text(f"Вы успешно вступили в клан '{clan.name}'!")
        except SQLAlchemyError as db_error:
            # Логируем ошибки SQLAlchemy
            logging.error(f"Database error: {db_error}")
            await callback.message.edit_text("Произошла ошибка при работе с базой данных.")
        except Exception as e:
            # Логируем любые другие ошибки
            logging.exception(f"Unexpected error for user {user_id} joining clan {clan_id}: {e}")
            await callback.message.edit_text(f"Произошла ошибка: {str(e)}")


# @dp.callback_query(F.data.startswith("join_clan"))
# async def join_clan(callback: types.CallbackQuery):
#     clan_id = int(callback.data.split("_")[1])  # Извлекаем ID клана
#     user_id = callback.from_user.id  # ID пользователя
#
#     async with session_maker() as session:  # Создаём сессию
#         try:
#             # Проверяем, состоит ли пользователь уже в каком-либо клане
#             existing_member = await session.execute(
#                 select(ClanMember).where(ClanMember.user_id == user_id)
#             )
#             if existing_member.scalars().first():
#                 await callback.message.edit_text("Вы уже состоите в клане.")
#                 return
#
#             # Проверяем, существует ли клан
#             clan_result = await session.execute(
#                 select(Clan).where(Clan.clan_id == clan_id)
#             )
#             clan = clan_result.scalars().first()
#             if not clan:
#                 await callback.message.edit_text("Клан не найден.")
#                 return
#
#             # Добавляем пользователя в клан
#             new_member = ClanMember(clan_id=clan_id, user_id=user_id)
#             session.add(new_member)
#             await session.commit()
#
#             # Уведомляем пользователя о вступлении
#             await callback.message.edit_text(f"Вы успешно вступили в клан '{clan.name}'!")
#         except Exception as e:
#             # Обрабатываем ошибки
#             await callback.message.edit_text(f"Произошла ошибка: {str(e)}")
# @dp.callback_query(F.data.startswith("join_"))
# async def process_join_clan(callback: types.CallbackQuery, state: FSMContext):
#     try:
#         clan_id = int(callback.data.split("_")[1])
#         user_id = callback.from_user.id
#         user_name = callback.from_user.full_name
#
#         async with session_maker() as session:
#             # Проверяем, состоит ли пользователь уже в клане
#             result = await session.execute(select(ClanMember).where(ClanMember.user_id == user_id))
#             if result.scalars().first():
#                 await callback.message.edit_text("Вы уже состоите в клане.")
#                 return
#
#             # Получаем информацию о клане
#             clan_result = await session.execute(select(Clan).where(Clan.clan_id == clan_id))
#             clan = clan_result.scalars().first()
#             if not clan:
#                 await callback.message.edit_text("Клан не найден.")
#                 return
#
#             # Уведомляем главу клана о запросе на вступление
#             leader_id = clan.leader_id
#             approve_buttons = InlineKeyboardMarkup(
#                 inline_keyboard=[
#                     [
#                         InlineKeyboardButton(text="Принять", callback_data=f"approve_{user_id}_{clan_id}"),
#                         InlineKeyboardButton(text="Отклонить", callback_data=f"reject_{user_id}_{clan_id}")
#                     ]
#                 ]
#             )
#
#             await bot.send_message(
#                 chat_id=leader_id,
#                 text=f"Пользователь {user_name} хочет вступить в ваш клан '{clan.name}'. Что вы хотите сделать?",
#                 reply_markup=approve_buttons
#             )
#
#             await callback.message.edit_text(f"Запрос на вступление в клан '{clan.name}' отправлен главе клана. Ожидайте ответа.")
#     except ValueError:
#         await callback.message.edit_text("Некорректный идентификатор клана.")
#     except Exception as e:
#         await callback.message.edit_text(f"Произошла ошибка: {str(e)}")





# Команда /start
@dp.message(Command('start'))
async def start_command(message: types.Message):
    await message.answer("Привет! Давай сыграем в шахматы?")
    start_button = InlineKeyboardButton(text="Начать игру", callback_data="start_game")
    rank_button = InlineKeyboardButton(text="🎖Рейтинговая игра", callback_data="rank_game")
    public_button = InlineKeyboardButton(text="Товарищеская игра", callback_data="public_game")
    practice_button = InlineKeyboardButton(text="🤖Игра с ботом", callback_data="practice_game")
    profile_button = InlineKeyboardButton(text="Мой профиль", callback_data="profile")
    clan_button = InlineKeyboardButton(text="Кланы", callback_data="clan")
    FriendGame_button = InlineKeyboardButton(text="Игра с другом", callback_data="friendGame")
    setting_button = InlineKeyboardButton(text="🛠Настройки", callback_data="setting")
    top100_button = InlineKeyboardButton(text="🏆Топ 100 игроков", callback_data="top100")
    shop_button = InlineKeyboardButton(text="💰Магазин", callback_data="shop")
    myBalance_button = InlineKeyboardButton(text="💎Мой баланс", callback_data="myBalance")
    feadback_button = InlineKeyboardButton(text="💬Оставить отзыв", callback_data="feedback")

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [start_button],
        [profile_button],
        [clan_button, FriendGame_button],
        [public_button, rank_button],
        [shop_button, myBalance_button],
        [practice_button],
        [feadback_button, setting_button],
        [top100_button]
    ])

    await message.answer("Нажми кнопку, чтобы начать:", reply_markup=keyboard)

# Обработчик нажатия "Топ 100 игроков"
@dp.callback_query(F.data == 'top100')
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

# Класс состояния
class FeedbackState(StatesGroup):
    waiting_for_feedback = State()  # Ожидание отзыва

# Обработчик нажатия "Оставить отзыв"
@dp.callback_query(F.data == 'feedback')
async def handle_feedback(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.answer("Пожалуйста, оставьте свой отзыв:")
    await state.set_state(FeedbackState.waiting_for_feedback)

@dp.message(FeedbackState.waiting_for_feedback)
async def save_feedback(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    feedback_text = message.text

    async with session_maker() as session:
        try:
            # Проверяем, оставлял ли пользователь отзыв в последние 24 часа
            last_24_hours = datetime.utcnow() - timedelta(days=1)
            result = await session.execute(
                select(Feedback).filter(
                    and_(
                        Feedback.user_id == user_id,
                        Feedback.created_at >= last_24_hours
                    )
                )
            )
            last_feedback = result.scalars().first()

            if last_feedback:
                # Если отзыв найден, информируем пользователя
                await message.answer("Вы уже оставляли отзыв сегодня. Пожалуйста, попробуйте позже.")
            else:
                # Создаем новый объект отзыва
                feedback = Feedback(user_id=user_id, feedback=feedback_text)

                # Добавляем отзыв в сессию
                session.add(feedback)
                await session.commit()  # Подтверждаем изменения в базе

                await message.answer("Спасибо за ваш отзыв!")
        except Exception as e:
            await message.answer(f"Произошла ошибка при сохранении отзыва: {str(e)}")
        finally:
            await state.clear()  # В случае ошибки или успешного добавления отзыва очищаем состояние

# Обработчик кнопки "Магазин"
@dp.callback_query(F.data == 'shop')
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
                        text=f"Купить {item.name}",
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
@dp.callback_query(F.data.startswith('buy_'))
async def handle_buy(callback_query: types.CallbackQuery):
    try:
        item_id = int(callback_query.data.split('_')[1])  # Получаем ID товара
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
            await session.commit()

            # Логика добавления товара в инвентарь (если нужно)
            # Например, можно добавить товар в таблицу инвентаря, если она есть

            # Отправляем сообщение о покупке
            await callback_query.message.answer(f"Вы купили {item.name} за {item.price} 💎!")

            # Возможно, уведомление администратора о покупке
            # await bot.send_message(admin_id, f"Пользователь {user.username} купил {item.name} за {item.price} 💎")

    except Exception as e:
        await callback_query.message.answer(f"Произошла ошибка при обработке покупки: {str(e)}")


# Генерация шахматной доски как inline клавиатуры
def generate_chessboard_inline_keyboard(board):
    inline_keyboard = []
    for rank in range(8):
        row_buttons = []
        for file in range(8):
            piece = board[rank][file]
            callback_data = f"piece_{rank}_{file}" if piece != " " else f"move_{rank}_{file}"
            row_buttons.append(InlineKeyboardButton(text=piece, callback_data=callback_data))
        inline_keyboard.append(row_buttons)
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

@dp.callback_query(F.data == 'start_game')
async def profile(callback_query: types.CallbackQuery):
    game = Game(0, 0)
    games.append(game)
    print(game.id)
    await bot.send_message(callback_query.message.chat.id, 'ААА', reply_markup=game.board.get_board(0))
    #await bot.send_message(callback_query.message.chat.id, 'ААА', reply_markup=game.board.get_board(1))


@dp.callback_query()
async def profile(callback_query: types.CallbackQuery):
    print(callback_query.data)
    game_id = int(callback_query.data.split(':')[0])
    cell_id = callback_query.data.split(':')[1]

    game = await get_game(callback_query, game_id)
    if game is None:
        return

    if cell_id in ('rook', 'bishop', 'queen', 'knight'):
        await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
        await callback_query.answer(cell_id)

        mes = int(callback_query.data.split(':')[2])
        fig = callback_query.data.split(':')[3]

        game.board.get_cell(fig).figure.type = FigureType._member_map_[cell_id]
        game.turn = (game.turn + 1) % 2

        await bot.edit_message_text(text='ААА', message_id=mes, reply_markup=game.board.get_board(0), chat_id=callback_query.message.chat.id)

        return

    mess = game.click(cell_id)
    if mess is not None:
        if mess == 'Превращение':
            c = game.turn
            await bot.send_message(chat_id=callback_query.message.chat.id, text='Выберите фигуру:',reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=Figure(FigureType.rook, c).get_pic(), callback_data=f'{game_id}:rook:{callback_query.message.message_id}:{cell_id}'), InlineKeyboardButton(text=Figure(FigureType.bishop, c).get_pic(), callback_data=f'{game_id}:bishop:{callback_query.message.message_id}:{cell_id}'), InlineKeyboardButton(text=Figure(FigureType.queen, c).get_pic(), callback_data=f'{game_id}:queen:{callback_query.message.message_id}:{cell_id}'), InlineKeyboardButton(text=Figure(FigureType.knight, c).get_pic(), callback_data=f'{game_id}:knight:{callback_query.message.message_id}:{cell_id}')]]))
        else:
            await callback_query.answer(text=mess)
    try:
        await bot.edit_message_text(text='ААА', message_id=callback_query.message.message_id, reply_markup=game.board.get_board(0), chat_id=callback_query.message.chat.id)
    except Exception:
        print('ой')
        await callback_query.answer()
# Запуск бота
async def main():
    print('Бот запущен')
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот завершил работу")

