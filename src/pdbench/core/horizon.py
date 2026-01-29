"""Horizon implementations for fixed and geometric stopping."""

from __future__ import annotations

from abc import ABC, abstractmethod

from pdbench.core.rng import SeededRNG
from pdbench.core.types import HorizonConfig


class Horizon(ABC):
    """Abstract base class for game horizons."""

    @abstractmethod
    def should_stop(self, round_index: int) -> bool:
        """Check if the game should stop after this round."""
        ...

    @abstractmethod
    def reset(self, seed: int | None = None) -> None:
        """Reset the horizon for a new game."""
        ...

    @property
    @abstractmethod
    def horizon_type(self) -> str:
        """Return the horizon type name."""
        ...

    @property
    @abstractmethod
    def total_rounds(self) -> int | None:
        """Return total rounds if fixed, None if geometric."""
        ...


class FixedHorizon(Horizon):
    """Fixed number of rounds."""

    def __init__(self, n_rounds: int) -> None:
        """Initialize with fixed number of rounds."""
        self._n_rounds = n_rounds

    def should_stop(self, round_index: int) -> bool:
        """Stop after n_rounds (0-indexed, so stop when round_index >= n_rounds)."""
        return round_index >= self._n_rounds

    def reset(self, seed: int | None = None) -> None:
        """No-op for fixed horizon."""
        pass

    @property
    def horizon_type(self) -> str:
        return "fixed"

    @property
    def total_rounds(self) -> int:
        return self._n_rounds


class GeometricHorizon(Horizon):
    """Geometric stopping with probability stop_prob each round."""

    def __init__(self, stop_prob: float, seed: int | None = None, max_rounds: int = 10000) -> None:
        """Initialize with stop probability and optional seed."""
        self._stop_prob = stop_prob
        self._max_rounds = max_rounds
        self._rng = SeededRNG(seed)
        self._stopped_at: int | None = None

    def should_stop(self, round_index: int) -> bool:
        """Check if should stop, sampling if this round hasn't been checked."""
        if round_index >= self._max_rounds:
            return True
        if self._stopped_at is not None and round_index >= self._stopped_at:
            return True
        if self._stopped_at is None and self._rng.should_stop(self._stop_prob):
            self._stopped_at = round_index
            return True
        return False

    def reset(self, seed: int | None = None) -> None:
        """Reset for a new game."""
        self._rng.reset(seed)
        self._stopped_at = None

    @property
    def horizon_type(self) -> str:
        return "geometric"

    @property
    def total_rounds(self) -> int | None:
        return None


def create_horizon(config: HorizonConfig, seed: int | None = None) -> Horizon:
    """Factory function to create a horizon from config."""
    if config.type == "fixed":
        return FixedHorizon(config.n_rounds)
    elif config.type == "geometric":
        return GeometricHorizon(config.stop_prob, seed=seed)
    else:
        raise ValueError(f"Unknown horizon type: {config.type}")
