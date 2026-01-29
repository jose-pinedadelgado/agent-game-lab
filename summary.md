# Agentic Cooperation Game Theory (pd-agents)

## Project Overview
A reproducible benchmark harness for studying AI agent cooperation and defection dynamics through the Iterated Prisoner's Dilemma (PD). The project enables systematic comparison of policy-based agents and LLM-powered agents in game-theoretic scenarios.

## Tech Stack
- **Language**: Python 3.12+
- **Package Manager**: UV
- **CLI Framework**: Typer
- **Config/Validation**: Pydantic v2, PyYAML
- **Data Processing**: Pandas, PyArrow (Parquet)
- **UI**: Streamlit (read-only viewer)
- **Testing**: pytest

## Key Components
- `src/pdbench/` - Main source code
  - `cli.py` - CLI commands (validate, run, aggregate, ui)
  - `core/` - Game engine (payoff, horizon, transcript, metrics, parsing)
  - `agents/` - Agent implementations
    - `policy.py` - Deterministic policy agents
    - `llm.py` - LLM-backed agents
  - `providers/` - LLM provider adapters (mock, litellm, openai, anthropic)
  - `runners/` - Experiment orchestration
  - `storage/` - JSONL/Parquet schemas and aggregation
  - `ui/` - Streamlit visualization app
- `configs/` - YAML configuration files
  - `experiment.yaml` - Main experiment config
  - `agents/` - Agent configurations
  - `prompts/` - System and round prompts
  - `personas/` - Agent persona definitions

## Policy Agents
| Agent | Strategy |
|-------|----------|
| ALLC | Always Cooperate |
| ALLD | Always Defect |
| TFT | Tit-for-Tat (copy opponent's last move) |
| GRIM | Grim Trigger (defect forever after first defection) |
| GTFT | Generous TFT (occasionally forgives) |
| WSLS | Win-Stay Lose-Shift |

## Metrics Computed
- `cooperation_rate` - Fraction of C actions
- `retaliation_rate` - P(D at t | opponent D at t-1)
- `forgiveness_rate` - P(C at t | opponent D at t-1)
- `exploitability_payoff_gap` - Payoff difference between agents
- `time_to_collapse` - First round where cooperation collapses
- `cooperation_rate_over_time` - Time series of cooperation rates

## Output Artifacts
- `run_manifest.json` - Run metadata, config snapshot, environment info
- `rounds.jsonl` - One JSON record per round with actions, payoffs, timestamps
- `aggregates.parquet` - Aggregated metrics per condition/replicate

## Purpose
Research platform for:
1. Benchmarking LLM agent behavior in strategic interactions
2. Comparing AI cooperation patterns to classic game theory strategies
3. Studying emergence of cooperation/defection in multi-round games
4. Reproducible experiments with deterministic seeding

## Timeline
- **Started**: January 2025
- **Current Phase**: Phase 1 (baseline)

## Status
Phase 1 implementation - core functionality complete with policy agents, mock LLM provider, experiment runner, and Streamlit viewer.

## Phase 1 Constraints
- No tools, no browsing, no long-term memory
- 2-player only
- Temperature=0 for determinism
- MockProvider for testing without API keys

## CLI Commands
```bash
pdbench validate configs/experiment.yaml    # Validate config
pdbench run configs/experiment.yaml --replicates 2    # Run experiment
pdbench aggregate data/runs/<run_id>    # Recompute aggregates
pdbench ui data/runs/<run_id>    # Launch Streamlit viewer
```
