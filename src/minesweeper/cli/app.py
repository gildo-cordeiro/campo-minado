"""Terminal interface: `python -m minesweeper`.

One class holds the screen, the turns and the score, and the screen is
cleared and redrawn every turn:

    ┌────────────── title (mode) / level ──────────────┐
    ├── board ──────────────┐ ┌── move/reasoning log ──┤
    │                       │ │                        │
    ├───────────────────── legend + score ─────────────┤
    message

Two modes:

* human: the player types the cell name (C4 opens, !C4 flags);
* agent: an agent from the registry plays and each move is drawn.

Settings not given on the command line are asked interactively. The other
files of the package: render.py draws the board, commands.py and coords.py
read what the player types, registry.py finds the agents.
"""

from __future__ import annotations

import argparse
import random
import re
import sys
import time
from collections.abc import Sequence
from dataclasses import dataclass

from rich.align import Align
from rich.console import Console, Group, RenderableType
from rich.panel import Panel
from rich.prompt import Confirm as RichConfirm
from rich.prompt import InvalidResponse, Prompt
from rich.table import Table
from rich.text import Text

from minesweeper.agents import Action, Agent, AgentStuckError, GameResult, play_game
from minesweeper.environment import (
    DIFFICULTIES,
    Cell,
    Game,
    GameStatus,
    InvalidMoveError,
    MoveResult,
    Observation,
    get_config,
)

from .commands import HELP_TEXT, Command, CommandError, CommandKind, parse_command
from .coords import cell_label, col_label
from .registry import discover_agents
from .render import CELL_WIDTH, LABEL_WIDTH, render_board, status_line

try:
    # Gives input() line editing and history (arrow keys). Not on Windows.
    import readline
except ImportError:
    readline = None
else:
    # Only moves go to the history (see read_move), not the s/n answers.
    readline.set_auto_history(False)

TITLE_STYLE = "bold cyan"
LOG_LINES = 25
DEFAULT_DELAY = 0.4

MOVE_PROMPT = f"[{TITLE_STYLE}]Sua jogada[/{TITLE_STYLE}] — célula para abrir (ex.: C4), !C4 bandeira, ? ajuda, q sair: "
_ANSI_CODE = re.compile(r"(\x1b\[[0-9;]*m)")

LEGEND = (
    "[dim]#[/dim]:fechada  [dim].[/dim]:vazia  [bold bright_blue]1[/bold bright_blue]-8:minas vizinhas  "
    "[bold magenta]F[/bold magenta]:bandeira  [red]*[/red]:mina  "
    "[bold yellow]x[/bold yellow]:bandeira errada  [reverse][ ][/reverse]:última jogada"
)

# Below this width the board and the log side by side do not fit, so the log
# goes under the board.
LOG_MIN_WIDTH = 40
BOARD_MIN_WIDTH = 50  # room for the board panel title and subtitle

DIFFICULTY_LABELS = {
    name: f"{config.rows}x{config.cols}, {config.mines} minas" for name, config in DIFFICULTIES.items()
}


def read_move(console: Console) -> str:
    """Ask for a move with history: the up and down arrows bring back earlier moves.

    The prompt goes to input() itself (not printed before it, as rich does),
    so readline knows its length and does not erase it when going through
    the history. Color codes are wrapped in \\x01 and \\x02 so readline does
    not count them as visible characters.
    """
    with console.capture() as capture:
        console.print(MOVE_PROMPT, end="")
    prompt = capture.get()
    if readline is not None and sys.stdin.isatty():
        prompt = _ANSI_CODE.sub("\x01\\1\x02", prompt)
    line = input(prompt)
    if readline is not None and line.strip():
        readline.add_history(line.strip())
    return line


class Confirm(RichConfirm):
    """rich's Confirm in Portuguese (s/n)."""

    choices = ["s", "n"]
    validate_error_message = "[prompt.invalid]Digite s ou n"

    def process_response(self, value: str) -> bool:
        value = value.strip().lower()
        if value not in self.choices:
            raise InvalidResponse(self.validate_error_message)
        return value == "s"


# --- Configuration ---


