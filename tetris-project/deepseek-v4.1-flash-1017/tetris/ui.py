from __future__ import annotations

from enum import Enum, auto

from .canvas import Canvas, Style
from .engine import BOARD_HEIGHT, BOARD_WIDTH, Game
from .pieces import SHAPES, Kind

MIN_WIDTH = 50
MIN_HEIGHT = 22
CONTENT_WIDTH = 50
CONTENT_HEIGHT = 22
BOARD_SIZE = 22
SIDEBAR_OFFSET = 24
SIDEBAR_WIDTH = 26

PIECE_STYLES: dict[Kind, Style] = {
    "I": Style.I,
    "J": Style.J,
    "L": Style.L,
    "O": Style.O,
    "S": Style.S,
    "T": Style.T,
    "Z": Style.Z,
}

CLEAR_NAMES = {1: "SINGLE", 2: "DOUBLE", 3: "TRIPLE", 4: "TETRIS"}

LOGO_GLYPHS = {
    "T": ("████", " ██ ", " ██ ", " ██ ", " ██ "),
    "E": ("████", "█   ", "███ ", "█   ", "████"),
    "R": ("███ ", "█  █", "███ ", "█ █ ", "█  █"),
    "I": ("███", " █ ", " █ ", " █ ", "███"),
    "S": ("████", "█   ", "████", "   █", "████"),
}

LOGO_LETTERS = (
    ("T", Style.T),
    ("E", Style.L),
    ("T", Style.T),
    ("R", Style.S),
    ("I", Style.I),
    ("S", Style.Z),
)


class Screen(Enum):
    MENU = auto()
    PLAYING = auto()
    PAUSED = auto()
    GAME_OVER = auto()


def render_scene(
    width: int,
    height: int,
    screen: Screen,
    game: Game | None = None,
    *,
    best: int = 0,
    new_best: bool = False,
) -> Canvas:
    canvas = Canvas(width, height)
    if width < MIN_WIDTH or height < MIN_HEIGHT:
        _render_too_small(canvas)
        return canvas
    if screen is Screen.MENU:
        _render_menu(canvas, best)
        return canvas
    if game is None:
        raise ValueError("game is required outside the menu")
    _render_game(canvas, game, screen, best)
    if screen is Screen.PAUSED:
        _render_pause_overlay(canvas)
    elif screen is Screen.GAME_OVER:
        _render_game_over_overlay(canvas, game, best, new_best)
    return canvas


def _content_origin(width: int, height: int) -> tuple[int, int]:
    return (
        (width - CONTENT_WIDTH) // 2,
        (height - CONTENT_HEIGHT) // 2,
    )


def _render_game(canvas: Canvas, game: Game, screen: Screen, best: int) -> None:
    x, y = _content_origin(canvas.width, canvas.height)
    _render_board(canvas, game, x, y, screen)
    _render_sidebar(canvas, game, x + SIDEBAR_OFFSET, y, best, screen)


def _render_board(canvas: Canvas, game: Game, x: int, y: int, screen: Screen) -> None:
    canvas.box(x, y, BOARD_SIZE, BOARD_SIZE)
    if screen is not Screen.GAME_OVER:
        ghost = game.ghost_piece()
        for column, row in ghost.cells:
            if 0 <= row < BOARD_HEIGHT and 0 <= column < BOARD_WIDTH:
                canvas.write(
                    x + 1 + column * 2,
                    y + 1 + row,
                    "░░",
                    PIECE_STYLES[ghost.kind],
                    dim=True,
                )
    for row in range(BOARD_HEIGHT):
        for column in range(BOARD_WIDTH):
            kind = game.board[row][column]
            if kind is not None:
                canvas.write(
                    x + 1 + column * 2,
                    y + 1 + row,
                    "██",
                    PIECE_STYLES[kind],
                )
    if screen is not Screen.GAME_OVER:
        for column, row in game.current.cells:
            if 0 <= row < BOARD_HEIGHT and 0 <= column < BOARD_WIDTH:
                canvas.write(
                    x + 1 + column * 2,
                    y + 1 + row,
                    "██",
                    PIECE_STYLES[game.current.kind],
                )


