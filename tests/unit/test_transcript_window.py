"""Unit tests for transcript and history windowing."""

import pytest

from pdbench.core.transcript import (
    TranscriptBuilder,
    format_cumulative_totals,
    format_history_text,
    format_horizon_text,
)
from pdbench.core.types import Action, Observation, RoundResult


def make_round_result(
    round_index: int,
    a_action: str,
    b_action: str,
    a_payoff: int,
    b_payoff: int,
    a_cum: int,
    b_cum: int,
) -> RoundResult:
    """Create a test round result."""
    return RoundResult(
        round_index=round_index,
        agent_a_action=Action(a_action),
        agent_b_action=Action(b_action),
        agent_a_payoff=a_payoff,
        agent_b_payoff=b_payoff,
        agent_a_cum_payoff=a_cum,
        agent_b_cum_payoff=b_cum,
    )


class TestTranscriptBuilder:
    """Tests for TranscriptBuilder."""

    def test_empty_history_on_first_round(self) -> None:
        """Test that first round has empty history."""
        builder = TranscriptBuilder(history_window=10)
        obs = builder.build_observation(round_number=1, for_agent="a")

        assert obs.history == []
        assert obs.round_number == 1
        assert obs.my_cumulative_payoff == 0
        assert obs.opponent_cumulative_payoff == 0

    def test_history_from_agent_a_perspective(self) -> None:
        """Test history is correctly built for agent A."""
        builder = TranscriptBuilder(history_window=10)

        # Add a round: A cooperates, B defects
        builder.add_round(make_round_result(0, "C", "D", 0, 5, 0, 5))

        obs = builder.build_observation(round_number=2, for_agent="a")

        assert len(obs.history) == 1
        my_action, opp_action, my_payoff, opp_payoff = obs.history[0]
        assert my_action == Action.COOPERATE
        assert opp_action == Action.DEFECT
        assert my_payoff == 0
        assert opp_payoff == 5

    def test_history_from_agent_b_perspective(self) -> None:
        """Test history is correctly built for agent B."""
        builder = TranscriptBuilder(history_window=10)

        # Add a round: A cooperates, B defects
        builder.add_round(make_round_result(0, "C", "D", 0, 5, 0, 5))

        obs = builder.build_observation(round_number=2, for_agent="b")

        assert len(obs.history) == 1
        my_action, opp_action, my_payoff, opp_payoff = obs.history[0]
        assert my_action == Action.DEFECT  # B's action
        assert opp_action == Action.COOPERATE  # A's action (opponent)
        assert my_payoff == 5
        assert opp_payoff == 0

    def test_history_window_limits(self) -> None:
        """Test that history window limits the number of rounds shown."""
        builder = TranscriptBuilder(history_window=3)

        # Add 5 rounds
        for i in range(5):
            builder.add_round(make_round_result(i, "C", "C", 3, 3, (i + 1) * 3, (i + 1) * 3))

        obs = builder.build_observation(round_number=6, for_agent="a")

        # Should only have last 3 rounds
        assert len(obs.history) == 3

    def test_cumulative_payoffs(self) -> None:
        """Test cumulative payoff tracking."""
        builder = TranscriptBuilder(history_window=10)

        builder.add_round(make_round_result(0, "C", "C", 3, 3, 3, 3))
        builder.add_round(make_round_result(1, "D", "C", 5, 0, 8, 3))

        obs_a = builder.build_observation(round_number=3, for_agent="a")
        assert obs_a.my_cumulative_payoff == 8
        assert obs_a.opponent_cumulative_payoff == 3

        obs_b = builder.build_observation(round_number=3, for_agent="b")
        assert obs_b.my_cumulative_payoff == 3
        assert obs_b.opponent_cumulative_payoff == 8

    def test_reset(self) -> None:
        """Test that reset clears history."""
        builder = TranscriptBuilder(history_window=10)
        builder.add_round(make_round_result(0, "C", "C", 3, 3, 3, 3))

        builder.reset()

        obs = builder.build_observation(round_number=1, for_agent="a")
        assert obs.history == []
        assert obs.my_cumulative_payoff == 0


class TestFormatHistoryText:
    """Tests for format_history_text."""

    def test_empty_history(self) -> None:
        """Test formatting empty history."""
        obs = Observation(
            round_number=1,
            history=[],
            my_cumulative_payoff=0,
            opponent_cumulative_payoff=0,
            payoff_matrix={},
            horizon_type="fixed",
            total_rounds=100,
        )
        text = format_history_text(obs)
        assert "first round" in text.lower()

    def test_with_history(self) -> None:
        """Test formatting history with entries."""
        obs = Observation(
            round_number=3,
            history=[
                (Action.COOPERATE, Action.COOPERATE, 3, 3),
                (Action.DEFECT, Action.COOPERATE, 5, 0),
            ],
            my_cumulative_payoff=8,
            opponent_cumulative_payoff=3,
            payoff_matrix={},
            horizon_type="fixed",
            total_rounds=100,
        )
        text = format_history_text(obs)

        assert "Round 1" in text
        assert "Round 2" in text
        assert "C" in text
        assert "D" in text


class TestFormatCumulativeTotals:
    """Tests for format_cumulative_totals."""

    def test_format(self) -> None:
        """Test cumulative totals formatting."""
        obs = Observation(
            round_number=5,
            history=[],
            my_cumulative_payoff=15,
            opponent_cumulative_payoff=10,
            payoff_matrix={},
            horizon_type="fixed",
            total_rounds=100,
        )
        text = format_cumulative_totals(obs)

        assert "15" in text
        assert "10" in text


class TestFormatHorizonText:
    """Tests for format_horizon_text."""

    def test_fixed_horizon(self) -> None:
        """Test fixed horizon formatting."""
        obs = Observation(
            round_number=5,
            history=[],
            my_cumulative_payoff=0,
            opponent_cumulative_payoff=0,
            payoff_matrix={},
            horizon_type="fixed",
            total_rounds=100,
        )
        text = format_horizon_text(obs)
        assert "100" in text

    def test_geometric_horizon(self) -> None:
        """Test geometric horizon formatting."""
        obs = Observation(
            round_number=5,
            history=[],
            my_cumulative_payoff=0,
            opponent_cumulative_payoff=0,
            payoff_matrix={},
            horizon_type="geometric",
            total_rounds=None,
        )
        text = format_horizon_text(obs)
        assert "continues" in text.lower() or "stopped" in text.lower()
