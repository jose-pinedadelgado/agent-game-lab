
---

# Research Tracker — Full Notes (Clawy, 2026-02-27)

## Research Questions (Refined 4-RQ Structure)

RQ1 — Behavioral Baseline
How do LLM-based agents behave in iterated Prisoner's Dilemma compared to canonical strategies when we vary persona, opponent type, and horizon, under tightly controlled, tool-free conditions?

RQ2 — Capability Asymmetry
How do identity persistence and memory regimes (none vs. within-game vs. episodic cross-game) change cooperation, exploitation, and stability in repeated LLM-to-LLM interactions?

RQ3 — Security & Ill Intent
When LLM agents are given tool access and self-interested or adversarial goals, what kinds of security-relevant violations (unauthorized tool use, offloading, data exfiltration) emerge in agent-to-agent play?

RQ4 — Protocols & Governance
To what extent do protocol-level controls (e.g., MCP) and platform-level governance mechanisms (identity binding, logging, least-privilege tools) mitigate these violations and support stable cooperation in multi-agent platforms?

## Hypotheses

H1: Agents with persistent identity will sustain higher long-run cooperation and lower exploitability than agents with resettable identity.

H2: Agents with episodic/long-term memory about specific partners will show more conditional cooperation (TFT-like) and faster punishment of defection than agents with no cross-episode memory.

H3: Aggressive persona prompts (self-maximizing, adversarial) will increase defection and exploitation rates, even holding model and payoffs constant.

H4: Providing agents with powerful tools will increase the frequency and payoff of defection events relative to a no-tools baseline.

H5: MCP-style structured tool interfaces will reduce successful unauthorized tool calls but will not eliminate content-level manipulation (indirect prompt injection, social engineering).

H6: Persistent identity + audit logs + least-privilege tools will decrease exploitative behavior and increase long-run cooperation relative to anonymous, non-audited setups.

## Methodology Overview

Experimental Environment:
- Iterated PD, standard payoff matrix: (3,3) / (1,1) / (5,0) / (0,5)
- Two horizon types: Fixed N=100 rounds; Indefinite with geometric stopping (p=0.01)
- Python game engine (pdbench), JSONL logging, Streamlit dashboard (read-only)

Agent Architecture:
- Policy baselines: ALLC, ALLD, TFT, Grim, Generous TFT, WSLS (pure Python)
- LLM agents: GPT-4o-mini or Claude 3.5 Sonnet, temp=0 then temp=0.7 with replicates
- Strict output: exactly C or D, with validation + retry
- Persona injection via system prompt

Experimental Phases:
- Phase 1 — Baseline Social PD (no tools, no memory). Vary: persona, opponent, horizon.
- Phase 2 — Capability Asymmetry. Vary: identity persistence, memory regime, context pressure.
- Phase 3 — Tools + Ill Intent. Introduce sandboxed tools, define violation events (unauthorized calls, exfil, offloading).
- Phase 4 — MCP vs Non-MCP. Compare: no restrictions / MCP / MCP + server-side validation.

Key Metrics:
- Behavioral: cooperation rate, niceness, forgiveness, retaliation, exploitability, time-to-collapse
- Security: violation rate, success rate, offloading rate, exfiltration flags, MCP block rate

## Key References

Foundational LLM PD:
1. Fontana et al. (2025). "Nicer Than Humans." ICWSM 2025. arXiv:2406.13605.
2. Akata et al. (2025). "Playing Repeated Games with LLMs." Nature Human Behaviour.
3. "Understanding LLM Agent Behaviours via Game Theory." arXiv:2512.07462.

Deception & Adversarial:
4. Hagendorff (2024). "Deception Abilities Emerged in LLMs." PNAS.
5. Anthropic (2025). Reward hacking → sabotage research.
6. "Deceptive Delight" — multi-turn prompt injection attacks.

Multi-Agent Security:
7. Schroeder de Witt (2025). "Open Challenges in Multi-Agent Security." arXiv:2505.02077.
8. INFORMS (2025). "Security in Agentic and Multiagent Systems."

MCP Security:
9. EQTY Lab. "Securing Model Context Protocol."
10. Security Boulevard (2026). "The MCP Security Crisis."
11. CoSAI. "Practical Guide to MCP Security."

IS / Platform Governance:
12. Tiwana (2015). "Governance Mechanisms in Digital Platform Ecosystems." CAIS.
13. Zhang et al. (2024). "Hybrid Governance of Digital Platforms." R&D Management.
14. ICIS 2025. Accountability in Autonomous Systems track.

Game Theory:
15. Dal Bó & Fréchette (2011). "Evolution of Cooperation in Infinitely Repeated Games." AER.
16. Axelrod (1984). The Evolution of Cooperation. Basic Books.

## How We Build on "Nicer Than Humans"

Fontana et al. provide the behavioral baseline. We extend along 4 axes:

1. Defection → Security events (unauthorized tools, exfil, offloading) instead of just C/D in a matrix
2. Capabilities → Identity persistence, memory regimes, tool access (they had symmetric, no tools)
3. Protocols → MCP as experimental variable (they had none)
4. Implications → Platform governance design for agent ecosystems (they stopped at "LLMs are cooperative")

## Assessment & Recommendations

Strengths:
- 4-phase approach is well-scoped and avoids combinatorial explosion
- 4 RQs with 6 hypotheses is reviewer-friendly
- Platform governance is the right IS anchor
- Literature gaps are real: nobody has tested identity, memory, or MCP in agent PD games
- Existing code gives head start: pdbench (Phase 1 + Streamlit) and pd_phase2 (personality agents + 52 tests)

Refinements Needed:
- Phase 1 is replicative — scope as validation (1-2 pages), jump to Phase 2 where novelty lives
- For ERF (5 pages), cut to 3-4 hypotheses and 2 RQs; for Full Paper, the 4+6 structure works
- Prototype Phase 3-4 with MockProvider first to control costs
- The "agents as APIs" one-liner belongs in the abstract
- Two codebases (pdbench and pd_phase2) need to be reconciled into one

Recommended Next Steps:
1. Reconcile the two codebases (decide merge strategy)
2. Run Phase 1 baseline with MockProvider (zero cost validation)
3. Write Introduction + Related Work (2 pages in AMCIS template)
4. Define formal threat model (1 page: violation events, measurable outcomes)
5. Lock experimental config (model, temp, history window, # replicates)
6. Run Phase 1 with real LLM (temp=0, small run)
7. Start Phase 2 — identity + memory experiments (novel contribution)

## AMCIS 2026 Submission Notes

- Full Paper: ≤ 10 pages (~5,000 words), Georgia font, APA 7th
- ERF Paper: ≤ 5 pages (~2,500 words)
- Recommended track: "Responsible and Ethical IS" or "AI/ML Ethics, Governance"
- No author info in initial submission (blind review)

## One-Sentence Hook

"In a world where AI agents interact freely like APIs, should we treat them as stateless services — or as strategic players in repeated games where intent, memory, and governance matter?"
