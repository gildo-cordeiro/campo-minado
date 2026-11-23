"""Chess-style cell names shown to the player: column letter + row number.

Columns are letters (A..Z, then AA, AB...) and rows start at 1, so the
cell (row=3, col=2) is "C4". Inside the code cells stay 0-based (row, col).
"""

from __future__ import annotations

import re

from minesweeper.environment import Cell

_CELL_PATTERN = re.compile(r"^([a-z]+)\s*(\d+)$")


def col_label(col: int) -> str:
    """0 -> A, 25 -> Z, 26 -> AA, 29 -> AD."""
    label = ""
    col += 1
    while col:
        col, rest = divmod(col - 1, 26)
        label = chr(ord("A") + rest) + label
    return label


def row_label(row: int) -> str:
    return str(row + 1)


def cell_label(cell: Cell) -> str:
    row, col = cell
    return f"{col_label(col)}{row_label(row)}"


def parse_cell(text: str) -> Cell | None:
    """'C4' (or 'c4', 'C 4') -> (3, 2). Return None if it is not a cell name.

    It does not check the board size; the caller does that.
    """
    match = _CELL_PATTERN.match(text.strip().lower())
    if match is None:
        return None
    letters, digits = match.groups()
    col = 0
    for letter in letters:
        col = col * 26 + (ord(letter) - ord("a") + 1)
    row = int(digits)
    if row < 1:
        return None
    return row - 1, col - 1
