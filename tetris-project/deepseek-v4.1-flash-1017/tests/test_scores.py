from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from tetris.scores import FileHighScoreStore, default_high_score_path


class HighScoreStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.path = Path(self.temp_dir.name) / "nested" / "highscore.json"
        self.store = FileHighScoreStore(self.path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_missing_file_loads_zero(self) -> None:
        self.assertEqual(self.store.load(), 0)

    def test_score_round_trips_and_creates_parent_directory(self) -> None:
        self.store.save(12_340)

        self.assertEqual(self.store.load(), 12_340)
        self.assertTrue(self.path.exists())
        self.assertEqual(json.loads(self.path.read_text()), {"high_score": 12_340})

    def test_lower_score_does_not_replace_high_score(self) -> None:
        self.store.save(500)
        self.store.save(200)

        self.assertEqual(self.store.load(), 500)

    def test_equal_score_is_not_rewritten(self) -> None:
        self.store.save(500)
        before = self.path.stat().st_mtime_ns

        self.store.save(500)

        self.assertEqual(self.path.stat().st_mtime_ns, before)

    def test_corrupt_file_loads_zero_and_can_be_repaired(self) -> None:
        self.path.parent.mkdir(parents=True)
        self.path.write_text("{not json")

        self.assertEqual(self.store.load(), 0)
        self.store.save(900)
        self.assertEqual(self.store.load(), 900)

    def test_wrong_value_type_loads_zero(self) -> None:
        self.path.parent.mkdir(parents=True)
        self.path.write_text(json.dumps({"high_score": "lots"}))

        self.assertEqual(self.store.load(), 0)

    def test_negative_score_is_rejected(self) -> None:
        self.store.save(-20)

        self.assertEqual(self.store.load(), 0)
        self.assertFalse(self.path.exists())

    def test_unwritable_path_does_not_raise(self) -> None:
        self.path.parent.mkdir(parents=True)
        self.path.mkdir()

        self.store.save(100)

        self.assertEqual(self.store.load(), 0)

    def test_default_path_respects_xdg_state_home(self) -> None:
        previous = os.environ.get("XDG_STATE_HOME")
        os.environ["XDG_STATE_HOME"] = self.temp_dir.name
        try:
            self.assertEqual(
                default_high_score_path(),
                Path(self.temp_dir.name) / "tetris-tui" / "highscore.json",
            )
        finally:
            if previous is None:
                os.environ.pop("XDG_STATE_HOME", None)
            else:
                os.environ["XDG_STATE_HOME"] = previous


if __name__ == "__main__":
    unittest.main()
