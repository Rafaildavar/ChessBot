import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram import F

TOKEN = '7735863677:AAELZ8O2QNCsQxkvDr0CMpqotJ7Xg4k7DiM'
bot = Bot(token=TOKEN)
dp = Dispatcher()


# Команда /start
@dp.message(Command('start'))
async def start_command(message: types.Message):
    await message.answer("Привет! Давай сыграем в шахматы?")
    start_button = InlineKeyboardButton(text="Начать игру", callback_data="start_game")
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
    await bot.send_message(callback_query.from_user.id, f"Ты выбрал {color} фигуры. Начинаем игру!")

    # Вызов функции генерации шахматного поля с учетом цвета
    keyboard = generate_chessboard(color)
    await bot.send_message(callback_query.from_user.id, "Шахматная доска:", reply_markup=keyboard)


# Генерация шахматного поля
def generate_chessboard(color):
    # Иконки фигур
    black_pieces = ["♜", "♞", "♝", "♛", "♚", "♝", "♞", "♜"]  # Черные фигуры
    white_pieces = ["♖", "♘", "♗", "♕", "♔", "♗", "♘", "♖"]  # Белые фигуры
    black_pawns = ["♟"] * 8  # Черные пешки
    white_pawns = ["♙"] * 8  # Белые пешки

    # Создаем список для клавиатуры
    inline_keyboard = []

    if color == 'черные':
        # Добавляем белые фигуры вверху
        inline_keyboard.append([InlineKeyboardButton(text=white_pieces[j], callback_data=f"piece_0_{j}") for j in range(8)])
        inline_keyboard.append([InlineKeyboardButton(text=white_pawns[j], callback_data=f"piece_1_{j}") for j in range(8)])

        # Добавляем пустые строки с кнопками для шахматного поля
        for i in range(4):  # Генерируем 4 строки для доски
            row_buttons = []
            for j in range(8):
                button_text = " "  # Текст кнопки (пустое пространство)
                button = InlineKeyboardButton(text=button_text, callback_data=f"move_{i + 2}_{j}")  # Создаем кнопку
                row_buttons.append(button)
            inline_keyboard.append(row_buttons)

        # Черные фигуры внизу
        inline_keyboard.append([InlineKeyboardButton(text=black_pawns[j], callback_data=f"piece_6_{j}") for j in range(8)])
        inline_keyboard.append([InlineKeyboardButton(text=black_pieces[j], callback_data=f"piece_7_{j}") for j in range(8)])

    else:
        # Черные фигуры вверху
        inline_keyboard.append([InlineKeyboardButton(text=black_pieces[j], callback_data=f"piece_0_{j}") for j in range(8)])
        inline_keyboard.append([InlineKeyboardButton(text=black_pawns[j], callback_data=f"piece_1_{j}") for j in range(8)])

        # Пустые строки с кнопками для шахматного поля
        for i in range(4):
            row_buttons = []
            for j in range(8):
                button_text = " "
                button = InlineKeyboardButton(text=button_text, callback_data=f"move_{i + 2}_{j}")
                row_buttons.append(button)
            inline_keyboard.append(row_buttons)

        # Белые фигуры внизу
        inline_keyboard.append([InlineKeyboardButton(text=white_pawns[j], callback_data=f"piece_6_{j}") for j in range(8)])
        inline_keyboard.append([InlineKeyboardButton(text=white_pieces[j], callback_data=f"piece_7_{j}") for j in range(8)])

    # Создаем клавиатуру с указанием inline_keyboard
    keyboard = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
    return keyboard


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())

