import curses
import time

from tetris_core import COLS, ROWS, SHAPES, COLORS, Game

BOARD_X = 2
BOARD_Y = 1
PANEL_X = BOARD_X + COLS * 2 + 5
MIN_WIDTH = PANEL_X + 22
MIN_HEIGHT = ROWS + 3

COLOR_MAP = {
    1: curses.COLOR_CYAN,
    2: curses.COLOR_YELLOW,
    3: curses.COLOR_MAGENTA,
    4: curses.COLOR_GREEN,
    5: curses.COLOR_RED,
    6: curses.COLOR_BLUE,
    7: curses.COLOR_WHITE,
}


def setup_colors(stdscr):
    if not curses.has_colors():
        return False
    curses.start_color()
    for pair, color in COLOR_MAP.items():
        curses.init_pair(pair, color, curses.COLOR_BLACK)
    return True


def cell_attr(pair, filled, colors):
    attr = 0
    if colors and pair:
        attr |= curses.color_pair(pair)
    if filled:
        attr |= curses.A_REVERSE
    return attr


def draw_board(stdscr, game, colors):
    for r in range(ROWS):
        for c in range(COLS):
            color = game.board.grid[r][c]
            stdscr.addstr(
                BOARD_Y + r,
                BOARD_X + 1 + c * 2,
                "  ",
                cell_attr(color, bool(color), colors),
            )

    r, c = game.piece_row, game.piece_col
    color = COLORS[game.current]
    for dr, dc in game.piece:
        rr, cc = r + dr, c + dc
        if 0 <= rr < ROWS:
            stdscr.addstr(
                BOARD_Y + rr,
                BOARD_X + 1 + cc * 2,
                "  ",
                cell_attr(color, True, colors),
            )

    ghost_row = r + game.drop_distance()
    for dr, dc in game.piece:
        rr = ghost_row + dr
        cc = c + dc
        if 0 <= rr < ROWS:
            stdscr.addstr(
                BOARD_Y + rr,
                BOARD_X + 1 + cc * 2,
                "▒▒",
                cell_attr(color, False, colors),
            )


def draw_border(stdscr):
    stdscr.addstr(BOARD_Y - 1, BOARD_X, "┌" + "─" * (COLS * 2) + "┐")
    for r in range(ROWS):
        stdscr.addstr(BOARD_Y + r, BOARD_X, "│")
        stdscr.addstr(BOARD_Y + r, BOARD_X + COLS * 2 + 1, "│")
    stdscr.addstr(BOARD_Y + ROWS, BOARD_X, "└" + "─" * (COLS * 2) + "┘")


def draw_next(stdscr, game, colors):
    x = PANEL_X
    y = BOARD_Y + 1
    stdscr.addstr(y, x, "NEXT")
    y += 1
    cells = SHAPES[game.next_shape]
    color = COLORS[game.next_shape]
    min_r = min(r for r, _ in cells)
    for r in range(min_r, min_r + 4):
        for c in range(4):
            if (r, c) in cells:
                stdscr.addstr(
                    y + r - min_r, x + c * 2, "  ", cell_attr(color, True, colors)
                )
            else:
                stdscr.addstr(y + r - min_r, x + c * 2, "  ")


def draw_stats(stdscr, game):
    x = PANEL_X
    y = BOARD_Y + 7
    stdscr.addstr(y, x, f"SCORE {game.score}")
    stdscr.addstr(y + 1, x, f"LEVEL  {game.level}")
    stdscr.addstr(y + 2, x, f"LINES  {game.lines}")


def draw_controls(stdscr):
    lines = [
        "← →  move",
        "↓    soft drop",
        "↑/Z rotate",
        "SPACE hard drop",
        "P pause",
        "R restart",
        "Q quit",
    ]
    x = PANEL_X
    y = BOARD_Y + 11
    for i, line in enumerate(lines):
        stdscr.addstr(y + i, x, line)


def draw_centered(stdscr, lines):
    max_y, max_x = stdscr.getmaxyx()
    for i, line in enumerate(lines):
        row = max_y // 2 - len(lines) // 2 + i
        col = max(0, (max_x - len(line)) // 2)
        stdscr.addstr(row, col, line)


def frame(stdscr, game, colors):
    stdscr.erase()
    stdscr.border()
    draw_border(stdscr)
    draw_board(stdscr, game, colors)
    draw_next(stdscr, game, colors)
    draw_stats(stdscr, game)
    draw_controls(stdscr)
    if game.paused:
        draw_centered(stdscr, ["PAUSED", "press P to resume"])
    elif game.over:
        draw_centered(
            stdscr, ["GAME OVER", f"score {game.score}", "press R to restart"]
        )
    stdscr.refresh()


def handle_key(game, ch):
    if ch == ord("q"):
        return "quit"
    if ch == ord("r"):
        return "restart"
    if ch == ord("p"):
        game.paused = not game.paused
        return None
    if ch == -1 or game.paused or game.over:
        return None
    if ch in (curses.KEY_LEFT, ord("a")):
        game.move(-1)
    elif ch in (curses.KEY_RIGHT, ord("d")):
        game.move(1)
    elif ch in (curses.KEY_DOWN, ord("s")):
        game.soft_drop()
    elif ch in (curses.KEY_UP, ord("w"), ord("z")):
        game.rotate()
    elif ch == ord(" "):
        game.hard_drop()
    return None


def run(stdscr):
    curses.curs_set(0)
    stdscr.keypad(True)
    stdscr.timeout(16)
    colors = setup_colors(stdscr)
    game = Game()
    last_tick = time.monotonic()
    while True:
        max_y, max_x = stdscr.getmaxyx()
        if max_y < MIN_HEIGHT or max_x < MIN_WIDTH:
            draw_centered(
                stdscr, ["Terminal too small", f"need ≥ {MIN_WIDTH}x{MIN_HEIGHT}"]
            )
            stdscr.refresh()
            if stdscr.getch() == ord("q"):
                return
            continue
        now = time.monotonic()
        if not game.paused and not game.over and now - last_tick >= game.interval():
            game.step()
            last_tick = now
        ch = stdscr.getch()
        if ch == curses.KEY_RESIZE:
            continue
        action = handle_key(game, ch)
        if action == "quit":
            return
        if action == "restart":
            game = Game()
            last_tick = time.monotonic()
        frame(stdscr, game, colors)
