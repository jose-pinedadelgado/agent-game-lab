"""Agent base interface."""

from __future__ import annotations

from typing import Protocol

from pdbench.core.types import Observation


class Agent(Protocol):
    """Protocol for all agents."""

    def reset(self, seed: int | None = None) -> None:
        """Reset the agent for a new game."""
        ...

    def act(self, obs: Observation) -> str:
        """Choose an action given an observation.

        Returns "C" or "D".
        """
        ...
