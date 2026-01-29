"""LLM-backed agent using provider adapters."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pdbench.agents.providers.base import ProviderClient
from pdbench.agents.providers.mock import MockProvider
from pdbench.core.parse import ParseError, RetryParser
from pdbench.core.payoff import PayoffMatrix
from pdbench.core.transcript import (
    format_cumulative_totals,
    format_history_text,
    format_horizon_text,
)
from pdbench.core.types import (
    LLMAgentConfig,
    MockConfig,
    Observation,
    PayoffMatrixConfig,
)


class LLMAgent:
    """LLM-backed agent that uses prompts and a provider to generate actions."""

    def __init__(
        self,
        config: LLMAgentConfig,
        provider: ProviderClient | None = None,
        config_base_path: Path | None = None,
    ) -> None:
        """Initialize the LLM agent.

        Args:
            config: LLM agent configuration.
            provider: Optional provider client. If None, creates based on config.
            config_base_path: Base path for resolving relative config paths.
        """
        self._config = config
        self._config_base_path = config_base_path or Path(".")
        self._parser = RetryParser(max_retries=config.output.retry.max_retries)

        # Create provider if not provided
        if provider is not None:
            self._provider = provider
        elif config.provider == "mock":
            self._provider = MockProvider(config=config.mock)
        else:
            raise ValueError(f"Unsupported provider: {config.provider}")

        # Load prompt templates
        self._system_prompt = self._load_prompt(config.prompting.system_prompt_path)
        self._round_prompt_template = self._load_prompt(config.prompting.round_prompt_path)
        self._persona_text = self._load_persona(config.prompting.persona)

        # Track raw responses for logging
        self._last_raw_response: str | None = None
        self._last_prompts: dict[str, str] | None = None

    def _load_prompt(self, path: str) -> str:
        """Load a prompt template from file."""
        full_path = self._config_base_path / path
        with open(full_path) as f:
            return f.read()

    def _load_persona(self, persona_name: str) -> str:
        """Load a persona fragment from file."""
        persona_path = (
            self._config_base_path
            / "configs"
            / "prompts"
            / "personas"
            / f"{persona_name}.md"
        )
        if persona_path.exists():
            with open(persona_path) as f:
                return f.read()
        return ""

    def reset(self, seed: int | None = None) -> None:
        """Reset the agent for a new game."""
        if hasattr(self._provider, "reset"):
            self._provider.reset(seed)
        self._last_raw_response = None
        self._last_prompts = None

    def _build_round_prompt(self, obs: Observation) -> str:
        """Build the round prompt from observation."""
        # Build payoff table text
        payoff_matrix = PayoffMatrix(PayoffMatrixConfig(**obs.payoff_matrix))
        payoff_table_text = payoff_matrix.format_table()

        # Build history text
        history_text = format_history_text(obs)

        # Build cumulative totals text
        if self._config.prompting.include_cumulative_totals:
            cumulative_totals_text = format_cumulative_totals(obs)
        else:
            cumulative_totals_text = "Not shown."

        # Build horizon text
        horizon_text = format_horizon_text(obs)

        # Format the round prompt
        return self._round_prompt_template.format(
            persona_text=self._persona_text,
            payoff_table_text=payoff_table_text,
            round_number=obs.round_number,
            horizon_text=horizon_text,
            cumulative_totals_text=cumulative_totals_text,
            history_text=history_text,
        )

    def act(self, obs: Observation) -> str:
        """Choose an action given an observation.

        Returns "C" or "D".
        """
        round_prompt = self._build_round_prompt(obs)

        self._last_prompts = {
            "system": self._system_prompt,
            "round": round_prompt,
        }

        # Get completion from provider
        response = self._provider.complete(
            system=self._system_prompt,
            prompt=round_prompt,
            temperature=self._config.temperature,
            max_tokens=self._config.max_tokens,
        )
        self._last_raw_response = response

        # Define retry callback
        def retry_callback(correction_prompt: str) -> str:
            new_prompt = round_prompt + "\n\n" + correction_prompt
            new_response = self._provider.complete(
                system=self._system_prompt,
                prompt=new_prompt,
                temperature=self._config.temperature,
                max_tokens=self._config.max_tokens,
            )
            self._last_raw_response = new_response
            return new_response

        # Parse with retries
        try:
            action = self._parser.parse_with_retry(response, retry_callback)
            return action.value
        except ParseError:
            # If all retries fail, default to cooperate (logged as error)
            return "C"

    @property
    def last_raw_response(self) -> str | None:
        """Get the last raw response from the provider."""
        return self._last_raw_response

    @property
    def last_prompts(self) -> dict[str, str] | None:
        """Get the last prompts sent to the provider."""
        return self._last_prompts

    @property
    def parse_attempts(self) -> list[Any]:
        """Get parse attempts from the last act() call."""
        return self._parser.attempts
