from __future__ import annotations

import unittest

from tetris.canvas import Style
from tetris.engine import Game
from tetris.pieces import Piece
from tetris.ui import Screen, render_scene


class UIRenderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.game = Game(seed=7)
        self.game.current = Piece("T", 0, 3, 0)
        self.game.board = [[None for _ in range(10)] for _ in range(20)]

    def test_menu_shows_logo_prompt_best_and_quit(self) -> None:
        canvas = render_scene(80, 24, Screen.MENU, best=12_400)
        text = canvas.to_text()

        self.assertIn("PRESS ENTER TO START", text)
        self.assertIn("STACK. CLEAR. SURVIVE.", text)
        self.assertIn("BEST  12,400", text)
        self.assertIn("Q  QUIT", text)
        self.assertNotIn("NEXT", text)

    def test_menu_without_score_shows_empty_state(self) -> None:
        text = render_scene(80, 24, Screen.MENU).to_text()

        self.assertIn("NO HIGH SCORE YET", text)
        self.assertNotIn("BEST  0", text)

    def test_menu_card_is_centered(self) -> None:
        canvas = render_scene(80, 24, Screen.MENU)

        self.assertEqual(canvas.cells[3][16].char, "╔")
        self.assertEqual(canvas.text_row(3)[16], "╔")

    def test_game_screen_has_board_dashboard_and_controls(self) -> None:
        canvas = render_scene(80, 24, Screen.PLAYING, self.game, best=10_000)
        text = canvas.to_text()

        for label in (
            "TETRIS",
            "NEXT",
            "HOLD",
            "SCORE",
            "LEVEL",
            "LINES",
            "BEST",
            "HARD DROP",
            "PAUSE",
            "QUIT",
        ):
            self.assertIn(label, text)
        self.assertEqual(canvas.cells[1][15].char, "┌")
        self.assertEqual(canvas.cells[1][39].char, "┌")
        self.assertEqual(canvas.cells[22][15].char, "└")

    def test_current_and_ghost_pieces_use_piece_style(self) -> None:
        canvas = render_scene(80, 24, Screen.PLAYING, self.game)

        current = canvas.cells[2][24]
        ghost = canvas.cells[20][24]
        self.assertEqual(current.char, "█")
        self.assertEqual(current.style, Style.T)
        self.assertFalse(current.dim)
        self.assertEqual(ghost.char, "░")
        self.assertEqual(ghost.style, Style.T)
        self.assertTrue(ghost.dim)

    def test_locked_piece_is_rendered_on_the_board(self) -> None:
        self.game.hard_drop()

        canvas = render_scene(80, 24, Screen.PLAYING, self.game)
        cell = canvas.cells[20][24]

        self.assertEqual(cell.char, "█")
        self.assertEqual(cell.style, Style.T)

    def test_score_level_lines_and_best_are_formatted(self) -> None:
        self.game.score = 12_340
        self.game.lines = 23
        self.game.level = 3

        text = render_scene(80, 24, Screen.PLAYING, self.game, best=10_000).to_text()

        self.assertIn("12,340", text)
        self.assertIn("LEVEL 03", text)
        self.assertIn("LINES 023", text)
        self.assertIn("10,000", text)

    def test_clear_and_combo_status_lines(self) -> None:
        self.game.last_clear = 4
        self.game.last_clear_points = 800
        text = render_scene(80, 24, Screen.PLAYING, self.game).to_text()
        self.assertIn("TETRIS  +800", text)

        self.game.last_clear = 0
        self.game.combo = 1
        text = render_scene(80, 24, Screen.PLAYING, self.game).to_text()
        self.assertIn("COMBO x2", text)

        self.game.combo = -1
        text = render_scene(80, 24, Screen.PLAYING, self.game).to_text()
        self.assertIn("STAY SHARP", text)

    def test_pause_overlay_dims_background_and_shows_resume_controls(self) -> None:
        canvas = render_scene(80, 24, Screen.PAUSED, self.game)
        text = canvas.to_text()

        self.assertIn("PAUSED", text)
        self.assertIn("P / ENTER  RESUME", text)
        self.assertIn("R RESTART   Q QUIT", text)
        self.assertTrue(canvas.cells[1][15].dim)
        self.assertFalse(canvas.cells[8][15].dim)

    def test_game_over_overlay_shows_score_and_new_best(self) -> None:
        self.game.score = 12_340
        self.game.game_over = True

        text = render_scene(
            80,
            24,
            Screen.GAME_OVER,
            self.game,
            best=12_340,
            new_best=True,
        ).to_text()

        self.assertIn("GAME OVER", text)
        self.assertIn("SCORE", text)
        self.assertIn("12,340", text)
        self.assertIn("BEST", text)
        self.assertIn("NEW HIGH SCORE", text)
        self.assertIn("ENTER  RESTART", text)
        self.assertIn("Q  QUIT", text)

    def test_game_over_overlay_hides_new_best_when_not_earned(self) -> None:
        self.game.game_over = True

        text = render_scene(
            80,
            24,
            Screen.GAME_OVER,
            self.game,
            best=20_000,
            new_best=False,
        ).to_text()

        self.assertIn("GAME OVER", text)
        self.assertNotIn("NEW HIGH SCORE", text)

    def test_game_over_does_not_render_a_floating_current_piece(self) -> None:
        self.game.game_over = True

        canvas = render_scene(80, 24, Screen.GAME_OVER, self.game)

        self.assertEqual(canvas.cells[2][24].char, " ")
        self.assertEqual(canvas.cells[20][24].char, " ")

    def test_exact_minimum_size_fits_the_game(self) -> None:
        canvas = render_scene(50, 22, Screen.PLAYING, self.game)
        text = canvas.to_text()

        self.assertNotIn("TOO SMALL", text)
        self.assertEqual(canvas.cells[0][0].char, "┌")
        self.assertEqual(canvas.cells[0][24].char, "┌")
        self.assertEqual(canvas.cells[21][0].char, "└")

    def test_small_terminal_explains_required_size(self) -> None:
        text = render_scene(49, 21, Screen.MENU).to_text()

        self.assertIn("TERMINAL TOO SMALL", text)
        self.assertIn("NEED 50 X 22", text)
        self.assertIn("NOW  49 X 21", text)

    def test_game_screens_require_a_game(self) -> None:
        with self.assertRaises(ValueError):
            render_scene(80, 24, Screen.PLAYING)


if __name__ == "__main__":
    unittest.main()
