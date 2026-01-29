"""Logging infrastructure: JSONL writer, manifest writer, config hashing."""

from __future__ import annotations

import hashlib
import json
import platform
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pdbench.core.types import Action


class JSONLWriter:
    """Writes JSON Lines files."""

    def __init__(self, path: Path) -> None:
        """Initialize with output path."""
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, record: dict[str, Any]) -> None:
        """Append a record to the JSONL file."""
        with open(self._path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, default=self._serialize) + "\n")

    def _serialize(self, obj: Any) -> Any:
        """Serialize non-standard types."""
        if isinstance(obj, Action):
            return obj.value
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, Path):
            return str(obj)
        raise TypeError(f"Cannot serialize {type(obj)}")


class RoundLogger:
    """Logs round data to JSONL."""

    def __init__(self, output_dir: Path, run_id: str) -> None:
        """Initialize with output directory and run ID."""
        self._writer = JSONLWriter(output_dir / "rounds.jsonl")
        self._run_id = run_id

    def log_round(
        self,
        condition: str,
        replicate: int,
        round_index: int,
        agent_a_action: Action,
        agent_b_action: Action,
        agent_a_payoff: int,
        agent_b_payoff: int,
        agent_a_cum_payoff: int,
        agent_b_cum_payoff: int,
        horizon_type: str,
        fixed_n: int | None = None,
        stop_prob: float | None = None,
        prompts: dict[str, str] | None = None,
        raw_responses: dict[str, str] | None = None,
    ) -> None:
        """Log a round result."""
        record = {
            "run_id": self._run_id,
            "condition": condition,
            "replicate": replicate,
            "round_index": round_index,
            "agent_a_action": agent_a_action.value,
            "agent_b_action": agent_b_action.value,
            "agent_a_payoff": agent_a_payoff,
            "agent_b_payoff": agent_b_payoff,
            "agent_a_cum_payoff": agent_a_cum_payoff,
            "agent_b_cum_payoff": agent_b_cum_payoff,
            "horizon_type": horizon_type,
            "fixed_n": fixed_n,
            "stop_prob": stop_prob,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        }
        if prompts:
            record["prompts"] = prompts
        if raw_responses:
            record["raw_responses"] = raw_responses
        self._writer.write(record)


def compute_config_hash(config: dict[str, Any]) -> str:
    """Compute a stable hash of the config for reproducibility tracking."""
    config_str = json.dumps(config, sort_keys=True, default=str)
    return hashlib.sha256(config_str.encode()).hexdigest()[:16]


def write_manifest(
    output_dir: Path,
    run_id: str,
    config: dict[str, Any],
    config_hash: str,
) -> None:
    """Write the run manifest JSON file."""
    manifest = {
        "run_id": run_id,
        "config_hash": config_hash,
        "config_snapshot": config,
        "environment": {
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        },
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "run_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)


def load_rounds_jsonl(path: Path) -> list[dict[str, Any]]:
    """Load all rounds from a JSONL file."""
    rounds = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rounds.append(json.loads(line))
    return rounds


def load_manifest(path: Path) -> dict[str, Any]:
    """Load the run manifest."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)
