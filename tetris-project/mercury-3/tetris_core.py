import random

COLS = 10
ROWS = 20

SHAPES = {
    "I": [(0, 1), (1, 1), (2, 1), (3, 1)],
    "O": [(0, 1), (0, 2), (1, 1), (1, 2)],
    "T": [(0, 0), (0, 1), (0, 2), (1, 1)],
    "S": [(0, 1), (0, 2), (1, 0), (1, 1)],
    "Z": [(0, 0), (0, 1), (1, 1), (1, 2)],
    "J": [(0, 0), (1, 0), (1, 1), (1, 2)],
    "L": [(0, 2), (1, 0), (1, 1), (1, 2)],
}

COLORS = {"I": 1, "O": 2, "T": 3, "S": 4, "Z": 5, "J": 6, "L": 7}

LINE_SCORES = {1: 100, 2: 300, 3: 500, 4: 800}


def rotate_cw(cells):
    return [(c, 3 - r) for (r, c) in cells]


class Board:
    def __init__(self, cols=COLS, rows=ROWS):
        self.cols = cols
        self.rows = rows
        self.grid = [[0] * cols for _ in range(rows)]

    def collides(self, cells, dr, dc):
        for r, c in cells:
            rr = r + dr
            cc = c + dc
            if cc < 0 or cc >= self.cols or rr >= self.rows:
                return True
            if rr >= 0 and self.grid[rr][cc]:
                return True
        return False

    def merge(self, cells, dr, dc, color):
        for r, c in cells:
            rr = r + dr
            cc = c + dc
            if rr >= 0:
                self.grid[rr][cc] = color

    def clear_lines(self):
        kept = [row for row in self.grid if any(cell == 0 for cell in row)]
        cleared = self.rows - len(kept)
        if cleared:
            self.grid = [[0] * self.cols for _ in range(cleared)] + kept
        return cleared


class Bag:
    def __init__(self, rng=None):
        self._rng = rng if rng is not None else random.Random()
        self._bag = []

    def next(self):
        if not self._bag:
            self._bag = list(SHAPES.keys())
            self._rng.shuffle(self._bag)
        return self._bag.pop()


class Game:
    def __init__(self, rng=None):
        self.board = Board()
        self.bag = Bag(rng)
        self.score = 0
        self.lines = 0
        self.level = 1
        self.over = False
        self.paused = False
        self.next_shape = self.bag.next()
        self.spawn()

    def spawn(self):
        self.current = self.next_shape
        self.next_shape = self.bag.next()
        cells = SHAPES[self.current]
        min_c = min(c for _, c in cells)
        max_c = max(c for _, c in cells)
        width = max_c - min_c + 1
        self.piece = cells
        self.piece_row = 0
        self.piece_col = (self.board.cols - width) // 2 - min_c
        if self.board.collides(self.piece, self.piece_row, self.piece_col):
            self.over = True

    def move(self, dx):
        if self.over or self.paused:
            return False
        if not self.board.collides(self.piece, self.piece_row, self.piece_col + dx):
            self.piece_col += dx
            return True
        return False

    def step(self):
        if self.over or self.paused:
            return False
        if not self.board.collides(self.piece, self.piece_row + 1, self.piece_col):
            self.piece_row += 1
            return True
        self.lock()
        return False

    def drop_distance(self):
        distance = 0
        while not self.board.collides(
            self.piece, self.piece_row + distance + 1, self.piece_col
        ):
            distance += 1
        return distance

    def hard_drop(self):
        if self.over or self.paused:
            return
        self.piece_row += self.drop_distance()
        self.lock()

    def soft_drop(self):
        return self.step()

    def rotate(self):
        if self.over or self.paused:
            return False
        rotated = rotate_cw(self.piece)
        for kick in (0, -1, 1, -2, 2):
            if not self.board.collides(rotated, self.piece_row, self.piece_col + kick):
                self.piece = rotated
                self.piece_col += kick
                return True
        return False

    def lock(self):
        self.board.merge(
            self.piece, self.piece_row, self.piece_col, COLORS[self.current]
        )
        cleared = self.board.clear_lines()
        if cleared:
            self.lines += cleared
            self.score += LINE_SCORES[cleared] * self.level
            self.level = self.lines // 10 + 1
        self.spawn()

    def interval(self):
        return max(0.03, 0.8 * (0.85 ** (self.level - 1)))
