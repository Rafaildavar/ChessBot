import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram import F
from aiogram.fsm.storage.memory import MemoryStorage

TOKEN = 'token'  # Замените на ваш реальный токен
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Инициализация состояния доски и выбранной фигуры для каждого пользователя
user_board_states = {}


# Команда /start
@dp.message(Command('start'))
async def start_command(message: types.Message):
    await message.answer("Привет! Давай сыграем в шахматы?")
    start_button = InlineKeyboardButton(text="Начать игру", callback_data="start_game")

    # Добавим остальные кнопки для интерфейса
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[start_button]])
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

    # Отправка шахматной доски с текстовыми обозначениями
    await send_chessboard_with_labels(callback_query.from_user.id)


# Инициализация шахматной доски
def initialize_board(color):
    if color == 'черные':
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
    else:
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


# Отправка шахматной доски с текстовыми обозначениями
async def send_chessboard_with_labels(user_id):
    board = user_board_states[user_id]["board"]

    # Создаем строку с обозначениями файлов (A-H)
    file_labels = "  A B C D E F G H\n"

    # Формируем доску с номерами рангов (1-8)
    board_str = ""
    for rank in range(8):
        rank_str = f"{8 - rank} "  # Добавляем номер ранга в начале строки
        for file in range(8):
            piece = board[rank][file]
            rank_str += f"{piece} "  # Добавляем фигуру и пробел
        board_str += rank_str + f"{8 - rank}\n"  # Добавляем номер ранга в конце строки

        # Добавляем обозначение файлов внизу
    board_str += file_labels

    # Отправляем доску пользователю
    await bot.send_message(user_id, f"Шахматная доска:\n{board_str}")

    # Отправляем клавиатуру для взаимодействия с доской
    keyboard = generate_chessboard_inline_keyboard(board)
    await bot.send_message(user_id, "Сделай ход:", reply_markup=keyboard)


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
            # Обновление доски и клавиатуры
            await send_chessboard_with_labels(user_id)
            await callback_query.answer(f"Фигура перемещена на {chr(65 + file)}{8 - rank}")
        else:
            await callback_query.answer("Сначала выберите фигуру для перемещения.")


# Запуск бота
async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())