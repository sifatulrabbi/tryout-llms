from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class Style(Enum):
    PLAIN = auto()
    DIM = auto()
    BORDER = auto()
    ACCENT = auto()
    TITLE = auto()
    GOLD = auto()
    DANGER = auto()
    I = auto()
    J = auto()
    L = auto()
    O = auto()
    S = auto()
    T = auto()
    Z = auto()


@dataclass(frozen=True, slots=True)
class Cell:
    char: str = " "
    style: Style = Style.PLAIN
    dim: bool = False


class Canvas:
    def __init__(self, width: int, height: int) -> None:
        if width < 0 or height < 0:
            raise ValueError("canvas dimensions cannot be negative")
        self.width = width
        self.height = height
        self.cells: list[list[Cell]] = [
            [Cell() for _ in range(width)] for _ in range(height)
        ]

    def set(
        self,
        x: int,
        y: int,
        char: str,
        style: Style = Style.PLAIN,
        *,
        dim: bool = False,
    ) -> None:
        if len(char) != 1:
            raise ValueError("canvas cells hold exactly one character")
        if 0 <= x < self.width and 0 <= y < self.height:
            self.cells[y][x] = Cell(char, style, dim)

    def write(
        self,
        x: int,
        y: int,
        text: str,
        style: Style = Style.PLAIN,
        *,
        dim: bool = False,
    ) -> None:
        for offset, char in enumerate(text):
            self.set(x + offset, y, char, style, dim=dim)

    def fill(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        char: str = " ",
        style: Style = Style.PLAIN,
        *,
        dim: bool = False,
    ) -> None:
        for row in range(y, y + height):
            for column in range(x, x + width):
                self.set(column, row, char, style, dim=dim)

    def box(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        *,
        style: Style = Style.BORDER,
        title: str = "",
        title_style: Style = Style.TITLE,
        double: bool = False,
    ) -> None:
        if width < 2 or height < 2:
            return
        if double:
            top_left, top_right, bottom_left, bottom_right = "╔", "╗", "╚", "╝"
            horizontal, vertical = "═", "║"
        else:
            top_left, top_right, bottom_left, bottom_right = "┌", "┐", "└", "┘"
            horizontal, vertical = "─", "│"

        self.set(x, y, top_left, style)
        self.set(x + width - 1, y, top_right, style)
        self.set(x, y + height - 1, bottom_left, style)
        self.set(x + width - 1, y + height - 1, bottom_right, style)
        for column in range(x + 1, x + width - 1):
            self.set(column, y, horizontal, style)
            self.set(column, y + height - 1, horizontal, style)
        for row in range(y + 1, y + height - 1):
            self.set(x, row, vertical, style)
            self.set(x + width - 1, row, vertical, style)

        if title and width >= len(title) + 5:
            self.write(x + 2, y, f" {title} ", title_style)

    def set_dim(self, x: int, y: int, dim: bool = True) -> None:
        if 0 <= x < self.width and 0 <= y < self.height:
            cell = self.cells[y][x]
            self.cells[y][x] = Cell(cell.char, cell.style, dim)

    def dim_all(self) -> None:
        for row in self.cells:
            for index, cell in enumerate(row):
                row[index] = Cell(cell.char, cell.style, True)

    def text_row(self, y: int) -> str:
        return "".join(cell.char for cell in self.cells[y])

    def to_text(self) -> str:
        return "\n".join(self.text_row(y) for y in range(self.height))
