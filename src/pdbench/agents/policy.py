"""Policy agents: ALLC, ALLD, TFT, GRIM, GTFT, WSLS."""

from __future__ import annotations

from pdbench.core.rng import SeededRNG
from pdbench.core.types import Action, Observation


class PolicyAgent:
    """Base class for policy agents."""

    def reset(self, seed: int | None = None) -> None:
        """Reset for a new game."""
        pass

    def act(self, obs: Observation) -> str:
        """Choose an action."""
        raise NotImplementedError


class ALLC(PolicyAgent):
    """Always Cooperate."""

    def act(self, obs: Observation) -> str:
        return "C"


class ALLD(PolicyAgent):
    """Always Defect."""

    def act(self, obs: Observation) -> str:
        return "D"


class TFT(PolicyAgent):
    """Tit-for-Tat: Start with C, then copy opponent's previous action."""

    def act(self, obs: Observation) -> str:
        if not obs.history:
            return "C"
        # History tuple: (my_action, opp_action, my_payoff, opp_payoff)
        _, opp_last_action, _, _ = obs.history[-1]
        return opp_last_action.value


class GRIM(PolicyAgent):
    """Grim Trigger: Cooperate until opponent defects, then always defect."""

    def __init__(self) -> None:
        self._triggered = False

    def reset(self, seed: int | None = None) -> None:
        self._triggered = False

    def act(self, obs: Observation) -> str:
        if self._triggered:
            return "D"

        # Check if opponent ever defected
        for _, opp_action, _, _ in obs.history:
            if opp_action == Action.DEFECT:
                self._triggered = True
                return "D"

        return "C"


class GTFT(PolicyAgent):
    """Generous Tit-for-Tat: Like TFT but forgives defections with probability generous_prob."""

    def __init__(self, generous_prob: float = 0.1, seed: int | None = None) -> None:
        self._generous_prob = generous_prob
        self._rng = SeededRNG(seed)

    def reset(self, seed: int | None = None) -> None:
        self._rng.reset(seed)

    def act(self, obs: Observation) -> str:
        if not obs.history:
            return "C"

        _, opp_last_action, _, _ = obs.history[-1]

        if opp_last_action == Action.DEFECT:
            # With generous_prob, forgive and cooperate anyway
            if self._rng.random() < self._generous_prob:
                return "C"
            return "D"

        return "C"


class WSLS(PolicyAgent):
    """Win-Stay Lose-Shift: Repeat last action if payoff >= threshold, otherwise switch."""

    def __init__(self, win_threshold: int = 3, seed: int | None = None) -> None:
        self._win_threshold = win_threshold
        self._rng = SeededRNG(seed)  # Not used currently but kept for interface consistency

    def reset(self, seed: int | None = None) -> None:
        self._rng.reset(seed)

    def act(self, obs: Observation) -> str:
        if not obs.history:
            return "C"

        my_last_action, _, my_last_payoff, _ = obs.history[-1]

        if my_last_payoff >= self._win_threshold:
            # Win: stay with the same action
            return my_last_action.value
        else:
            # Lose: switch
            return "D" if my_last_action == Action.COOPERATE else "C"


# Registry of policy agents
POLICY_REGISTRY: dict[str, type[PolicyAgent]] = {
    "ALLC": ALLC,
    "ALLD": ALLD,
    "TFT": TFT,
    "GRIM": GRIM,
    "GTFT": GTFT,
    "WSLS": WSLS,
}


def create_policy_agent(
    policy_name: str,
    generous_prob: float = 0.1,
    wsls_win_threshold: int = 3,
    seed: int | None = None,
) -> PolicyAgent:
    """Create a policy agent by name."""
    if policy_name not in POLICY_REGISTRY:
        raise ValueError(f"Unknown policy: {policy_name}. Available: {list(POLICY_REGISTRY.keys())}")

    cls = POLICY_REGISTRY[policy_name]

    if cls == GTFT:
        return GTFT(generous_prob=generous_prob, seed=seed)
    elif cls == WSLS:
        return WSLS(win_threshold=wsls_win_threshold, seed=seed)
    elif cls == GRIM:
        return GRIM()
    else:
        return cls()
