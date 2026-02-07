"""Unit tests for CrewAI-style agent."""

from __future__ import annotations

from pathlib import Path

import pytest

from pdbench.agents.crewai import CrewAIAgent, _format_persona_text, _load_crewai_profile
from pdbench.agents.providers.mock import MockProvider
from pdbench.core.types import (
    CrewAIAgentConfig,
    MockConfig,
    Observation,
    PromptingConfig,
)


@pytest.fixture
def config_base_path() -> Path:
    """Project root for resolving config paths."""
    return Path(__file__).parent.parent.parent


class TestLoadCrewAIProfile:
    """Tests for profile resolution from inline or file."""

    def test_inline_profile(self, config_base_path: Path) -> None:
        config = CrewAIAgentConfig(
            role="Test role",
            goal="Test goal",
            backstory="Test backstory",
        )
        profile = _load_crewai_profile(config, config_base_path)
        assert profile["role"] == "Test role"
        assert profile["goal"] == "Test goal"
        assert profile["backstory"] == "Test backstory"

    def test_file_profile(self, config_base_path: Path) -> None:
        config = CrewAIAgentConfig(
            agents_file="agents/crewai/agents.yaml",
            agent_key="strategic_cooperator",
        )
        profile = _load_crewai_profile(config, config_base_path)
        assert "mutual benefit" in profile["role"].lower() or "cooperation" in profile["role"].lower()
        assert profile["goal"]
        assert profile["backstory"]

    def test_file_profile_ruthless(self, config_base_path: Path) -> None:
        config = CrewAIAgentConfig(
            agents_file="agents/crewai/agents.yaml",
            agent_key="ruthless_optimizer",
        )
        profile = _load_crewai_profile(config, config_base_path)
        assert "self-interest" in profile["goal"].lower() or "own payoff" in profile["goal"].lower()

    def test_missing_agent_key_raises(self, config_base_path: Path) -> None:
        config = CrewAIAgentConfig(
            agents_file="agents/crewai/agents.yaml",
            agent_key="nonexistent_agent",
        )
        with pytest.raises(ValueError, match="nonexistent_agent"):
            _load_crewai_profile(config, config_base_path)

    def test_missing_file_raises(self, config_base_path: Path) -> None:
        config = CrewAIAgentConfig(
            agents_file="agents/crewai/does_not_exist.yaml",
            agent_key="test",
        )
        with pytest.raises(FileNotFoundError):
            _load_crewai_profile(config, config_base_path)

    def test_no_inline_no_file_raises(self, config_base_path: Path) -> None:
        config = CrewAIAgentConfig()  # No inline, no file ref
        with pytest.raises(ValueError, match="either inline"):
            _load_crewai_profile(config, config_base_path)

    def test_partial_inline_uses_file(self, config_base_path: Path) -> None:
        """If only some inline fields set, fall through to file lookup."""
        config = CrewAIAgentConfig(
            role="Partial",  # goal and backstory missing
            agents_file="agents/crewai/agents.yaml",
            agent_key="adaptive_diplomat",
        )
        profile = _load_crewai_profile(config, config_base_path)
        # Should use file-based profile, not partial inline
        assert "diplomat" in profile["backstory"].lower()


class TestFormatPersonaText:
    """Tests for persona text formatting."""

    def test_format(self) -> None:
        profile = {"role": "R", "goal": "G", "backstory": "B"}
        text = _format_persona_text(profile)
        assert "**Role:** R" in text
        assert "**Goal:** G" in text
        assert "**Backstory:** B" in text


class TestCrewAIAgent:
    """Tests for CrewAIAgent initialization and behavior."""

    def test_init_inline(self, config_base_path: Path) -> None:
        config = CrewAIAgentConfig(
            role="Cooperator",
            goal="Cooperate always",
            backstory="Friendly agent",
            provider="mock",
            mock=MockConfig(mode="fixed", fixed_output="C"),
        )
        agent = CrewAIAgent(config=config, config_base_path=config_base_path)
        assert "**Role:** Cooperator" in agent._persona_text
        assert "**Goal:** Cooperate always" in agent._persona_text

    def test_init_from_file(self, config_base_path: Path) -> None:
        config = CrewAIAgentConfig(
            agents_file="agents/crewai/agents.yaml",
            agent_key="strategic_cooperator",
            provider="mock",
            mock=MockConfig(mode="fixed", fixed_output="C"),
        )
        agent = CrewAIAgent(config=config, config_base_path=config_base_path)
        assert "**Role:**" in agent._persona_text
        assert "**Goal:**" in agent._persona_text
        assert "**Backstory:**" in agent._persona_text

    def test_act_returns_valid_action(self, config_base_path: Path) -> None:
        config = CrewAIAgentConfig(
            role="Player",
            goal="Play well",
            backstory="Smart agent",
            provider="mock",
            mock=MockConfig(mode="fixed", fixed_output="D"),
        )
        agent = CrewAIAgent(config=config, config_base_path=config_base_path)
        agent.reset()

        obs = Observation(
            round_number=1,
            history=[],
            my_cumulative_payoff=0,
            opponent_cumulative_payoff=0,
            payoff_matrix={"C": {"C": [3, 3], "D": [0, 5]}, "D": {"C": [5, 0], "D": [1, 1]}},
            horizon_type="fixed",
            total_rounds=10,
        )
        action = agent.act(obs)
        assert action in ("C", "D")
        assert action == "D"

    def test_act_cooperate(self, config_base_path: Path) -> None:
        config = CrewAIAgentConfig(
            role="Cooperator",
            goal="Always cooperate",
            backstory="Nice",
            provider="mock",
            mock=MockConfig(mode="fixed", fixed_output="C"),
        )
        agent = CrewAIAgent(config=config, config_base_path=config_base_path)
        agent.reset()

        obs = Observation(
            round_number=1,
            history=[],
            my_cumulative_payoff=0,
            opponent_cumulative_payoff=0,
            payoff_matrix={"C": {"C": [3, 3], "D": [0, 5]}, "D": {"C": [5, 0], "D": [1, 1]}},
            horizon_type="fixed",
            total_rounds=10,
        )
        assert agent.act(obs) == "C"

    def test_with_explicit_provider(self, config_base_path: Path) -> None:
        config = CrewAIAgentConfig(
            role="Tester",
            goal="Test",
            backstory="Testing",
        )
        mock = MockProvider(config=MockConfig(mode="fixed", fixed_output="D"))
        agent = CrewAIAgent(config=config, provider=mock, config_base_path=config_base_path)
        agent.reset()

        obs = Observation(
            round_number=1,
            history=[],
            my_cumulative_payoff=0,
            opponent_cumulative_payoff=0,
            payoff_matrix={"C": {"C": [3, 3], "D": [0, 5]}, "D": {"C": [5, 0], "D": [1, 1]}},
            horizon_type="fixed",
            total_rounds=5,
        )
        assert agent.act(obs) == "D"
