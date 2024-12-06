from enum import Enum, auto
from typing import Literal, Optional

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton





Color = Literal[0, 1]
Offset = tuple[int, int]
alp = list('abcdefgh')


class FigureType(Enum):
    pawn = auto()
    rook = auto()
    knight = auto()
    bishop = auto()
    queen = auto()
    king = auto()


class Figure:
    def __init__(self, f_type: FigureType, color: Color) -> None:
        self.type: FigureType = f_type
        self.color: Color = color

    def get_pic(self) -> str:
        match self.type, self.color:
            case FigureType.pawn, 0:
                return '♙'
            case FigureType.pawn, 1:
                return '♟'
            case FigureType.rook, 0:
                return '♖'
            case FigureType.rook, 1:
                return '♜'
            case FigureType.knight, 0:
                return '♘'
            case FigureType.knight, 1:
                return '♞'
            case FigureType.bishop, 0:
                return '♗'
            case FigureType.bishop, 1:
                return '♝'
            case FigureType.queen, 0:
                return '♕'
            case FigureType.queen, 1:
                return '♛'
            case FigureType.king, 0:
                return '♔'
            case FigureType.king, 1:
                return '♚'

    def get_moves_offsets(self) -> list[Offset]:

        def get_rook(ran: int = 7):
            vertical = [(0, y) for y in range(-ran, ran + 1)]
            horizontal = [(x, 0) for x in range(-ran, ran + 1)]
            vertical.remove((0, 0))
            horizontal.remove((0, 0))
            return vertical + horizontal

        def get_bishop(ran: int = 7):
            one = [(i, i) for i in range(-ran, ran + 1)]
            two = [(i, -i) for i in range(-ran, ran + 1)]
            one.remove((0, 0))
            two.remove((0, 0))
            return one + two

        match self.type:
            case FigureType.knight:
                return [(1, 2), (2, 1), (-1, -2), (-2, -1), (1, -2), (-1, 2), (2, -1), (-2, 1)]
            case FigureType.rook:
                return get_rook()
            case FigureType.bishop:
                return get_bishop()
            case FigureType.queen:
                return get_bishop() + get_rook()
            case FigureType.king:
                return get_bishop(1) + get_rook(1)
            case FigureType.pawn:  # ходы пешки ситуативные, поэтому написаны не здесь
                return []


class Cell:
    def __init__(self, let: str, num: int, figure: Figure = None) -> None:
        self.letter: str = let
        self.number: int = num
        self.figure: Figure = figure

    def get_id(self) -> str:
        return f'{self.letter}{self.number}'

    def __str__(self):
        return self.get_id()

    def __repr__(self):
        return str(self) + (str(self.figure.type.name) if self.figure is not None else '')


class CastlingState(Enum):
    two = auto()  # разрешены обе
    left = auto()  # разрешена левая
    right = auto()  # разрешена правая
    null = auto()  # не разрешена


