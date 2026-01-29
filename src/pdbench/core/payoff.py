"""Payoff matrix implementation for Prisoner's Dilemma."""

from __future__ import annotations

from pdbench.core.types import Action, PayoffMatrixConfig


class PayoffMatrix:
    """Payoff matrix for the Prisoner's Dilemma."""

    def __init__(self, config: PayoffMatrixConfig | None = None) -> None:
        """Initialize with optional config, defaults to standard PD payoffs."""
        if config is None:
            config = PayoffMatrixConfig()

        self._matrix: dict[tuple[Action, Action], tuple[int, int]] = {}
        for row_action in ["C", "D"]:
            row_data = getattr(config, row_action)
            for col_action in ["C", "D"]:
                payoffs = row_data[col_action]
                self._matrix[(Action(row_action), Action(col_action))] = (
                    payoffs[0],
                    payoffs[1],
                )

    def get_payoffs(self, action_a: Action, action_b: Action) -> tuple[int, int]:
        """Get payoffs for (agent_a, agent_b) actions.

        Returns (agent_a_payoff, agent_b_payoff).
        """
        return self._matrix[(action_a, action_b)]

    def to_dict(self) -> dict[str, dict[str, list[int]]]:
        """Convert to dictionary format for serialization."""
        result: dict[str, dict[str, list[int]]] = {"C": {}, "D": {}}
        for (a, b), (pa, pb) in self._matrix.items():
            result[a.value][b.value] = [pa, pb]
        return result

    def format_table(self) -> str:
        """Format the payoff matrix as a readable table."""
        lines = [
            "Your action | Opponent action | Your payoff | Opponent payoff",
            "------------|-----------------|-------------|----------------",
        ]
        for my_action in [Action.COOPERATE, Action.DEFECT]:
            for opp_action in [Action.COOPERATE, Action.DEFECT]:
                my_payoff, opp_payoff = self.get_payoffs(my_action, opp_action)
                lines.append(
                    f"     {my_action}      |        {opp_action}        |      {my_payoff}      |       {opp_payoff}"
                )
        return "\n".join(lines)