@dataclass
class Settings:
    """mode is 'human' or 'agent'; agent_name is only set in agent mode."""

    mode: str
    difficulty: str
    agent_name: str | None = None

    @property
    def level_label(self) -> str:
        return f"Nível {self.difficulty}: {DIFFICULTY_LABELS[self.difficulty]}"


def ask_settings(
    console: Console,
    agents: dict[str, type[Agent]],
    mode: str | None = None,
    difficulty: str | None = None,
    agent_name: str | None = None,
) -> Settings:
    """Ask only the settings that were not given."""
    if mode is None:
        if agents:
            mode = Prompt.ask(
                "Modo (human: você joga, agent: um agente joga)",
                choices=["human", "agent"],
                default="human",
                console=console,
            )
        else:
            console.print("[dim]Nenhum agente implementado ainda: modo human.[/dim]")
            mode = "human"

    if mode == "agent" and agent_name is None:
        agent_name = Prompt.ask("Agente", choices=list(agents), default=next(iter(agents)), console=console)

    if difficulty is None:
        for name, label in DIFFICULTY_LABELS.items():
            console.print(f"[dim]  {name}: {label}[/dim]")
        difficulty = Prompt.ask("Dificuldade", choices=list(DIFFICULTIES), default="easy", console=console)

    return Settings(mode, difficulty, agent_name if mode == "agent" else None)


# --- Interface ---


