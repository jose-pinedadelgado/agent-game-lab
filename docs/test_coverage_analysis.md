# Test Coverage Analysis

Generated: 2026-02-16

## Current State: 56% Overall Line Coverage

Running `pytest --cov=pdbench --cov-report=term-missing` reveals **56% line coverage** with **3 test failures**.

### Per-Module Coverage

| Module | Stmts | Miss | Cover | Key Missing Lines |
|--------|-------|------|-------|-------------------|
| `core/payoff.py` | 26 | 0 | **100%** | — |
| `core/transcript.py` | 47 | 0 | **100%** | — |
| `agents/crewai.py` | 29 | 0 | **100%** | — |
| `core/metrics.py` | 93 | 1 | **99%** | line 100 |
| `core/parse.py` | 51 | 1 | **98%** | line 90 |
| `core/horizon.py` | 58 | 1 | **98%** | line 76 |
| `core/types.py` | 115 | 3 | **97%** | 217–220 (`load_config_file`) |
| `agents/policy.py` | 73 | 4 | **95%** | 18, 76, 90, 101 |
| `runners/registry.py` | 38 | 2 | **95%** | 32, 77 |
| `runners/run_experiment.py` | 79 | 6 | **92%** | 87, 89, 94, 96, 153–154 |
| `storage/schema.py` | 17 | 2 | **88%** | 45, 54 |
| `agents/llm.py` | 75 | 12 | **84%** | 55, 84, 106, 144–175 |
| `core/rng.py` | 24 | 5 | **79%** | 22, 35, 43–45 |
| `agents/providers/mock.py` | 27 | 8 | **70%** | 52–62, 67 |
| `agents/providers/openai.py` | 13 | 4 | **69%** | 23–24, 34–43 |
| `core/logging.py` | 53 | 17 | **68%** | 30–36, 82–84, 119–130 |
| `storage/aggregate.py` | 40 | 21 | **48%** | 20, 36–72, 77–82 |
| `cli.py` | 108 | 108 | **0%** | all lines |
| `ui/streamlit_app.py` | 413 | 413 | **0%** | all lines |
| `agents/base.py` | 6 | 6 | **0%** | protocol definition |
| **TOTAL** | **1390** | **614** | **56%** | |

### Failing Tests (3)

All caused by the same root issue: the registry creates `OpenAIProvider` instead of `MockProvider` when loading LLM agents from config refs, because `OPENAI_API_KEY` is not set.

- `tests/integration/test_runner_with_mock.py::test_run_with_llm_agent`
- `tests/integration/test_runner_with_mock.py::test_run_with_crewai_agent`
- `tests/e2e/test_cli_smoke.py::test_run_command`

---

## Priority Areas for Improvement

### 1. Fix MockProvider Integration Bug (Critical)

`registry.py:create_agent_from_ref()` at line 64 creates an `LLMAgent` without injecting a `MockProvider`. The `LLMAgent.__init__` falls through to `OpenAIProvider` because `llm_default.yaml` sets `provider: "litellm"`, which isn't even a supported provider — it would hit the "Unsupported provider" error path.

For tests to work without API keys (a spec requirement), either:
- Change `llm_default.yaml` to use `provider: "mock"` for default experiments, or
- Have the registry detect mock config and inject a `MockProvider`, or
- Add a `"litellm"` provider adapter

**Impact:** Unblocks 3 failing tests.

### 2. `storage/aggregate.py` — 48% Coverage (High)

The entire `recompute_aggregates()` (lines 46–72) and `compute_condition_averages()` (lines 77–82) are untested.

**Needed tests:**
- `write_aggregates()` with various metric inputs and empty list edge case
- `recompute_aggregates()` from a rounds.jsonl file
- `compute_condition_averages()` across replicates
- `load_aggregates()` round-trip with `write_aggregates()`

### 3. `cli.py` — 0% Coverage (High)

No CLI tests use `typer.testing.CliRunner`. The E2E tests use subprocess but fail.

**Needed tests:**
- `validate` with valid/invalid/missing configs
- `run` with `--dry-run` flag
- `run` with `--replicates` override
- `aggregate` with valid/missing run directory
- `ui` command output verification
- Error paths for all commands

