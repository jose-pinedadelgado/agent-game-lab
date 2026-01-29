"""Registry: Maps config to agent objects, loads YAML refs with overrides."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from pdbench.agents.llm import LLMAgent
from pdbench.agents.policy import create_policy_agent
from pdbench.core.types import (
    AgentRef,
    LLMAgentConfig,
    PolicyAgentConfig,
)


def load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file."""
    with open(path) as f:
        return yaml.safe_load(f)


def merge_overrides(base: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    """Deep merge overrides into base config."""
    result = base.copy()
    for key, value in overrides.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_overrides(result[key], value)
        else:
            result[key] = value
    return result


def create_agent_from_ref(
    ref: AgentRef,
    config_base_path: Path,
    seed: int | None = None,
) -> Any:
    """Create an agent from a config reference with overrides."""
    # Load the referenced config file
    config_path = config_base_path / "configs" / ref.ref
    base_config = load_yaml(config_path)

    # Apply overrides
    merged_config = merge_overrides(base_config, ref.overrides)

    agent_type = merged_config.get("type")

    if agent_type == "policy":
        policy_config = PolicyAgentConfig(**merged_config)
        return create_policy_agent(
            policy_name=policy_config.policy,
            generous_prob=policy_config.policy_params.generous_prob,
            wsls_win_threshold=policy_config.policy_params.wsls_win_threshold,
            seed=seed,
        )

    elif agent_type == "llm":
        llm_config = LLMAgentConfig(**merged_config)
        return LLMAgent(
            config=llm_config,
            config_base_path=config_base_path,
        )

    else:
        raise ValueError(f"Unknown agent type: {agent_type}")


class AgentRegistry:
    """Registry for creating agents from config."""

    def __init__(self, config_base_path: Path) -> None:
        """Initialize with config base path."""
        self._config_base_path = config_base_path

    def create_agent(self, ref: AgentRef, seed: int | None = None) -> Any:
        """Create an agent from a reference."""
        return create_agent_from_ref(ref, self._config_base_path, seed=seed)
