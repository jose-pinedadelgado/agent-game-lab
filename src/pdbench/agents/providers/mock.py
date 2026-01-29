"""Mock provider for testing and default runs."""

from __future__ import annotations

from pdbench.core.rng import SeededRNG
from pdbench.core.types import MockConfig


class MockProvider:
    """Mock provider that returns deterministic outputs."""

    def __init__(
        self,
        config: MockConfig | None = None,
        seed: int | None = None,
    ) -> None:
        """Initialize the mock provider.

        Args:
            config: Mock configuration.
            seed: Random seed for scripted mode.
        """
        self._config = config or MockConfig()
        self._rng = SeededRNG(seed)
        self._call_count = 0
        self._scripted_index = 0

    def reset(self, seed: int | None = None) -> None:
        """Reset the provider state."""
        self._rng.reset(seed)
        self._call_count = 0
        self._scripted_index = 0

    def complete(
        self,
        *,
        system: str,
        prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Return a mock completion.

        In 'fixed' mode, always returns fixed_output.
        In 'scripted' mode, returns outputs from scripted_outputs list in order.
        """
        self._call_count += 1

        if self._config.mode == "fixed":
            return self._config.fixed_output

        elif self._config.mode == "scripted":
            if not self._config.scripted_outputs:
                return self._config.fixed_output

            output = self._config.scripted_outputs[
                self._scripted_index % len(self._config.scripted_outputs)
            ]
            self._scripted_index += 1
            return output

        return self._config.fixed_output

    @property
    def call_count(self) -> int:
        """Get the number of complete() calls."""
        return self._call_count
