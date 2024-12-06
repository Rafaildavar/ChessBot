from typing import Literal

from board import Board, FigureType, Figure, CastlingState


class Game:
    id_counter = 0

    def __init__(self, player1: int, player2: int) -> None:
        self.id = Game.id_counter
        Game.id_counter += 1

        self.white_player: int = player1
        self.black_player: int = player2
        self.turn: Literal[0, 1] = 0
        self.board: Board = Board(self.id)

        self.pressed_cell: str | None = None

    def click(self, cell_id: str) -> str | None:
        cell = self.board.get_cell(cell_id)
        if cell.figure is not None:
            if cell.figure.color == self.turn:
                self.pressed_cell = cell_id

            elif self.pressed_cell is not None:
                return self.move(cell_id)  # атака
            else:
                return 'Выберите свою фигуру!'
        else:
            if self.pressed_cell is None:
                return 'Выберите свою фигуру!'
            else:
                return self.move(cell_id)  # просто ход

    def move(self, to: str) -> str:
        if not self.board.validaion_move(self.pressed_cell, to):
            mes = f'Невозможный ход! ({self.pressed_cell}-{to})'
            self.pressed_cell = None
            return mes

        cell = self.board.get_cell(self.pressed_cell)
        cell2 = self.board.get_cell(to)

        if cell.figure.type is FigureType.king:
            if cell.figure.color == 0:
                self.board.white_castling = CastlingState.null
                if to == 'c1':
                    self.board.get_cell('a1').figure = None
                    self.board.get_cell('d1').figure = Figure(FigureType.rook, cell.figure.color)
                elif to == 'g1':
                    self.board.get_cell('h1').figure = None
                    self.board.get_cell('f1').figure = Figure(FigureType.rook, cell.figure.color)
            else:
                self.board.black_castling = CastlingState.null
                if to == 'c8':
                    self.board.get_cell('a8').figure = None
                    self.board.get_cell('d8').figure = Figure(FigureType.rook, cell.figure.color)
                elif to == 'g8':
                    self.board.get_cell('h8').figure = None
                    self.board.get_cell('f8').figure = Figure(FigureType.rook, cell.figure.color)

        if cell.figure.type is FigureType.rook:
            if cell.figure.color == 0:
                if cell.get_id() == 'a1':
                    if self.board.white_castling is CastlingState.two:
                        self.board.white_castling = CastlingState.right
                    else:
                        self.board.white_castling = CastlingState.null
                elif cell.get_id() == 'h1':
                    if self.board.white_castling is CastlingState.two:
                        self.board.white_castling = CastlingState.left
                    else:
                        self.board.white_castling = CastlingState.null
            elif cell.figure.color == 1:
                if cell.get_id() == 'a8':
                    if self.board.black_castling is CastlingState.two:
                        self.board.black_castling = CastlingState.right
                    else:
                        self.board.black_castling = CastlingState.null
                elif cell.get_id() == 'h8':
                    if self.board.black_castling is CastlingState.two:
                        self.board.black_castling = CastlingState.left
                    else:
                        self.board.black_castling = CastlingState.null

        cell2.figure = cell.figure
        cell.figure = None
        self.pressed_cell = None

        if cell2.figure.type is FigureType.pawn and (cell2.figure.color == 0 and cell2.number == 8) or (cell2.figure.color == 1 and cell2.number == 1):
            return 'Превращение'
        self.turn = (self.turn + 1) % 2

