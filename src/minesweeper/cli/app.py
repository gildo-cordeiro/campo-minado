"""Entry point of the terminal interface: `python -m minesweeper`.

Two modes:

* human: the player types commands to open cells and place flags;
* agent: an agent from the registry plays and each move is drawn.
"""

from __future__ import annotations

import argparse
import random
from collections.abc import Sequence

from rich.console import Console
from rich.text import Text

from minesweeper.agents import (
    Action,
    ActionType,
    Agent,
    AgentStuckError,
    GameResult,
    play_game,
)
from minesweeper.environment import (
    DIFFICULTIES,
    Game,
    GameStatus,
    InvalidMoveError,
    MoveResult,
    get_config,
)

from .commands import HELP_TEXT, CommandError, CommandKind, parse_command
from .registry import discover_agents
from .render import render_board, status_line


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m minesweeper",
        description="Campo Minado Probabilístico: jogue ou assista um agente jogar.",
    )
    parser.add_argument(
        "--mode",
        choices=("human", "agent"),
        default="human",
        help="human: você joga; agent: um agente joga (padrão: human)",
    )
    parser.add_argument(
        "--difficulty",
        choices=tuple(DIFFICULTIES),
        default="easy",
        help="easy 9x9/10 minas, medium 16x16/40, hard 16x30/99 (padrão: easy)",
    )
    parser.add_argument(
        "--agent",
        metavar="NOME",
        help="nome do agente, obrigatório com --mode agent",
    )
    parser.add_argument(
        "--seed",
        type=int,
        help="seed do tabuleiro; a mesma seed repete a mesma partida",
    )
    return parser


def main(argv: Sequence[str] | None = None, console: Console | None = None) -> int:
    """Run the CLI and return the exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)
    console = console or Console()

    agent: Agent | None = None
    if args.mode == "agent":
        agents = discover_agents()
        if not agents:
            parser.error("nenhum agente foi implementado ainda em minesweeper.agents")
        available = ", ".join(agents)
        if args.agent is None:
            parser.error(f"--mode agent exige --agent (disponíveis: {available})")
        if args.agent not in agents:
            parser.error(f"agente '{args.agent}' não existe (disponíveis: {available})")
        agent = agents[args.agent]()

    config = get_config(args.difficulty)
    seed = args.seed if args.seed is not None else random.randrange(2**31)
    game = Game(config, seed=seed)

    console.print(Text("Campo Minado Probabilístico", style="bold"))
    console.print(
        f"Nível {args.difficulty}: {config.rows}x{config.cols}, "
        f"{config.mines} minas | seed {seed}"
    )

    if agent is not None:
        return run_agent(game, agent, console)
    return run_human(game, console)


# ----- human mode -------------------------------------------------------


def run_human(game: Game, console: Console) -> int:
    """Interactive loop: read a command, apply it and draw the board."""
    console.print("Digite '?' para ver os comandos.\n")

    needs_draw = True
    while not game.is_over:
        if needs_draw:
            draw_board(console, game)
        needs_draw = True
        try:
            line = console.input("> ")
        except (EOFError, KeyboardInterrupt):
            console.print("\nPartida encerrada.")
            return 0

        try:
            command = parse_command(line)
        except CommandError as error:
            console.print(Text(str(error), style="red"))
            needs_draw = False
            continue

        if command.kind is CommandKind.QUIT:
            console.print("Partida encerrada.")
            return 0
        if command.kind is CommandKind.HELP:
            console.print(HELP_TEXT)
            needs_draw = False
            continue

        error_message = apply_human_command(game, command.kind, command.row, command.col)
        if error_message:
            console.print(Text(error_message, style="red"))
            needs_draw = False

    draw_board(console, game)
    if game.status is GameStatus.WON:
        console.print(Text("Você venceu!", style="bold green"))
    else:
        console.print(Text("Você abriu uma mina. Fim de jogo.", style="bold red"))
    return 0


def apply_human_command(game: Game, kind: CommandKind, row: int, col: int) -> str | None:
    """Apply a reveal or flag command. Return an error message, or None if it worked."""
    if not game.in_bounds(row, col):
        return (
            f"A célula ({row}, {col}) está fora do tabuleiro "
            f"(linhas 0 a {game.rows - 1}, colunas 0 a {game.cols - 1})."
        )
    try:
        if kind is CommandKind.REVEAL:
            result = game.reveal(row, col)
            if not result.changed:
                return f"A célula ({row}, {col}) já está aberta ou tem bandeira."
        else:
            result = game.toggle_flag(row, col)
            if not result.changed:
                return f"A célula ({row}, {col}) já está aberta: só dá para marcar célula fechada."
    except InvalidMoveError as error:
        return f"Jogada inválida: {error}"
    return None


# ----- agent mode -------------------------------------------------------


def run_agent(game: Game, agent: Agent, console: Console) -> int:
    """Let the agent play the whole game, drawing the board after each move."""
    console.print(f"Agente: {agent.name}\n")
    step = 0

    def on_step(_observation: object, action: Action, result: MoveResult) -> None:
        nonlocal step
        step += 1
        console.print(Text(f"Jogada {step}: {describe_action(action, result)}", style="bold"))
        draw_board(console, game, highlight=action.cell)
        console.print()

    try:
        outcome = play_game(agent, game, on_step=on_step)
    except AgentStuckError as error:
        console.print(Text(str(error), style="bold red"))
        return 1

    print_summary(console, outcome)
    return 0


def describe_action(action: Action, result: MoveResult) -> str:
    cell = f"({action.row}, {action.col})"
    if action.type is ActionType.REVEAL:
        text = f"abrir {cell}" + (" [chute]" if action.is_guess else "")
    elif action.type is ActionType.FLAG:
        text = f"colocar bandeira em {cell}"
    else:
        text = f"tirar bandeira de {cell}"
    if not result.changed:
        text += " - sem efeito"
    return text


def print_summary(console: Console, outcome: GameResult) -> None:
    if outcome.won:
        console.print(Text("O agente venceu!", style="bold green"))
    else:
        console.print(Text("O agente abriu uma mina.", style="bold red"))
    console.print(f"  Jogadas: {outcome.moves} (abrir: {outcome.reveals}, bandeiras: {outcome.flags})")
    console.print(f"  Chutes: {outcome.guesses} | jogadas sem efeito: {outcome.wasted_moves}")
    console.print(
        f"  Células abertas: {outcome.revealed_cells}/{outcome.config.safe_cells} "
        f"({outcome.revealed_ratio:.0%})"
    )
    console.print(f"  Tempo por jogada: {outcome.seconds_per_move * 1000:.2f} ms")


# ----- shared drawing ---------------------------------------------------


def draw_board(console: Console, game: Game, highlight: tuple[int, int] | None = None) -> None:
    """Draw the board and the status line. Shows the mines once the game is over."""
    observation = game.observe()
    mines = game.mine_positions() if game.is_over else frozenset()
    console.print(
        render_board(
            observation,
            mines=mines,
            exploded=game.exploded_cell,
            highlight=highlight,
        )
    )
    console.print(status_line(observation))
