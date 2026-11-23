"""Draws the board in the terminal with rich.

render_board only builds a rich Text from an Observation, so it can be
tested and reused by other parts of the CLI (for example, to overlay
probabilities later).

Symbols (plain ASCII, so any terminal shows them):

    #  closed cell          F  flag
    .  opened cell with 0   1..8  number of adjacent mines
    *  mine (after the game ends)
    x  wrong flag (after the game ends)
"""

from __future__ import annotations

from collections.abc import Collection

from rich.text import Text

from minesweeper.environment import FLAGGED, HIDDEN, Cell, GameStatus, Observation

CELL_WIDTH = 3
LABEL_WIDTH = 3
LABEL_STYLE = "bold cyan"

NUMBER_STYLES = {
    1: "bold bright_blue",
    2: "bold green",
    3: "bold red",
    4: "bold blue",
    5: "bold dark_red",
    6: "bold cyan",
    7: "bold magenta",
    8: "bold white",
}


def _symbol(
    observation: Observation,
    cell: Cell,
    mines: frozenset[Cell],
    exploded: Cell | None,
) -> tuple[str, str]:
    """Return (character, style) for one cell."""
    value = observation.value(*cell)
    is_mine = cell in mines

    if cell == exploded:
        return "*", "bold white on red"
    if value == FLAGGED:
        if observation.is_over and mines and not is_mine:
            return "x", "bold yellow"
        return "F", "bold magenta"
    if value == HIDDEN:
        if observation.is_over and is_mine:
            if observation.status is GameStatus.WON:
                return "F", "bold green"
            return "*", "red"
        return "#", "dim"
    if value == 0:
        return ".", "dim"
    return str(value), NUMBER_STYLES[value]


def render_board(
    observation: Observation,
    *,
    mines: Collection[Cell] = (),
    exploded: Cell | None = None,
    highlight: Cell | None = None,
) -> Text:
    """Build the board with row and column numbers.

    mines and exploded are only given when the game is over, to show where
    the mines were. highlight marks a cell with brackets (the cell the last
    move acted on).
    """
    mine_set = frozenset(mines)
    text = Text()

    text.append(" " * LABEL_WIDTH)
    for col in range(observation.cols):
        text.append(f"{col:^{CELL_WIDTH}}", style=LABEL_STYLE)
    text.append("\n")

    for row in range(observation.rows):
        text.append(f"{row:>{LABEL_WIDTH - 1}} ", style=LABEL_STYLE)
        for col in range(observation.cols):
            symbol, style = _symbol(observation, (row, col), mine_set, exploded)
            if (row, col) == highlight:
                text.append(f"[{symbol}]", style=f"{style} reverse")
            else:
                text.append(f" {symbol} ", style=style)
        text.append("\n")

    text.rstrip()
    return text


def status_line(observation: Observation) -> Text:
    """Remaining mines (mines minus flags) and number of moves."""
    return Text(
        f"Minas restantes: {observation.mines_left}  |  Jogadas: {observation.moves}",
        style="bold",
    )
