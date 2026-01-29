"""Metrics computation for Prisoner's Dilemma experiments."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from pdbench.core.types import Action


@dataclass
class ConditionMetrics:
    """Metrics for a single condition/replicate."""

    condition: str
    replicate: int
    total_rounds: int

    # Per-agent cooperation rates
    agent_a_cooperation_rate: float
    agent_b_cooperation_rate: float
    overall_cooperation_rate: float

    # Cooperation rate over time (as JSON string for storage)
    cooperation_rate_over_time: str

    # Retaliation and forgiveness (per-agent)
    agent_a_retaliation_rate: float | None
    agent_b_retaliation_rate: float | None
    agent_a_forgiveness_rate: float | None
    agent_b_forgiveness_rate: float | None

    # Payoff gaps
    agent_a_total_payoff: int
    agent_b_total_payoff: int
    exploitability_gap_a: int  # b_payoff - a_payoff (positive means a is exploited)
    exploitability_gap_b: int  # a_payoff - b_payoff

    # Time to collapse
    time_to_collapse: int | None


def compute_cooperation_rate(actions: list[str]) -> float:
    """Compute fraction of C actions."""
    if not actions:
        return 0.0
    return sum(1 for a in actions if a == "C") / len(actions)


def compute_cooperation_rate_over_time(
    agent_a_actions: list[str],
    agent_b_actions: list[str],
) -> list[float]:
    """Compute cooperation rate at each round (cumulative)."""
    rates = []
    a_coops = 0
    b_coops = 0
    for i, (a, b) in enumerate(zip(agent_a_actions, agent_b_actions)):
        if a == "C":
            a_coops += 1
        if b == "C":
            b_coops += 1
        # Overall cooperation rate up to this round
        total_actions = 2 * (i + 1)
        total_coops = a_coops + b_coops
        rates.append(total_coops / total_actions)
    return rates


def compute_retaliation_rate(
    my_actions: list[str],
    opponent_actions: list[str],
) -> float | None:
    """Compute fraction of times I defect at t given opponent defected at t-1."""
    if len(my_actions) < 2:
        return None

    defect_after_defect = 0
    opponent_defects = 0

    for t in range(1, len(my_actions)):
        if opponent_actions[t - 1] == "D":
            opponent_defects += 1
            if my_actions[t] == "D":
                defect_after_defect += 1

    if opponent_defects == 0:
        return None

    return defect_after_defect / opponent_defects


def compute_forgiveness_rate(
    my_actions: list[str],
    opponent_actions: list[str],
) -> float | None:
    """Compute fraction of times I cooperate at t given opponent defected at t-1."""
    if len(my_actions) < 2:
        return None

    coop_after_defect = 0
    opponent_defects = 0

    for t in range(1, len(my_actions)):
        if opponent_actions[t - 1] == "D":
            opponent_defects += 1
            if my_actions[t] == "C":
                coop_after_defect += 1

    if opponent_defects == 0:
        return None

    return coop_after_defect / opponent_defects


def compute_time_to_collapse(
    agent_a_actions: list[str],
    agent_b_actions: list[str],
    k: int = 10,
    threshold: float = 0.2,
) -> int | None:
    """Compute time to collapse.

    Collapse = first round t such that in the next k rounds,
    the cooperation rate (both agents) <= threshold.

    Returns None if never collapses.
    """
    n = len(agent_a_actions)
    if n < k:
        return None

    for t in range(n - k + 1):
        # Check next k rounds starting from t
        window_a = agent_a_actions[t : t + k]
        window_b = agent_b_actions[t : t + k]

        total_coops = sum(1 for a in window_a if a == "C") + sum(1 for b in window_b if b == "C")
        coop_rate = total_coops / (2 * k)

        if coop_rate <= threshold:
            return t

    return None


def compute_metrics_for_replicate(
    rounds: list[dict[str, Any]],
    condition: str,
    replicate: int,
    collapse_k: int = 10,
    collapse_threshold: float = 0.2,
) -> ConditionMetrics:
    """Compute all metrics for a single condition/replicate."""
    # Extract action sequences
    agent_a_actions = [r["agent_a_action"] for r in rounds]
    agent_b_actions = [r["agent_b_action"] for r in rounds]

    # Cooperation rates
    a_coop_rate = compute_cooperation_rate(agent_a_actions)
    b_coop_rate = compute_cooperation_rate(agent_b_actions)
    overall_coop_rate = (a_coop_rate + b_coop_rate) / 2

    # Cooperation rate over time
    coop_over_time = compute_cooperation_rate_over_time(agent_a_actions, agent_b_actions)

    # Retaliation and forgiveness
    a_retaliation = compute_retaliation_rate(agent_a_actions, agent_b_actions)
    b_retaliation = compute_retaliation_rate(agent_b_actions, agent_a_actions)
    a_forgiveness = compute_forgiveness_rate(agent_a_actions, agent_b_actions)
    b_forgiveness = compute_forgiveness_rate(agent_b_actions, agent_a_actions)

    # Total payoffs
    a_total = rounds[-1]["agent_a_cum_payoff"] if rounds else 0
    b_total = rounds[-1]["agent_b_cum_payoff"] if rounds else 0

    # Time to collapse
    collapse = compute_time_to_collapse(
        agent_a_actions, agent_b_actions, k=collapse_k, threshold=collapse_threshold
    )

    return ConditionMetrics(
        condition=condition,
        replicate=replicate,
        total_rounds=len(rounds),
        agent_a_cooperation_rate=a_coop_rate,
        agent_b_cooperation_rate=b_coop_rate,
        overall_cooperation_rate=overall_coop_rate,
        cooperation_rate_over_time=json.dumps(coop_over_time),
        agent_a_retaliation_rate=a_retaliation,
        agent_b_retaliation_rate=b_retaliation,
        agent_a_forgiveness_rate=a_forgiveness,
        agent_b_forgiveness_rate=b_forgiveness,
        agent_a_total_payoff=a_total,
        agent_b_total_payoff=b_total,
        exploitability_gap_a=b_total - a_total,
        exploitability_gap_b=a_total - b_total,
        time_to_collapse=collapse,
    )
