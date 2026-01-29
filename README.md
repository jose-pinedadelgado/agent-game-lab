# pd-agents (Phase 1): Iterated Prisoner's Dilemma Benchmark

Phase 1 baseline benchmark harness for iterated Prisoner's Dilemma (PD) between agents:
- Policy agents (ALLC/ALLD/TFT/GRIM/GTFT/WSLS)
- LLM agent wrapper (pluggable providers)
- Reproducible runner (seeded RNG, fixed/geometric horizons)
- Artifacts: JSONL round logs + Parquet aggregates
- Read-only Streamlit viewer

**Phase 1 scope:** no tools, no browsing, no long-term memory beyond per-round transcript.

---

## Requirements
- Python 3.12+
- `uv` installed

---

## Install

From repo root:

```bash
uv sync
```

---

## Quick Start

### Validate configuration

```bash
uv run pdbench validate configs/experiment.yaml
```

### Run experiment

```bash
uv run pdbench run configs/experiment.yaml --replicates 2
```

### View results

```bash
uv run pdbench ui data/runs/phase1_smoke_v1
```

---

## Run Tests

```bash
uv run pytest -q
```

---

## Output Artifacts

After running an experiment, the output directory contains:

- `run_manifest.json` - Run metadata, config snapshot, environment info
- `rounds.jsonl` - One JSON record per round with actions, payoffs, timestamps
- `aggregates.parquet` - Aggregated metrics per condition/replicate

---

## CLI Commands

| Command | Description |
|---------|-------------|
| `pdbench validate <config>` | Validate experiment configuration |
| `pdbench run <config> [--replicates N] [--dry-run]` | Run experiment |
| `pdbench aggregate <run_dir>` | Recompute aggregates from rounds.jsonl |
| `pdbench ui <run_dir>` | Launch Streamlit viewer |

---

## Configuration

See `configs/experiment.yaml` for the full experiment configuration schema.

### Agent Types

**Policy agents** (`configs/agents/policies.yaml`):
- `ALLC` - Always Cooperate
- `ALLD` - Always Defect
- `TFT` - Tit-for-Tat
- `GRIM` - Grim Trigger
- `GTFT` - Generous Tit-for-Tat
- `WSLS` - Win-Stay Lose-Shift

**LLM agents** (`configs/agents/llm_default.yaml`):
- Uses MockProvider by default (no API keys needed)
- Configurable prompts and personas

---

## Metrics

- `cooperation_rate` - Fraction of C actions
- `retaliation_rate` - P(D at t | opponent D at t-1)
- `forgiveness_rate` - P(C at t | opponent D at t-1)
- `exploitability_payoff_gap` - Payoff difference between agents
- `time_to_collapse` - First round where cooperation collapses
- `cooperation_rate_over_time` - Time series of cooperation rates
