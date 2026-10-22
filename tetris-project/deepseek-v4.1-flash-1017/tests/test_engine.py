from __future__ import annotations

import random
import unittest
from collections import deque

from tetris.engine import BOARD_HEIGHT, BOARD_WIDTH, LOCK_DELAY_MS, Game, SevenBag
from tetris.pieces import KINDS, Piece


class ScriptedSource:
    def __init__(self, *kinds: str) -> None:
        self._scripted = deque(kinds)
        self._fallback = deque(KINDS)

    def take(self) -> str:
        if self._scripted:
            return self._scripted.popleft()
        kind = self._fallback.popleft()
        self._fallback.append(kind)
        return kind


def make_game(*kinds: str) -> Game:
    source = ScriptedSource(*(kinds or ("T", "I", "O", "S", "Z", "J", "L")))
    return Game(source=source)


def empty_board() -> list[list[str | None]]:
    return [[None for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]


class SevenBagTests(unittest.TestCase):
    def test_each_group_of_seven_contains_every_tetromino_once(self) -> None:
        bag = SevenBag(random.Random(42))
        draws = [bag.take() for _ in range(7 * 20)]
        for start in range(0, len(draws), 7):
            self.assertEqual(set(draws[start : start + 7]), set(KINDS))


class GameStartTests(unittest.TestCase):
    def test_new_game_has_current_piece_preview_and_empty_board(self) -> None:
        game = make_game("T", "I", "O", "S", "Z", "J", "L")

        self.assertEqual(game.current.kind, "T")
        self.assertEqual(game.next_queue, ("I", "O", "S", "Z"))
        self.assertEqual(game.score, 0)
        self.assertEqual(game.lines, 0)
        self.assertEqual(game.level, 1)
        self.assertIsNone(game.hold)
        self.assertFalse(game.game_over)
        self.assertTrue(game.can_hold)
        self.assertTrue(all(cell is None for row in game.board for cell in row))

    def test_gravity_moves_a_piece_after_one_interval(self) -> None:
        game = make_game()
        interval = game.gravity_interval_ms
        start_y = game.current.y

        game.advance(interval - 1)
        self.assertEqual(game.current.y, start_y)
        game.advance(1)
        self.assertEqual(game.current.y, start_y + 1)


class MovementTests(unittest.TestCase):
    def test_horizontal_movement_stops_at_the_wall(self) -> None:
        game = make_game()

        for _ in range(10):
            if not game.move(-1, 0):
                break

        self.assertEqual(min(x for x, _ in game.current.cells), 0)
        self.assertFalse(game.move(-1, 0))

    def test_rotation_wall_kicks_piece_back_into_playfield(self) -> None:
        game = make_game()
        game.current = Piece("T", 1, -1, 0)

        self.assertTrue(game.rotate(-1))
        self.assertEqual(game.current.rotation, 0)
        self.assertEqual(game.current.x, 0)

    def test_i_piece_uses_its_own_wall_kick_offsets(self) -> None:
        game = make_game()
        game.current = Piece("I", 1, -1, 0)

        self.assertTrue(game.rotate(-1))
        self.assertEqual(game.current.rotation, 0)
        self.assertEqual(game.current.x, 1)

    def test_rotation_can_be_blocked(self) -> None:
        game = make_game()
        game.current = Piece("T", 0, 3, 17)
        for x, y in ((4, 19), (3, 19), (3, 16), (3, 17)):
            game.board[y][x] = "J"

        self.assertFalse(game.rotate(1))

    def test_soft_drop_scores_one_per_row_without_locking(self) -> None:
        game = make_game()

        for _ in range(5):
            self.assertTrue(game.soft_drop())

        self.assertEqual(game.current.kind, "T")
        self.assertEqual(game.current.y, 5)
        self.assertEqual(game.score, 5)

    def test_hard_drop_scores_two_per_row_and_locks_piece(self) -> None:
        game = make_game("T", "I", "O", "S", "Z")

        distance = game.hard_drop()

        self.assertEqual(distance, 18)
        self.assertEqual(game.score, 36)
        self.assertEqual(game.current.kind, "I")
        self.assertEqual(game.board[18][4], "T")
        self.assertEqual(game.board[19][3:6], ["T", "T", "T"])
        self.assertEqual(game.lines, 0)

    def test_ghost_piece_rests_on_top_of_stack(self) -> None:
        game = make_game()
        game.board[18][4] = "J"
        game.current = Piece("O", 0, 4, 0)

        ghost = game.ghost_piece()

        self.assertEqual(ghost.y, 16)
        self.assertEqual(game.hard_drop(), 16)
        self.assertEqual(game.score, 32)


class HoldTests(unittest.TestCase):
    def test_hold_swaps_pieces_and_only_allows_one_hold_per_piece(self) -> None:
        game = make_game("T", "I", "O", "S", "Z", "J", "L")

        self.assertTrue(game.hold_piece())
        self.assertEqual(game.hold, "T")
        self.assertEqual(game.current.kind, "I")
        self.assertFalse(game.can_hold)
        self.assertFalse(game.hold_piece())

        game.hard_drop()
        self.assertTrue(game.can_hold)
        self.assertTrue(game.hold_piece())
        self.assertEqual(game.hold, "O")
        self.assertEqual(game.current.kind, "T")

    def test_empty_hold_takes_piece_from_preview(self) -> None:
        game = make_game("T", "I", "O", "S", "Z", "J")

        game.hold_piece()

        self.assertEqual(game.current.kind, "I")
        self.assertEqual(game.next_queue, ("O", "S", "Z", "J"))


class LineClearTests(unittest.TestCase):
    def ready_single_clear(self, game: Game) -> None:
        game.board = empty_board()
        for x in list(range(3)) + list(range(7, 10)):
            game.board[19][x] = "J"
        game.current = Piece("I", 0, 3, 18)

    def ready_tetris(self, game: Game) -> None:
        game.board = empty_board()
        for y in range(16, 20):
            for x in range(9):
                game.board[y][x] = "J"
        game.current = Piece("I", 1, 7, 16)

    def test_single_line_clear_scores_one_hundred_and_removes_row(self) -> None:
        game = make_game()
        self.ready_single_clear(game)

        game.hard_drop()

        self.assertEqual(game.lines, 1)
        self.assertEqual(game.score, 100)
        self.assertEqual(game.last_clear, 1)
        self.assertEqual(game.last_clear_points, 100)
        self.assertTrue(all(cell is None for row in game.board for cell in row))

    def test_tetris_scores_eight_hundred(self) -> None:
        game = make_game()
        self.ready_tetris(game)

        game.hard_drop()

        self.assertEqual(game.lines, 4)
        self.assertEqual(game.score, 800)
        self.assertEqual(game.last_clear, 4)
        self.assertTrue(all(cell is None for row in game.board for cell in row))

    def test_consecutive_clears_award_combo_bonus(self) -> None:
        game = make_game()
        self.ready_single_clear(game)
        game.hard_drop()
        self.ready_single_clear(game)

        game.hard_drop()

        self.assertEqual(game.lines, 2)
        self.assertEqual(game.score, 250)
        self.assertEqual(game.combo, 1)

    def test_crossing_ten_lines_increases_level_after_scoring(self) -> None:
        game = make_game()
        game.lines = 9
        self.ready_single_clear(game)

        game.hard_drop()

        self.assertEqual(game.lines, 10)
        self.assertEqual(game.level, 2)
        self.assertEqual(game.score, 100)

    def test_combo_resets_after_a_lock_without_a_clear(self) -> None:
        game = make_game()
        self.ready_single_clear(game)
        game.hard_drop()
        self.ready_single_clear(game)
        game.hard_drop()
        self.assertEqual(game.combo, 1)

        game.board = empty_board()
        game.current = Piece("T", 0, 3, 0)
        game.hard_drop()

        self.assertEqual(game.combo, -1)
        self.assertEqual(game.last_clear, 0)


class LockDelayTests(unittest.TestCase):
    def grounded_game(self) -> Game:
        game = make_game()
        game.board[19][4] = "J"
        game.current = Piece("O", 0, 4, 17)
        return game

    def test_piece_locks_after_lock_delay(self) -> None:
        game = self.grounded_game()

        game.advance(LOCK_DELAY_MS - 1)
        self.assertEqual(game.current.kind, "O")
        game.advance(1)
        self.assertEqual(game.current.kind, "I")

    def test_successful_move_resets_lock_delay(self) -> None:
        game = self.grounded_game()
        game.advance(400)

        self.assertTrue(game.move(-1, 0))
        game.advance(400)
        self.assertEqual(game.current.kind, "O")
        game.advance(100)
        self.assertEqual(game.current.kind, "I")


class GameOverTests(unittest.TestCase):
    def test_game_over_when_next_piece_cannot_spawn(self) -> None:
        game = make_game()
        game.board = empty_board()
        game.board[19][4] = "J"
        for x in range(3, 7):
            game.board[0][x] = "J"
            game.board[1][x] = "J"
        game.current = Piece("O", 0, 4, 17)

        game.advance(LOCK_DELAY_MS)

        self.assertTrue(game.game_over)

    def test_hard_drop_into_blocked_spawn_top_outs(self) -> None:
        game = make_game()
        game.board[0][3:7] = ["J", "J", "J", "J"]
        game.board[1][3:7] = ["J", "J", "J", "J"]
        game.current = Piece("O", 0, 4, 17)

        game.hard_drop()

        self.assertTrue(game.game_over)


if __name__ == "__main__":
    unittest.main()
