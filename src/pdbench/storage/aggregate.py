"""Aggregation: compute aggregated metrics, write Parquet."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from pdbench.core.logging import load_rounds_jsonl
from pdbench.core.metrics import ConditionMetrics, compute_metrics_for_replicate


def write_aggregates(output_dir: Path, metrics: list[ConditionMetrics]) -> None:
    """Write aggregated metrics to Parquet file."""
    if not metrics:
        return

    # Convert to list of dicts
    records = [asdict(m) for m in metrics]

    # Create DataFrame
    df = pd.DataFrame(records)

    # Write to Parquet
    parquet_path = output_dir / "aggregates.parquet"
    table = pa.Table.from_pandas(df)
    pq.write_table(table, parquet_path)


def load_aggregates(output_dir: Path) -> pd.DataFrame:
    """Load aggregated metrics from Parquet file."""
    parquet_path = output_dir / "aggregates.parquet"
    return pd.read_parquet(parquet_path)


def recompute_aggregates(
    output_dir: Path,
    collapse_k: int = 10,
    collapse_threshold: float = 0.2,
) -> None:
    """Recompute aggregated metrics from rounds.jsonl (idempotent)."""
    rounds_path = output_dir / "rounds.jsonl"
    rounds = load_rounds_jsonl(rounds_path)

    # Group by condition and replicate
    grouped: dict[tuple[str, int], list[dict[str, Any]]] = {}
    for r in rounds:
        key = (r["condition"], r["replicate"])
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(r)

    # Compute metrics for each group
    metrics = []
    for (condition, replicate), group_rounds in sorted(grouped.items()):
        # Sort by round_index to ensure correct order
        group_rounds.sort(key=lambda x: x["round_index"])
        m = compute_metrics_for_replicate(
            rounds=group_rounds,
            condition=condition,
            replicate=replicate,
            collapse_k=collapse_k,
            collapse_threshold=collapse_threshold,
        )
        metrics.append(m)

    # Write aggregates
    write_aggregates(output_dir, metrics)


def compute_condition_averages(df: pd.DataFrame) -> pd.DataFrame:
    """Compute average metrics across replicates for each condition."""
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    # Exclude replicate from averaging
    if "replicate" in numeric_cols:
        numeric_cols.remove("replicate")

    return df.groupby("condition")[numeric_cols].mean().reset_index()