### 4. `core/logging.py` — 68% Coverage (Medium-High)

**Untested code:**
- `JSONLWriter._serialize()` — `Action`, `datetime`, and `Path` serialization branches (lines 30–36)
- `write_manifest()` (lines 94–114) — never called in unit tests
- `load_rounds_jsonl()` (lines 117–124) — never tested directly
- `load_manifest()` (lines 129–130) — never tested directly

These are critical for reproducibility — corrupt output would silently break experiment results.

### 5. `agents/llm.py` — 84% Coverage, No Unit Tests (Medium-High)

No dedicated unit test file exists for `LLMAgent`. Only tested indirectly through integration tests (which fail).

**Needed tests:**
- `LLMAgent.__init__()` with explicitly passed MockProvider
- `act()` — correct prompt construction, provider call, parse flow
- `act()` with retry — provider returns invalid then valid output
- `act()` when all retries fail — verify default to "C" (line 160)
- `_build_round_prompt()` — placeholder substitution
- Unsupported provider error (line 55)
- Missing persona file returns empty string (line 84)

### 6. `agents/providers/mock.py` — 70% Coverage (Medium)

The "scripted" mode (lines 52–62) is never tested.

**Needed tests:**
- Scripted mode with a list of outputs
- Scripted mode wrapping (index exceeds list length)
- Scripted mode with empty list (falls back to fixed_output)
- `call_count` tracking
- `reset()` clearing state

### 7. `core/rng.py` — 79% Coverage (Medium)

**Untested methods:**
- `choice()` — random selection from sequence
- `seed` property
- `fork()` — derived seed for independent streams
- `fork()` with `seed=None` — returns unseeded RNG

### 8. `runners/run_experiment.py` — Prompt/Response Capture (Medium)

Lines 87, 89, 94, 96 (`store_prompts` / `store_raw_responses` branches) are untested because they require an LLM agent with a working MockProvider. Needs integration test that:

- Runs a game with `store_prompts=True` and LLM agent using MockProvider
- Verifies `prompts` field appears in rounds.jsonl
- Verifies `raw_responses` in output

### 9. Geometric Horizon in Runner (Low-Medium)

No integration test runs a game with geometric horizon. Missing verification that:
- Games with geometric horizon stop randomly based on seed
- `horizon_type` and `stop_prob` appear correctly in rounds.jsonl

### 10. `runners/registry.py` — Config Merging Edge Cases (Low-Medium)

**Untested:**
- `merge_overrides()` with nested dict deep merge (line 32)
- `merge_overrides()` with conflicting keys at different levels
- Unknown agent type error path (line 77)
- `load_yaml()` with invalid files

### 11. `storage/schema.py` — 88% Coverage (Low)

**Untested:**
- `validate_manifest()` — never called directly
- `validate_round_record()` with missing fields

### 12. Streamlit UI — 0% Coverage (Low Priority)

935 lines with no tests. Minimum testable without Streamlit runtime:
- `load_run_data()` — loading manifest/rounds/aggregates
- Data transformation functions

---

## Recommended Action Plan

| Priority | Action | Expected Coverage Gain |
|----------|--------|----------------------|
| 1 | Fix provider resolution bug so tests pass offline | Unblocks 3 tests |
| 2 | Add `tests/unit/test_llm_agent.py` | +12 lines covered in llm.py |
| 3 | Add `tests/unit/test_mock_provider.py` | +8 lines in mock.py |
| 4 | Add `tests/unit/test_aggregate.py` | +21 lines in aggregate.py |
| 5 | Add `tests/unit/test_logging.py` | +17 lines in logging.py |
| 6 | Add `tests/unit/test_rng.py` | +5 lines in rng.py |
| 7 | Add CLI tests with `CliRunner` | +108 lines in cli.py |
| 8 | Add `tests/unit/test_registry.py` | +2 lines in registry.py |

Completing items 1–6 would bring coverage from **56% to approximately 80%**. Adding CLI tests (item 7) would push it to **~88%**. The remaining gap is mostly `streamlit_app.py` (935 lines) and `agents/base.py` (6 lines, protocol-only).
