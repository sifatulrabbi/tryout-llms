from __future__ import annotations

import curses
import io
import sys
import unittest
from contextlib import redirect_stderr
from unittest.mock import patch

from tetris.app import command_for_key, main
from tetris.controller import Command


class KeyMappingTests(unittest.TestCase):
    def test_arrow_and_letter_movement_keys(self) -> None:
        for key in (curses.KEY_LEFT, ord("a"), ord("h")):
            self.assertIs(command_for_key(key), Command.MOVE_LEFT)
        for key in (curses.KEY_RIGHT, ord("d"), ord("l")):
            self.assertIs(command_for_key(key), Command.MOVE_RIGHT)
        for key in (curses.KEY_DOWN, ord("s"), ord("j")):
            self.assertIs(command_for_key(key), Command.SOFT_DROP)

    def test_rotation_keys(self) -> None:
        for key in (curses.KEY_UP, ord("w"), ord("k"), ord("x")):
            self.assertIs(command_for_key(key), Command.ROTATE_CW)
        for key in (ord("z"), ord("Z")):
            self.assertIs(command_for_key(key), Command.ROTATE_CCW)

    def test_action_and_meta_keys(self) -> None:
        self.assertIs(command_for_key(ord(" ")), Command.HARD_DROP)
        self.assertIs(command_for_key(ord("c")), Command.HOLD)
        self.assertIs(command_for_key(ord("p")), Command.PAUSE)
        self.assertIs(command_for_key(27), Command.PAUSE)
        self.assertIs(command_for_key(ord("r")), Command.RESTART)
        self.assertIs(command_for_key(ord("q")), Command.QUIT)
        self.assertIs(command_for_key(3), Command.QUIT)
        for key in (10, 13, curses.KEY_ENTER):
            self.assertIs(command_for_key(key), Command.CONFIRM)

    def test_unmapped_key_is_ignored(self) -> None:
        self.assertIsNone(command_for_key(-1))
        self.assertIsNone(command_for_key(ord("9")))


class EntryPointTests(unittest.TestCase):
    def test_non_interactive_stdout_explains_requirement(self) -> None:
        stderr = io.StringIO()
        with (
            patch.object(sys, "stdin", io.StringIO()),
            patch.object(sys, "stdout", io.StringIO()),
            redirect_stderr(stderr),
        ):
            result = main()

        self.assertEqual(result, 1)
        self.assertIn("needs an interactive terminal", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
