from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Protocol


class HighScoreStore(Protocol):
    def load(self) -> int: ...

    def save(self, score: int) -> None: ...


class FileHighScoreStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> int:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return 0
        if not isinstance(data, dict):
            return 0
        score = data.get("high_score")
        if isinstance(score, int) and not isinstance(score, bool) and score >= 0:
            return score
        return 0

    def save(self, score: int) -> None:
        if score <= 0 or score <= self.load():
            return
        temp_path: Path | None = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            descriptor, temp_name = tempfile.mkstemp(
                prefix=f".{self.path.name}.",
                suffix=".tmp",
                dir=self.path.parent,
            )
            temp_path = Path(temp_name)
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                json.dump({"high_score": score}, handle)
                handle.write("\n")
            os.replace(temp_path, self.path)
        except OSError:
            return
        finally:
            if temp_path is not None:
                try:
                    temp_path.unlink(missing_ok=True)
                except OSError:
                    pass


def default_high_score_path() -> Path:
    state_home = os.environ.get("XDG_STATE_HOME")
    base = Path(state_home) if state_home else Path.home() / ".local" / "state"
    return base / "tetris-tui" / "highscore.json"
