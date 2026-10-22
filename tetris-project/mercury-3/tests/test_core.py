import unittest

from tetris_core import Board, Game, SHAPES, COLORS, rotate_cw


class RotateTests(unittest.TestCase):
    def test_t_rotates_clockwise(self):
        self.assertEqual(
            sorted(rotate_cw(SHAPES["T"])),
            sorted([(0, 3), (1, 3), (2, 3), (1, 2)]),
        )

    def test_i_rotates_horizontal(self):
        self.assertEqual(
            sorted(rotate_cw(SHAPES["I"])),
            sorted([(1, 0), (1, 1), (1, 2), (1, 3)]),
        )

    def test_four_rotations_return_to_start(self):
        for name, cells in SHAPES.items():
            rotated = cells
            for _ in range(4):
                rotated = rotate_cw(rotated)
            self.assertEqual(sorted(rotated), sorted(cells), name)

    def test_all_shapes_have_four_blocks(self):
        for name, cells in SHAPES.items():
            self.assertEqual(len(cells), 4, name)


class BoardTests(unittest.TestCase):
    def test_collides_with_walls_and_floor(self):
        board = Board()
        self.assertTrue(board.collides([(0, 0)], 0, -1))
        self.assertTrue(board.collides([(0, 0)], 0, board.cols))
        self.assertTrue(board.collides([(0, 0)], board.rows, 0))

    def test_collides_with_filled_cell(self):
        board = Board()
        board.grid[5][3] = 1
        self.assertTrue(board.collides([(5, 3)], 0, 0))
        self.assertFalse(board.collides([(6, 3)], 0, 0))

    def test_clear_lines_removes_only_full_rows(self):
        board = Board()
        for c in range(board.cols):
            board.grid[board.rows - 1][c] = 1
            board.grid[board.rows - 2][c] = 1
        board.grid[board.rows - 3][0] = 1
        self.assertEqual(board.clear_lines(), 2)
        self.assertTrue(all(cell == 0 for cell in board.grid[0]))
        self.assertTrue(all(cell == 0 for cell in board.grid[1]))
        self.assertEqual(board.grid[board.rows - 1][0], 1)
        self.assertEqual(board.grid[board.rows - 1][1], 0)

    def test_merge_writes_color(self):
        board = Board()
        board.merge([(0, 0), (1, 1)], 5, 2, 3)
        self.assertEqual(board.grid[5][2], 3)
        self.assertEqual(board.grid[6][3], 3)


class GameTests(unittest.TestCase):
    def seed(self):
        import random

        return random.Random(1234)

    def test_spawn_places_piece_on_top(self):
        game = Game(self.seed())
        self.assertEqual(game.piece_row, 0)
        self.assertFalse(game.over)

    def test_move_works_and_bumps_walls(self):
        game = Game(self.seed())
        game.piece_row = 10
        self.assertTrue(game.move(1))
        self.assertTrue(game.move(-1))
        self.assertFalse(game.move(-20))
        self.assertFalse(game.move(20))
        self.assertEqual(game.piece_col, 3)

    def test_step_gravity_until_floor(self):
        game = Game(self.seed())
        moves = 0
        while game.step():
            moves += 1
        self.assertIn(moves, (16, 18))

    def test_hard_drop_locks_on_floor(self):
        game = Game(self.seed())
        color = COLORS[game.current]
        col = game.piece_col
        game.hard_drop()
        self.assertEqual(game.board.grid[19][col], color)

    def drop_i_at_left(self, game):
        game.piece = SHAPES["I"]
        game.current = "I"
        game.piece_row = 0
        game.piece_col = -1
        game.hard_drop()

    def test_filling_row_scores_and_levels(self):
        game = Game(self.seed())
        for c in range(1, game.board.cols):
            game.board.grid[19][c] = 1
        self.drop_i_at_left(game)
        self.assertEqual(game.lines, 1)
        self.assertEqual(game.score, 100)

    def test_tetris_scores_800(self):
        game = Game(self.seed())
        for r in (19, 18, 17, 16):
            for c in range(1, game.board.cols):
                game.board.grid[r][c] = 1
        self.drop_i_at_left(game)
        self.assertEqual(game.lines, 4)
        self.assertEqual(game.score, 800)

    def test_bag_gives_seven_distinct_shapes(self):
        from tetris_core import Bag

        bag = Bag(self.seed())
        seen = [bag.next() for _ in range(7)]
        self.assertEqual(len(set(seen)), 7)

    def test_game_over_when_stack_reaches_top(self):
        game = Game(self.seed())
        for c in range(game.board.cols):
            game.board.grid[0][c] = 1
            game.board.grid[1][c] = 1
        game.spawn()
        self.assertTrue(game.over)

    def test_rotation_kicks_off_left_wall(self):
        game = Game(self.seed())
        game.piece = SHAPES["I"]
        game.piece_col = -1
        game.piece_row = 10
        self.assertTrue(game.rotate())
        self.assertGreaterEqual(game.piece_col, 0)
        self.assertFalse(
            game.board.collides(game.piece, game.piece_row, game.piece_col)
        )

    def test_pause_blocks_all_actions(self):
        game = Game(self.seed())
        game.paused = True
        self.assertFalse(game.move(1))
        self.assertFalse(game.step())
        self.assertFalse(game.rotate())
        game.paused = False
        self.assertTrue(game.move(1))

    def test_level_rises_every_ten_lines(self):
        game = Game(self.seed())
        for _ in range(10):
            for c in range(1, game.board.cols):
                game.board.grid[19][c] = 1
            self.drop_i_at_left(game)
        self.assertEqual(game.lines, 10)
        self.assertGreaterEqual(game.level, 2)

    def test_speed_increases_with_level(self):
        game = Game(self.seed())
        first = game.interval()
        game.level = 10
        self.assertLess(game.interval(), first)


if __name__ == "__main__":
    unittest.main()
