"""Integration tests for logging schema validation."""

import json
import tempfile
from pathlib import Path

import pandas as pd
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
from pdbench.storage.schema import (
    ROUNDS_REQUIRED_FIELDS,
    validate_manifest,
    validate_round_record,
)


@pytest.fixture
def config_base_path() -> Path:
    """Get the config base path (project root)."""
    return Path(__file__).parent.parent.parent


@pytest.fixture
def experiment_output(config_base_path: Path) -> Path:
    """Run a small experiment and return output dir."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "schema_test"

        config = FullExperimentConfig(
            run=RunConfig(
                run_id="schema_test",
                seed=42,
                output_dir=str(output_path),
                store_prompts=True,
                store_raw_responses=True,
            ),
            game=GameConfig(),
            horizon=HorizonConfig(type="fixed", n_rounds=5),
            experiment=ExperimentConfig(
                replicates=2,
                conditions=[
                    ConditionConfig(
                        name="ALLC_vs_ALLD",
                        agent_a=AgentRef(
                            ref="agents/policies.yaml",
                            overrides={"policy": "ALLC"},
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

        run_experiment(config=config, config_base_path=config_base_path)
        yield output_path


class TestRoundsJsonlSchema:
    """Tests for rounds.jsonl schema."""

    def test_all_required_fields_present(self, experiment_output: Path) -> None:
        """Test that all required fields are present in each round."""
        rounds_path = experiment_output / "rounds.jsonl"

        with open(rounds_path) as f:
            for i, line in enumerate(f):
                record = json.loads(line)
                missing = validate_round_record(record)
                assert not missing, f"Round {i} missing fields: {missing}"

    def test_action_values(self, experiment_output: Path) -> None:
        """Test that action values are valid."""
        rounds_path = experiment_output / "rounds.jsonl"

        with open(rounds_path) as f:
            for line in f:
                record = json.loads(line)
                assert record["agent_a_action"] in ["C", "D"]
                assert record["agent_b_action"] in ["C", "D"]

    def test_payoff_consistency(self, experiment_output: Path) -> None:
        """Test that cumulative payoffs are consistent."""
        rounds_path = experiment_output / "rounds.jsonl"

        # Group by condition and replicate
        grouped: dict[tuple[str, int], list[dict]] = {}
        with open(rounds_path) as f:
            for line in f:
                record = json.loads(line)
                key = (record["condition"], record["replicate"])
                if key not in grouped:
                    grouped[key] = []
                grouped[key].append(record)

        for key, rounds in grouped.items():
            rounds.sort(key=lambda x: x["round_index"])

            cum_a = 0
            cum_b = 0
            for r in rounds:
                cum_a += r["agent_a_payoff"]
                cum_b += r["agent_b_payoff"]
                assert r["agent_a_cum_payoff"] == cum_a
                assert r["agent_b_cum_payoff"] == cum_b


class TestManifestSchema:
    """Tests for run_manifest.json schema."""

    def test_manifest_required_fields(self, experiment_output: Path) -> None:
        """Test that manifest has required fields."""
        manifest_path = experiment_output / "run_manifest.json"

        with open(manifest_path) as f:
            manifest = json.load(f)

        missing = validate_manifest(manifest)
        assert not missing, f"Manifest missing fields: {missing}"

    def test_manifest_config_snapshot(self, experiment_output: Path) -> None:
        """Test that config snapshot is present."""
        manifest_path = experiment_output / "run_manifest.json"

        with open(manifest_path) as f:
            manifest = json.load(f)

        assert "config_snapshot" in manifest
        assert "run" in manifest["config_snapshot"]
        assert "experiment" in manifest["config_snapshot"]


class TestAggregatesParquet:
    """Tests for aggregates.parquet schema."""

    def test_parquet_readable(self, experiment_output: Path) -> None:
        """Test that parquet file is readable."""
        parquet_path = experiment_output / "aggregates.parquet"
        df = pd.read_parquet(parquet_path)

        assert len(df) > 0

    def test_parquet_columns(self, experiment_output: Path) -> None:
        """Test that parquet has expected columns."""
        parquet_path = experiment_output / "aggregates.parquet"
        df = pd.read_parquet(parquet_path)

        expected_cols = [
            "condition",
            "replicate",
            "total_rounds",
            "agent_a_cooperation_rate",
            "agent_b_cooperation_rate",
            "overall_cooperation_rate",
            "agent_a_total_payoff",
            "agent_b_total_payoff",
        ]

        for col in expected_cols:
            assert col in df.columns, f"Missing column: {col}"

    def test_metrics_values(self, experiment_output: Path) -> None:
        """Test that metrics have reasonable values."""
        parquet_path = experiment_output / "aggregates.parquet"
        df = pd.read_parquet(parquet_path)

        # ALLC always cooperates, ALLD always defects
        for _, row in df.iterrows():
            assert row["agent_a_cooperation_rate"] == 1.0  # ALLC
            assert row["agent_b_cooperation_rate"] == 0.0  # ALLD
            assert row["total_rounds"] == 5
