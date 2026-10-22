from __future__ import annotations

import unittest

from tetris.pieces import (
    KICKS_I,
    KICKS_JLSTZ,
    KINDS,
    SHAPES,
    Piece,
    kicks_for,
    spawn_piece,
)


class PieceGeometryTests(unittest.TestCase):
    def test_every_rotation_has_four_distinct_cells(self) -> None:
        for kind in KINDS:
            for rotation in range(4):
                cells = SHAPES[kind][rotation]
                self.assertEqual(len(cells), 4, (kind, rotation))
                self.assertEqual(len(set(cells)), 4, (kind, rotation))

    def test_spawn_positions_follow_guideline_columns(self) -> None:
        expected_min_columns = {
            "I": 3,
            "J": 3,
            "L": 3,
            "O": 4,
            "S": 3,
            "T": 3,
            "Z": 3,
        }
        expected_top_rows = {
            "I": 1,
            "J": 0,
            "L": 0,
            "O": 0,
            "S": 0,
            "T": 0,
            "Z": 0,
        }
        for kind, expected in expected_min_columns.items():
            piece = spawn_piece(kind)
            self.assertEqual(min(x for x, _ in piece.cells), expected)
            self.assertEqual(min(y for _, y in piece.cells), expected_top_rows[kind])

    def test_kick_tables_have_five_offsets_starting_at_origin(self) -> None:
        for table in (KICKS_I, KICKS_JLSTZ):
            self.assertEqual(len(table), 8)
            for offsets in table.values():
                self.assertEqual(len(offsets), 5)
                self.assertEqual(offsets[0], (0, 0))

    def test_o_piece_never_needs_to_move_to_rotate(self) -> None:
        self.assertEqual(kicks_for("O", 0, 1), ((0, 0),))

    def test_moved_and_rotated_return_new_pieces(self) -> None:
        piece = Piece("T", 0, 3, 0)
        self.assertEqual(piece.moved(1, 2), Piece("T", 0, 4, 2))
        self.assertEqual(piece.rotated(1), Piece("T", 1, 3, 0))
        self.assertEqual(piece.rotated(-1), Piece("T", 3, 3, 0))


if __name__ == "__main__":
    unittest.main()
