from __future__ import annotations

import random
from collections import deque
from typing import Protocol

from .pieces import KINDS, Kind, Piece, kicks_for, spawn_piece

BOARD_WIDTH = 10
BOARD_HEIGHT = 20
PREVIEW_COUNT = 4
LOCK_DELAY_MS = 500.0
MAX_LOCK_RESETS = 15
MIN_GRAVITY_MS = 80.0

LINE_CLEAR_POINTS = {1: 100, 2: 300, 3: 500, 4: 800}


class PieceSource(Protocol):
    def take(self) -> Kind: ...


class SevenBag:
    def __init__(self, rng: random.Random | None = None) -> None:
        self._rng = rng or random.Random()
        self._bag: list[Kind] = []

    def take(self) -> Kind:
        if not self._bag:
            self._bag = list(KINDS)
            self._rng.shuffle(self._bag)
        return self._bag.pop()


class Game:
    def __init__(
        self,
        source: PieceSource | None = None,
        *,
        seed: int | None = None,
    ) -> None:
        if source is not None and seed is not None:
            raise ValueError("pass source or seed, not both")
        self._source = source or SevenBag(random.Random(seed))
        self.board: list[list[Kind | None]] = [
            [None for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)
        ]
        self._queue: deque[Kind] = deque()
        self.current = spawn_piece(self._source.take())
        self._fill_preview()
        self.hold: Kind | None = None
        self.can_hold = True
        self.score = 0
        self.lines = 0
        self.level = 1
        self.combo = -1
        self.last_clear = 0
        self.last_clear_points = 0
        self.game_over = False
        self._gravity_elapsed = 0.0
        self._lock_elapsed = 0.0
        self._lock_resets = 0

    @property
    def next_queue(self) -> tuple[Kind, ...]:
        return tuple(self._queue)

    @property
    def grounded(self) -> bool:
        return not self._valid(self.current.moved(0, 1))

    @property
    def gravity_interval_ms(self) -> float:
        return max(MIN_GRAVITY_MS, 850.0 * (0.85 ** (self.level - 1)))

    def move(self, dx: int, dy: int) -> bool:
        if self.game_over:
            return False
        candidate = self.current.moved(dx, dy)
        if not self._valid(candidate):
            return False
        self.current = candidate
        self._after_shift()
        return True

    def soft_drop(self) -> bool:
        if self.game_over:
            return False
        candidate = self.current.moved(0, 1)
        if not self._valid(candidate):
            return False
        self.current = candidate
        self.score += 1
        self._gravity_elapsed = 0.0
        self._after_shift()
        return True

    def hard_drop(self) -> int:
        if self.game_over:
            return 0
        distance = 0
        while True:
            candidate = self.current.moved(0, 1)
            if not self._valid(candidate):
                break
            self.current = candidate
            distance += 1
        self.score += distance * 2
        self._gravity_elapsed = 0.0
        self._lock_current_piece()
        return distance

    def rotate(self, direction: int) -> bool:
        if self.game_over or direction == 0:
            return False
        target_rotation = (self.current.rotation + direction) % 4
        for dx, dy in kicks_for(
            self.current.kind, self.current.rotation, target_rotation
        ):
            candidate = Piece(
                self.current.kind,
                target_rotation,
                self.current.x + dx,
                self.current.y + dy,
            )
            if self._valid(candidate):
                self.current = candidate
                self._after_shift()
                return True
        return False

    def hold_piece(self) -> bool:
        if self.game_over or not self.can_hold:
            return False
        current_kind = self.current.kind
        if self.hold is None:
            self.hold = current_kind
            incoming = self._next_from_preview()
        else:
            incoming = self.hold
            self.hold = current_kind
        self.current = spawn_piece(incoming)
        self.can_hold = False
        self._reset_timers()
        if not self._valid(self.current):
            self.game_over = True
        return True

    def ghost_piece(self) -> Piece:
        ghost = self.current
        while self._valid(ghost.moved(0, 1)):
            ghost = ghost.moved(0, 1)
        return ghost

    def advance(self, elapsed_ms: float) -> None:
        if self.game_over or elapsed_ms <= 0:
            return
        remaining = float(elapsed_ms)
        while remaining > 0 and not self.game_over:
            if self.grounded:
                needed = LOCK_DELAY_MS - self._lock_elapsed
                if needed > 0:
                    step = min(remaining, needed)
                    self._lock_elapsed += step
                    remaining -= step
                if self._lock_elapsed >= LOCK_DELAY_MS:
                    self._lock_current_piece()
                    continue
                break

            interval = self.gravity_interval_ms
            needed = interval - self._gravity_elapsed
            step = min(remaining, needed)
            self._gravity_elapsed += step
            remaining -= step
            if self._gravity_elapsed >= interval - 1e-9:
                self._gravity_elapsed = 0.0
                self.current = self.current.moved(0, 1)
                self._lock_elapsed = 0.0

    def _fill_preview(self) -> None:
        while len(self._queue) < PREVIEW_COUNT:
            self._queue.append(self._draw())

    def _draw(self) -> Kind:
        return self._source.take()

    def _next_from_preview(self) -> Kind:
        kind = self._queue.popleft()
        self._fill_preview()
        return kind

    def _valid(self, piece: Piece) -> bool:
        for x, y in piece.cells:
            if not (0 <= x < BOARD_WIDTH and 0 <= y < BOARD_HEIGHT):
                return False
            if self.board[y][x] is not None:
                return False
        return True

    def _after_shift(self) -> None:
        if self.grounded:
            if self._lock_resets < MAX_LOCK_RESETS:
                self._lock_elapsed = 0.0
                self._lock_resets += 1
        else:
            self._lock_elapsed = 0.0

    def _reset_timers(self) -> None:
        self._gravity_elapsed = 0.0
        self._lock_elapsed = 0.0
        self._lock_resets = 0

    def _lock_current_piece(self) -> None:
        for x, y in self.current.cells:
            if 0 <= y < BOARD_HEIGHT and 0 <= x < BOARD_WIDTH:
                self.board[y][x] = self.current.kind
        full_rows = [
            y
            for y in range(BOARD_HEIGHT)
            if all(cell is not None for cell in self.board[y])
        ]
        clear_count = len(full_rows)
        for y in full_rows:
            del self.board[y]
            self.board.insert(0, [None for _ in range(BOARD_WIDTH)])

        if clear_count:
            self.combo += 1
            base_points = LINE_CLEAR_POINTS[clear_count] * self.level
            combo_points = 50 * self.combo * self.level if self.combo > 0 else 0
            points = base_points + combo_points
            self.score += points
            self.lines += clear_count
            self.level = 1 + self.lines // 10
            self.last_clear = clear_count
            self.last_clear_points = points
        else:
            self.combo = -1
            self.last_clear = 0
            self.last_clear_points = 0

        self.can_hold = True
        self._reset_timers()
        self.current = spawn_piece(self._next_from_preview())
        if not self._valid(self.current):
            self.game_over = True
