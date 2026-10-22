from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal, TypeAlias

Kind: TypeAlias = Literal["I", "J", "L", "O", "S", "T", "Z"]
Coordinate: TypeAlias = tuple[int, int]
Rotation: TypeAlias = int

KINDS: Final[tuple[Kind, ...]] = ("I", "J", "L", "O", "S", "T", "Z")

SHAPES: Final[dict[Kind, tuple[tuple[Coordinate, ...], ...]]] = {
    "I": (
        ((0, 1), (1, 1), (2, 1), (3, 1)),
        ((2, 0), (2, 1), (2, 2), (2, 3)),
        ((0, 2), (1, 2), (2, 2), (3, 2)),
        ((1, 0), (1, 1), (1, 2), (1, 3)),
    ),
    "J": (
        ((0, 0), (0, 1), (1, 1), (2, 1)),
        ((1, 0), (2, 0), (1, 1), (1, 2)),
        ((0, 1), (1, 1), (2, 1), (2, 2)),
        ((1, 0), (1, 1), (0, 2), (1, 2)),
    ),
    "L": (
        ((2, 0), (0, 1), (1, 1), (2, 1)),
        ((1, 0), (1, 1), (1, 2), (2, 2)),
        ((0, 1), (1, 1), (2, 1), (0, 2)),
        ((0, 0), (1, 0), (1, 1), (1, 2)),
    ),
    "O": (
        ((0, 0), (1, 0), (0, 1), (1, 1)),
        ((0, 0), (1, 0), (0, 1), (1, 1)),
        ((0, 0), (1, 0), (0, 1), (1, 1)),
        ((0, 0), (1, 0), (0, 1), (1, 1)),
    ),
    "S": (
        ((1, 0), (2, 0), (0, 1), (1, 1)),
        ((1, 0), (1, 1), (2, 1), (2, 2)),
        ((1, 1), (2, 1), (0, 2), (1, 2)),
        ((0, 0), (0, 1), (1, 1), (1, 2)),
    ),
    "T": (
        ((1, 0), (0, 1), (1, 1), (2, 1)),
        ((1, 0), (1, 1), (2, 1), (1, 2)),
        ((0, 1), (1, 1), (2, 1), (1, 2)),
        ((1, 0), (0, 1), (1, 1), (1, 2)),
    ),
    "Z": (
        ((0, 0), (1, 0), (1, 1), (2, 1)),
        ((2, 0), (1, 1), (2, 1), (1, 2)),
        ((0, 1), (1, 1), (1, 2), (2, 2)),
        ((1, 0), (0, 1), (1, 1), (0, 2)),
    ),
}

SPAWN_X: Final[dict[Kind, int]] = {
    "I": 3,
    "J": 3,
    "L": 3,
    "O": 4,
    "S": 3,
    "T": 3,
    "Z": 3,
}

SPAWN_Y: Final[int] = 0

KICKS_JLSTZ: Final[dict[tuple[int, int], tuple[Coordinate, ...]]] = {
    (0, 1): ((0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)),
    (1, 0): ((0, 0), (1, 0), (1, 1), (0, -2), (1, -2)),
    (1, 2): ((0, 0), (1, 0), (1, 1), (0, -2), (1, -2)),
    (2, 1): ((0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)),
    (2, 3): ((0, 0), (1, 0), (1, -1), (0, 2), (1, 2)),
    (3, 2): ((0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)),
    (3, 0): ((0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)),
    (0, 3): ((0, 0), (1, 0), (1, -1), (0, 2), (1, 2)),
}

KICKS_I: Final[dict[tuple[int, int], tuple[Coordinate, ...]]] = {
    (0, 1): ((0, 0), (-2, 0), (1, 0), (-2, 1), (1, -2)),
    (1, 0): ((0, 0), (2, 0), (-1, 0), (2, -1), (-1, 2)),
    (1, 2): ((0, 0), (-1, 0), (2, 0), (-1, -2), (2, 1)),
    (2, 1): ((0, 0), (1, 0), (-2, 0), (1, 2), (-2, -1)),
    (2, 3): ((0, 0), (2, 0), (-1, 0), (2, -1), (-1, 2)),
    (3, 2): ((0, 0), (-2, 0), (1, 0), (-2, 1), (1, -2)),
    (3, 0): ((0, 0), (1, 0), (-2, 0), (1, 2), (-2, -1)),
    (0, 3): ((0, 0), (-1, 0), (2, 0), (-1, -2), (2, 1)),
}

KICKS_O: Final[tuple[Coordinate, ...]] = ((0, 0),)


@dataclass(frozen=True, slots=True)
class Piece:
    kind: Kind
    rotation: int
    x: int
    y: int

    @property
    def cells(self) -> tuple[Coordinate, ...]:
        return tuple(
            (self.x + dx, self.y + dy)
            for dx, dy in SHAPES[self.kind][self.rotation % 4]
        )

    def moved(self, dx: int, dy: int) -> Piece:
        return Piece(self.kind, self.rotation, self.x + dx, self.y + dy)

    def rotated(self, direction: int) -> Piece:
        return Piece(self.kind, (self.rotation + direction) % 4, self.x, self.y)


def spawn_piece(kind: Kind) -> Piece:
    return Piece(kind=kind, rotation=0, x=SPAWN_X[kind], y=SPAWN_Y)


def kicks_for(
    kind: Kind, from_rotation: int, to_rotation: int
) -> tuple[Coordinate, ...]:
    if kind == "O":
        return KICKS_O
    table = KICKS_I if kind == "I" else KICKS_JLSTZ
    return table[(from_rotation % 4, to_rotation % 4)]
