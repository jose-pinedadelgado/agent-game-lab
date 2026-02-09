# Session Summary

*Last updated: 2026-02-08*

---

## This Session's Work (6 commits: 5fc7440 → 850a3bf)

### 1. CrewAI-Style YAML Agent Definitions (5fc7440)

Added a new `type: "crewai"` agent type that uses structured `role`/`goal`/`backstory` fields instead of free-form persona markdown files. Follows CrewAI's YAML format convention — no `crewai` package dependency.

**Files created:**
- `configs/agents/crewai/agents.yaml` — 3 agent profiles (strategic_cooperator, ruthless_optimizer, adaptive_diplomat)
- `configs/agents/crewai_base.yaml` — Base config for CrewAI agents
- `src/pdbench/agents/crewai.py` — `CrewAIAgent` class (~60 lines), subclasses `LLMAgent`
- `tests/unit/test_crewai_agent.py` — 12 unit tests

**Files modified:**
- `src/pdbench/core/types.py` — Added `CrewAIAgentConfig` Pydantic model
- `src/pdbench/runners/registry.py` — Added `"crewai"` branch
- `src/pdbench/cli.py` — Extended validation for CrewAI refs
- `configs/experiment.yaml` — Added 2 CrewAI conditions
- `tests/integration/test_runner_with_mock.py` — Added CrewAI integration test

### 2. OpenAI Provider Adapter (a23712a)

Implemented a real LLM provider so agents can call OpenAI.

- `src/pdbench/agents/providers/openai.py` — `OpenAIProvider` (~30 lines) using `openai` SDK
- `src/pdbench/agents/llm.py` — Added `elif config.provider == "openai":` with lazy import
- `pyproject.toml` — Added `openai>=1.0.0` dependency
- Includes `# TODO` for LiteLLM multi-provider adapter

### 3. Live OpenAI Experiment Runs (ac2cca9)

Switched `crewai_base.yaml` to `provider: "openai"` / `model: "gpt-4.1-mini"` and ran experiments.

**Key findings with gpt-4.1-mini:**
- `strategic_cooperator` vs TFT → 100% mutual cooperation (locked in)
- `ruthless_optimizer` vs ALLD → Cooperated 50 rounds, then switched to all-D (slow to learn)
- `adaptive_diplomat` vs ALLD (temp=1.2) → Fast retaliation (D by round 1), periodic forgiveness probes (~every 10 rounds), 12% cooperation. Replicates diverge at high temperature.

### 4. Streamlit UI: CrewAI Agents (9dc95cd)

- Switched `llm_default.yaml` to OpenAI provider
- Added all 3 CrewAI agents to Streamlit dropdowns, descriptions, tournament mode
- Added `build_agent_ref()` helper for proper AgentRef construction by agent type

### 5. CrewAI Tournament (c3c33d3)

Full round-robin: 3 CrewAI personas × 6 policy agents (18 matchups, 2 replicates).

**Tournament results (avg payoff across all opponents):**
| Agent | Avg Payoff | Strategy |
|-------|-----------|----------|
| strategist | 132.4 | Full cooperation except vs ALLD |
| diplomat | 132.3 | Same pattern, with forgiveness probes |
| ruthless | 104.3 | Exploits ALLC/WSLS, punished by retaliators |

**Key insight:** The "selfish" persona performs worst overall. Cooperative personas sustain 3/round with 5 of 6 opponents; ruthless burns relationships and gets stuck at 1/round.

### 6. Tournament Results Viewer (850a3bf)

Added to the Streamlit Tournament tab:
- Saved tournament run selector
- Leaderboard with medals and avg payoff
- Matchup breakdown table (coop rates, payoffs, collapse)
- Payoff matrix heatmap (color-coded)
- Cooperation rate heatmap

---

## Current State of the Codebase

### What's fully working
- Phase 1 PD engine (payoffs, horizons, transcripts, parsing, metrics)
- 6 policy agents (ALLC, ALLD, TFT, GRIM, GTFT, WSLS)
- LLM agent with MockProvider and OpenAI provider
- CrewAI agent type with 3 personas
- CLI: validate, run, aggregate, ui
- Streamlit UI with 4 tabs (Run, View, Replay, Tournament)
- 105 tests passing
- Output artifacts: run_manifest.json, rounds.jsonl, aggregates.parquet

### Config files
- `configs/experiment.yaml` — Main experiment (8 conditions including CrewAI)
- `configs/tournament_crewai.yaml` — Tournament config (18 matchups)
- `configs/agents/llm_default.yaml` — Now uses OpenAI (gpt-4.1-mini)
- `configs/agents/crewai_base.yaml` — Now uses OpenAI (gpt-4.1-mini)
- `configs/agents/policies.yaml` — Policy agent base
- `configs/agents/crewai/agents.yaml` — 3 CrewAI personas

### Saved run data
- `data/runs/phase1_smoke_v1/` — Main experiment results (all conditions)
- `data/runs/tournament_crewai_vs_policy/` — Tournament results

---

## Action Items for Next Session

### Urgent
- **Rotate OpenAI API key** — the key was accidentally exposed in chat. Generate a new one at https://platform.openai.com/api-keys and update `.env`.

### TODO from code
- **Implement LiteLLM provider** — `# TODO` in `src/pdbench/agents/providers/openai.py`. Would allow Anthropic, Cohere, etc. via one adapter.

### Potential next steps
- **More CrewAI personas** — The agents.yaml format makes it easy to add new personalities. Interesting ones to try: a "paranoid" agent, a "random explorer", a "grudge-holder who forgives after N rounds."
- **Higher replicates + analysis** — Run tournament with more replicates (10-20) to get confidence intervals on the payoff differences.
- **Temperature sweep** — Run diplomat vs ALLD at temps 0.0, 0.3, 0.7, 1.0, 1.5 to study how randomness affects strategy.
- **CrewAI vs CrewAI matchups** — Pit the LLM personas against each other (strategist vs ruthless, etc.)
- **Geometric horizon** — All runs so far used fixed 50 rounds. Geometric horizon (unknown endpoint) may change LLM behavior since endgame exploitation is less predictable.
- **Streamlit deprecation warnings** — Replace `use_container_width` with `width` parameter (deadline was 2025-12-31).

### Phase 1 non-goals (still out of scope)
- Pre-game negotiation / chat
- Tool use, MCP, web access
- Long-term memory across episodes
- Multi-agent >2 players
- Complex agent frameworks (LangChain/AutoGen)

---

## Quick Reference Commands

```bash
# Run tests
uv run pytest -q

# Validate config
uv run pdbench validate configs/experiment.yaml

# Run experiment
uv run pdbench run configs/experiment.yaml --replicates 2

# Run tournament
uv run pdbench run configs/tournament_crewai.yaml --replicates 2

# Launch UI
uv run pdbench ui data/runs/phase1_smoke_v1

# Recompute metrics
uv run pdbench aggregate data/runs/phase1_smoke_v1
```
