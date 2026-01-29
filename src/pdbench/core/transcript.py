"""Transcript and history window construction."""

from __future__ import annotations

from pdbench.core.types import Action, Observation, RoundResult


class TranscriptBuilder:
    """Builds transcript/observation for agents from game history."""

    def __init__(
        self,
        history_window: int = 10,
        include_cumulative_totals: bool = True,
        payoff_matrix: dict[str, dict[str, list[int]]] | None = None,
        horizon_type: str = "fixed",
        total_rounds: int | None = None,
    ) -> None:
        """Initialize the transcript builder."""
        self._history_window = history_window
        self._include_cumulative_totals = include_cumulative_totals
        self._payoff_matrix = payoff_matrix or {
            "C": {"C": [3, 3], "D": [0, 5]},
            "D": {"C": [5, 0], "D": [1, 1]},
        }
        self._horizon_type = horizon_type
        self._total_rounds = total_rounds
        self._rounds: list[RoundResult] = []

    def add_round(self, result: RoundResult) -> None:
        """Add a round result to the transcript."""
        self._rounds.append(result)

    def reset(self) -> None:
        """Clear all rounds."""
        self._rounds = []

    def build_observation(
        self,
        round_number: int,
        for_agent: str,  # "a" or "b"
    ) -> Observation:
        """Build an observation for the specified agent."""
        # Get windowed history
        window_start = max(0, len(self._rounds) - self._history_window)
        windowed_rounds = self._rounds[window_start:]

        # Build history tuples from agent's perspective
        history: list[tuple[Action, Action, int, int]] = []
        for r in windowed_rounds:
            if for_agent == "a":
                history.append((
                    r.agent_a_action,
                    r.agent_b_action,
                    r.agent_a_payoff,
                    r.agent_b_payoff,
                ))
            else:
                history.append((
                    r.agent_b_action,
                    r.agent_a_action,
                    r.agent_b_payoff,
                    r.agent_a_payoff,
                ))

        # Get cumulative payoffs
        if self._rounds:
            last_round = self._rounds[-1]
            if for_agent == "a":
                my_cum = last_round.agent_a_cum_payoff
                opp_cum = last_round.agent_b_cum_payoff
            else:
                my_cum = last_round.agent_b_cum_payoff
                opp_cum = last_round.agent_a_cum_payoff
        else:
            my_cum = 0
            opp_cum = 0

        return Observation(
            round_number=round_number,
            history=history,
            my_cumulative_payoff=my_cum,
            opponent_cumulative_payoff=opp_cum,
            payoff_matrix=self._payoff_matrix,
            horizon_type=self._horizon_type,  # type: ignore
            total_rounds=self._total_rounds,
        )


def format_history_text(observation: Observation) -> str:
    """Format history as readable text for prompts."""
    if not observation.history:
        return "No history yet (this is the first round)."

    lines = []
    start_round = observation.round_number - len(observation.history)
    for i, (my_action, opp_action, my_payoff, opp_payoff) in enumerate(observation.history):
        round_num = start_round + i
        lines.append(
            f"Round {round_num}: You played {my_action}, Opponent played {opp_action} "
            f"-> You got {my_payoff}, Opponent got {opp_payoff}"
        )
    return "\n".join(lines)


def format_cumulative_totals(observation: Observation) -> str:
    """Format cumulative totals for prompts."""
    return (
        f"Your cumulative payoff: {observation.my_cumulative_payoff}\n"
        f"Opponent's cumulative payoff: {observation.opponent_cumulative_payoff}"
    )


def format_horizon_text(observation: Observation) -> str:
    """Format horizon information for prompts."""
    if observation.horizon_type == "fixed" and observation.total_rounds is not None:
        return f" of {observation.total_rounds}"
    return " (game continues until stopped)"
