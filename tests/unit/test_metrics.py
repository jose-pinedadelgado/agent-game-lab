"""Unit tests for metrics computation."""

import pytest

from pdbench.core.metrics import (
    compute_cooperation_rate,
    compute_cooperation_rate_over_time,
    compute_forgiveness_rate,
    compute_metrics_for_replicate,
    compute_retaliation_rate,
    compute_time_to_collapse,
)


class TestCooperationRate:
    """Tests for cooperation_rate metric."""

    def test_all_cooperate(self) -> None:
        """Test 100% cooperation."""
        actions = ["C", "C", "C", "C", "C"]
        assert compute_cooperation_rate(actions) == 1.0

    def test_all_defect(self) -> None:
        """Test 0% cooperation."""
        actions = ["D", "D", "D", "D", "D"]
        assert compute_cooperation_rate(actions) == 0.0

    def test_mixed(self) -> None:
        """Test mixed cooperation."""
        actions = ["C", "C", "D", "D", "C"]
        assert compute_cooperation_rate(actions) == 0.6

    def test_empty(self) -> None:
        """Test empty list."""
        assert compute_cooperation_rate([]) == 0.0


class TestCooperationRateOverTime:
    """Tests for cooperation_rate_over_time metric."""

    def test_cumulative_calculation(self) -> None:
        """Test that rates are cumulative."""
        a_actions = ["C", "C", "D", "C"]
        b_actions = ["C", "D", "C", "C"]

        rates = compute_cooperation_rate_over_time(a_actions, b_actions)

        # Round 1: 2/2 = 1.0
        assert rates[0] == 1.0

        # Round 2: 3/4 = 0.75
        assert rates[1] == 0.75

        # Round 3: 4/6 ≈ 0.667
        assert abs(rates[2] - 0.6667) < 0.01

        # Round 4: 6/8 = 0.75
        assert rates[3] == 0.75


class TestRetaliationRate:
    """Tests for retaliation_rate metric."""

    def test_always_retaliates(self) -> None:
        """Test 100% retaliation."""
        my_actions = ["C", "D", "D", "D"]  # Defect after every opponent defect
        opp_actions = ["D", "D", "D", "C"]

        rate = compute_retaliation_rate(my_actions, opp_actions)
        assert rate == 1.0

    def test_never_retaliates(self) -> None:
        """Test 0% retaliation."""
        my_actions = ["C", "C", "C", "C"]  # Never defect
        opp_actions = ["D", "D", "D", "C"]

        rate = compute_retaliation_rate(my_actions, opp_actions)
        assert rate == 0.0

    def test_partial_retaliation(self) -> None:
        """Test partial retaliation."""
        my_actions = ["C", "D", "C", "D"]  # Defect after 2 of 3 opponent defects
        opp_actions = ["D", "D", "D", "C"]

        rate = compute_retaliation_rate(my_actions, opp_actions)
        assert abs(rate - 0.6667) < 0.01

    def test_no_opponent_defects(self) -> None:
        """Test when opponent never defects."""
        my_actions = ["C", "C", "C"]
        opp_actions = ["C", "C", "C"]

        rate = compute_retaliation_rate(my_actions, opp_actions)
        assert rate is None

    def test_too_short(self) -> None:
        """Test with insufficient history."""
        rate = compute_retaliation_rate(["C"], ["D"])
        assert rate is None


class TestForgivenessRate:
    """Tests for forgiveness_rate metric."""

    def test_always_forgives(self) -> None:
        """Test 100% forgiveness."""
        my_actions = ["C", "C", "C", "C"]  # Always cooperate
        opp_actions = ["D", "D", "D", "C"]

        rate = compute_forgiveness_rate(my_actions, opp_actions)
        assert rate == 1.0

    def test_never_forgives(self) -> None:
        """Test 0% forgiveness."""
        my_actions = ["C", "D", "D", "D"]  # Never cooperate after defect
        opp_actions = ["D", "D", "D", "C"]

        rate = compute_forgiveness_rate(my_actions, opp_actions)
        assert rate == 0.0

    def test_no_opponent_defects(self) -> None:
        """Test when opponent never defects."""
        rate = compute_forgiveness_rate(["C", "C"], ["C", "C"])
        assert rate is None


class TestTimeToCollapse:
    """Tests for time_to_collapse metric."""

    def test_immediate_collapse(self) -> None:
        """Test collapse at round 0."""
        a_actions = ["D"] * 20
        b_actions = ["D"] * 20

        collapse = compute_time_to_collapse(a_actions, b_actions, k=10, threshold=0.2)
        assert collapse == 0

    def test_delayed_collapse(self) -> None:
        """Test collapse after some cooperation."""
        a_actions = ["C"] * 5 + ["D"] * 15
        b_actions = ["C"] * 5 + ["D"] * 15

        collapse = compute_time_to_collapse(a_actions, b_actions, k=10, threshold=0.2)
        # Collapse should occur shortly after round 5
        assert collapse is not None
        assert 0 <= collapse <= 10

    def test_never_collapses(self) -> None:
        """Test mutual cooperation that never collapses."""
        a_actions = ["C"] * 50
        b_actions = ["C"] * 50

        collapse = compute_time_to_collapse(a_actions, b_actions, k=10, threshold=0.2)
        assert collapse is None

    def test_too_few_rounds(self) -> None:
        """Test with fewer rounds than k."""
        collapse = compute_time_to_collapse(["C"] * 5, ["C"] * 5, k=10)
        assert collapse is None


class TestComputeMetricsForReplicate:
    """Tests for compute_metrics_for_replicate."""

    def test_basic_metrics(self) -> None:
        """Test basic metrics computation."""
        rounds = [
            {
                "round_index": 0,
                "agent_a_action": "C",
                "agent_b_action": "C",
                "agent_a_payoff": 3,
                "agent_b_payoff": 3,
                "agent_a_cum_payoff": 3,
                "agent_b_cum_payoff": 3,
            },
            {
                "round_index": 1,
                "agent_a_action": "C",
                "agent_b_action": "D",
                "agent_a_payoff": 0,
                "agent_b_payoff": 5,
                "agent_a_cum_payoff": 3,
                "agent_b_cum_payoff": 8,
            },
        ]

        metrics = compute_metrics_for_replicate(
            rounds=rounds,
            condition="test",
            replicate=0,
        )

        assert metrics.condition == "test"
        assert metrics.replicate == 0
        assert metrics.total_rounds == 2
        assert metrics.agent_a_cooperation_rate == 1.0
        assert metrics.agent_b_cooperation_rate == 0.5
        assert metrics.agent_a_total_payoff == 3
        assert metrics.agent_b_total_payoff == 8
        assert metrics.exploitability_gap_a == 5  # b - a = 8 - 3
