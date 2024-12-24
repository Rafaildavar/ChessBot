from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

statistic_button = InlineKeyboardButton(text="⚔️📈Игровая статистика", callback_data="statistics")
rank_button = InlineKeyboardButton(text="🎖Рейтинговая игра", callback_data="rank_game")
public_button = InlineKeyboardButton(text="⚔️Обычная игра", callback_data="public_game")
profile_button = InlineKeyboardButton(text="👤Мой профиль", callback_data="profile")
clan_button = InlineKeyboardButton(text="🛡Кланы", callback_data="clan")
friend_game_button = InlineKeyboardButton(text="🎫Приватная игра", callback_data="friendGame")
setting_button = InlineKeyboardButton(text="🛠Настройки", callback_data="setting")
top100_button = InlineKeyboardButton(text="🏆Таблица лидеров", callback_data="leadersTable")
shop_button = InlineKeyboardButton(text="💰Магазин", callback_data="shop")
myBalance_button = InlineKeyboardButton(text="💎Мой баланс", callback_data="myBalance")
feedback_button = InlineKeyboardButton(text="💬Оставить отзыв", callback_data="feedback")
events_button = InlineKeyboardButton(text="⛩События", callback_data="event")

main_menu_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [profile_button],
        [clan_button, friend_game_button],
        [public_button, rank_button],
        [feedback_button, setting_button],
        [shop_button, myBalance_button],
        [events_button,top100_button],
        [statistic_button]
    ])
clan_actions = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Создать клан", callback_data="create_clan")],
    [InlineKeyboardButton(text="Вступить в клан", callback_data="join_clan")],
    [InlineKeyboardButton(text="Управление кланами", callback_data="manage_clan")],
    [InlineKeyboardButton(text="Назад", callback_data="back_to_main_menu")]
])
stat_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Статистика обычных игр", callback_data="public_stat")],
    [InlineKeyboardButton(text="Статистика рейтинговых игр", callback_data="ranked_stat")],
    [InlineKeyboardButton(text="Общая статистика", callback_data="main_stat")],
    [InlineKeyboardButton(text="Статистика приватных игр", callback_data="private_stat")],
    [InlineKeyboardButton(text="Назад", callback_data="back_to_main_menu")]

])
keyboards = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Купить 50💎", callback_data="Bbuy_50")],
        [InlineKeyboardButton(text="Купить 100💎", callback_data="Bbuy_100")],
        [InlineKeyboardButton(text="Купить 500💎", callback_data="Bbuy_500")],
        [InlineKeyboardButton(text="Купить 1000💎", callback_data="Bbuy_1000")],
        [InlineKeyboardButton(text="Назад", callback_data="back_to_main_menu")]
    ])
# private_board = InlineKeyboardMarkup(inline_keyboard=[
#         [InlineKeyboardButton(text="Создать код для друга", callback_data="create")],
#         [InlineKeyboardButton(text="Ввести код приглашения", callback_data="get")],
#         [InlineKeyboardButton(text="Назад", callback_data="back_to_main_menu")]
#     ])

event_board = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💻 Релиз проекта", callback_data="release_event")],
        # [InlineKeyboardButton(text="❄️ Зимний фестиваль", callback_data="winter_festival")],
    ])

claim_gift_board = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text= "Забрать подарок", callback_data="claim_gift")]
     ])
menu_button = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Назад", callback_data="back_to_main_menu")]
     ])

leaders_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Топ 100 игроков по проценту побед", callback_data="top100")],
    [InlineKeyboardButton(text="Рейтинг игроков", callback_data="top100rang")] ,
    [InlineKeyboardButton(text="Рейтинг кланов", callback_data="top100clans")],
    [InlineKeyboardButton(text="Назад", callback_data="back_to_main_menu")]
     ])