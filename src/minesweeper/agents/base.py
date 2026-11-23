"""Common interface for every agent.

To create a new agent, subclass Agent and implement choose_action:

    class MyAgent(Agent):
        name = "my-agent"

        def choose_action(self, observation: Observation) -> Action:
            row, col = observation.hidden_cells()[0]
            return Action.reveal(row, col, is_guess=True)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

from minesweeper.environment import Cell, Observation


class ActionType(str, Enum):
    REVEAL = "reveal"
    FLAG = "flag"
    UNFLAG = "unflag"


@dataclass(frozen=True)
class Action:
    """One decision of the agent.

    is_guess tells the runner that the agent had no logical certainty about
    this move. It feeds the "number of guesses" metric of the PEAS model.
    """

    type: ActionType
    row: int
    col: int
    is_guess: bool = False

    @classmethod
    def reveal(cls, row: int, col: int, is_guess: bool = False) -> Action:
        return cls(ActionType.REVEAL, row, col, is_guess)

    @classmethod
    def flag(cls, row: int, col: int) -> Action:
        return cls(ActionType.FLAG, row, col)

    @classmethod
    def unflag(cls, row: int, col: int) -> Action:
        return cls(ActionType.UNFLAG, row, col)

    @property
    def cell(self) -> Cell:
        return self.row, self.col


class Agent(ABC):
    """Base class: receives what it sees and decides the next action."""

    name: str = "agent"

    def reset(self, seed: int | None = None) -> None:
        """Called by the runner before each new game.

        Override it to clear the agent's memory or to seed its own random
        generator, so that a game can be repeated exactly.
        """

    @abstractmethod
    def choose_action(self, observation: Observation) -> Action:
        """Return the next action, based only on the observation."""

    def explain(self) -> list[str]:
        """Lines explaining the last decision, shown in the CLI's reasoning log.

        Optional: override it to show why the agent chose its last action
        (deduced cells, probabilities...). Lines may use rich markup, e.g.
        "[green]safe[/green]". The CLI calls it right after each action.
        """
        return []
