from datetime import datetime, timedelta

from aiogram import F
from aiogram import Router
from aiogram import types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy import and_
from sqlalchemy.future import select


from aiogram.types import ContentType
from database.db import User, Feedback, Statistic
from database.db import session_maker
from gameLogic.game import Lobby
from kbds.State import FeedbackState, ProfileState
from kbds.inline import main_menu_keyboard
from utils.game_relation import lobbies, games
from utils.game_relation import send_board

message_router = Router()


#Обработчик message для команды Старт
@message_router.message(Command('start'))
async def start_command(message: types.Message):
    await message.answer("Привет! Давай сыграем в шахматы?")
    await message.answer("Нажми кнопку, чтобы начать:", reply_markup=main_menu_keyboard)
#Обработчик message для команды Старт
@message_router.message(Command('start'))
async def back_to_main(message: types.Message):

    await message.answer("Нажми кнопку, чтобы начать:", reply_markup=main_menu_keyboard)


#Обработчик для профиля
@message_router.message(ProfileState.waiting_for_username)
async def process_username(message: types.Message, state: FSMContext):
    await state.update_data(username=message.text)
    username = message.text
    user_id = message.from_user.id
    async with session_maker() as session:
        try:
            # Сохраняем профиль в базу данных
            user = User(user_id=user_id, username=username)
            states = Statistic(user_id = user_id,username=username)

            session.add(user)
            session.add(states)

            await session.commit()

            await message.answer(
                f"Ваш профиль создан!\n"
                f"Имя пользователя: {username}\n"
            )

        except Exception as e:
            await message.answer(f"Произошла ошибка: введите корректный username")
            print({str(e)})

    await state.clear()


#Обработчик callback_query для кнопки Оставить отзыв
@message_router.callback_query(F.data == 'feedback')
async def handle_feedback(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.answer("Пожалуйста, оставьте свой отзыв:")
    await state.set_state(FeedbackState.waiting_for_feedback)





#Обработчик message для команды Оставить отзыв
@message_router.message(FeedbackState.waiting_for_feedback)
async def save_feedback(message: types.Message, state: FSMContext):
    feedback_text = message.text
    user_id = message.from_user.id
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
            print("Текущий статус пользователя:", await state.get_state())
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


# # Получение кода игры от пользователя
# @message_router.message()
# async def handle_game_code(message: types.Message):
#     game_code: str = message.text.strip()
#     user_id: int = message.from_user.id
#     if len(game_code) != 5 or not game_code.isdigit():
#         return
#
#     lobby: Lobby = next(filter(lambda s_lobby: s_lobby.private and
#                                                s_lobby.private_code == game_code and
#                                                s_lobby.first_player != user_id,
#                                lobbies), None)
#     if lobby is None:
#         return
#
#     game = lobby.start_game(user_id)
#     lobbies.remove(lobby)
#     games.append(game)
#     await send_board(game)


@message_router.message(F.content_type == ContentType.SUCCESSFUL_PAYMENT)
async def successful_payment(message: types.Message):
    payment_info = message.successful_payment.total_amount # Получаем информацию о платеже
    amount =  payment_info // 100  # Сумма в рублях
    # payload = payment_info['invoice_payload']  # Полезная нагрузка

    await message.answer(f"Оплат на сумму {amount} рублей прошла успешно!")