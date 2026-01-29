"""Schema definitions for rounds.jsonl and run_manifest.json."""

from __future__ import annotations

from typing import Any

# Required fields in rounds.jsonl
ROUNDS_REQUIRED_FIELDS = [
    "run_id",
    "condition",
    "replicate",
    "round_index",
    "agent_a_action",
    "agent_b_action",
    "agent_a_payoff",
    "agent_b_payoff",
    "agent_a_cum_payoff",
    "agent_b_cum_payoff",
    "horizon_type",
    "timestamp_utc",
]

# Optional fields in rounds.jsonl
ROUNDS_OPTIONAL_FIELDS = [
    "fixed_n",
    "stop_prob",
    "prompts",
    "raw_responses",
]

# Required fields in run_manifest.json
MANIFEST_REQUIRED_FIELDS = [
    "run_id",
    "config_hash",
    "config_snapshot",
    "environment",
]


def validate_round_record(record: dict[str, Any]) -> list[str]:
    """Validate a round record. Returns list of missing required fields."""
    missing = []
    for field in ROUNDS_REQUIRED_FIELDS:
        if field not in record:
            missing.append(field)
    return missing


def validate_manifest(manifest: dict[str, Any]) -> list[str]:
    """Validate a manifest. Returns list of missing required fields."""
    missing = []
    for field in MANIFEST_REQUIRED_FIELDS:
        if field not in manifest:
            missing.append(field)
    return missing
