from gameLogic.game import Game
import asyncio
from config import bot
from aiogram.fsm.context import FSMContext


games = []  # Список для хранения информации о созданных играх
lobbies = []  # Список лобби


async def get_game(callback, game_id: int) -> Game | None:
    game = next(filter(lambda g: g.id == game_id, games), None)
    if game is None:
        await callback.answer('Игра не существует')
        return
    return game


async def board_update( game: Game, outcome: bool = False) -> None:
    async with asyncio.TaskGroup() as tg:
        for player in (game.white_player, game.black_player):
            message_text = await game.get_outcome_message() if outcome else await game.get_message()
            # Проверяем, что текст сообщения не None
            if message_text is None:
                message_text = "Информация недоступна."  # или любое другое значение по умолчанию

            tg.create_task(
                bot.edit_message_text(
                    text=message_text,
                    message_id=player.message_board,
                    reply_markup=game.get_board(player is game.white_player,),
                    chat_id=player.player_id
                )
            )


async def send_board(game: Game) -> None:
    async def _send(splayer):
        message = await bot.send_message(
            text= await  game.get_message(),
                                         reply_markup= game.get_board(splayer is game.white_player),
                                         chat_id=splayer.player_id)
        splayer.message_board = message.message_id

    async with asyncio.TaskGroup() as tg:
        for player in (game.white_player, game.black_player):
            await tg.create_task(_send(player))