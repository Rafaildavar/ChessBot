from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

statistic_button = InlineKeyboardButton(text="⚔️📈Игровая статистика", callback_data="statistics")
rank_button = InlineKeyboardButton(text="🎖Рейтинговая игра", callback_data="rank_game")
public_button = InlineKeyboardButton(text="⚔️Обычная игра", callback_data="public_game")
profile_button = InlineKeyboardButton(text="👤Мой профиль", callback_data="profile")
clan_button = InlineKeyboardButton(text="🛡Кланы", callback_data="clan")
friend_game_button = InlineKeyboardButton(text="🎫Приватная игра", callback_data="friendGame")
setting_button = InlineKeyboardButton(text="🛠Настройки", callback_data="setting")
top100_button = InlineKeyboardButton(text="🏆Топ 100 игроков", callback_data="top100")
shop_button = InlineKeyboardButton(text="💰Магазин", callback_data="shop")
myBalance_button = InlineKeyboardButton(text="💎Мой баланс", callback_data="myBalance")
feedback_button = InlineKeyboardButton(text="💬Оставить отзыв", callback_data="feedback")
ivents_button = InlineKeyboardButton(text="⛩События", callback_data="event")

main_menu_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [profile_button],
        [clan_button, friend_game_button],
        [public_button, rank_button],
        [feedback_button, setting_button],
        [shop_button, myBalance_button],
        [ivents_button,top100_button],
        [statistic_button]
    ])
clan_actions = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Создать клан", callback_data="create_clan")],
    [InlineKeyboardButton(text="Вступить в клан", callback_data="join_clan")],
    [InlineKeyboardButton(text="Управление кланами", callback_data="manage_clan")]
])
stat_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Статистика обычных игр", callback_data="public_stat")],
    [InlineKeyboardButton(text="Статистика рейтинговых игр", callback_data="ranked_stat")],
    [InlineKeyboardButton(text="Общая статистика", callback_data="main_stat")],
    [InlineKeyboardButton(text="Статистика приватных игр", callback_data="private_stat")],
    [InlineKeyboardButton(text="Назад", callback_data="back_to_main_menu")]

])
