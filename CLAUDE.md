# Claude Project Guidance

## Scope
Implement ONLY Phase 1 (baseline iterated Prisoner's Dilemma). No tools, no browsing, no multi-agent >2, no long-term memory.

## Source of truth
- Follow @docs/phase1_spec.md exactly.
- @instructions.md contains additional background but should not override the spec.

## Working style
- Prefer small, reviewable commits/steps.
- After each major component, run tests locally and fix failures before continuing.

## Required commands (must pass)
- `pytest -q`
- `pdbench validate configs/experiment.yaml`
- `pdbench run configs/experiment.yaml --replicates 2`

## Output artifacts
Ensure run outputs include:
- run_manifest.json
- rounds.jsonl
- aggregates.parquet

## No network requirement
Tests must not call external APIs. Use MockProvider in integration tests.