"""Reads and validates the commands typed by the human player."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CommandKind(str, Enum):
    REVEAL = "reveal"
    FLAG = "flag"
    HELP = "help"
    QUIT = "quit"


class CommandError(ValueError):
    """The text typed is not a valid command. The message is shown to the player."""


@dataclass(frozen=True)
class Command:
    kind: CommandKind
    row: int = 0
    col: int = 0


_ALIASES = {
    "a": CommandKind.REVEAL,
    "abrir": CommandKind.REVEAL,
    "r": CommandKind.REVEAL,
    "reveal": CommandKind.REVEAL,
    "b": CommandKind.FLAG,
    "bandeira": CommandKind.FLAG,
    "f": CommandKind.FLAG,
    "flag": CommandKind.FLAG,
    "?": CommandKind.HELP,
    "h": CommandKind.HELP,
    "ajuda": CommandKind.HELP,
    "help": CommandKind.HELP,
    "q": CommandKind.QUIT,
    "sair": CommandKind.QUIT,
    "quit": CommandKind.QUIT,
}

HELP_TEXT = """\
Comandos (linhas e colunas começam em 0):
  a <linha> <coluna>   abrir uma célula        (ex.: a 3 4)
  b <linha> <coluna>   colocar ou tirar bandeira (ex.: b 3 4)
  ?                    mostrar esta ajuda
  q                    sair da partida
Também valem: abrir, bandeira, ajuda, sair. A vírgula é opcional (a 3,4)."""


def parse_command(line: str) -> Command:
    """Turn a typed line into a Command, or raise CommandError."""
    parts = line.replace(",", " ").split()
    if not parts:
        raise CommandError("Digite um comando. Use '?' para ver a ajuda.")

    kind = _ALIASES.get(parts[0].lower())
    if kind is None:
        raise CommandError(f"Comando desconhecido: '{parts[0]}'. Use '?' para ver a ajuda.")
    if kind in (CommandKind.HELP, CommandKind.QUIT):
        return Command(kind)

    if len(parts) != 3:
        raise CommandError(f"Use: {parts[0]} <linha> <coluna>  (exemplo: {parts[0]} 3 4).")
    try:
        row, col = int(parts[1]), int(parts[2])
    except ValueError:
        raise CommandError("Linha e coluna devem ser números inteiros.") from None
    return Command(kind, row, col)