def _render_sidebar(
    canvas: Canvas,
    game: Game,
    x: int,
    y: int,
    best: int,
    screen: Screen,
) -> None:
    canvas.box(x, y, SIDEBAR_WIDTH, BOARD_SIZE, title="TETRIS")
    inner_x = x + 1

    canvas.write(inner_x + 2, y + 1, "NEXT", Style.DIM)
    for index, kind in enumerate(game.next_queue):
        _draw_mini_piece(canvas, kind, inner_x + 2 + index * 5, y + 2)

    canvas.write(inner_x + 2, y + 5, "HOLD", Style.DIM)
    if game.hold is None:
        canvas.write(inner_x + 3, y + 6, "····", Style.DIM)
    else:
        _draw_mini_piece(canvas, game.hold, inner_x + 2, y + 6)

    for column in range(inner_x + 2, inner_x + 22):
        canvas.set(column, y + 8, "─", Style.BORDER, dim=True)

    canvas.write(inner_x + 2, y + 9, "SCORE", Style.DIM)
    _write_right(
        canvas, inner_x + 2, inner_x + 22, y + 10, f"{game.score:,}", Style.TITLE
    )

    canvas.write(inner_x + 2, y + 11, "LEVEL", Style.DIM)
    canvas.write(inner_x + 8, y + 11, f"{game.level:02d}", Style.TITLE)
    canvas.write(inner_x + 14, y + 11, "LINES", Style.DIM)
    canvas.write(inner_x + 20, y + 11, f"{game.lines:03d}", Style.TITLE)

    canvas.write(inner_x + 2, y + 12, "BEST", Style.DIM)
    _write_right(canvas, inner_x + 2, inner_x + 22, y + 12, f"{best:,}", Style.GOLD)

    _draw_binding(canvas, inner_x + 2, y + 14, "←→", "MOVE")
    _draw_binding(canvas, inner_x + 12, y + 14, "↓", "SOFT DROP")
    _draw_binding(canvas, inner_x + 2, y + 15, "↑/X", "ROTATE")
    _draw_binding(canvas, inner_x + 14, y + 15, "Z", "CCW")
    _draw_binding(canvas, inner_x + 2, y + 16, "SPACE", "HARD DROP")
    _draw_binding(canvas, inner_x + 2, y + 17, "C", "HOLD")
    _draw_binding(canvas, inner_x + 14, y + 17, "P", "PAUSE")
    _draw_binding(canvas, inner_x + 2, y + 18, "R", "RESTART")
    _draw_binding(canvas, inner_x + 14, y + 18, "Q", "QUIT")

    status, status_style = _status_line(game, screen)
    canvas.write(inner_x + 2, y + 20, status, status_style)


def _status_line(game: Game, screen: Screen) -> tuple[str, Style]:
    if screen is Screen.GAME_OVER:
        return "TOP OUT", Style.DANGER
    if game.last_clear:
        name = CLEAR_NAMES[game.last_clear]
        return f"{name}  +{game.last_clear_points:,}", Style.ACCENT
    if game.combo > 0:
        return f"COMBO x{game.combo + 1}", Style.GOLD
    return "STAY SHARP", Style.DIM


def _draw_binding(canvas: Canvas, x: int, y: int, key: str, action: str) -> None:
    canvas.write(x, y, key, Style.ACCENT)
    canvas.write(x + len(key) + 1, y, action, Style.DIM)


def _draw_mini_piece(canvas: Canvas, kind: Kind, x: int, y: int) -> None:
    cells = SHAPES[kind][0]
    min_x = min(column for column, _ in cells)
    min_y = min(row for _, row in cells)
    max_x = max(column for column, _ in cells)
    max_y = max(row for _, row in cells)
    width = max_x - min_x + 1
    height = max_y - min_y + 1
    offset_x = (4 - width + 1) // 2
    offset_y = (2 - height + 1) // 2
    for column, row in cells:
        canvas.set(
            x + offset_x + column - min_x,
            y + offset_y + row - min_y,
            "█",
            PIECE_STYLES[kind],
        )


def _write_right(
    canvas: Canvas,
    left: int,
    right: int,
    y: int,
    text: str,
    style: Style,
) -> None:
    start = max(left, right - len(text))
    canvas.write(start, y, text, style)


