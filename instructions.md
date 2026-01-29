Below is a concrete “Phase 1” architecture sketch you can hand to a team and start building immediately, plus a practical delivery plan, team roles, tech choices, and how we’ll test that it actually works.

---

## Repo + module sketch (boring on purpose = reproducible)

```
pd-agents/
  README.md
  pyproject.toml                  # Poetry/uv-managed deps
  .env.example                    # API keys (never commit .env)
  .gitignore
  docker/
    Dockerfile
  configs/
    experiment.yaml               # main experiment config
    games/
      pd_default.yaml
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
    __init__.py
    cli.py                        # `pdbench run ...`, `pdbench ui ...`, `pdbench validate ...`
    core/
      types.py                    # dataclasses/pydantic types
      rng.py                      # seeded RNG utilities
      payoff.py                   # PD payoff matrix + scoring
      horizon.py                  # fixed / geometric stopping
      transcript.py               # history window construction
      parse.py                    # strict output parsing + retry policy
      metrics.py                  # coop rate, retaliation, forgiveness, etc.
      logging.py                  # JSONL + Parquet writers, run manifests
    agents/
      base.py                     # Agent interface
      policy.py                   # ALLC/ALLD/TFT/Grim/GTFT/WSLS
      llm.py                      # LLM-backed agent using provider adapters
      providers/
        base.py                   # ProviderClient interface
        openai.py                 # optional
        anthropic.py              # optional
        litellm.py                # optional “one adapter to many”
    runners/
      run_experiment.py           # orchestrates replicates + conditions
      registry.py                 # maps config -> agent objects
    storage/
      schema.py                   # run schema definitions
      aggregate.py                # compute aggregated metrics
    ui/
      streamlit_app.py            # loads saved results + plots/replay
  tests/
    unit/
      test_payoff.py
      test_horizon.py
      test_policy_agents.py
      test_parsing.py
      test_transcript_window.py
    integration/
      test_runner_with_mock_llm.py
      test_logging_schema.py
    e2e/
      test_cli_smoke.py
  data/
    .gitkeep
```

Key design choice: **the experiment runner produces files** (JSONL/Parquet) and **Streamlit only reads them**. That separation keeps your experiments deterministic and auditable.

---

## Config schema (YAML) so you can swap models/prompts/providers fast

### `configs/experiment.yaml`

```yaml
run:
  run_id: "phase1_baseline_v1"
  seed: 1337
  output_dir: "data/runs/phase1_baseline_v1"
  store_prompts: true           # optionally redact later
  store_raw_responses: true

game:
  name: "prisoners_dilemma"
  payoff_matrix:
    # You (row) vs Other (col): (your_payoff, other_payoff)
    C:
      C: [3, 3]
      D: [0, 5]
    D:
      C: [5, 0]
      D: [1, 1]

horizon:
  type: "fixed"                 # "fixed" or "geometric"
  n_rounds: 100                 # used if fixed
  stop_prob: 0.02               # used if geometric

experiment:
  replicates: 20
  conditions:
    - name: "LLM_vs_ALLD"
      agent_a: {ref: "agents/llm_default.yaml", overrides: {persona: "cooperative"}}
      agent_b: {ref: "agents/policies.yaml", overrides: {policy: "ALLD"}}

    - name: "LLM_vs_TFT"
      agent_a: {ref: "agents/llm_default.yaml", overrides: {persona: "cooperative"}}
      agent_b: {ref: "agents/policies.yaml", overrides: {policy: "TFT"}}

metrics:
  report:
    - cooperation_rate
    - cooperation_rate_over_time
    - retaliation_rate
    - forgiveness_rate
    - exploitability_payoff_gap
    - time_to_collapse
```

### `configs/agents/llm_default.yaml`

```yaml
type: "llm"
provider: "litellm"             # or "openai"/"anthropic"
model: "gpt-4.1-mini"           # example; swap freely
temperature: 0.0                # start deterministic in Phase 1
max_tokens: 10

prompting:
  system_prompt_path: "configs/prompts/pd_system.md"
  round_prompt_path: "configs/prompts/pd_round.md"
  persona: "cooperative"        # maps to configs/prompts/personas/*.md
  history_window: 10            # include last N rounds in the prompt
  include_cumulative_totals: true

output:
  format: "single_token"        # "single_token" or "json"
  allowed: ["C", "D"]
  retry:
    max_retries: 2
    on_invalid: "reprompt_same_context"  # no extra info leakage
```

### `configs/agents/policies.yaml`

```yaml
type: "policy"
policy: "TFT"                   # overridden per condition
policy_params:
  generous_prob: 0.1            # for generous TFT, if used
```

This gives you a clean path to “change provider / change prompt / change persona” without touching code.

---

## “Senior architect” plan: what we build first, and what we *don’t* build yet

### Guiding principles (Phase 1)

1. **Determinism first:** temp=0, seeded RNG, stable prompts, stable parsing.
2. **Strict outputs:** only `C` or `D` (or strict JSON). Everything else triggers retry and is logged.
3. **Every round is logged:** prompt inputs, action, payoffs, cumulative totals, and parsed result.
4. **No tools, no browsing, no long-term memory:** keep the causal chain clean.

### Deliverables

* **Core PD engine** (rules, horizon, payoffs)
* **Policy agents** (ALLC/ALLD/TFT/Grim/GTFT/WSLS) in pure Python
* **LLM agent wrapper** (provider adapters + prompt templates + parsing)
* **Runner + config** (batch experiments, replicates, outputs)
* **Metrics + aggregation**
* **Streamlit viewer** (replay + charts + filtering)
* **Tests + CI** (so you can trust results)

