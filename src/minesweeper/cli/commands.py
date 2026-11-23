"""Reads and validates the commands typed by the human player.

A move is just a cell name, chess style:

    C4    open the cell in column C, row 4
    !C4   place or remove a flag on C4
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .coords import parse_cell


class CommandKind(str, Enum):
    REVEAL = "reveal"
    FLAG = "flag"
    HELP = "help"
    QUIT = "quit"


class CommandError(ValueError):
    """The text typed is not a valid command. The message is shown to the player."""


@dataclass(frozen=True)
class Command:
    """row and col are 0-based, like everywhere else in the code."""

    kind: CommandKind
    row: int = 0
    col: int = 0


_WORDS = {
    "?": CommandKind.HELP,
    "ajuda": CommandKind.HELP,
    "help": CommandKind.HELP,
    "q": CommandKind.QUIT,
    "sair": CommandKind.QUIT,
    "quit": CommandKind.QUIT,
}

HELP_TEXT = """\
Digite a célula pelo nome: a letra da coluna e o número da linha.
  C4     abrir a célula C4
  !C4    colocar ou tirar bandeira em C4
  ?      mostrar esta ajuda
  q      sair da partida
Maiúsculas e minúsculas tanto faz (c4 = C4)."""


def parse_command(line: str) -> Command:
    """Turn a typed line into a Command, or raise CommandError."""
    text = line.strip()
    if not text:
        raise CommandError("Digite uma célula (ex.: C4). Use '?' para ver a ajuda.")

    word = _WORDS.get(text.lower())
    if word is not None:
        return Command(word)

    kind = CommandKind.REVEAL
    if text.startswith("!"):
        kind = CommandKind.FLAG
        text = text[1:]

    cell = parse_cell(text)
    if cell is None:
        raise CommandError(
            f"Não entendi '{line.strip()}'. Digite a coluna e a linha, como C4 (ou !C4 para bandeira)."
        )
    return Command(kind, *cell)
