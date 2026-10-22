import unittest

from tetris_core import Game
from tetris_tui import frame, handle_key


class FakeScreen:
    def __init__(self, height=60, width=80):
        self.height = height
        self.width = width
        self.writes = []
        self.border_calls = 0
        self.erased = 0

    def getmaxyx(self):
        return self.height, self.width

    def addstr(self, y, x, text, attr=0):
        self.writes.append((y, x, text, attr))

    def border(self):
        self.border_calls += 1

    def erase(self):
        self.erased += 1

    def refresh(self):
        pass


class TuiTests(unittest.TestCase):
    def test_frame_renders_board_and_panels(self):
        screen = FakeScreen()
        game = Game()
        frame(screen, game, False)
        texts = " ".join(text for _, _, text, _ in screen.writes)
        self.assertIn("NEXT", texts)
        self.assertIn("SCORE", texts)
        self.assertIn("LEVEL", texts)
        self.assertIn("LINES", texts)
        self.assertIn("Q quit", texts)
        self.assertEqual(screen.border_calls, 1)
        self.assertEqual(screen.erased, 1)

    def test_frame_draws_all_rows_of_playfield(self):
        screen = FakeScreen()
        game = Game()
        frame(screen, game, False)
        rows = set(y for y, _, _, _ in screen.writes)
        self.assertIn(1, rows)
        self.assertIn(20, rows)

    def test_frame_shows_game_over_overlay(self):
        screen = FakeScreen()
        game = Game()
        game.over = True
        frame(screen, game, False)
        texts = " ".join(text for _, _, text, _ in screen.writes)
        self.assertIn("GAME OVER", texts)
        self.assertIn("R to restart", texts)

    def test_handle_key_moves_game(self):
        game = Game()
        start = game.piece_col
        handle_key(game, ord("d"))
        self.assertEqual(game.piece_col, start + 1)
        handle_key(game, ord("a"))
        self.assertEqual(game.piece_col, start)

    def test_handle_key_pause_and_actions(self):
        game = Game()
        handle_key(game, ord("p"))
        self.assertTrue(game.paused)
        start = game.piece_col
        handle_key(game, ord("d"))
        self.assertEqual(game.piece_col, start)
        handle_key(game, ord("p"))
        handle_key(game, ord("d"))
        self.assertEqual(game.piece_col, start + 1)

    def test_handle_key_quit_and_restart_actions(self):
        game = Game()
        self.assertEqual(handle_key(game, ord("q")), "quit")
        self.assertEqual(handle_key(game, ord("r")), "restart")


if __name__ == "__main__":
    unittest.main()