class MinesweeperCLI:
    """Full-screen terminal interface, redrawn every turn."""

    def __init__(
        self,
        settings: Settings,
        agents: dict[str, type[Agent]],
        seed: int | None = None,
        delay: float = DEFAULT_DELAY,
        console: Console | None = None,
    ) -> None:
        self.console = console or Console()
        self.agents = agents
        self.delay = delay
        self.next_seed = seed
        self.wins = 0
        self.losses = 0
        self.configure(settings)

    def configure(self, settings: Settings) -> None:
        self.settings = settings
        self.config = get_config(settings.difficulty)
        self.agent: Agent | None = None
        if settings.mode == "agent":
            assert settings.agent_name is not None
            self.agent = self.agents[settings.agent_name]()

    def reset(self) -> None:
        seed = self.next_seed if self.next_seed is not None else random.randrange(2**31)
        self.next_seed = None  # only the first game uses the --seed given
        self.game = Game(self.config, seed=seed)
        self.log: list[str] = []
        self.highlight: Cell | None = None
        self.message = ""

    @property
    def player_label(self) -> str:
        return "Humano" if self.agent is None else f"Agente {self.agent.name}"

    # --- Rendering ---

    def render_board_panel(self) -> Panel:
        """The board, with the mines shown once the game is over."""
        game = self.game
        observation = game.observe()
        mines = game.mine_positions() if game.is_over else frozenset()
        board = render_board(observation, mines=mines, exploded=game.exploded_cell, highlight=self.highlight)
        return Panel(
            Align.center(board),
            title=f"Tabuleiro (seed {game.seed})",
            subtitle=status_line(observation).plain,
        )

    def render_log(self) -> Panel:
        title = "Log de Jogadas" if self.agent is None else "Log de Raciocínio do Agente"
        text = "\n".join(self.log[-LOG_LINES:]) or "[dim]Aguardando a primeira jogada...[/dim]"
        return Panel(Text.from_markup(text), title=title)

    def render_legend(self) -> Panel:
        score = f"Placar ({self.player_label}) — vitórias {self.wins} × {self.losses} derrotas"
        return Panel(Text.from_markup(f"{LEGEND}\n{score}", justify="center"), title="Legenda")

    def render_main(self) -> RenderableType:
        """Board on the left and log on the right, or stacked if the terminal is narrow."""
        board_panel, log_panel = self.render_board_panel(), self.render_log()
        board_width = max(LABEL_WIDTH + CELL_WIDTH * self.config.cols + 4, BOARD_MIN_WIDTH)
        if self.console.width < board_width + LOG_MIN_WIDTH:
            return Group(board_panel, log_panel)

        grid = Table.grid(expand=True, padding=(0, 1))
        grid.add_column(min_width=board_width)
        grid.add_column(ratio=1)
        grid.add_row(board_panel, log_panel)
        return grid

    def render(self) -> None:
        self.console.clear()
        self.console.print(header_panel(self.player_label, self.settings.level_label))
        self.console.print(self.render_main())
        self.console.print(self.render_legend())
        if self.message:
            self.console.print(Align.center(Text.from_markup(self.message)))
            self.message = ""

    # --- Human turns ---

    def ask_command(self) -> Command:
        """Read lines until a reveal or flag command arrives.

        Typing errors and the help are shown right below the prompt, without
        redrawing the screen. 'q' raises KeyboardInterrupt to end the session.
        """
        while True:
            line = read_move(self.console)
            try:
                command = parse_command(line)
            except CommandError as error:
                self.console.print(f"[red]{error}[/red]")
                continue
            if command.kind is CommandKind.QUIT:
                raise KeyboardInterrupt
            if command.kind is CommandKind.HELP:
                self.console.print(Panel(HELP_TEXT, title="Ajuda", expand=False))
                continue
            return command

    def human_turn(self) -> None:
        while True:
            command = self.ask_command()
            result = apply_command(self.game, command)
            if isinstance(result, MoveResult):
                break
            self.console.print(f"[red]{result}[/red]")

        self.highlight = result.cell
        self.log.append(move_header(self.game.moves, command_to_action(command), result))
        if len(result.revealed) > 1:
            self.log.append(f"  abriu {len(result.revealed)} células")

    # --- Agent turns ---

    def on_agent_step(self, _observation: Observation, action: Action, result: MoveResult) -> None:
        assert self.agent is not None
        self.log.append(move_header(self.game.moves, action, result))
        self.log.extend(self.agent.explain())
        self.highlight = action.cell
        if not self.game.is_over:
            self.render()
            time.sleep(self.delay)

    def agent_game(self) -> GameResult | None:
        assert self.agent is not None
        try:
            return play_game(self.agent, self.game, on_step=self.on_agent_step)
        except AgentStuckError as error:
            self.log.append(f"[bold red]{error}[/bold red]")
            return None

    # --- Game loop ---

    def play_game(self) -> None:
        self.reset()
        outcome: GameResult | None = None

        if self.agent is None:
            while not self.game.is_over:
                self.render()
                self.human_turn()
        else:
            self.render()
            time.sleep(self.delay)
            outcome = self.agent_game()

        self.finish(outcome)
        self.render()

    def finish(self, outcome: GameResult | None) -> None:
        """Update the score and write the end-of-game message."""
        status = self.game.status
        if status is GameStatus.WON:
            self.wins += 1
            who = "Você venceu" if self.agent is None else "O agente venceu"
            self.message = f"[bold green]FIM DE JOGO: {who}![/bold green]"
        elif status is GameStatus.LOST:
            self.losses += 1
            who = "Você abriu" if self.agent is None else "O agente abriu"
            self.message = f"[bold red]FIM DE JOGO: {who} uma mina![/bold red]"
        else:
            self.message = "[bold yellow]FIM DE JOGO: o agente não terminou a partida.[/bold yellow]"
        self.log.append(self.message)
        if outcome is not None:
            self.log.extend(summary_lines(outcome))

    def run(self) -> None:
        try:
            while True:
                self.play_game()
                if not Confirm.ask("Jogar novamente?", default=True, console=self.console):
                    break
                if Confirm.ask("Alterar configurações?", default=False, console=self.console):
                    self.configure(ask_settings(self.console, self.agents))
        except (KeyboardInterrupt, EOFError):
            pass
        self.console.print(f"\n[{TITLE_STYLE}]Sessão encerrada.[/{TITLE_STYLE}]")


def header_panel(player_label: str, subtitle: str) -> Panel:
    title = f"[{TITLE_STYLE}]Campo Minado Probabilístico — {player_label}[/{TITLE_STYLE}]"
    return Panel(Align.center(title), subtitle=subtitle)


# --- Moves and log lines ---


def command_to_action(command: Command) -> Action:
    if command.kind is CommandKind.REVEAL:
        return Action.reveal(command.row, command.col)
    return Action.flag(command.row, command.col)


