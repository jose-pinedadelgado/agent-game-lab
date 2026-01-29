"""Unit tests for horizon implementations."""

import pytest

from pdbench.core.horizon import FixedHorizon, GeometricHorizon, create_horizon
from pdbench.core.types import HorizonConfig


class TestFixedHorizon:
    """Tests for FixedHorizon."""

    def test_stops_at_n_rounds(self) -> None:
        """Test that fixed horizon stops at exactly n rounds."""
        horizon = FixedHorizon(n_rounds=10)

        # Rounds 0-9 should not stop
        for i in range(10):
            assert not horizon.should_stop(i), f"Should not stop at round {i}"

        # Round 10 and beyond should stop
        assert horizon.should_stop(10)
        assert horizon.should_stop(11)
        assert horizon.should_stop(100)

    def test_total_rounds(self) -> None:
        """Test total_rounds property."""
        horizon = FixedHorizon(n_rounds=50)
        assert horizon.total_rounds == 50
        assert horizon.horizon_type == "fixed"

    def test_reset_is_noop(self) -> None:
        """Test that reset doesn't change behavior."""
        horizon = FixedHorizon(n_rounds=10)
        horizon.reset()
        assert not horizon.should_stop(5)
        assert horizon.should_stop(10)


class TestGeometricHorizon:
    """Tests for GeometricHorizon."""

    def test_deterministic_with_seed(self) -> None:
        """Test that geometric horizon is deterministic with same seed."""
        horizon1 = GeometricHorizon(stop_prob=0.1, seed=42)
        horizon2 = GeometricHorizon(stop_prob=0.1, seed=42)

        # Find when first horizon stops
        stop_round = None
        for i in range(1000):
            if horizon1.should_stop(i):
                stop_round = i
                break

        # Reset and check second horizon stops at same round
        horizon1.reset(seed=42)
        horizon2.reset(seed=42)

        for i in range(stop_round):
            assert not horizon1.should_stop(i)
            assert not horizon2.should_stop(i)

        assert horizon1.should_stop(stop_round)

    def test_different_seeds_different_outcomes(self) -> None:
        """Test that different seeds can produce different stop times."""
        # Run multiple trials to find different outcomes
        stop_rounds = set()
        for seed in range(100):
            horizon = GeometricHorizon(stop_prob=0.1, seed=seed)
            for i in range(1000):
                if horizon.should_stop(i):
                    stop_rounds.add(i)
                    break

        # Should have multiple different stop rounds
        assert len(stop_rounds) > 1

    def test_stop_prob_zero_never_stops_early(self) -> None:
        """Test that stop_prob=0 never stops (until max_rounds)."""
        horizon = GeometricHorizon(stop_prob=0.0, seed=42, max_rounds=100)

        for i in range(100):
            assert not horizon.should_stop(i)

        assert horizon.should_stop(100)

    def test_stop_prob_one_stops_immediately(self) -> None:
        """Test that stop_prob=1 stops at round 0."""
        horizon = GeometricHorizon(stop_prob=1.0, seed=42)
        assert horizon.should_stop(0)

    def test_properties(self) -> None:
        """Test horizon properties."""
        horizon = GeometricHorizon(stop_prob=0.1, seed=42)
        assert horizon.horizon_type == "geometric"
        assert horizon.total_rounds is None


class TestCreateHorizon:
    """Tests for create_horizon factory."""

    def test_create_fixed(self) -> None:
        """Test creating fixed horizon from config."""
        config = HorizonConfig(type="fixed", n_rounds=100)
        horizon = create_horizon(config)

        assert isinstance(horizon, FixedHorizon)
        assert horizon.total_rounds == 100

    def test_create_geometric(self) -> None:
        """Test creating geometric horizon from config."""
        config = HorizonConfig(type="geometric", stop_prob=0.05)
        horizon = create_horizon(config, seed=42)

        assert isinstance(horizon, GeometricHorizon)
        assert horizon.total_rounds is None

    def test_invalid_type(self) -> None:
        """Test that invalid horizon type raises error."""
        config = HorizonConfig(type="fixed")
        # Manually set invalid type to bypass pydantic validation
        object.__setattr__(config, "type", "invalid")

        with pytest.raises(ValueError, match="Unknown horizon type"):
            create_horizon(config)
