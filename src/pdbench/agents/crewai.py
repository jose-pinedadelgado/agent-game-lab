"""CrewAI-style agent: structured role/goal/backstory personality definitions."""

from __future__ import annotations

from pathlib import Path

import yaml

from pdbench.agents.llm import LLMAgent
from pdbench.agents.providers.base import ProviderClient
from pdbench.core.types import CrewAIAgentConfig, LLMAgentConfig


def _load_crewai_profile(
    config: CrewAIAgentConfig,
    config_base_path: Path,
) -> dict[str, str]:
    """Resolve role/goal/backstory from inline fields or agents_file + agent_key.

    Returns a dict with keys 'role', 'goal', 'backstory'.
    """
    # Inline definition takes precedence
    if config.role is not None and config.goal is not None and config.backstory is not None:
        return {
            "role": config.role.strip(),
            "goal": config.goal.strip(),
            "backstory": config.backstory.strip(),
        }

    # File-based definition
    if config.agents_file is None or config.agent_key is None:
        raise ValueError(
            "CrewAI agent must have either inline role/goal/backstory "
            "or agents_file + agent_key"
        )

    agents_path = config_base_path / "configs" / config.agents_file
    with open(agents_path) as f:
        agents_data = yaml.safe_load(f)

    if config.agent_key not in agents_data:
        available = ", ".join(agents_data.keys())
        raise ValueError(
            f"Agent key '{config.agent_key}' not found in {agents_path}. "
            f"Available keys: {available}"
        )

    profile = agents_data[config.agent_key]
    return {
        "role": profile["role"].strip(),
        "goal": profile["goal"].strip(),
        "backstory": profile["backstory"].strip(),
    }


def _format_persona_text(profile: dict[str, str]) -> str:
    """Assemble role/goal/backstory into a persona_text string."""
    return (
        f"**Role:** {profile['role']}\n"
        f"**Goal:** {profile['goal']}\n"
        f"**Backstory:** {profile['backstory']}"
    )


class CrewAIAgent(LLMAgent):
    """LLM agent with CrewAI-style role/goal/backstory personality."""

    def __init__(
        self,
        config: CrewAIAgentConfig,
        provider: ProviderClient | None = None,
        config_base_path: Path | None = None,
    ) -> None:
        base_path = config_base_path or Path(".")

        # Resolve the CrewAI profile
        profile = _load_crewai_profile(config, base_path)
        persona_text = _format_persona_text(profile)

        # Convert to LLMAgentConfig for the parent class
        llm_config = LLMAgentConfig(
            type="llm",
            provider=config.provider,
            model=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            mock=config.mock,
            prompting=config.prompting,
            output=config.output,
        )

        super().__init__(
            config=llm_config,
            provider=provider,
            config_base_path=base_path,
        )

        # Override persona text with assembled CrewAI profile
        self._persona_text = persona_text