---

## Team composition to build ASAP (roles + exact responsibilities)

Assuming you add a manager, here’s a lean team that can ship fast without stepping on each other.

### 1) Engineering Manager / TPM (1)

**Tech:** Jira/Linear, GitHub Projects, basic Python literacy
**Tasks:**

* Own backlog and milestones (Phase 1 scope control)
* Define “definition of done” for each deliverable
* Coordinate reviews, merge policy, release tags
* Ensure reproducibility checklist is met (seeds, configs, outputs)

### 2) Research Lead (Game theory / evaluation) (1)

**Tech:** Python, pandas, stats basics
**Tasks:**

* Specify payoff matrix variants (if any) and horizon settings
* Define metrics formally (retaliation/forgiveness/time-to-collapse)
* Decide minimum replicates + how to report uncertainty
* Create “experiment matrix” for Phase 1 (which matchups get run)

### 3) Core Backend Engineer (Experiment engine + runner) (1)

**Tech:** Python 3.11+, pydantic, typer, pytest
**Tasks:**

* Implement PD game engine (round loop, scoring)
* Implement horizon logic (fixed + geometric)
* Implement runner that loads YAML configs, runs replicates, writes outputs
* Implement policy agents + registry that builds agents from configs

### 4) LLM Integrations Engineer (Provider adapters + prompting) (1)

**Tech:** Python, provider SDKs or LiteLLM, robust parsing
**Tasks:**

* Implement `ProviderClient` abstraction + at least one provider adapter
* Implement prompt templating (system + round + persona + history window)
* Implement strict parsing + retry logic + “invalid output” telemetry
* Add optional response caching keyed by prompt hash (nice speedup)

### 5) Data/Analytics Engineer (Logging + schema + aggregation) (1)

**Tech:** JSONL, Parquet (pyarrow), duckdb optional, pandas
**Tasks:**

* Define run schema: run_manifest.json, rounds.jsonl, metrics.parquet, aggregates.parquet
* Implement writers and ensure stable column naming/types
* Implement aggregation functions and sanity checks
* Build “replay” loader used by Streamlit

### 6) Frontend / Streamlit Engineer (1)

**Tech:** Streamlit, pandas, matplotlib/plotly (your choice)
**Tasks:**

* Streamlit app that can:

  * select runs/conditions/replicates
  * show per-round actions (timeline)
  * show payoffs over time
  * filter by matchup, persona, horizon
* Add “export” buttons: CSV/Parquet download, PDF report later (optional)

### 7) QA / Test Engineer (part-time or 1)

**Tech:** pytest, hypothesis (optional), CI
**Tasks:**

* Unit tests for payoff/horizon/policy agents/parsing
* Integration tests with a **mock LLM** (predictable outputs)
* E2E CLI smoke tests + output schema validation

### 8) DevOps (part-time)

**Tech:** Docker, GitHub Actions, secrets management
**Tasks:**

* Dockerfile for reproducible runs
* CI workflow: lint + tests + minimal smoke run
* Secrets handling pattern (local `.env`, CI secrets, never in logs)

> If you want to go ultra-lean: roles 6–8 can be part-time, but **do not** skip tests/logging. That’s where papers get rejected.

---

## Tech choices (pragmatic defaults)

* **Python**: 3.11+
* **Config**: YAML + pydantic models (clear validation)
* **CLI**: Typer (nice DX)
* **Logging/Storage**: JSONL for per-round events + Parquet for aggregates
* **Data**: pandas + pyarrow; optional duckdb for fast queries
* **UI**: Streamlit
* **Testing**: pytest (+ coverage), optional hypothesis for fuzzing parser
* **CI**: GitHub Actions (lint + unit + integration)
* **LLM providers**: either direct SDK adapters, or **LiteLLM** as a single adapter layer (your call)

---

## Testing plan: how we know it works (and stays working)

### Unit tests (fast, deterministic)

* **Payoff correctness**: every action pair maps to correct payoffs
* **Horizon**:

  * fixed N ends at N rounds
  * geometric stop_prob ends with expected distribution (test via seeded RNG + bounds)
* **Policy agents**:

  * TFT: starts C, mirrors last opponent move
  * Grim: cooperates until first D then always D
  * WSLS: switches on loss, stays on win
* **Transcript window**: last N rounds included, older rounds excluded, totals correct
* **Parser**: accepts only `C`/`D` (or strict JSON), rejects everything else

### Integration tests (mock LLM)

* Mock provider returns a scripted sequence; runner produces:

  * valid rounds.jsonl schema
  * correct metrics.parquet
  * expected cooperation rate and payoff totals
* Retry behavior: first response invalid → second response valid → log shows both

### E2E smoke tests (realistic)

* `pdbench validate configs/experiment.yaml` (config sanity)
* `pdbench run configs/experiment.yaml --replicates 2 --dry-run false`
* `pdbench ui data/runs/...` loads the run and shows replay

### Reproducibility checks

* Running the same config twice with temp=0 yields identical actions/payoffs (or identical *given same provider determinism*; if not deterministic, you’ll detect it immediately)

---

## A couple of Phase-1 constraints I’d enforce hard

* Start with **temp=0** and only later introduce stochasticity + replicates.
* Keep prompts **short and structured**; include:

  * rules
  * payoff table
  * last N rounds
  * current round number
  * cumulative totals
* Don’t do pre-game negotiation chat yet (it changes the construct).

---

If you want, I can also draft:

* the exact `pd_system.md` and `pd_round.md` prompt templates (with strict “output only C/D” formatting), and
* a minimal `pdbench` CLI command set (`run`, `validate`, `aggregate`, `ui`, `replay`).
