from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio
#Старая обоочка
# Состояния для FSM (машины состояний)
class ProfileState(StatesGroup):
    waiting_for_username = State()
    waiting_for_telegram_name = State()

TOKEN = '7735863677:AAELZ8O2QNCsQxkvDr0CMpqotJ7Xg4k7DiM'  # Замените на ваш реальный токен
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Пункт "Мой профиль"
@dp.callback_query(F.data == 'profile')
async def profile(callback_query: types.CallbackQuery, state: FSMContext):
    try:
        user_id = callback_query.from_user.id
        async with await get_db_connection() as conn:  # Используем await для вызова корутины
            async with conn.cursor() as cursor:
                # Проверяем, есть ли профиль пользователя
                await cursor.execute("SELECT username, telegram_name, wins, losses, total_games, win_percentage  FROM users WHERE user_id = %s", (user_id,))
                result = await cursor.fetchone()

                if result:
                    username, telegram_name, wins, losses, total_games, win_percentage = result
                    await callback_query.message.answer(
                        f"Ваш профиль:\n"
                        f"Имя пользователя: {username}\n"
                        f"Количество побед: {wins}\n"
                        f"Количество поражений: {losses}\n"
                        f"Количество проведенных партий: {total_games}\n"
                        f"Соотношение побед: {win_percentage}\n"
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


# Обработчик ввода telegram имени
@dp.message(ProfileState.waiting_for_telegram_name)
async def process_telegram_name(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    username = user_data.get("username")
    telegram_name = message.text
    user_id = message.from_user.id

    # Сохраняем профиль в базу данных
    async with await get_db_connection() as conn:  # Добавлено await
        async with conn.cursor() as cursor:
            await cursor.execute(
                "INSERT INTO users (user_id, username, telegram_name) VALUES (%s, %s, %s) "
                "ON DUPLICATE KEY UPDATE username=%s, telegram_name=%s",
                (user_id, username, telegram_name, username, telegram_name)
            )
            await conn.commit()

    await message.answer(
        f"Ваш профиль создан!\n"
        f"Имя пользователя: {username}\n"
    )
    await state.clear()


# Инициализация состояния доски и выбранной фигуры для каждого пользователя
user_board_states = {}

# Команда /start
@dp.message(Command('start'))
async def start_command(message: types.Message):
    await message.answer("Привет! Давай сыграем в шахматы?")
    start_button = InlineKeyboardButton(text="Начать игру", callback_data="start_game")
    rank_button = InlineKeyboardButton(text="🎖Рейтинговая игра", callback_data="rank_game")
    public_button = InlineKeyboardButton(text="Товарищеская игра", callback_data="public_game")
    practice_button = InlineKeyboardButton(text="🤖Игра с ботом", callback_data="practice_game")
    profile_button = InlineKeyboardButton(text="Мой профиль", callback_data="profile")
    clan_button = InlineKeyboardButton(text="Добавить в клан", callback_data="clan")
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

# Обработчик нажатия "Начать игру"
@dp.callback_query(F.data == 'start_game')
async def start_game(callback_query: types.CallbackQuery):
    await callback_query.answer()

    # Предложение выбора цвета фигур
    color_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Черные", callback_data="color_black")],
        [InlineKeyboardButton(text="Белые", callback_data="color_white")]
    ])
    await bot.send_message(callback_query.from_user.id, "Выбери цвет фигур, за которые будешь играть:",
                           reply_markup=color_keyboard)

# Обработчик выбора цвета
@dp.callback_query(F.data.in_({'color_black', 'color_white'}))
async def choose_color(callback_query: types.CallbackQuery):
    await callback_query.answer()

    color = "черные" if callback_query.data == 'color_black' else "белые"
    user_id = callback_query.from_user.id

    # Инициализация состояния доски для пользователя
    user_board_states[user_id] = {
        "board": initialize_board(color),
        "selected_piece": None
    }

    await bot.send_message(callback_query.from_user.id, f"Ты выбрал {color} фигуры. Начинаем игру!")

    # Отправка шахматной доски
    keyboard = generate_chessboard_inline_keyboard(user_board_states[user_id]["board"])
    await bot.send_message(callback_query.from_user.id, "Шахматная доска:", reply_markup=keyboard)

