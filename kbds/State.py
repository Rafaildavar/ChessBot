from aiogram.fsm.state import StatesGroup, State


# Состояния для FSM (машины состояний)
class ProfileState(StatesGroup):
    waiting_for_username = State()
    waiting_for_telegram_name = State()
class ClanState(StatesGroup):
    enter_name = State()
    confirm_join = State()

class PublicState(StatesGroup):
    waiting_for_pub = State()
    waiting_for_pub_game = State()

class FeedbackState(StatesGroup):
    waiting_for_feedback = State()

class PrivateState(StatesGroup):
    waiting_for_code = State()
    waiting_for_private = State()
    waiting_for_private_game = State()
    waiting_for_friend_join = State()