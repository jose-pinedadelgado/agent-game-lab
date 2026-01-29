# Phase 1 Spec: Iterated Prisoner’s Dilemma (Baseline “Social” PD)

## Goal
Build a reproducible, configurable benchmark harness for **iterated Prisoner’s Dilemma (PD)** between agents, focused on **Phase 1** only:
- No tools
- No browsing
- No long-term memory beyond the transcript provided per round
- Emphasis on determinism, logging, and testability

This project must:
- Run locally end-to-end without API keys (via a `MockProvider`)
- Support plugging in real LLM providers later (adapter interface)
- Provide CLI + artifacts (JSONL/Parquet) + a read-only Streamlit viewer

## Non-goals (explicitly out of scope for Phase 1)
- Pre-game negotiation / chat
- Tool use, MCP, web access, external APIs (in runtime; tests must be offline)
- Long-term memory / episodic memory persistence across episodes
- Multi-agent >2 (Phase 1 is 2-player only)
- Complex agent frameworks (LangChain/AutoGen/etc.)

---

## Definitions

### Action space
Agents choose exactly one action each round:
- `C` = Cooperate
- `D` = Defect

### Payoff matrix
Default PD payoffs (configurable):
- (C,C) = (3,3)
- (C,D) = (0,5)
- (D,C) = (5,0)
- (D,D) = (1,1)

### Horizon types
- **Fixed horizon:** run exactly `N` rounds.
- **Geometric horizon:** after each round, stop with probability `stop_prob` (seeded RNG).

### Transcript window
On round *t*, the agent receives a context containing:
- Rules + payoff table
- Round number
- Cumulative totals (optional flag)
- The **last `history_window` rounds** of actions and payoffs

No other memory is allowed in Phase 1.

---

## Repository structure (required)
Create this layout (some files may be added, but do not remove these requirements):

```
pd-agents/
README.md
pyproject.toml
.env.example
.gitignore

configs/
experiment.yaml
agents/
llm_default.yaml
policies.yaml
prompts/
pd_system.md
pd_round.md
personas/
cooperative.md
exploitative.md
tit_for_tat.md
grim_trigger.md
generous_tft.md
wsls.md

src/pdbench/
init.py
cli.py
core/
types.py
rng.py
payoff.py
horizon.py
transcript.py
parse.py
metrics.py
logging.py
agents/
base.py
policy.py
llm.py
providers/
base.py
mock.py
litellm.py # optional
openai.py # optional
anthropic.py # optional
runners/
run_experiment.py
registry.py
storage/
schema.py
aggregate.py
ui/
streamlit_app.py

tests/
unit/
integration/
e2e/

data/
.gitkeep
```

---

## Tech choices
### Language & packaging
- Python 3.12+
- Use `pyproject.toml` with **UV only**
- CLI: `typer`
- Config parsing/validation: `pydantic` (v2 preferred) + `pyyaml`
- Data: `pandas`, `pyarrow`
- Tests: `pytest`

### Style tooling (recommended)
- `ruff` for lint (and optionally formatting)

---

## Core abstractions (must implement)

### Agent interface
All agents implement:

```python
from typing import Protocol

class Agent(Protocol):
    def reset(self, seed: int | None = None) -> None: ...
    def act(self, obs: "Observation") -> str:  # returns "C" or "D"
        ...
```
Requirements:

act() must return exactly "C" or "D" after parsing/validation.

Policy agents are pure python and do not call providers.

LLM agents call a provider, parse output, and retry on invalid output.

Provider interface

Providers implement:
```
from typing import Protocol

class ProviderClient(Protocol):
    def complete(
        self,
        *,
        system: str,
        prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> str: ...
```
Required:

MockProvider with deterministic outputs for integration tests and default configs.

Optional adapters:

LiteLLM adapter (recommended for real usage)

OpenAI / Anthropic direct adapters (optional)

Policy agents (must implement)

In src/pdbench/agents/policy.py, implement:

ALLC: always cooperate

ALLD: always defect

TFT (Tit-for-Tat): start C, then copy opponent’s previous action

GRIM: start C, if opponent ever defects, defect forever after

GTFT (Generous TFT): like TFT but occasionally forgives a defect with probability generous_prob

WSLS (Win-Stay Lose-Shift): if last round payoff >= win threshold, repeat action; otherwise switch

Prompting (must implement)
Files

configs/prompts/pd_system.md

configs/prompts/pd_round.md

