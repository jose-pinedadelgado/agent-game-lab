# PDBench Architecture Guide

This document explains how PDBench works, from the UI to the core game logic.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [UI Overview](#ui-overview)
3. [Code Architecture](#code-architecture)
4. [Key Code Flows](#key-code-flows)
5. [Data Structures](#data-structures)
6. [Configuration System](#configuration-system)
7. [Agents](#agents)
8. [Metrics](#metrics)
9. [Output Artifacts](#output-artifacts)

---

## Quick Start

```bash
# Install dependencies
uv sync

# Validate config
uv run pdbench validate configs/experiment.yaml

# Run experiment
uv run pdbench run configs/experiment.yaml --replicates 2

# View results
uv run pdbench ui data/runs/phase1_smoke_v1
```

---

## UI Overview

The Streamlit UI (`src/pdbench/ui/streamlit_app.py`) provides a full interface for **running experiments and viewing results**.

### Launch the UI

```bash
uv run pdbench ui data/runs/phase1_smoke_v1

# Or launch directly:
uv run streamlit run src/pdbench/ui/streamlit_app.py
```

### UI Tabs

The UI has **4 main tabs**:

| Tab | Purpose |
|-----|---------|
| 🧪 **Run Experiment** | Configure and run new experiments |
| 📊 **View Results** | Browse and analyze past experiments |
| 🎬 **Animated Replay** | Watch games play out round-by-round |
| 🏆 **Tournament** | Run round-robin tournaments between strategies |

---

### Tab 1: Run Experiment

Configure experiments directly in the browser:

```
┌─────────────────────────────────────────────────────────────┐
│  🧪 Run New Experiment                                       │
├─────────────────────────────┬───────────────────────────────┤
│  Agent A                    │  Agent B                      │
│  ┌─────────────────────┐    │  ┌─────────────────────┐     │
│  │  🪞 Tit-for-Tat     │    │  │  😈 Always Defect   │     │
│  │  [dropdown]         │    │  │  [dropdown]         │     │
│  └─────────────────────┘    │  └─────────────────────┘     │
├─────────────────────────────┴───────────────────────────────┤
│  ⚙️ Game Settings                                            │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ Horizon:     │ │ Rounds: 50   │ │ Replicates:3 │        │
│  │ ○ Fixed      │ │ [slider]     │ │ [slider]     │        │
│  │ ○ Geometric  │ │              │ │              │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
├─────────────────────────────────────────────────────────────┤
│  [🚀 Run Experiment]                                        │
└─────────────────────────────────────────────────────────────┘
```

**Features:**
- Select any policy agent (ALLC, ALLD, TFT, GRIM, GTFT, WSLS) or MockLLM
- Choose Fixed horizon (exact rounds) or Geometric (random stopping)
- Adjust number of replicates
- View payoff matrix
- Results shown immediately after run

---

### Tab 2: View Results

```
┌─────────────────────────────────────────────────────────────┐
│  📊 View Results                                             │
│  [Select Run: exp_20260126_120000 ▼]                        │
│  [Condition: TFT_vs_ALLD ▼] [Replicate: 0 ▼]               │
├─────────────────────────────────────────────────────────────┤
│  🎮 Game Timeline                                            │
│  🟢🟢🔴🔴🔴🔴🔴🔴🔴🔴  (Agent A actions)                        │
│  🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴  (Agent B actions)                        │
├─────────────────────────────┬───────────────────────────────┤
│  Actions Over Time          │  Cumulative Payoffs           │
│  [line chart]               │  [line chart]                 │
├─────────────────────────────┴───────────────────────────────┤
│  📈 Metrics                                                  │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐                       │
│  │  50  │ │ 2%   │ │ 49   │ │  0   │                       │
│  │Rounds│ │A Coop│ │A Pay │ │Collap│                       │
│  └──────┘ └──────┘ └──────┘ └──────┘                       │
└─────────────────────────────────────────────────────────────┘
```

---

### Tab 3: Animated Replay

Watch games unfold in real-time:

```
┌─────────────────────────────────────────────────────────────┐
│  🎬 Animated Replay                                          │
│  [Select Run] [Condition] [Replicate] [Speed: 300ms]        │
├─────────────────────────────┬───────────────────────────────┤
│  🪞 Tit-for-Tat             │  😈 Always Defect             │
├─────────────────────────────┴───────────────────────────────┤
│  Round 5 of 50                                              │
│  ┌─────────────┐      ⚔️      ┌─────────────┐              │
│  │     🗡️      │              │     🗡️      │              │
│  │      D      │              │      D      │              │
│  │   +1 point  │              │   +1 point  │              │
│  └─────────────┘              └─────────────┘              │
│                                                             │
│  History: 🟢🔴🔴🔴🔴  (last 5 rounds)                         │
│                                                             │
│  [▶️ Play Replay]                                           │
└─────────────────────────────────────────────────────────────┘
```

**Features:**
- Adjustable playback speed
- Color-coded action display (🟢 = Cooperate, 🔴 = Defect)
- Running score with delta
- History trail

---

### Tab 4: Tournament

Run round-robin tournaments:

```
┌─────────────────────────────────────────────────────────────┐
│  🏆 Tournament Mode                                          │
│  Select Strategies: [ALLC] [ALLD] [TFT] [GRIM]              │
│  Rounds: 50    Replicates: 3    Horizon: Fixed              │
│  [🚀 Run Tournament]                                        │
├─────────────────────────────────────────────────────────────┤
│  🏅 Leaderboard                                              │
│  🥇 🪞 TFT: 142.5 avg points                                 │
│  🥈 💀 GRIM: 138.2 avg points                               │
│  🥉 🕊️ ALLC: 120.0 avg points                               │
│  4. 😈 ALLD: 95.3 avg points                                │
├─────────────────────────────────────────────────────────────┤
│  📊 Matchup Results                                          │
│  [table of all matchup scores]                              │
└─────────────────────────────────────────────────────────────┘
```

---

### Visual Design Elements

Inspired by [The Evolution of Trust](https://ncase.me/trust/) by Nicky Case:

| Element | Implementation |
|---------|---------------|
| **Agent Cards** | Emoji + name + strategy description with gradient background |
| **Action Display** | Color-coded cards (🟢 green = C, 🔴 red = D) with payoff |
| **History Trail** | Row of emoji showing action sequence for each agent |
| **Animated Replay** | Frame-by-frame playback with adjustable speed |
| **Tournament Leaderboard** | Medal rankings with strategy scores |

### Game Timeline Visualization

The timeline shows each agent's actions as a sequence of emoji:

```
A: 🟢🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴
B: 🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴
🟢 = Cooperate (C), 🔴 = Defect (D)
```

This shows at a glance:
- TFT starts with 🟢 (cooperate), then mirrors opponent's 🔴 (defect)
- ALLD always plays 🔴 (defect)

### Color/Emoji Scheme

```
Cooperate (C): 🟢 🤝
Defect (D):    🔴 🗡️
```

---

## Code Architecture

```
src/pdbench/
├── __init__.py            # Package init, version
├── cli.py                 # Typer CLI (validate, run, aggregate, ui)
│
├── core/                  # Core game logic
│   ├── types.py           # Pydantic models (Action, Observation, configs)
│   ├── rng.py             # Seeded RNG for determinism
│   ├── payoff.py          # Payoff matrix (C,C)→(3,3), etc.
│   ├── horizon.py         # Fixed/Geometric stopping rules
│   ├── transcript.py      # History window for agent observations
│   ├── parse.py           # Parse "C"/"D" from LLM output + retry
│   ├── metrics.py         # Compute cooperation_rate, retaliation, etc.
│   └── logging.py         # JSONL writer, manifest writer
│
├── agents/                # Agent implementations
│   ├── base.py            # Agent protocol (reset, act)
│   ├── policy.py          # ALLC, ALLD, TFT, GRIM, GTFT, WSLS
│   ├── llm.py             # LLM agent (prompts + provider + parsing)
│   └── providers/
│       ├── base.py        # ProviderClient protocol
│       └── mock.py        # MockProvider for testing
│
├── runners/               # Experiment orchestration
│   ├── registry.py        # Load YAML configs → create agents
│   └── run_experiment.py  # Main loop: conditions × replicates × rounds
│
├── storage/               # Output handling
│   ├── schema.py          # Validation for rounds.jsonl fields
│   └── aggregate.py       # Compute & write aggregates.parquet
│
└── ui/
    └── streamlit_app.py   # Read-only dashboard
```

### Module Responsibilities

| Module | Purpose |
|--------|---------|
| `cli.py` | Entry point. Parses commands, loads config, calls runner |
| `core/types.py` | All Pydantic models for config validation and data structures |
| `core/payoff.py` | Payoff matrix: maps (Action, Action) → (payoff_a, payoff_b) |
| `core/horizon.py` | Decides when game ends (fixed N rounds or geometric stopping) |
| `core/transcript.py` | Builds observation for agents with windowed history |
| `core/parse.py` | Extracts C/D from LLM output, handles retries on invalid output |
| `core/metrics.py` | Computes all metrics from round data |
| `agents/policy.py` | Deterministic policy agents (no LLM calls) |
| `agents/llm.py` | LLM-backed agent with prompt rendering |
| `runners/run_experiment.py` | Main game loop orchestration |
| `storage/aggregate.py` | Writes Parquet files with computed metrics |

---

## Key Code Flows

### 1. Running an Experiment

```
cli.py:run()
    └── run_experiment.py:run_experiment()
            ├── write_manifest()           # Save config snapshot
            ├── For each condition:
            │   └── For each replicate:
            │       ├── registry.create_agent(a)
            │       ├── registry.create_agent(b)
            │       ├── create_horizon()
            │       └── run_single_game()
            │           └── Loop until horizon.should_stop():
            │               ├── transcript.build_observation()
            │               ├── agent_a.act(obs)
            │               ├── agent_b.act(obs)
            │               ├── payoff_matrix.get_payoffs()
            │               └── logger.log_round()
            └── write_aggregates()         # Compute metrics → Parquet
```

### 2. Agent Decision Flow (LLM)

```
llm.py:LLMAgent.act(obs)
    ├── _build_round_prompt(obs)     # Format history, payoffs, persona
    ├── provider.complete(...)        # Call LLM (or MockProvider)
    ├── parser.parse_with_retry()     # Extract C/D, retry if invalid
    └── return "C" or "D"
```

### 3. Single Game Loop

```python
# Simplified from run_experiment.py:run_single_game()

while not horizon.should_stop(round_index):
    # Build observations from each agent's perspective
    obs_a = transcript.build_observation(round_index + 1, "a")
    obs_b = transcript.build_observation(round_index + 1, "b")

    # Get actions
    action_a = agent_a.act(obs_a)  # Returns "C" or "D"
    action_b = agent_b.act(obs_b)

    # Score
    payoff_a, payoff_b = payoff_matrix.get_payoffs(action_a, action_b)

    # Log
    logger.log_round(...)

    round_index += 1
```

---

## Data Structures

### Observation (what agents see)

```python
Observation(
    round_number=5,
    history=[                             # Last N rounds (configurable window)
        (Action.C, Action.D, 0, 5),       # (my_action, opp_action, my_pay, opp_pay)
        (Action.D, Action.D, 1, 1),
    ],
    my_cumulative_payoff=10,
    opponent_cumulative_payoff=15,
    payoff_matrix={"C": {"C": [3,3], "D": [0,5]}, "D": {"C": [5,0], "D": [1,1]}},
    horizon_type="fixed",
    total_rounds=50,
)
```

### Round Record (what gets logged to rounds.jsonl)

```json
{
  "run_id": "phase1_smoke_v1",
  "condition": "TFT_vs_ALLD",
  "replicate": 0,
  "round_index": 3,
  "agent_a_action": "D",
  "agent_b_action": "D",
  "agent_a_payoff": 1,
  "agent_b_payoff": 1,
  "agent_a_cum_payoff": 8,
  "agent_b_cum_payoff": 16,
  "horizon_type": "fixed",
  "fixed_n": 50,
  "stop_prob": null,
  "timestamp_utc": "2026-01-26T09:59:45.654190+00:00",
  "prompts": {"agent_a": {"system": "...", "round": "..."}},
  "raw_responses": {"agent_a": "D"}
}
```

### Payoff Matrix

Default Prisoner's Dilemma payoffs:

|  | Opponent C | Opponent D |
|--|------------|------------|
| **You C** | (3, 3) | (0, 5) |
| **You D** | (5, 0) | (1, 1) |

- Mutual cooperation: both get 3
- Mutual defection: both get 1
- Exploitation: defector gets 5, cooperator gets 0

---

## Configuration System

### Experiment Config (`configs/experiment.yaml`)

```yaml
run:
  run_id: "phase1_smoke_v1"
  seed: 1337
  output_dir: "data/runs/phase1_smoke_v1"
  store_prompts: true
  store_raw_responses: true

game:
  payoff_matrix:
    C: {C: [3, 3], D: [0, 5]}
    D: {C: [5, 0], D: [1, 1]}

horizon:
  type: "fixed"      # or "geometric"
  n_rounds: 50
  stop_prob: 0.02    # only for geometric

experiment:
  replicates: 5
  conditions:
    - name: "TFT_vs_ALLD"
      agent_a:
        ref: "agents/policies.yaml"
        overrides: {policy: "TFT"}
      agent_b:
        ref: "agents/policies.yaml"
        overrides: {policy: "ALLD"}

metrics:
  collapse:
    k: 10
    cooperation_threshold: 0.2
```

### Agent Config Loading

```
experiment.yaml
    └── conditions[0].agent_a.ref = "agents/policies.yaml"
                                          └── overrides: {policy: "TFT"}

registry.py:create_agent_from_ref()
    ├── Load agents/policies.yaml
    ├── Merge overrides
    └── create_policy_agent("TFT")  →  TFT()
```

---

## Agents

### Policy Agents (No LLM)

| Agent | Strategy |
|-------|----------|
| **ALLC** | Always Cooperate |
| **ALLD** | Always Defect |
| **TFT** | Start C, then copy opponent's last action |
| **GRIM** | Cooperate until opponent defects once, then always defect |
| **GTFT** | Like TFT, but forgive defection with probability `generous_prob` |
| **WSLS** | Win-Stay Lose-Shift: repeat action if payoff ≥ threshold, else switch |

### TFT Implementation

```python
class TFT(PolicyAgent):
    def act(self, obs: Observation) -> str:
        if not obs.history:
            return "C"                    # Start cooperative
        _, opp_last_action, _, _ = obs.history[-1]
        return opp_last_action.value      # Mirror opponent
```

### LLM Agent

Uses prompts + provider to generate actions:

1. Load system prompt (`configs/prompts/pd_system.md`)
2. Load round prompt template (`configs/prompts/pd_round.md`)
3. Load persona (`configs/prompts/personas/*.md`)
4. Render prompt with current observation
5. Call provider (MockProvider or real LLM)
6. Parse output to C/D (with retry on invalid)

---

## Metrics

Computed in `core/metrics.py`:

| Metric | Definition |
|--------|------------|
| `cooperation_rate` | Fraction of C actions (per-agent and overall) |
| `cooperation_rate_over_time` | Cumulative cooperation rate at each round |
| `retaliation_rate` | P(D at t \| opponent D at t-1) |
| `forgiveness_rate` | P(C at t \| opponent D at t-1) |
| `exploitability_payoff_gap` | opponent_total - agent_total |
| `time_to_collapse` | First round where next k rounds have coop_rate ≤ threshold |

### Time to Collapse

```python
def compute_time_to_collapse(a_actions, b_actions, k=10, threshold=0.2):
    """
    Find first round t where cooperation collapses:
    - Look at window of k rounds starting at t
    - If cooperation rate ≤ threshold, collapse occurred at t
    """
    for t in range(len(a_actions) - k + 1):
        window_coop = count_coops(a_actions[t:t+k], b_actions[t:t+k])
        if window_coop / (2 * k) <= threshold:
            return t
    return None  # Never collapsed
```

---

## Output Artifacts

After running an experiment, `output_dir` contains:

| File | Format | Contents |
|------|--------|----------|
| `run_manifest.json` | JSON | Run metadata, config snapshot, environment info |
| `rounds.jsonl` | JSON Lines | One record per round (actions, payoffs, timestamps) |
| `aggregates.parquet` | Parquet | Computed metrics per condition/replicate |

### Viewing Outputs

```bash
# Raw rounds
head -3 data/runs/phase1_smoke_v1/rounds.jsonl

# Aggregated metrics
uv run python -c "
import pandas as pd
df = pd.read_parquet('data/runs/phase1_smoke_v1/aggregates.parquet')
print(df[['condition', 'overall_cooperation_rate', 'time_to_collapse']])
"

# Full dashboard
uv run pdbench ui data/runs/phase1_smoke_v1
```

---

## CLI Commands

| Command | Description |
|---------|-------------|
| `pdbench validate <config>` | Validate YAML config and check file references |
| `pdbench run <config> [--replicates N] [--dry-run]` | Run experiment |
| `pdbench aggregate <run_dir>` | Recompute aggregates from rounds.jsonl |
| `pdbench ui <run_dir>` | Launch Streamlit viewer |

---

## Testing

```bash
# All tests
uv run pytest -q

# Unit tests only
uv run pytest tests/unit -v

# Integration tests (uses MockProvider)
uv run pytest tests/integration -v

# E2E CLI tests
uv run pytest tests/e2e -v
```

Tests are organized as:
- `tests/unit/` - Test individual components (payoff, horizon, parsing, etc.)
- `tests/integration/` - Test runner with MockProvider, validate output schemas
- `tests/e2e/` - Test CLI commands end-to-end

---

## Adding New Features

### Adding a New Policy Agent

1. Add class in `src/pdbench/agents/policy.py`:
```python
class MyPolicy(PolicyAgent):
    def act(self, obs: Observation) -> str:
        # Your logic here
        return "C" or "D"
```

2. Register in `POLICY_REGISTRY`:
```python
POLICY_REGISTRY = {
    ...
    "MYPOLICY": MyPolicy,
}
```

3. Use in config:
```yaml
agent_a:
  ref: "agents/policies.yaml"
  overrides: {policy: "MYPOLICY"}
```

### Adding a New Metric

1. Add computation function in `src/pdbench/core/metrics.py`
2. Add field to `ConditionMetrics` dataclass
3. Compute in `compute_metrics_for_replicate()`
4. (Optional) Display in Streamlit UI

---

## Future: Evolution Visualization

Inspired by [The Evolution of Trust](https://ncase.me/trust/), here's how population evolution could be visualized in a future phase:

### Concept: Population Dynamics

Instead of just 1v1 games, simulate a **population of agents** that evolve over generations:

```
Generation 1:  🕊️🕊️🕊️😈😈🪞🪞💀
               ↓ (play tournament, reproduce based on fitness)
Generation 2:  🕊️😈😈🪞🪞🪞💀💀
               ↓
Generation 3:  😈🪞🪞🪞🪞💀💀💀
               ...
Generation N:  🪞🪞🪞🪞🪞🪞🪞🪞  (TFT dominates!)
```

### Proposed Visualization Components

#### 1. Population Bar Chart (Animated)

```
Gen 1:  ALLC ████████░░░░░░░░░░░░ 40%
        ALLD ████░░░░░░░░░░░░░░░░ 20%
        TFT  ██████░░░░░░░░░░░░░░ 30%
        GRIM ██░░░░░░░░░░░░░░░░░░ 10%

Gen 50: ALLC ░░░░░░░░░░░░░░░░░░░░  0%
        ALLD ██░░░░░░░░░░░░░░░░░░ 10%
        TFT  ████████████████░░░░ 80%
        GRIM ██░░░░░░░░░░░░░░░░░░ 10%
```

#### 2. Population Over Time (Stacked Area Chart)

```
100% ┌────────────────────────────────┐
     │▓▓▓▓▓▓                          │ ALLC (dies out)
     │░░░░░░▓▓▓▓▓▓▓▓                  │ ALLD (rises then falls)
     │████████████████████████████████│ TFT (dominates)
     │▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒│ GRIM (stable minority)
  0% └────────────────────────────────┘
     Gen 1                        Gen 100
```

#### 3. Agent Grid (Like Game of Life)

Show agents as colored cells that change over generations:

```
┌──────────────────────────────────────┐
│ 🕊️🕊️😈🪞💀🕊️😈🪞🪞💀 │ Gen 1
│ 🕊️😈😈🪞🪞🕊️😈🪞💀💀 │ Gen 2
│ 😈😈🪞🪞🪞😈🪞🪞💀💀 │ Gen 3
│ ...                                  │
└──────────────────────────────────────┘
```

#### 4. Interactive Sliders

Like Nicky Case's game, allow users to tune:
- **Miscommunication rate**: How often C is seen as D (noise)
- **Initial population mix**: Starting percentages of each strategy
- **Reproduction rate**: How strongly fitness affects offspring
- **Mutation rate**: Chance of random strategy change

### Implementation Approach

```python
# Pseudocode for evolution simulation

class Population:
    def __init__(self, strategies: dict[str, int]):
        """Initialize with strategy counts, e.g., {"TFT": 10, "ALLD": 5}"""
        self.agents = []
        for strategy, count in strategies.items():
            self.agents.extend([strategy] * count)

    def run_generation(self) -> dict[str, float]:
        """Run tournament, return fitness scores."""
        scores = {agent: 0 for agent in set(self.agents)}

        # Each agent plays against every other
        for i, a in enumerate(self.agents):
            for j, b in enumerate(self.agents):
                if i != j:
                    a_score, b_score = play_game(a, b)
                    scores[a] += a_score

        return scores

    def reproduce(self, scores: dict[str, float]) -> None:
        """Replace population based on fitness (roulette wheel selection)."""
        total = sum(scores.values())
        probs = {s: scores[s] / total for s in scores}

        new_agents = random.choices(
            list(probs.keys()),
            weights=list(probs.values()),
            k=len(self.agents)
        )
        self.agents = new_agents

# Main evolution loop
population = Population({"ALLC": 25, "ALLD": 25, "TFT": 25, "GRIM": 25})
history = []

for gen in range(100):
    scores = population.run_generation()
    history.append(count_strategies(population))
    population.reproduce(scores)

# Visualize history as animated stacked area chart
```

### Key Insights to Visualize

From The Evolution of Trust, key lessons to show:

1. **Nice guys finish first** - Cooperative strategies (TFT) beat exploitative ones in the long run
2. **Forgiveness matters** - GTFT can outperform strict TFT when there's noise
3. **Retaliation is necessary** - ALLC gets exploited and dies out
4. **Environment shapes behavior** - The same strategy can thrive or die depending on the population mix

### Streamlit Implementation Notes

For Phase 2+, add a new tab "🧬 Evolution":

```python
def render_evolution_tab():
    st.header("🧬 Population Evolution")

    # Initial population sliders
    st.subheader("Initial Population")
    allc_pct = st.slider("ALLC %", 0, 100, 25)
    alld_pct = st.slider("ALLD %", 0, 100, 25)
    tft_pct = st.slider("TFT %", 0, 100, 25)
    grim_pct = st.slider("GRIM %", 0, 100, 25)

    # Parameters
    generations = st.slider("Generations", 10, 500, 100)
    noise = st.slider("Miscommunication %", 0, 20, 5)

    if st.button("🧬 Run Evolution"):
        # Run simulation and show animated results
        ...
```

---

## Changelog

| Date | Changes |
|------|---------|
| 2026-01-26 | Initial Phase 1 implementation |
| 2026-01-26 | Added interactive UI with Run Experiment, Animated Replay, Tournament tabs |

---

*Last updated: 2026-01-26*
