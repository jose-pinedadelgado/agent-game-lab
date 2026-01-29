"""Integration tests for runner with MockProvider."""

import tempfile
from pathlib import Path

import pytest

from pdbench.core.types import (
    AgentRef,
    ConditionConfig,
    ExperimentConfig,
    FullExperimentConfig,
    GameConfig,
    HorizonConfig,
    MetricsConfig,
    RunConfig,
)
from pdbench.runners.run_experiment import run_experiment


@pytest.fixture
def config_base_path() -> Path:
    """Get the config base path (project root)."""
    # Navigate from tests/integration to project root
    return Path(__file__).parent.parent.parent


@pytest.fixture
def temp_output_dir() -> Path:
    """Create a temporary output directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestRunnerWithMockProvider:
    """Integration tests for the experiment runner."""

    def test_run_small_experiment(
        self, config_base_path: Path, temp_output_dir: Path
    ) -> None:
        """Test running a small experiment with mock provider."""
        config = FullExperimentConfig(
            run=RunConfig(
                run_id="test_run",
                seed=42,
                output_dir=str(temp_output_dir / "test_run"),
                store_prompts=False,
                store_raw_responses=False,
            ),
            game=GameConfig(),
            horizon=HorizonConfig(type="fixed", n_rounds=5),
            experiment=ExperimentConfig(
                replicates=2,
                conditions=[
                    ConditionConfig(
                        name="TFT_vs_ALLD",
                        agent_a=AgentRef(
                            ref="agents/policies.yaml",
                            overrides={"policy": "TFT"},
                        ),
                        agent_b=AgentRef(
                            ref="agents/policies.yaml",
                            overrides={"policy": "ALLD"},
                        ),
                    ),
                ],
            ),
            metrics=MetricsConfig(),
        )

        output_dir = run_experiment(
            config=config,
            config_base_path=config_base_path,
            replicates_override=2,
        )

        # Verify output files exist
        assert (output_dir / "run_manifest.json").exists()
        assert (output_dir / "rounds.jsonl").exists()
        assert (output_dir / "aggregates.parquet").exists()

    def test_run_with_llm_agent(
        self, config_base_path: Path, temp_output_dir: Path
    ) -> None:
        """Test running with LLM agent using MockProvider."""
        config = FullExperimentConfig(
            run=RunConfig(
                run_id="test_llm_run",
                seed=42,
                output_dir=str(temp_output_dir / "test_llm_run"),
                store_prompts=True,
                store_raw_responses=True,
            ),
            game=GameConfig(),
            horizon=HorizonConfig(type="fixed", n_rounds=3),
            experiment=ExperimentConfig(
                replicates=1,
                conditions=[
                    ConditionConfig(
                        name="MockLLM_vs_TFT",
                        agent_a=AgentRef(
                            ref="agents/llm_default.yaml",
                            overrides={"persona": "cooperative"},
                        ),
                        agent_b=AgentRef(
                            ref="agents/policies.yaml",
                            overrides={"policy": "TFT"},
                        ),
                    ),
                ],
            ),
            metrics=MetricsConfig(),
        )

        output_dir = run_experiment(
            config=config,
            config_base_path=config_base_path,
        )

        # Verify output files exist
        assert (output_dir / "run_manifest.json").exists()
        assert (output_dir / "rounds.jsonl").exists()
        assert (output_dir / "aggregates.parquet").exists()

    def test_tft_vs_alld_behavior(
        self, config_base_path: Path, temp_output_dir: Path
    ) -> None:
        """Test that TFT vs ALLD produces expected behavior."""
        import json

        config = FullExperimentConfig(
            run=RunConfig(
                run_id="test_behavior",
                seed=42,
                output_dir=str(temp_output_dir / "test_behavior"),
            ),
            game=GameConfig(),
            horizon=HorizonConfig(type="fixed", n_rounds=10),
            experiment=ExperimentConfig(
                replicates=1,
                conditions=[
                    ConditionConfig(
                        name="TFT_vs_ALLD",
                        agent_a=AgentRef(
                            ref="agents/policies.yaml",
                            overrides={"policy": "TFT"},
                        ),
                        agent_b=AgentRef(
                            ref="agents/policies.yaml",
                            overrides={"policy": "ALLD"},
                        ),
                    ),
                ],
            ),
            metrics=MetricsConfig(),
        )

        output_dir = run_experiment(
            config=config,
            config_base_path=config_base_path,
        )

        # Load rounds
        rounds = []
        with open(output_dir / "rounds.jsonl") as f:
            for line in f:
                rounds.append(json.loads(line))

        # TFT starts with C, ALLD always plays D
        # Round 0: TFT=C, ALLD=D
        assert rounds[0]["agent_a_action"] == "C"
        assert rounds[0]["agent_b_action"] == "D"

        # Round 1+: TFT mirrors ALLD's D, so both play D
        for r in rounds[1:]:
            assert r["agent_a_action"] == "D"
            assert r["agent_b_action"] == "D"
