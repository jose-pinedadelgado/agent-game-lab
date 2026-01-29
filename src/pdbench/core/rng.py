"""Seeded RNG utilities for deterministic experiments."""

from __future__ import annotations

import random
from typing import TypeVar

T = TypeVar("T")


class SeededRNG:
    """A seeded random number generator for deterministic experiments."""

    def __init__(self, seed: int | None = None) -> None:
        """Initialize with an optional seed."""
        self._seed = seed
        self._rng = random.Random(seed)

    @property
    def seed(self) -> int | None:
        """Get the seed."""
        return self._seed

    def reset(self, seed: int | None = None) -> None:
        """Reset the RNG with a new seed."""
        self._seed = seed if seed is not None else self._seed
        self._rng = random.Random(self._seed)

    def random(self) -> float:
        """Return a random float in [0, 1)."""
        return self._rng.random()

    def choice(self, seq: list[T]) -> T:
        """Return a random element from a non-empty sequence."""
        return self._rng.choice(seq)

    def should_stop(self, stop_prob: float) -> bool:
        """Return True with probability stop_prob."""
        return self._rng.random() < stop_prob

    def fork(self, suffix: int = 0) -> "SeededRNG":
        """Create a new RNG with a derived seed for independent streams."""
        if self._seed is None:
            return SeededRNG(None)
        return SeededRNG(self._seed + suffix + 1)
