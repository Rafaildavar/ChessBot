import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram import F
from aiogram.fsm.storage.memory import MemoryStorage
import random

TOKEN = 'token'  # Замените на ваш реальный токен
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Инициализация состояния доски и выбранной фигуры для каждого пользователя
user_board_states = {}
games = {}  # Словарь для хранения информации о созданных играх

# Пример данных профиля для каждого пользователя
user_profiles = {
    64747383: {
        "name": "вая",
        "rating": 10,
        "total_games": 4,
        "wins": 3,
        "losses": 0,
        "draws": 1,
        "win_percentage": 75.0,
        "win_rank": "2693-3741",
        "rating_rank": "331-354"
    }
}

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
    FriendGame_button = InlineKeyboardButton(text="Игра с другом", callback_data="friend_game")
    setting_button = InlineKeyboardButton(text="🛠Настройки", callback_data="setting")
    top100_button = InlineKeyboardButton(text="🏆Топ 100 игроков", callback_data="top100")
    shop_button = InlineKeyboardButton(text="💰Магазин", callback_data="shop")
    myBalance_button = InlineKeyboardButton(text="💎Мой баланс", callback_data="myBalance")
    feadback_button = InlineKeyboardButton(text="💬Оставить отзыв", callback_data="feadback")

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

# Обработчик профиля
@dp.callback_query(F.data == 'profile')
async def profile(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    profile_data = user_profiles.get(user_id, None)

    if profile_data:
        profile_message = f"""
        🏠️ Мой профиль:

        Имя: {profile_data['name']} [{user_id}]
        🎖 Рейтинг: {profile_data['rating']}
        🎮 Всего игр: {profile_data['total_games']}
        🏆 Всего побед: {profile_data['wins']}
        🥴 Всего проигрышей: {profile_data['losses']}
        ☯️ Всего ничьих: {profile_data['draws']}
        🎯 Процент побед: {profile_data['win_percentage']}%

        🏆 Место в ТОПе по победам: {profile_data['win_rank']}
        🎖 Место в ТОПе по рейтингу: {profile_data['rating_rank']}
        """
        await callback_query.message.answer(profile_message)
    else:
        await callback_query.message.answer("Ваш профиль пока не создан.")

# Обработчик игры с другом
@dp.callback_query(F.data == 'friend_game')
async def friend_game(callback_query: types.CallbackQuery):
    await callback_query.answer()

    # Создание уникального кода игры
    game_code = str(random.randint(1000, 9999))

    # Инициализация состояния доски для создателя игры
    user_id = callback_query.from_user.id
    games[game_code] = {
        "board": initialize_board('белые'),
        "players": [user_id],
        "turn": 'белые'
    }

    # Сообщение с кодом для подключения друга
    await bot.send_message(callback_query.from_user.id,
                           f"Код для приглашения друга: {game_code}. Передайте его другу для подключения.")

    # Ожидание присоединения друга
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Присоединиться к игре", callback_data="join_game")]
    ])
    await bot.send_message(callback_query.from_user.id, "Ожидаем подключения друга...", reply_markup=keyboard)


# Присоединение к игре
@dp.callback_query(F.data == 'join_game')
async def join_game(callback_query: types.CallbackQuery):
    await callback_query.answer()

    # Запросить у пользователя код игры
    await bot.send_message(callback_query.from_user.id, "Введите код игры для подключения:")


# Получение кода игры от пользователя
@dp.message()
async def handle_game_code(message: types.Message):
    game_code = message.text.strip()

    # Проверка, существует ли игра с таким кодом
    if game_code in games and len(games[game_code]["players"]) == 1:
        user_id = message.from_user.id
        games[game_code]["players"].append(user_id)

        # Начало игры после подключения обоих игроков
        await bot.send_message(message.chat.id, "Ты присоединился к игре. Игра начинается!")

        # Отправка шахматной доски обоим игрокам
        for player in games[game_code]["players"]:
            keyboard = generate_chessboard_inline_keyboard(games[game_code]["board"])
            await bot.send_message(player, "Шахматная доска:", reply_markup=keyboard)
    else:
        await message.reply("Игра с таким кодом не найдена или уже занята.")


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
            [" "] * 8,  # 6
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

    # Поиск активной игры, в которой участвует пользователь
    active_game = None
    for game_code, game_data in games.items():
        if user_id in game_data["players"]:
            active_game = game_data
            break

    if not active_game:
        await callback_query.answer("Сначала начните игру с другом.")
        return

    board = active_game["board"]
    selected_piece = user_board_states.get(user_id, {}).get("selected_piece", None)
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
        user_board_states[user_id] = {"selected_piece": (rank, file)}
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

            # Обновление клавиатуры для обоих игроков
            keyboard = generate_chessboard_inline_keyboard(board)
            for player in active_game["players"]:
                await bot.edit_message_reply_markup(chat_id=player, message_id=callback_query.message.message_id,
                                                    reply_markup=keyboard)
async def main():
    await dp.start_polling(bot)
# Запуск бота
if __name__ == '__main__':
    asyncio.run(main())
