"""Unit tests for payoff matrix."""

import pytest

from pdbench.core.payoff import PayoffMatrix
from pdbench.core.types import Action, PayoffMatrixConfig


class TestPayoffMatrix:
    """Tests for PayoffMatrix."""

    def test_default_payoffs(self) -> None:
        """Test default PD payoff matrix."""
        pm = PayoffMatrix()

        # (C, C) = (3, 3)
        assert pm.get_payoffs(Action.COOPERATE, Action.COOPERATE) == (3, 3)

        # (C, D) = (0, 5)
        assert pm.get_payoffs(Action.COOPERATE, Action.DEFECT) == (0, 5)

        # (D, C) = (5, 0)
        assert pm.get_payoffs(Action.DEFECT, Action.COOPERATE) == (5, 0)

        # (D, D) = (1, 1)
        assert pm.get_payoffs(Action.DEFECT, Action.DEFECT) == (1, 1)

    def test_custom_payoffs(self) -> None:
        """Test custom payoff matrix."""
        config = PayoffMatrixConfig(
            C={"C": [4, 4], "D": [0, 6]},
            D={"C": [6, 0], "D": [2, 2]},
        )
        pm = PayoffMatrix(config)

        assert pm.get_payoffs(Action.COOPERATE, Action.COOPERATE) == (4, 4)
        assert pm.get_payoffs(Action.COOPERATE, Action.DEFECT) == (0, 6)
        assert pm.get_payoffs(Action.DEFECT, Action.COOPERATE) == (6, 0)
        assert pm.get_payoffs(Action.DEFECT, Action.DEFECT) == (2, 2)

    def test_to_dict(self) -> None:
        """Test serialization to dict."""
        pm = PayoffMatrix()
        d = pm.to_dict()

        assert d["C"]["C"] == [3, 3]
        assert d["C"]["D"] == [0, 5]
        assert d["D"]["C"] == [5, 0]
        assert d["D"]["D"] == [1, 1]

    def test_format_table(self) -> None:
        """Test table formatting."""
        pm = PayoffMatrix()
        table = pm.format_table()

        assert "Your action" in table
        assert "Opponent action" in table
        assert "C" in table
        assert "D" in table


class TestAction:
    """Tests for Action enum."""

    def test_action_values(self) -> None:
        """Test action string values."""
        assert Action.COOPERATE.value == "C"
        assert Action.DEFECT.value == "D"
        assert str(Action.COOPERATE) == "C"
        assert str(Action.DEFECT) == "D"

    def test_action_from_string(self) -> None:
        """Test creating actions from strings."""
        assert Action("C") == Action.COOPERATE
        assert Action("D") == Action.DEFECT

    def test_invalid_action(self) -> None:
        """Test that invalid actions raise ValueError."""
        with pytest.raises(ValueError):
            Action("X")
