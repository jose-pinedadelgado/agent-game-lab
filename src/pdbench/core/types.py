"""Core types and Pydantic models for PDBench."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field


class Action(str, Enum):
    """Prisoner's Dilemma actions."""

    COOPERATE = "C"
    DEFECT = "D"

    def __str__(self) -> str:
        return self.value


class RoundResult(BaseModel):
    """Result of a single round."""

    round_index: int
    agent_a_action: Action
    agent_b_action: Action
    agent_a_payoff: int
    agent_b_payoff: int
    agent_a_cum_payoff: int
    agent_b_cum_payoff: int


class Observation(BaseModel):
    """Observation passed to an agent for decision-making."""

    round_number: int
    history: list[tuple[Action, Action, int, int]]  # (my_action, opp_action, my_payoff, opp_payoff)
    my_cumulative_payoff: int
    opponent_cumulative_payoff: int
    payoff_matrix: dict[str, dict[str, list[int]]]
    horizon_type: Literal["fixed", "geometric"]
    total_rounds: int | None = None  # Only for fixed horizon


class PayoffMatrixConfig(BaseModel):
    """Payoff matrix configuration."""

    C: dict[str, list[int]] = Field(default_factory=lambda: {"C": [3, 3], "D": [0, 5]})
    D: dict[str, list[int]] = Field(default_factory=lambda: {"C": [5, 0], "D": [1, 1]})


class GameConfig(BaseModel):
    """Game configuration."""

    name: str = "prisoners_dilemma"
    payoff_matrix: PayoffMatrixConfig = Field(default_factory=PayoffMatrixConfig)


class HorizonConfig(BaseModel):
    """Horizon configuration."""

    type: Literal["fixed", "geometric"] = "fixed"
    n_rounds: int = 100
    stop_prob: float = 0.02


class CollapseConfig(BaseModel):
    """Configuration for time-to-collapse metric."""

    k: int = 10
    cooperation_threshold: float = 0.2


class MetricsConfig(BaseModel):
    """Metrics configuration."""

    collapse: CollapseConfig = Field(default_factory=CollapseConfig)
    report: list[str] = Field(
        default_factory=lambda: [
            "cooperation_rate",
            "cooperation_rate_over_time",
            "retaliation_rate",
            "forgiveness_rate",
            "exploitability_payoff_gap",
            "time_to_collapse",
        ]
    )


class RunConfig(BaseModel):
    """Run configuration."""

    run_id: str
    seed: int = 1337
    output_dir: str = "data/runs"
    store_prompts: bool = True
    store_raw_responses: bool = True


class AgentRef(BaseModel):
    """Reference to an agent config file with optional overrides."""

    ref: str
    overrides: dict[str, Any] = Field(default_factory=dict)


class ConditionConfig(BaseModel):
    """Experiment condition configuration."""

    name: str
    agent_a: AgentRef
    agent_b: AgentRef


class ExperimentConfig(BaseModel):
    """Experiment configuration."""

    replicates: int = 5
    conditions: list[ConditionConfig]


class FullExperimentConfig(BaseModel):
    """Full experiment configuration from YAML."""

    run: RunConfig
    game: GameConfig = Field(default_factory=GameConfig)
    horizon: HorizonConfig = Field(default_factory=HorizonConfig)
    experiment: ExperimentConfig
    metrics: MetricsConfig = Field(default_factory=MetricsConfig)


class MockConfig(BaseModel):
    """Mock provider configuration."""

    mode: Literal["fixed", "scripted"] = "fixed"
    fixed_output: str = "C"
    scripted_outputs: list[str] = Field(default_factory=list)


class RetryConfig(BaseModel):
    """Retry configuration for output parsing."""

    max_retries: int = 2
    on_invalid: str = "reprompt_same_context"


class OutputConfig(BaseModel):
    """Output parsing configuration."""

    format: Literal["single_token", "json"] = "single_token"
    allowed: list[str] = Field(default_factory=lambda: ["C", "D"])
    retry: RetryConfig = Field(default_factory=RetryConfig)


class PromptingConfig(BaseModel):
    """Prompting configuration for LLM agents."""

    system_prompt_path: str = "configs/prompts/pd_system.md"
    round_prompt_path: str = "configs/prompts/pd_round.md"
    persona: str = "cooperative"
    history_window: int = 10
    include_cumulative_totals: bool = True


class LLMAgentConfig(BaseModel):
    """LLM agent configuration."""

    type: Literal["llm"] = "llm"
    provider: str = "mock"
    model: str = "mock-001"
    temperature: float = 0.0
    max_tokens: int = 10
    mock: MockConfig = Field(default_factory=MockConfig)
    prompting: PromptingConfig = Field(default_factory=PromptingConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)


class PolicyParams(BaseModel):
    """Parameters for policy agents."""

    generous_prob: float = 0.1
    wsls_win_threshold: int = 3


class PolicyAgentConfig(BaseModel):
    """Policy agent configuration."""

    type: Literal["policy"] = "policy"
    policy: str = "TFT"
    policy_params: PolicyParams = Field(default_factory=PolicyParams)


def load_config_file(path: Path) -> dict[str, Any]:
    """Load a YAML config file."""
    import yaml

    with open(path) as f:
        return yaml.safe_load(f)
