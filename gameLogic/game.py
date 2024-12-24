import random
import asyncio
from typing import Literal, Final, Optional
import chess
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


from database.orm_query import get_user_name, update_user_attributes, get_item_id

alp: Final[list[str]] = list('abcdefgh')

lobby_codes: set = set()

private_log = False
rang_log = False

# Пример асинхронной функции
# async def get_user_name1(player_id: int) -> str:
#     # Здесь должна быть логика получения имени пользователя
#     await asyncio.sleep(1)  # Имитация асинхронной операции
#     return f" {player_id}"






class Player:
    def __init__(self, player_id: int, message_id: int = None) -> None:
        self.player_id: int = player_id
        self.message_board: int = message_id
        self.private: bool = False
        self.rang: bool = False

    def run_get_user_name(self):
        return asyncio.run(get_user_name(self.player_id))

class Game:
    id_counter = 0

    def __init__(self, player1_id: int, player2_id: int, title: str = 'Обычная игра 🏁') -> None:
        self.id = Game.id_counter
        Game.id_counter += 1

        self.white_player: Player = Player(player1_id)
        self.black_player: Player = Player(player2_id)
        self.board: chess.Board = chess.Board()
        self.choosing_shape: Literal[-1, 0, 1] = -1
        self.title: str = title

        self.pressed_cell: Optional[str] = None
    def get_board(self, color: bool) -> InlineKeyboardMarkup:
        # color = 0 if color else 1
        inline_keyboard = []

        lines = ''.join(list(map(lambda s: int(s) * '0' if s.isdigit() else s, list(self.board.board_fen())))).split('/')

        lines, num = (lines, range(8, 0, -1)) if color else (reversed(lines), range(1, 9))

        for row, n in zip(lines, num):
            row_buttons = []
            final_row, t_alp = (list(row), alp) if color else (reversed(list(row)), reversed(alp))
            for cell, l in zip(final_row, t_alp):

                row_buttons.append(InlineKeyboardButton(
                    text=chess.UNICODE_PIECE_SYMBOLS[cell] if cell in chess.UNICODE_PIECE_SYMBOLS else ' ',
                    callback_data=f'{self.id}:{l}{n}'))
            inline_keyboard.append(row_buttons)
        return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

    def click(self, cell_id: str, user_id: int) -> tuple[Optional[str], bool]:
        piece: chess.Piece = self.board.piece_at(chess.parse_square(cell_id))

        if user_id != (self.white_player if self.board.turn else self.black_player).player_id:
            return 'Сейчас не ваш ход!', False

        if piece is not None:
            # piece.color = 0 if piece.color else 1
            if piece.color == self.board.turn:

                self.pressed_cell = cell_id
                return None, True
            elif self.pressed_cell is not None:
                return self.move(cell_id), True  # атака
            else:
                return 'Выберите свою фигуру!', False
        else:
            if self.pressed_cell is None:
                return 'Выберите свою фигуру!', False
            else:
                return self.move(cell_id), True  # просто ход

    def move(self, to: str) -> str:
        move: str = f'{self.pressed_cell}{to}'
        self.pressed_cell = None
        if move not in list(map(lambda move: move.uci()[:4], self.board.legal_moves)):
            mes = f'Невозможный ход! ({self.pressed_cell}{to})'
            return mes

        self.board.push(chess.Move.from_uci(move))

        if (self.board.turn and any((self.board.piece_type_at(square) is chess.PAWN for square in chess.SQUARES[:8]))) or \
           (not self.board.turn and any((self.board.piece_type_at(square) is chess.PAWN for square in chess.SQUARES[56:]))):
            self.choosing_shape = 1 if self.board.turn else 0
            return 'Превращение'


    async def get_message(self) -> str:
        white_name = await get_user_name(self.white_player.player_id)
        white_item = await get_item_id(self.black_player.player_id)
        black_name = await get_user_name(self.black_player.player_id)
        black_item = await get_item_id(self.black_player.player_id)



        return f'{self.title}\n' \
                   f'{white_name}{white_item}⬜ vs {black_name}{black_item}⬛\n' \
                   f'Ход: {"Белых⬜" if self.board.turn else "Чёрных⬛"}\n' \
                   f'{"Поставлен шах!" if self.board.is_check() else ""}\n' \
                   f'{f"Выбрана {self.pressed_cell}" if self.pressed_cell is not None else ""}'.strip()

    async def get_outcome_message(self) -> Optional[str]:
        white_name = await get_user_name(self.white_player.player_id)
        white_item = await get_item_id(self.black_player.player_id)
        black_name = await get_user_name(self.black_player.player_id)
        black_item = await get_item_id(self.black_player.player_id)
        outcome: chess.Outcome = self.board.outcome()
        if outcome is None:
            return

        match outcome.termination:
            case chess.Termination.CHECKMATE:
                message = 'Поставлен мат!'
            case chess.Termination.STALEMATE:
                message = 'Патовая ситуация.'
            case chess.Termination.INSUFFICIENT_MATERIAL:
                message = 'Недостаточно фигур!'
            case _:
                message = 'Конец игры'

        if outcome.winner is not None:
            # Определяем победителя
            winner = 'Победа ' + ('белых⬜!' if outcome.winner else 'чёрных⬛!')
            self.white_player.private = private_log
            self.black_player.private = private_log
            self.white_player.rang = rang_log
            self.black_player.rang = rang_log

            # Обновляем статистику в зависимости от победителя
            if outcome.winner:  # Если выиграли белые

                await update_user_attributes(self.white_player.player_id, winner,self.white_player.private,self.white_player.rang)
                await update_user_attributes(self.black_player.player_id, 'Поражение чёрных⬛!',self.black_player.private,self.black_player.rang)
            else:  # Если выиграли черные
                await update_user_attributes(self.white_player.player_id, 'Поражение белых⬜!',self.black_player.private,self.black_player.rang)
                await update_user_attributes(self.black_player.player_id, winner, self.white_player.private,self.white_player.rang)

        else:
            # Ничья
            winner = 'Ничья!'
            await update_user_attributes(self.white_player.player_id, winner,self.white_player.private,self.white_player.rang)
            await update_user_attributes(self.black_player.player_id, winner,self.black_player.private,self.black_player.rang)
        return f'Игра закончена!\n' \
               f'{white_name}{white_item}⬜ vs {black_name}{black_item}⬛\n' \
               f'{winner}\n' \
               f'{message}'


        # if outcome.winner is not None:
            # # if outcome.winner:
            # #     winner = 'Победа ' + 'белых⬜!'
            # #     await update_user_attributes(self.white_player.player_id,winner)
            # # else:
            # #     winner = 'Победа ' + 'чёрных⬛!'
            # #     await update_user_attributes(self.white_player.player_id, winner)



        # else:
        #     winner = 'Ничья!'
        #     # Ничья
        #     await update_user_attributes(self.white_player.player_id, winner)
        #     await update_user_attributes(self.black_player.player_id, winner)
        #
        # return f'Игра закончена!\n' \
        #            f'{black_name}⬜ vs {white_name}⬛\n' \
        #            f'{winner}\n' \
        #            f'{message}'




class Lobby:
    id_counter = 0

    def __init__(self, player_id: int, private: bool = False, rank: bool = False) -> None:
        self.id = Lobby.id_counter
        Lobby.id_counter += 1

        self.first_player: int = player_id
        self.private: bool = private
        self.rank: bool = rank
        if self.private:
            code = str(random.randint(10000, 99999))
            while code in lobby_codes:
                code = str(random.randint(10000, 99999))

            self.private_code = code
            lobby_codes.add(code)
        else:
            self.private_code = None

    def start_game(self, player2_id) -> Game:
        global private_log
        global rang_log
        if self.private_code:
            lobby_codes.remove(self.private_code)

        players = [self.first_player, player2_id]
        random.shuffle(players)
        rang_log = False
        private_log = False
        if self.private:
            title = 'Приватная игра 🤝'
            private_log = True
        elif self.rank:
            title = 'Ранговая игра 🏆'
            rang_log = True
        else:
            title = 'Обычная игра 🏁'
        return Game(*players, title=title)




