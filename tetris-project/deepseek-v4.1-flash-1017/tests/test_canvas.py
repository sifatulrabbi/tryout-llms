from __future__ import annotations

import unittest

from tetris.canvas import Canvas, Style


class CanvasTests(unittest.TestCase):
    def test_write_and_to_text(self) -> None:
        canvas = Canvas(7, 3)
        canvas.write(1, 1, "TETRIS", Style.ACCENT)

        self.assertEqual(canvas.to_text(), "       \n TETRIS\n       ")

    def test_writes_are_clipped_at_edges(self) -> None:
        canvas = Canvas(3, 2)
        canvas.write(-1, 0, "ABC", Style.TITLE)
        canvas.write(2, 1, "XY", Style.TITLE)

        self.assertEqual(canvas.text_row(0), "BC ")
        self.assertEqual(canvas.text_row(1), "  X")

    def test_box_draws_corners_edges_and_title(self) -> None:
        canvas = Canvas(20, 5)
        canvas.box(0, 0, 20, 5, title="HELLO", double=True)

        self.assertEqual(canvas.cells[0][0].char, "╔")
        self.assertEqual(canvas.cells[0][19].char, "╗")
        self.assertEqual(canvas.cells[4][0].char, "╚")
        self.assertEqual(canvas.cells[4][19].char, "╝")
        self.assertIn(" HELLO ", canvas.text_row(0))
        self.assertEqual(canvas.cells[2][0].char, "║")
        self.assertEqual(canvas.cells[2][19].char, "║")

    def test_fill_and_dim_all(self) -> None:
        canvas = Canvas(4, 3)
        canvas.fill(1, 1, 2, 2, "█", Style.T)
        self.assertFalse(canvas.cells[2][2].dim)

        canvas.dim_all()

        self.assertEqual(canvas.cells[1][1].char, "█")
        self.assertEqual(canvas.cells[1][1].style, Style.T)
        self.assertTrue(canvas.cells[1][1].dim)
        self.assertTrue(canvas.cells[0][0].dim)
        self.assertTrue(canvas.cells[2][2].dim)

    def test_single_character_cells_are_enforced(self) -> None:
        canvas = Canvas(2, 2)
        with self.assertRaises(ValueError):
            canvas.set(0, 0, "AB")

    def test_negative_dimensions_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            Canvas(-1, 2)


if __name__ == "__main__":
    unittest.main()
