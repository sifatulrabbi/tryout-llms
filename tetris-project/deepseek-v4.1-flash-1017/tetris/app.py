from __future__ import annotations

import curses
import locale
import sys
import time

from .canvas import Canvas, Style
from .controller import Command, TetrisController
from .scores import FileHighScoreStore, HighScoreStore, default_high_score_path
from .ui import MIN_HEIGHT, MIN_WIDTH, render_scene

FRAME_MS = 16
MAX_FRAME_MS = 250.0


class Palette:
    def __init__(self) -> None:
        self._attrs: dict[Style, int] = {}
        if not curses.has_colors():
            self._init_without_color()
            return
        curses.start_color()
        try:
            curses.use_default_colors()
            background = -1
        except curses.error:
            background = curses.COLOR_BLACK
        if curses.COLORS >= 256:
            colors = {
                Style.BORDER: 240,
                Style.DIM: 245,
                Style.ACCENT: 51,
                Style.TITLE: 231,
                Style.GOLD: 220,
                Style.DANGER: 196,
                Style.I: 51,
                Style.J: 33,
                Style.L: 208,
                Style.O: 226,
                Style.S: 46,
                Style.T: 201,
                Style.Z: 196,
            }
        else:
            colors = {
                Style.BORDER: curses.COLOR_BLUE,
                Style.DIM: curses.COLOR_WHITE,
                Style.ACCENT: curses.COLOR_CYAN,
                Style.TITLE: curses.COLOR_WHITE,
                Style.GOLD: curses.COLOR_YELLOW,
                Style.DANGER: curses.COLOR_RED,
                Style.I: curses.COLOR_CYAN,
                Style.J: curses.COLOR_BLUE,
                Style.L: curses.COLOR_YELLOW,
                Style.O: curses.COLOR_YELLOW,
                Style.S: curses.COLOR_GREEN,
                Style.T: curses.COLOR_MAGENTA,
                Style.Z: curses.COLOR_RED,
            }
        for pair_number, (style, color) in enumerate(colors.items(), start=1):
            try:
                curses.init_pair(pair_number, color, background)
            except curses.error:
                self._init_without_color()
                return
            self._attrs[style] = curses.color_pair(pair_number)
        self._attrs[Style.PLAIN] = curses.A_NORMAL
        for style in (Style.TITLE, Style.ACCENT, Style.GOLD, Style.DANGER):
            self._attrs[style] |= curses.A_BOLD
        for style in (
            Style.I,
            Style.J,
            Style.L,
            Style.O,
            Style.S,
            Style.T,
            Style.Z,
        ):
            self._attrs[style] |= curses.A_BOLD
        if curses.COLORS < 256:
            self._attrs[Style.DIM] |= curses.A_DIM

    def _init_without_color(self) -> None:
        self._attrs = {style: curses.A_NORMAL for style in Style}
        self._attrs[Style.DIM] = curses.A_DIM
        self._attrs[Style.BORDER] = curses.A_DIM
        for style in (
            Style.TITLE,
            Style.ACCENT,
            Style.GOLD,
            Style.DANGER,
            Style.I,
            Style.J,
            Style.L,
            Style.O,
            Style.S,
            Style.T,
            Style.Z,
        ):
            self._attrs[style] = curses.A_BOLD

    def attr(self, style: Style, dim: bool = False) -> int:
        value = self._attrs.get(style, curses.A_NORMAL)
        if dim:
            value |= curses.A_DIM
        return value


def command_for_key(key: int) -> Command | None:
    if key in (curses.KEY_LEFT, ord("a"), ord("A"), ord("h"), ord("H")):
        return Command.MOVE_LEFT
    if key in (curses.KEY_RIGHT, ord("d"), ord("D"), ord("l"), ord("L")):
        return Command.MOVE_RIGHT
    if key in (curses.KEY_DOWN, ord("s"), ord("S"), ord("j"), ord("J")):
        return Command.SOFT_DROP
    if key in (
        curses.KEY_UP,
        ord("w"),
        ord("W"),
        ord("k"),
        ord("K"),
        ord("x"),
        ord("X"),
    ):
        return Command.ROTATE_CW
    if key in (ord("z"), ord("Z")):
        return Command.ROTATE_CCW
    if key == ord(" "):
        return Command.HARD_DROP
    if key in (ord("c"), ord("C")):
        return Command.HOLD
    if key in (27, ord("p"), ord("P")):
        return Command.PAUSE
    if key in (ord("r"), ord("R")):
        return Command.RESTART
    if key in (ord("q"), ord("Q"), 3):
        return Command.QUIT
    if key in (10, 13, curses.KEY_ENTER):
        return Command.CONFIRM
    return None


def paint(stdscr: curses.window, canvas: Canvas, palette: Palette) -> None:
    stdscr.erase()
    height, width = stdscr.getmaxyx()
    visible_height = min(canvas.height, height)
    visible_width = min(canvas.width, width)
    for row in range(visible_height):
        column = 0
        while column < visible_width:
            cell = canvas.cells[row][column]
            style = cell.style
            dim = cell.dim
            start = column
            chars = [cell.char]
            column += 1
            while column < visible_width:
                next_cell = canvas.cells[row][column]
                if next_cell.style is not style or next_cell.dim != dim:
                    break
                chars.append(next_cell.char)
                column += 1
            try:
                stdscr.addstr(row, start, "".join(chars), palette.attr(style, dim))
            except curses.error:
                pass
    stdscr.refresh()


def _run(stdscr: curses.window, store: HighScoreStore) -> None:
    try:
        curses.curs_set(0)
    except curses.error:
        pass
    try:
        curses.set_escdelay(25)
    except AttributeError:
        pass
    stdscr.keypad(True)
    stdscr.timeout(FRAME_MS)
    palette = Palette()
    controller = TetrisController(store)
    last_time = time.monotonic()

    while controller.running:
        now = time.monotonic()
        elapsed = min(MAX_FRAME_MS, max(0.0, (now - last_time) * 1000.0))
        last_time = now
        height, width = stdscr.getmaxyx()
        large_enough = width >= MIN_WIDTH and height >= MIN_HEIGHT
        if large_enough:
            controller.tick(elapsed)
        canvas = render_scene(
            width,
            height,
            controller.screen,
            controller.game,
            best=controller.best,
            new_best=controller.new_best,
        )
        paint(stdscr, canvas, palette)

        key = stdscr.getch()
        if key == -1:
            continue
        if key == curses.KEY_RESIZE:
            stdscr.clear()
            last_time = time.monotonic()
            continue
        if not large_enough and key not in (ord("q"), ord("Q"), 3):
            continue
        command = command_for_key(key)
        if command is not None:
            controller.handle(command)


def main() -> int:
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        print(
            "Tetris needs an interactive terminal. Run `python3 -m tetris` "
            "from a terminal window.",
            file=sys.stderr,
        )
        return 1
    locale.setlocale(locale.LC_ALL, "")
    store = FileHighScoreStore(default_high_score_path())
    try:
        curses.wrapper(_run, store)
    except KeyboardInterrupt:
        return 130
    except curses.error as error:
        print(f"Terminal error: {error}", file=sys.stderr)
        return 1
    return 0
