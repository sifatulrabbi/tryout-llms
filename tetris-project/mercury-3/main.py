#!/usr/bin/env python3
import curses

from tetris_tui import run


def main():
    curses.wrapper(run)


if __name__ == "__main__":
    main()