def _render_menu(canvas: Canvas, best: int) -> None:
    card_width = 48
    card_height = 18
    x = (canvas.width - card_width) // 2
    y = (canvas.height - card_height) // 2
    canvas.box(
        x,
        y,
        card_width,
        card_height,
        style=Style.ACCENT,
        double=True,
    )

    logo_x = x + (card_width - 28) // 2
    _draw_logo(canvas, logo_x, y + 2)
    _center(canvas, x, card_width, y + 8, "STACK. CLEAR. SURVIVE.", Style.DIM)
    _center(canvas, x, card_width, y + 10, "PRESS ENTER TO START", Style.TITLE)

    if best > 0:
        _center(canvas, x, card_width, y + 12, f"BEST  {best:,}", Style.GOLD)
    else:
        _center(canvas, x, card_width, y + 12, "NO HIGH SCORE YET", Style.DIM)

    _center(
        canvas,
        x,
        card_width,
        y + 14,
        "ARROWS MOVE   SPACE DROP   C HOLD",
        Style.DIM,
    )
    _center(canvas, x, card_width, y + 15, "Q  QUIT", Style.DIM)


def _draw_logo(canvas: Canvas, x: int, y: int) -> None:
    cursor = x
    for letter, style in LOGO_LETTERS:
        glyph = LOGO_GLYPHS[letter]
        for row, line in enumerate(glyph):
            for column, char in enumerate(line):
                if char != " ":
                    canvas.set(cursor + column, y + row, char, style)
        cursor += len(glyph[0]) + 1


def _center(
    canvas: Canvas,
    card_x: int,
    card_width: int,
    y: int,
    text: str,
    style: Style,
) -> None:
    canvas.write(card_x + (card_width - len(text)) // 2, y, text, style)


def _overlay_card(
    canvas: Canvas,
    width: int,
    height: int,
    title: str,
    title_style: Style = Style.TITLE,
) -> tuple[int, int]:
    content_x, content_y = _content_origin(canvas.width, canvas.height)
    x = content_x
    y = content_y + (CONTENT_HEIGHT - height) // 2
    canvas.dim_all()
    canvas.fill(x + 1, y + 1, width - 2, height - 2, " ", Style.PLAIN)
    canvas.box(
        x,
        y,
        width,
        height,
        style=Style.BORDER,
        title=title,
        title_style=title_style,
        double=True,
    )
    return x, y


def _render_pause_overlay(canvas: Canvas) -> None:
    width = 22
    height = 7
    x, y = _overlay_card(canvas, width, height, "PAUSED")
    _center(canvas, x, width, y + 2, "TAKE A BREATH", Style.DIM)
    _center(canvas, x, width, y + 4, "P / ENTER  RESUME", Style.TITLE)
    _center(canvas, x, width, y + 5, "R RESTART   Q QUIT", Style.DIM)


def _render_game_over_overlay(
    canvas: Canvas, game: Game, best: int, new_best: bool
) -> None:
    width = 22
    height = 10
    x, y = _overlay_card(
        canvas,
        width,
        height,
        "GAME OVER",
        title_style=Style.DANGER,
    )
    _stat_row(canvas, x, width, y + 2, "SCORE", f"{game.score:,}", Style.TITLE)
    _stat_row(canvas, x, width, y + 3, "BEST", f"{best:,}", Style.GOLD)
    if new_best:
        _center(canvas, x, width, y + 4, "NEW HIGH SCORE", Style.ACCENT)
    _center(canvas, x, width, y + 6, "ENTER  RESTART", Style.ACCENT)
    _center(canvas, x, width, y + 7, "Q  QUIT", Style.DIM)


def _stat_row(
    canvas: Canvas,
    card_x: int,
    card_width: int,
    y: int,
    label: str,
    value: str,
    style: Style,
) -> None:
    canvas.write(card_x + 3, y, label, Style.DIM)
    _write_right(canvas, card_x + 3, card_x + card_width - 2, y, value, style)


def _render_too_small(canvas: Canvas) -> None:
    _center(
        canvas,
        0,
        canvas.width,
        max(0, canvas.height // 2 - 1),
        "TERMINAL TOO SMALL",
        Style.DANGER,
    )
    _center(
        canvas,
        0,
        canvas.width,
        max(0, canvas.height // 2 + 1),
        f"NEED {MIN_WIDTH} X {MIN_HEIGHT}",
        Style.DIM,
    )
    _center(
        canvas,
        0,
        canvas.width,
        max(0, canvas.height // 2 + 2),
        f"NOW  {canvas.width} X {canvas.height}",
        Style.DIM,
    )