configs/prompts/personas/*.md (persona fragments)

Requirements

The final prompt must be deterministic and fully logged (if store_prompts=true).

Agents must be instructed to output ONLY C or D (or strict JSON if configured).

Prompt rendering must use Python .format() placeholders (no Jinja2 dependency).

Output format

Default: single token

Allowed outputs: "C" or "D" (case-insensitive trimming permitted)

Anything else is invalid

Retry policy:

max_retries in config (default 2)

On invalid output: re-prompt with a brief correction instruction and the same round context

Log each attempt

Configuration schema (required)
configs/experiment.yaml (example must exist)

Must include:

run metadata (run_id, seed, output_dir)

game payoff matrix

horizon config (fixed/geometric)

experiment conditions (matchups) with overrides

metrics list (and collapse parameters)

configs/agents/llm_default.yaml

Must include:

provider name + model identifier

decoding (temperature, max_tokens)

prompting (system prompt path, round prompt path, persona name, history_window, include totals)

output parsing rules and retry config

MockProvider configuration so the default run works without keys

configs/agents/policies.yaml

Must include:

type=policy and a policy name (overridable in conditions)

The code must support config references like:

agent_a: {ref: "agents/llm_default.yaml", overrides: {persona: "cooperative"}}

Runner behavior (must implement)
CLI commands

Implement pdbench CLI with Typer:

pdbench validate <config_path>

Validates YAML schema and referenced file paths.

Prints a short summary.

pdbench run <config_path> [--replicates N] [--dry-run]

Runs all conditions × replicates.

Writes artifacts into output_dir.

pdbench aggregate <run_dir>

Recomputes aggregated metrics from rounds JSONL (idempotent).

pdbench ui <run_dir>

Launches Streamlit viewer or prints exact Streamlit command.

Determinism

Use seed for:

geometric horizon stopping RNG

policy stochasticity (e.g., GTFT forgiveness)

mock provider deterministic behavior

LLM providers may be non-deterministic; Phase 1 defaults should run with temperature=0.

Storage & schemas (must implement)
Output directory (required files)

Given output_dir = data/runs/<run_id>:

run_manifest.json (run metadata, config snapshot hash, environment info)

rounds.jsonl (one JSON per round event)

aggregates.parquet (aggregated metrics)

rounds.jsonl schema (minimum fields)

Per record:

run_id, condition, replicate, round_index

agent_a_action, agent_b_action

agent_a_payoff, agent_b_payoff

agent_a_cum_payoff, agent_b_cum_payoff

horizon_type, fixed_n, stop_prob

timestamp_utc

Optional when configured:

prompts: {system: ..., round: ...} or prompt hashes

raw_responses: {agent_a: ..., agent_b: ...}

Metrics (must implement)

Compute per condition×replicate, plus condition-average across replicates.

Required metrics definitions

cooperation_rate

fraction of rounds where action == C (report per-agent and overall)

cooperation_rate_over_time

time series (store as JSON string or separate table) of cooperation by round

retaliation_rate

fraction of times agent defects at round t given opponent defected at round t-1

forgiveness_rate

fraction of times agent cooperates at round t given opponent defected at round t-1

exploitability_payoff_gap

(opponent_total_payoff - agent_total_payoff) (report both directions)

time_to_collapse
Define “collapse” as:

the first round index t such that in the next k rounds (default k=10),
the cooperation rate (both agents) <= threshold (default 0.2).

If never collapses, set to None.

k and threshold must be configurable and recorded in the manifest.

Streamlit UI (read-only, must implement)

A Streamlit app that:

Loads a run_dir

Lets user select: condition, replicate

Displays:

per-round actions timeline

cumulative payoff over time

headline metrics panel

Must not re-run experiments; UI is for visualization only.

Testing requirements (must implement)

All tests must pass without network and without API keys.

Unit tests

payoff matrix correctness

fixed/geometric horizon determinism given seed

policy agents behavior

transcript windowing

output parsing/validation + retry logic

Integration tests

runner executes a small experiment using MockProvider

validates:

output files created

rounds.jsonl schema fields exist

aggregates.parquet metrics match expected values

E2E smoke tests

pdbench validate configs/experiment.yaml

pdbench run configs/experiment.yaml --replicates 2

verify run directory contains required files

Acceptance criteria (must be true)

uv run pytest -q passes

uv run pdbench validate configs/experiment.yaml succeeds

uv run pdbench run configs/experiment.yaml --replicates 2 creates:

rounds.jsonl

run_manifest.json

aggregates.parquet

Streamlit app loads the run directory and renders charts without errors

Notes

Keep dependencies minimal.

Log everything needed to reproduce.

Keep architecture boring, explicit, and auditable.
