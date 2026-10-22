from __future__ import annotations

from collections.abc import Callable
from enum import Enum, auto

from .engine import Game
from .scores import HighScoreStore
from .ui import Screen


class Command(Enum):
    MOVE_LEFT = auto()
    MOVE_RIGHT = auto()
    SOFT_DROP = auto()
    HARD_DROP = auto()
    ROTATE_CW = auto()
    ROTATE_CCW = auto()
    HOLD = auto()
    PAUSE = auto()
    RESTART = auto()
    CONFIRM = auto()
    QUIT = auto()


class TetrisController:
    def __init__(
        self,
        store: HighScoreStore,
        game_factory: Callable[[], Game] = Game,
    ) -> None:
        self._store = store
        self._game_factory = game_factory
        self.screen = Screen.MENU
        self.game: Game | None = None
        self.best = store.load()
        self.new_best = False
        self.running = True

    def handle(self, command: Command) -> None:
        if not self.running:
            return
        if command is Command.QUIT:
            self._record_abandoned_score()
            self.running = False
            return
        if self.screen is Screen.MENU:
            if command in (Command.CONFIRM, Command.RESTART):
                self._start_game()
            return
        if command is Command.RESTART:
            self._record_abandoned_score()
            self._start_game()
            return
        if self.screen is Screen.GAME_OVER:
            if command is Command.CONFIRM:
                self._start_game()
            return
        if self.screen is Screen.PAUSED:
            if command in (Command.PAUSE, Command.CONFIRM):
                self.screen = Screen.PLAYING
            return
        self._handle_playing(command)

    def tick(self, elapsed_ms: float) -> None:
        if not self.running or self.screen is not Screen.PLAYING or self.game is None:
            return
        self.game.advance(elapsed_ms)
        if self.game.game_over:
            self._finish_game()

    def _handle_playing(self, command: Command) -> None:
        game = self.game
        if game is None:
            return
        if command is Command.MOVE_LEFT:
            game.move(-1, 0)
        elif command is Command.MOVE_RIGHT:
            game.move(1, 0)
        elif command is Command.SOFT_DROP:
            game.soft_drop()
        elif command is Command.HARD_DROP:
            game.hard_drop()
        elif command is Command.ROTATE_CW:
            game.rotate(1)
        elif command is Command.ROTATE_CCW:
            game.rotate(-1)
        elif command is Command.HOLD:
            game.hold_piece()
        elif command is Command.PAUSE:
            self.screen = Screen.PAUSED
            return
        else:
            return
        if game.game_over:
            self._finish_game()

    def _start_game(self) -> None:
        self.game = self._game_factory()
        self.screen = Screen.PLAYING
        self.new_best = False

    def _finish_game(self) -> None:
        game = self.game
        if game is None:
            return
        self.screen = Screen.GAME_OVER
        if game.score > self.best:
            self.best = game.score
            self.new_best = True
            self._store.save(self.best)
        else:
            self.new_best = False

    def _record_abandoned_score(self) -> None:
        if self.screen not in (Screen.PLAYING, Screen.PAUSED) or self.game is None:
            return
        if self.game.score > self.best:
            self.best = self.game.score
            self._store.save(self.best)
