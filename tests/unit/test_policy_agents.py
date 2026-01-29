"""Unit tests for policy agents."""

import pytest

from pdbench.agents.policy import (
    ALLC,
    ALLD,
    GRIM,
    GTFT,
    TFT,
    WSLS,
    create_policy_agent,
)
from pdbench.core.types import Action, Observation


def make_obs(
    round_number: int = 1,
    history: list[tuple[str, str, int, int]] | None = None,
) -> Observation:
    """Create a test observation."""
    if history is None:
        history_typed = []
    else:
        history_typed = [
            (Action(my), Action(opp), my_p, opp_p)
            for my, opp, my_p, opp_p in history
        ]

    return Observation(
        round_number=round_number,
        history=history_typed,
        my_cumulative_payoff=0,
        opponent_cumulative_payoff=0,
        payoff_matrix={"C": {"C": [3, 3], "D": [0, 5]}, "D": {"C": [5, 0], "D": [1, 1]}},
        horizon_type="fixed",
        total_rounds=100,
    )


class TestALLC:
    """Tests for Always Cooperate."""

    def test_always_cooperates(self) -> None:
        """Test that ALLC always returns C."""
        agent = ALLC()

        # First round
        assert agent.act(make_obs(1)) == "C"

        # After opponent cooperates
        assert agent.act(make_obs(2, [("C", "C", 3, 3)])) == "C"

        # After opponent defects
        assert agent.act(make_obs(2, [("C", "D", 0, 5)])) == "C"


class TestALLD:
    """Tests for Always Defect."""

    def test_always_defects(self) -> None:
        """Test that ALLD always returns D."""
        agent = ALLD()

        # First round
        assert agent.act(make_obs(1)) == "D"

        # After any history
        assert agent.act(make_obs(2, [("D", "C", 5, 0)])) == "D"
        assert agent.act(make_obs(2, [("D", "D", 1, 1)])) == "D"


class TestTFT:
    """Tests for Tit-for-Tat."""

    def test_starts_with_cooperate(self) -> None:
        """Test that TFT cooperates on first round."""
        agent = TFT()
        assert agent.act(make_obs(1)) == "C"

    def test_mirrors_opponent(self) -> None:
        """Test that TFT copies opponent's last action."""
        agent = TFT()

        # After opponent cooperates, cooperate
        obs = make_obs(2, [("C", "C", 3, 3)])
        assert agent.act(obs) == "C"

        # After opponent defects, defect
        obs = make_obs(2, [("C", "D", 0, 5)])
        assert agent.act(obs) == "D"

        # Back to cooperate after opponent cooperates
        obs = make_obs(3, [("C", "D", 0, 5), ("D", "C", 5, 0)])
        assert agent.act(obs) == "C"


class TestGRIM:
    """Tests for Grim Trigger."""

    def test_starts_with_cooperate(self) -> None:
        """Test that GRIM cooperates on first round."""
        agent = GRIM()
        assert agent.act(make_obs(1)) == "C"

    def test_cooperates_while_opponent_cooperates(self) -> None:
        """Test that GRIM cooperates if opponent never defected."""
        agent = GRIM()

        obs = make_obs(2, [("C", "C", 3, 3)])
        assert agent.act(obs) == "C"

        obs = make_obs(3, [("C", "C", 3, 3), ("C", "C", 3, 3)])
        assert agent.act(obs) == "C"

    def test_defects_forever_after_opponent_defects(self) -> None:
        """Test that GRIM defects forever after opponent defects once."""
        agent = GRIM()

        # Opponent defects
        obs = make_obs(2, [("C", "D", 0, 5)])
        assert agent.act(obs) == "D"

        # Even if opponent cooperates again, GRIM keeps defecting
        obs = make_obs(3, [("C", "D", 0, 5), ("D", "C", 5, 0)])
        assert agent.act(obs) == "D"

    def test_reset_clears_trigger(self) -> None:
        """Test that reset clears the triggered state."""
        agent = GRIM()

        # Trigger GRIM
        obs = make_obs(2, [("C", "D", 0, 5)])
        agent.act(obs)

        # Reset
        agent.reset()

        # Should cooperate again
        assert agent.act(make_obs(1)) == "C"


class TestGTFT:
    """Tests for Generous Tit-for-Tat."""

    def test_starts_with_cooperate(self) -> None:
        """Test that GTFT cooperates on first round."""
        agent = GTFT(generous_prob=0.1, seed=42)
        assert agent.act(make_obs(1)) == "C"

    def test_deterministic_with_seed(self) -> None:
        """Test that GTFT is deterministic with same seed."""
        agent1 = GTFT(generous_prob=0.5, seed=42)
        agent2 = GTFT(generous_prob=0.5, seed=42)

        # After opponent defects, outcomes should match
        obs = make_obs(2, [("C", "D", 0, 5)])

        result1 = agent1.act(obs)
        result2 = agent2.act(obs)

        assert result1 == result2

    def test_sometimes_forgives(self) -> None:
        """Test that GTFT sometimes forgives defection."""
        # With high generous_prob, should sometimes cooperate after defection
        results = set()
        for seed in range(100):
            agent = GTFT(generous_prob=0.5, seed=seed)
            obs = make_obs(2, [("C", "D", 0, 5)])
            results.add(agent.act(obs))

        # Should have both C and D outcomes
        assert results == {"C", "D"}


class TestWSLS:
    """Tests for Win-Stay Lose-Shift."""

    def test_starts_with_cooperate(self) -> None:
        """Test that WSLS cooperates on first round."""
        agent = WSLS(win_threshold=3)
        assert agent.act(make_obs(1)) == "C"

    def test_stays_on_win(self) -> None:
        """Test that WSLS repeats action if payoff >= threshold."""
        agent = WSLS(win_threshold=3)

        # Got 3 from mutual cooperation, stay with C
        obs = make_obs(2, [("C", "C", 3, 3)])
        assert agent.act(obs) == "C"

        # Got 5 from defecting against cooperator, stay with D
        obs = make_obs(2, [("D", "C", 5, 0)])
        assert agent.act(obs) == "D"

    def test_shifts_on_loss(self) -> None:
        """Test that WSLS switches action if payoff < threshold."""
        agent = WSLS(win_threshold=3)

        # Got 0 from cooperating against defector, switch to D
        obs = make_obs(2, [("C", "D", 0, 5)])
        assert agent.act(obs) == "D"

        # Got 1 from mutual defection, switch to C
        obs = make_obs(2, [("D", "D", 1, 1)])
        assert agent.act(obs) == "C"


class TestCreatePolicyAgent:
    """Tests for policy agent factory."""

    def test_create_all_policies(self) -> None:
        """Test that all policies can be created."""
        for policy_name in ["ALLC", "ALLD", "TFT", "GRIM", "GTFT", "WSLS"]:
            agent = create_policy_agent(policy_name)
            # Should be able to act
            result = agent.act(make_obs(1))
            assert result in ["C", "D"]

    def test_invalid_policy(self) -> None:
        """Test that invalid policy name raises error."""
        with pytest.raises(ValueError, match="Unknown policy"):
            create_policy_agent("INVALID")
