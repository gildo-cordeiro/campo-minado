"""Registry of agents by name.

Every module inside minesweeper/agents/ is scanned, and each concrete
subclass of Agent is registered under its `name` attribute. A new agent
therefore shows up in `--agent <name>` as soon as its file exists, without
changing the CLI.
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil

import minesweeper.agents as agents_package
from minesweeper.agents import Agent

# Modules of the agents package that do not define agents.
_NON_AGENT_MODULES = frozenset({"base", "runner"})


def discover_agents() -> dict[str, type[Agent]]:
    """Return {name: agent class} for every agent found, sorted by name."""
    found: dict[str, type[Agent]] = {}
    for module_info in pkgutil.iter_modules(agents_package.__path__):
        if module_info.name in _NON_AGENT_MODULES:
            continue
        module = importlib.import_module(f"{agents_package.__name__}.{module_info.name}")
        for _, candidate in inspect.getmembers(module, inspect.isclass):
            if (
                issubclass(candidate, Agent)
                and not inspect.isabstract(candidate)
                and candidate.__module__ == module.__name__  # skip re-exports
            ):
                if candidate.name in found:
                    raise ValueError(
                        f"two agents use the name '{candidate.name}': "
                        f"{found[candidate.name].__module__} and {candidate.__module__}"
                    )
                found[candidate.name] = candidate
    return dict(sorted(found.items()))