# Инициализация шахматной доски
def initialize_board(color):
    if color == 'черные':
        board = [
            ["♜", "♞", "♝", "♛", "♚", "♝", "♞", "♜"],  # 8
            ["♟"] * 8,  # 7
            [" "] * 8,  # 6
            [" "] * 8,  # 5
            [" "] * 8,  # 4
            [" "] * 8,  # 3
            ["♙"] * 8,  # 2
            ["♖", "♘", "♗", "♕", "♔", "♗", "♘", "♖"]  # 1
        ]
    else:
        board = [
            ["♖", "♘", "♗", "♕", "♔", "♗", "♘", "♖"],  # 8
            ["♙"] * 8,  # 7
            [""] * 8,  # 6
            [" "] * 8,  # 5
            [" "] * 8,  # 4
            [" "] * 8,  # 3
            ["♟"] * 8,  # 2
            ["♜", "♞", "♝", "♛", "♚", "♝", "♞", "♜"]  # 1
        ]
    return board


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


# Обработка нажатий на клетки доски
@dp.callback_query(F.data.startswith('move_') | F.data.startswith('piece_'))
async def handle_board_action(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    if user_id not in user_board_states:
        await callback_query.answer("Сначала начните игру с помощью /start.")
        return

    board = user_board_states[user_id]["board"]
    selected_piece = user_board_states[user_id]["selected_piece"]
    data = callback_query.data.split('_')

    action = data[0]
    rank = int(data[1])
    file = int(data[2])

    if action == 'piece':
        piece = board[rank][file]
        if piece == " ":
            await callback_query.answer("Пустая клетка.")
            return
        # Сохраняем выбранную фигуру
        user_board_states[user_id]["selected_piece"] = (rank, file)
        await callback_query.answer(f"Выбрана фигура: {piece} на {chr(65 + file)}{8 - rank}")
    elif action == 'move':
        if selected_piece:
            start_rank, start_file = selected_piece
            piece = board[start_rank][start_file]
            # Здесь можно добавить логику проверки допустимости хода
            board[rank][file] = piece
            board[start_rank][start_file] = " "
            # Очистка выбранной фигуры
            user_board_states[user_id]["selected_piece"] = None
            # Обновление клавиатуры
            keyboard = generate_chessboard_inline_keyboard(board)
            await bot.edit_message_reply_markup(chat_id=user_id, message_id=callback_query.message.message_id,
                                                reply_markup=keyboard)
            await callback_query.answer(f"Фигура перемещена на {chr(65 + file)}{8 - rank}")
        else:
            await callback_query.answer("Сначала выберите фигуру для перемещения.")

class FeedbackState(StatesGroup):
    waiting_for_feedback = State()

# Обработчик нажатия "Оставить отзыв"
@dp.callback_query(F.data == 'feedback')
async def handle_feedback(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.answer("Пожалуйста, оставьте свой отзыв:")
    await state.set_state(FeedbackState.waiting_for_feedback)

@dp.message(FeedbackState.waiting_for_feedback)
async def save_feedback(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    feedback_text = message.text

    async with await get_db_connection() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                "INSERT INTO feedback (user_id, feedback) VALUES (%s, %s)",
                (user_id, feedback_text)
            )
            await conn.commit()

    await message.answer("Спасибо за ваш отзыв!")
    await state.clear()

@dp.callback_query(F.data == 'top100')
async def handle_top100(callback_query: types.CallbackQuery):
    try:
        async with await get_db_connection() as conn:
            async with conn.cursor() as cursor:
                # Запрос для получения топ 100 пользователей по win_percentage
                await cursor.execute(
                    "SELECT username, win_percentage FROM users ORDER BY win_percentage DESC LIMIT 100"
                )
                top_users = await cursor.fetchall()

                if top_users:
                    response = "🏆 Топ 100 игроков по соотношению побед:\n"
                    for i, (username, win_percentage) in enumerate(top_users, start=1):
                        response += f"{i}. {username} - {win_percentage}% побед\n"
                else:
                    response = "Пока нет данных для отображения Топ 100."

        await callback_query.message.answer(response)
    except Exception as e:
        await callback_query.message.answer(f"Произошла ошибка при получении Топ 100: {str(e)}")

# Запуск бота
async def main():
    await dp.start_polling(bot)


# Исправлено условие для точки входа
if __name__ == '__main__':
    asyncio.run(main())