# TUI Tetris

A Tetris game that runs in your terminal. Zero dependencies — just Python 3.

## Run

```sh
python3 main.py
```

## Controls

| Key                    | Action            |
| ---------------------- | ----------------- |
| `←` / `→` or `A` / `D` | move left / right |
| `↓` or `S`             | soft drop         |
| `↑` / `W` / `Z`        | rotate            |
| `Space`                | hard drop         |
| `P`                    | pause / resume    |
| `R`                    | restart           |
| `Q`                    | quit              |

## Play

- **Ghost piece** shows where the current piece will land.
- **NEXT panel** previews the upcoming piece.
- **7-bag randomizer**: all seven pieces appear before any repeats.
- **Scoring** (classic): 100 / 300 / 500 / 800 points for clearing 1 / 2 / 3 / 4 lines, multiplied by your level. You level up every 10 lines, and the piece falls faster each level.

## Architecture

- `tetris_core.py` — pure game logic (board, shapes, rotation with wall kicks, collision, line clearing, scoring, bag). No terminal I/O; fully unit-tested.
- `tetris_tui.py` — curses adapter: rendering and keyboard input only.
- `main.py` — entry point.

## Test

```sh
python3 -m unittest discover -s tests -v
```
