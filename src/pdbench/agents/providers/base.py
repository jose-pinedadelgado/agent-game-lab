"""Provider base interface."""

from __future__ import annotations

from typing import Protocol


class ProviderClient(Protocol):
    """Protocol for LLM provider clients."""

    def complete(
        self,
        *,
        system: str,
        prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Generate a completion.

        Args:
            system: System prompt.
            prompt: User/round prompt.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.

        Returns:
            The generated text.
        """
        ...