class Board:
    def generate(self) -> None:
        figures = (FigureType.rook, FigureType.knight, FigureType.bishop, FigureType.queen, FigureType.king, FigureType.bishop, FigureType.knight, FigureType.rook)
        for n in range(8, 0, -1):
            line = []
            for l in alp:
                figure = None
                if n == 7:
                    figure = Figure(FigureType.pawn, 1)
                elif n == 2:
                    figure = Figure(FigureType.pawn, 0)
                elif n == 8:
                    figure = Figure(figures[alp.index(l)], 1)
                elif n == 1:
                    figure = Figure(figures[alp.index(l)], 0)
                line.append(Cell(l, n, figure))
            self.cells.append(line)

    def get_board(self, color: Color) -> InlineKeyboardMarkup:
        inline_keyboard = []

        cells = self.cells if color == 0 else reversed(self.cells)
        for row in cells:
            row_buttons = []
            final_row = row if color == 0 else reversed(row)
            for cell in final_row:
                pic = cell.figure.get_pic() if cell.figure is not None else ' '
                row_buttons.append(InlineKeyboardButton(text=pic, callback_data=f'{self.id}:{cell.get_id()}'))
            inline_keyboard.append(row_buttons)
        return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

    def get_cell(self, cell_id: str) -> Optional[Cell]:
        let, num = cell_id[0], cell_id[1]
        if num.isdigit():
            num = int(num)
        else:
            return None
        if let not in alp or num not in range(1, 9):
            return None

        return self.cells[8 - num][alp.index(let)]

    def get_cells_between(self, first: Cell, second: Cell) -> tuple[Cell, ...]:
        step1 = 1 if ord(first.letter) < ord(second.letter) else -1
        step2 = 1 if first.number < second.number else -1

        if first.letter != second.letter and first.number != second.number:
            return tuple(self.get_cell(f'{let}{num}') for let, num in zip(
                (chr(j) for j in range(ord(first.letter) + step1, ord(second.letter), step1)),
                range(first.number + step2, second.number, step2)
                )
            )
        elif first.letter == second.letter:
            return tuple(self.get_cell(f'{first.letter}{num}') for num in range(first.number + step2, second.number, step2))
        elif first.number == second.number:
            return tuple(self.get_cell(f'{chr(let)}{first.number}') for let in range(ord(first.letter) + step1, ord(second.letter), step1))

    def get_list_cells(self) -> list[Cell]:
        cells: list[Cell] = []
        for i in self.cells:
            cells += i
        return cells

    def get_available_moves(self, cell: Cell) -> list[Cell]:
        result = []
        for offset in cell.figure.get_moves_offsets():
            move_cell = self.get_cell(f'{chr(ord(cell.letter) + offset[0])}{cell.number + offset[1]}')
            if move_cell is None:
                continue
            if cell.figure.type is FigureType.knight:
                result.append(move_cell)
            else:
                if all(map(lambda c: c.figure is None, self.get_cells_between(cell, move_cell))):
                    result.append(move_cell)
        return result

    def validaion_move(self, id_from: str, id_to: str) -> bool:
        cell = self.get_cell(id_from)
        to = self.get_cell(id_to)
        if cell is None or to is None:
            return False
        if cell.figure is None:
            return False

        a_moves = self.get_available_moves(cell)
        if cell.figure.type not in (FigureType.pawn, FigureType.king):
            return to in a_moves
        else:
            if to in a_moves:
                return True
            else:
                if cell.figure.type is FigureType.pawn:
                    if cell.figure.color == 0:
                        if to.number == cell.number + 1 and to.letter == cell.letter and to.figure is None:
                            return True
                        elif cell.number == 2 and to.number == 4 and to.letter == cell.letter and to.figure is None and self.get_cell(f'{cell.letter}{3}').figure is None:
                            return True
                        elif to.figure is not None and to.figure.color == 1 and to.number == cell.number + 1 and (to.letter == chr(ord(cell.letter) - 1) or to.letter == chr(ord(cell.letter) + 1)):
                            return True
                    if cell.figure.color == 1:
                        if to.number == cell.number - 1 and to.letter == cell.letter and to.figure is None:
                            return True
                        elif cell.number == 7 and to.number == 5 and to.letter == cell.letter and to.figure is None and self.get_cell(f'{cell.letter}{6}').figure is None:
                            return True
                        elif to.figure is not None and to.figure.color == 0 and to.number == cell.number - 1 and (to.letter == chr(ord(cell.letter) - 1) or to.letter == chr(ord(cell.letter) + 1)):
                            return True
                elif cell.figure.type is FigureType.king:
                    castle = self.white_castling if cell.figure.color == 0 else self.black_castling
                    if castle in (CastlingState.two, CastlingState.left) and to.letter == 'c' and all(map(lambda c: c.figure is None, self.get_cells_between(cell, self.get_cell(f'a{cell.number}')))):
                        return True
                    elif castle in (CastlingState.two, CastlingState.right) and to.letter == 'g' and all(map(lambda c: c.figure is None, self.get_cells_between(cell, self.get_cell(f'h{cell.number}')))):
                        return True
        return False

    def __init__(self, id: int) -> None:
        self.cells: list[list[Cell]] = []
        self.id: int = id
        self.white_castling: CastlingState = CastlingState.two
        self.black_castling: CastlingState = CastlingState.two
        self.generate()
