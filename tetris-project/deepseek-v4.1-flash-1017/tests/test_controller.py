from __future__ import annotations

import unittest

from tetris.controller import Command, TetrisController
from tetris.engine import Game
from tetris.ui import Screen


class MemoryStore:
    def __init__(self, score: int = 0) -> None:
        self.score = score
        self.saved: list[int] = []

    def load(self) -> int:
        return self.score

    def save(self, score: int) -> None:
        self.saved.append(score)
        self.score = max(self.score, score)


def make_controller(store: MemoryStore | None = None) -> TetrisController:
    return TetrisController(
        store or MemoryStore(),
        game_factory=lambda: Game(seed=99),
    )


class ControllerTests(unittest.TestCase):
    def test_starts_on_menu_with_persisted_best(self) -> None:
        controller = make_controller(MemoryStore(700))

        self.assertIs(controller.screen, Screen.MENU)
        self.assertEqual(controller.best, 700)
        self.assertIsNone(controller.game)
        self.assertTrue(controller.running)

    def test_confirm_starts_a_game_from_menu(self) -> None:
        controller = make_controller()

        controller.handle(Command.CONFIRM)

        self.assertIs(controller.screen, Screen.PLAYING)
        self.assertIsNotNone(controller.game)
        self.assertFalse(controller.new_best)

    def test_game_commands_move_and_drop_piece(self) -> None:
        controller = make_controller()
        controller.handle(Command.CONFIRM)
        assert controller.game is not None
        start_x = controller.game.current.x

        controller.handle(Command.MOVE_LEFT)
        self.assertEqual(controller.game.current.x, start_x - 1)

        controller.handle(Command.HARD_DROP)
        self.assertTrue(
            any(cell is not None for row in controller.game.board for cell in row)
        )

    def test_pause_freezes_gravity_and_resume_continues_it(self) -> None:
        controller = make_controller()
        controller.handle(Command.CONFIRM)
        assert controller.game is not None
        start_y = controller.game.current.y

        controller.handle(Command.PAUSE)
        self.assertIs(controller.screen, Screen.PAUSED)
        controller.tick(10_000)
        self.assertEqual(controller.game.current.y, start_y)

        controller.handle(Command.CONFIRM)
        self.assertIs(controller.screen, Screen.PLAYING)
        controller.tick(controller.game.gravity_interval_ms + 1)
        self.assertEqual(controller.game.current.y, start_y + 1)

    def test_restart_swaps_in_a_fresh_game_and_records_abandoned_score(self) -> None:
        store = MemoryStore()
        controller = make_controller(store)
        controller.handle(Command.CONFIRM)
        assert controller.game is not None
        first_game = controller.game
        first_game.score = 450

        controller.handle(Command.RESTART)

        self.assertIsNot(controller.game, first_game)
        assert controller.game is not None
        self.assertEqual(controller.game.score, 0)
        self.assertEqual(store.saved, [450])
        self.assertEqual(controller.best, 450)

    def test_quit_stops_the_loop_and_records_current_score(self) -> None:
        store = MemoryStore()
        controller = make_controller(store)
        controller.handle(Command.CONFIRM)
        assert controller.game is not None
        controller.game.score = 900

        controller.handle(Command.QUIT)

        self.assertFalse(controller.running)
        self.assertEqual(store.saved, [900])

    def test_quit_from_menu_does_not_write_a_score(self) -> None:
        store = MemoryStore(300)
        controller = make_controller(store)

        controller.handle(Command.QUIT)

        self.assertFalse(controller.running)
        self.assertEqual(store.saved, [])

    def test_game_over_records_new_high_score(self) -> None:
        store = MemoryStore(100)
        controller = make_controller(store)
        controller.handle(Command.CONFIRM)
        assert controller.game is not None
        controller.game.score = 500
        controller.game.game_over = True

        controller.tick(1)

        self.assertIs(controller.screen, Screen.GAME_OVER)
        self.assertEqual(controller.best, 500)
        self.assertTrue(controller.new_best)
        self.assertEqual(store.saved, [500])

    def test_game_over_with_lower_score_keeps_existing_best(self) -> None:
        store = MemoryStore(1_000)
        controller = make_controller(store)
        controller.handle(Command.CONFIRM)
        assert controller.game is not None
        controller.game.score = 500
        controller.game.game_over = True

        controller.tick(1)

        self.assertEqual(controller.best, 1_000)
        self.assertFalse(controller.new_best)
        self.assertEqual(store.saved, [])

    def test_confirm_on_game_over_starts_fresh_game(self) -> None:
        controller = make_controller()
        controller.handle(Command.CONFIRM)
        assert controller.game is not None
        controller.game.game_over = True
        controller.tick(1)

        controller.handle(Command.CONFIRM)

        self.assertIs(controller.screen, Screen.PLAYING)
        assert controller.game is not None
        self.assertEqual(controller.game.score, 0)
        self.assertFalse(controller.new_best)

    def test_non_confirm_commands_do_nothing_on_menu(self) -> None:
        controller = make_controller()

        controller.handle(Command.MOVE_LEFT)
        controller.handle(Command.PAUSE)

        self.assertIs(controller.screen, Screen.MENU)
        self.assertIsNone(controller.game)

    def test_restart_command_starts_game_from_menu(self) -> None:
        controller = make_controller()

        controller.handle(Command.RESTART)

        self.assertIs(controller.screen, Screen.PLAYING)


if __name__ == "__main__":
    unittest.main()