def apply_command(game: Game, command: Command) -> MoveResult | str:
    """Apply a reveal or flag command. Return its result, or an error message."""
    row, col = command.row, command.col
    name = cell_label((row, col))
    if not game.in_bounds(row, col):
        return (
            f"A célula {name} está fora do tabuleiro "
            f"(colunas A a {col_label(game.cols - 1)}, linhas 1 a {game.rows})."
        )
    try:
        if command.kind is CommandKind.REVEAL:
            result = game.reveal(row, col)
            if not result.changed:
                if game.observe().is_flagged(row, col):
                    return f"A célula {name} tem bandeira. Tire com !{name} antes de abrir."
                return f"A célula {name} já está aberta."
        else:
            result = game.toggle_flag(row, col)
            if not result.changed:
                return f"A célula {name} já está aberta: só dá para marcar célula fechada."
    except InvalidMoveError as error:
        return f"Jogada inválida: {error}"
    return result


def describe_move(action: Action, result: MoveResult) -> str:
    """'abrir C4', 'bandeira em C4'... with markers for guesses and mines."""
    cell = cell_label(action.cell)
    if result.action == "reveal":
        text = f"abrir {cell}" + (" [yellow]\\[chute][/yellow]" if action.is_guess else "")
    elif result.action == "flag":
        text = f"bandeira em {cell}"
    else:
        text = f"tirar bandeira de {cell}"
    if result.hit_mine:
        text += " [bold red]MINA![/bold red]"
    if not result.changed:
        text += " [dim]- sem efeito[/dim]"
    return text


def move_header(number: int, action: Action, result: MoveResult) -> str:
    return f"[bold white]─── Jogada {number}: {describe_move(action, result)} ───[/bold white]"


def summary_lines(outcome: GameResult) -> list[str]:
    """Metrics of an agent's game, shown in the log when it ends."""
    return [
        f"[bold]Jogadas: {outcome.moves}[/bold] [dim](abrir={outcome.reveals} bandeiras={outcome.flags})[/dim]",
        f"Chutes: {outcome.guesses} | jogadas sem efeito: {outcome.wasted_moves}",
        f"Células abertas: {outcome.revealed_cells}/{outcome.config.safe_cells} ({outcome.revealed_ratio:.0%})",
        f"Tempo por jogada: {outcome.seconds_per_move * 1000:.2f} ms",
    ]


# --- Entry point ---


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m minesweeper",
        description=(
            "Campo Minado Probabilístico: jogue ou assista um agente jogar. "
            "O que não for passado por argumento é perguntado ao iniciar."
        ),
    )
    parser.add_argument(
        "--mode",
        choices=("human", "agent"),
        help="human: você joga; agent: um agente joga",
    )
    parser.add_argument(
        "--difficulty",
        choices=tuple(DIFFICULTIES),
        help="easy 9x9/10 minas, medium 16x16/40, hard 16x30/99",
    )
    parser.add_argument(
        "--agent",
        metavar="NOME",
        help="nome do agente (modo agent)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        help="seed do primeiro tabuleiro; a mesma seed repete a mesma partida",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=DEFAULT_DELAY,
        help=f"segundos entre as jogadas do agente (padrão: {DEFAULT_DELAY})",
    )
    return parser


def main(argv: Sequence[str] | None = None, console: Console | None = None) -> int:
    """Run the CLI and return the exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)
    console = console or Console()

    agents = discover_agents()
    if args.agent is not None:
        if not agents:
            parser.error("nenhum agente foi implementado ainda em minesweeper.agents")
        if args.agent not in agents:
            parser.error(f"agente '{args.agent}' não existe (disponíveis: {', '.join(agents)})")
        if args.mode is None:
            args.mode = "agent"
    if args.mode == "agent" and not agents:
        parser.error("nenhum agente foi implementado ainda em minesweeper.agents")

    needs_questions = args.mode is None or args.difficulty is None or (args.mode == "agent" and args.agent is None)
    if needs_questions:
        console.clear()
        console.print(header_panel("configuração", "[dim]Ctrl+C para sair[/dim]"))
    try:
        settings = ask_settings(console, agents, args.mode, args.difficulty, args.agent)
    except (KeyboardInterrupt, EOFError):
        return 0

    MinesweeperCLI(settings, agents, seed=args.seed, delay=args.delay, console=console).run()
    return 0
