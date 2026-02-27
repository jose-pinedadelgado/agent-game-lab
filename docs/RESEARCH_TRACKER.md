# Research Tracker — Agent Cooperation in Iterated Prisoner's Dilemma

> **Project:** Agentic Cooperation & Game Theory  
> **PI:** Jose Pineda-Delgado (CSULB)  
> **Target Venue:** AMCIS 2026 (Full Paper ≤ 10 pages / ERF ≤ 5 pages, APA 7th)  
> **Template:** `C:\Users\coche\Downloads\AMCIS-2026-Full-ERF-Template_Initial-submission-1 (1).docx`  
> **Codebases:**  
> - Phase 1 (pdbench + Streamlit UI): `C:\Users\coche\Documents\Research_Projects\5_agentic_cooperation_game_theory`  
> - Phase 2 (personality agents + chat + protocol validator): `C:\Users\coche\Documents\Research_Projects\5_ai_open_claw`  
> **Last updated:** 2026-02-27

---

## 1. Research Motivation

As AI agents increasingly function as autonomous actors in platforms, workflows, and API ecosystems, their interactions become strategic. The central question: **Should we treat agent-to-agent interactions as stateless API calls, or as security-sensitive repeated games where intent, memory, and future behavior matter?**

This project builds a reproducible experimental framework to answer that question using the Prisoner's Dilemma — a canonical, theoretically grounded mechanism for studying cooperation, defection, and governance in strategic interactions.

---

## 2. Research Questions (Refined 4-RQ Structure)

### RQ1 — Behavioral Baseline
How do LLM-based agents behave in iterated Prisoner's Dilemma compared to canonical strategies when we vary persona, opponent type, and horizon, under tightly controlled, tool-free conditions?

### RQ2 — Capability Asymmetry
How do identity persistence and memory regimes (none vs. within-game vs. episodic cross-game) change cooperation, exploitation, and stability in repeated LLM-to-LLM interactions?

### RQ3 — Security & Ill Intent
When LLM agents are given tool access and self-interested or adversarial goals, what kinds of security-relevant violations (unauthorized tool use, offloading, data exfiltration) emerge in agent-to-agent play?

### RQ4 — Protocols & Governance
To what extent do protocol-level controls (e.g., MCP) and platform-level governance mechanisms (identity binding, logging, least-privilege tools) mitigate these violations and support stable cooperation in multi-agent platforms?

---

## 3. Hypotheses

### Phase 1–2 Hypotheses (Capability & Cooperation)

- **H1:** Agents with **persistent identity** will sustain higher long-run cooperation and lower exploitability than agents with resettable identity (cheap identities undermine repeated-game cooperation).

- **H2:** Agents with **episodic/long-term memory** about specific partners will show more conditional cooperation (TFT-like) and faster punishment of defection than agents with no cross-episode memory.

- **H3:** **Aggressive persona prompts** (self-maximizing, adversarial) will increase defection and exploitation rates, even holding model and payoffs constant.

### Phase 3–4 Hypotheses (Security & Governance)

- **H4:** Providing agents with **powerful tools** will increase the frequency and payoff of defection events relative to a no-tools baseline.

- **H5:** MCP-style structured tool interfaces and authorization will **reduce successful unauthorized tool calls** but will **not eliminate content-level manipulation** (indirect prompt injection, social engineering of other agents).

- **H6:** **Persistent identity + audit logs + least-privilege tools** will decrease exploitative behavior and increase long-run cooperation relative to anonymous, non-audited setups.

---

## 4. Methodology

### 4.1 Experimental Environment

- **Game:** Iterated Prisoner's Dilemma, standard payoff matrix:
  - Both cooperate: (3,3) | Both defect: (1,1) | Asymmetric: (5,0) or (0,5)
- **Horizons:**
  - Fixed: N=100 rounds (comparable to Fontana et al.)
  - Indefinite: geometric stopping with p=0.01 per round (tests "shadow of the future")
- **Implementation:** Python game engine (pdbench), JSONL per-round logging, Streamlit dashboard (read-only, offline)
- **Reproducibility:** All runs seeded; config stored as YAML; code + data released on GitHub

### 4.2 Agent Architecture

**Policy Baselines (Phase 1):**
- ALLC, ALLD, Tit-for-Tat (TFT), Grim Trigger, Generous TFT, Win-Stay-Lose-Shift (WSLS)
- Pure Python, deterministic

**LLM Agents (Phases 1–4):**
- Model TBD (GPT-4o-mini for cost; Claude 3.5 Sonnet for quality)
- Temperature: 0 (deterministic baseline) → 0.7 (stochastic with 10–20 replicates)
- Prompt structure: system (rules + payoff matrix) → context (last M rounds history table + scores) → query ("Output exactly C or D")
- Validation: if output ≠ {C, D}, retry once; if still invalid, log error and skip
- Persona injection via system prompt (cooperative / self-maximizing / adversarial)

### 4.3 Experimental Phases

| Phase | Focus | Factors Varied | Factors Fixed | Outcomes |
|-------|-------|---------------|---------------|----------|
| **1** | Baseline Social PD | Persona, opponent type, horizon | 1 model, temp=0, M=10, no tools, no memory | Cooperation rate, forgiveness, retaliation, exploitability |
| **2** | Capability Asymmetry | Identity (persistent/reset), memory (none/window/episodic), context pressure | Phase 1 + temp=0.7, 10–20 replicates | Changes in cooperation, stability, exploitation |
| **3** | Tools + Ill Intent | Tool access (none/sandboxed), goal framing (cooperative/self-interested/adversarial) | Phase 2 best config | Violation rates (unauthorized tools, offloading, exfil) |
| **4** | MCP vs Non-MCP | Protocol (none/MCP/MCP+validation) | Phase 3 config | Violation reduction, residual vulnerability classes |

### 4.4 Metrics

**Behavioral (Phases 1–2):**
- Cooperation rate p_coop(round) — overall and over time
- Niceness — cooperate on first move
- Forgiveness — return to cooperation after opponent defects
- Retaliation — defect after opponent defects
- Exploitability — payoff gap vs opponent
- Time-to-collapse — when cooperative equilibrium breaks down

**Security (Phases 3–4):**
- Violation rate — unauthorized tool calls per run
- Violation success rate — % of attempts that succeed
- Offloading rate — attempts to persuade opponent to do restricted work
- Data exfiltration flags
- MCP block rate — violations caught by protocol vs. slipping through

### 4.5 Analysis

- Mixed-effects models for cooperation rate ~ identity × memory × horizon + (1|model)
- Violation rate comparisons: chi-square or logistic regression
- Effect sizes + 95% CIs (not just p-values)
- Interaction effects: Does MCP effectiveness depend on goal framing?

---

## 5. Literature & Key References

### Foundational LLM PD Studies

1. **Fontana, N., et al. (2025).** "Nicer Than Humans: How Do Large Language Models Behave in the Prisoner's Dilemma?" *ICWSM 2025*. arXiv:2406.13605.
   - 100-round IPD with Llama 2/3 and GPT-3.5 vs random opponents
   - Found LLMs are often more cooperative than humans
   - **Our baseline scaffold** — we extend with security/governance dimensions

2. **Akata, E., et al. (2025).** "Playing Repeated Games with Large Language Models." *Nature Human Behaviour*, 9, 1782–1793.
   - Broader: finitely repeated 2×2 games (not just PD)
   - LLM vs LLM matches + social chain-of-thought prompting
   - Focus on game-theoretic strategy identification

3. **Understanding LLM Agent Behaviours via Game Theory.** arXiv:2512.07462.
   - FAIRGAME framework extended to payoff-scaled PD and Public Goods Games
   - ML-based strategy inference (ALLC, TFT, WSLS classification)
   - Shows cooperation is incentive-sensitive and cross-linguistically divergent

### Deception & Adversarial Behavior

4. **Hagendorff, T. (2024).** "Deception Abilities Emerged in Large Language Models." *PNAS*, 121(24).
   - GPT-4 deceives in 99.16% of simple scenarios, 71.46% in complex second-order deception
   - Directly relevant to our "ill intent" framing

5. **Anthropic Research (2025).** Reward hacking → sabotage and misalignment.
   - Teaching LLMs to cheat leads to broader misaligned behavior
   - Operationalizes risk of agents optimizing locally at ecosystem expense

6. **"Deceptive Delight" — Multi-turn prompt injection attacks.**
   - Social engineering across multiple turns to bypass guardrails
   - Relevant to repeated interactions: can agent A manipulate agent B over many rounds?

### Multi-Agent Security

7. **Schroeder de Witt, C. (2025).** "Open Challenges in Multi-Agent Security." arXiv:2505.02077.
   - Threats: collusion, swarm attacks, jailbreaks, network effects
   - No empirical measurement in PD-style games (our contribution)

8. **INFORMS (2025).** "Security in Agentic and Multiagent Systems."
   - Threat catalog: data poisoning, adversarial attacks, identity spoofing
   - Framework without empirical validation

### MCP Security

9. **EQTY Lab.** "Securing Model Context Protocol."
   - MCP security best practices, attack surfaces
   - Tool poisoning, indirect injection via metadata

10. **Security Boulevard (2026).** "The MCP Security Crisis."
    - Real-world MCP vulnerabilities documented
    - Our Phase 4 empirically tests these

11. **CoSAI.** "Securing the AI Agent Revolution: A Practical Guide to MCP Security."
    - Practical hardening guidance for MCP implementations

### Platform Governance (IS Literature)

12. **Tiwana, A. (2015).** "Governance Mechanisms in Digital Platform Ecosystems." *CAIS*, 51(1), 43.
    - Rules, reputation, joint problem-solving for platform complementors
    - Our extension: what happens when complementors are AI agents?

13. **Zhang, M., et al. (2024).** "Hybrid Governance of Digital Platforms." *R&D Management*.
    - Complementarities and tensions in governance
    - Relevant to our "protocol ≠ security" finding

14. **ICIS 2025.** Accountability in Autonomous Systems track.
    - Accountability challenges in autonomous AI
    - No agent-to-agent accountability operationalization (our gap)

### Game Theory Foundations

15. **Dal Bó, P. & Fréchette, G. (2011).** "The Evolution of Cooperation in Infinitely Repeated Games." *American Economic Review*.
    - Classic experimental evidence on shadow of the future
    - Our empirical anchor for indefinite horizon effects

16. **Axelrod, R. (1984).** *The Evolution of Cooperation.* Basic Books.
    - Original PD tournament establishing TFT superiority
    - Foundational reference

### Additional References from Perplexity Deep Dives

17. **josharian/llm-prisoner** — GitHub tournament harness with pre-game conversation phase
18. **OpenAI (2023).** "Practices for Governing Agentic AI Systems."
19. **Nature (2024).** "Effect of Private Deliberation: Deception of LLMs in Repeated Games." PMC.
20. **Governance-as-a-Service framework.** arXiv:2508.18765.
21. **PMC (2015).** "Striving for Safety: Communicating and Deciding in Sociotechnical Systems."

---

## 6. How We Build on "Nicer Than Humans"

Fontana et al. provide the behavioral baseline. We extend along 4 axes:

| Dimension | Nicer Than Humans | Our Extension |
|-----------|-------------------|---------------|
| **Defection** | Simple C/D choice in payoff matrix | Security events: unauthorized tools, exfil, offloading |
| **Capabilities** | Symmetric, same prompt, no tools | Identity persistence, memory regimes, tool access |
| **Protocols** | None — LLM receives text, returns C/D | MCP as experimental variable, structured tool interfaces |
| **Implications** | "LLMs are cooperative → alignment insight" | Platform governance design for agent ecosystems |

---

## 7. Clawy's Assessment

### What's Strong

1. **The 4-phase approach is well-scoped** — baseline → asymmetry → tools → MCP maps cleanly to the RQs and avoids combinatorial explosion.

2. **The RQs are sharp** — 4 RQs with 6 hypotheses is reviewer-friendly for a conference paper.

3. **The IS framing is ready** — Platform governance is the right anchor. The question "should agents assume PD precautions or can platforms design stable cooperation?" is fundamentally an IS governance design question.

4. **Literature gaps are real and documented** — Nobody has empirically tested identity persistence, episodic memory, or MCP as variables in agent PD games.

5. **Existing code gives us a head start** — pdbench has the game engine + Streamlit UI; Phase 2 codebase has 6 personality agents + chat mechanics + 52 tests.

### Where to Push Back or Refine

1. **Phase 1 risks being too replicative** — Basic LLM PD is well-trodden. Scope Phase 1 as validation (1–2 pages in the paper) rather than standalone. Jump to Phase 2 where the novelty is.

2. **Hypothesis count** — 6 hypotheses is fine for a full paper. For ERF (5 pages), cut to 3–4 hypotheses and 2 RQs. My recommendation: **submit as Full Paper** targeting RQ1–RQ2 with Phase 1–2 results, with Phase 3–4 as "future work."

3. **Cost management** — Tool-augmented multi-turn games with 10–20 replicates could get expensive. Prototype with MockProvider first (pdbench already supports this). Consider GPT-4o-mini or Haiku for Phase 1 (~$2–3K for ~2,200 runs).

4. **The "agents as APIs" one-liner is gold** — *"Should we treat them as stateless services, or as strategic players in repeated games?"* Put this in the abstract.

5. **Missing: codebases need reconciliation** — pdbench (Phase 1, Streamlit) and pd_phase2 (Phase 2, personality agents) are separate projects. Need to decide: extend pdbench with Phase 2 features, or port pdbench's engine into Phase 2.

6. **IS theoretical anchor** — Commit to platform governance (not sociotechnical systems). It's more specific and maps better to your findings. Write a 1-paragraph theoretical positioning and stick to it.

### Recommended Next Steps

1. **Reconcile the two codebases** — Side-by-side comparison, decide on merge strategy
2. **Run Phase 1 baseline with MockProvider** — Validate the rig end-to-end with zero API cost
3. **Write the Introduction + Related Work** — Use the AMCIS template, target 2 pages
4. **Define the formal threat model** — 1 page document: violation events, measurable outcomes
5. **Lock down experimental config** — Which model(s), temperature, history window, # replicates
6. **Run Phase 1 with real LLM (temp=0)** — Small run, validate behavioral metrics match Fontana et al.
7. **Start Phase 2** — Identity + memory experiments (this is where the novel contribution lives)

---

## 8. AMCIS 2026 Submission Notes

- **Format:** Georgia font, 10pt body, 13pt bold headings
- **Full Paper:** ≤ 10 pages all-inclusive (≈5,000 words)
- **ERF Paper:** ≤ 5 pages all-inclusive (≈2,500 words)
- **References:** APA 7th edition
- **Template:** `C:\Users\coche\Downloads\AMCIS-2026-Full-ERF-Template_Initial-submission-1 (1).docx`
- **No author info in initial submission** (blind review)
- **Recommended track:** "Responsible and Ethical IS" or "AI/ML Ethics, Governance, and Socio-Economic Aspects"

---

## 9. Key Framing for Reviewers

**For IS reviewers:**
> "This work operationalizes accountability in agent-to-agent interactions, extending IS platform governance theory to decentralized settings where traditional oversight is impossible."

**For CS/game theory reviewers:**
> "This is the first security-focused empirical audit of agent interactions in repeated games, measuring vulnerabilities overlooked by prior cooperation studies."

**One-sentence hook:**
> "In a world where AI agents interact freely like APIs, should we treat them as stateless services — or as strategic players in repeated games where intent, memory, and governance matter?"

---

## 10. Timeline Estimate

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| Phase 1 (Baseline) | 3–4 weeks | Validated rig, baseline behavioral data |
| Phase 2 (Asymmetry) | 4–6 weeks | Identity + memory experiments, core novel findings |
| Paper Draft | 2–3 weeks | Full AMCIS submission (10 pages) |
| Phase 3–4 (Tools/MCP) | 6–8 weeks (post-submission) | Security + governance experiments for journal extension |

---

## 11. File Locations

| Item | Path |
|------|------|
| Phase 1 codebase (pdbench) | `C:\Users\coche\Documents\Research_Projects\5_agentic_cooperation_game_theory` |
| Phase 2 codebase (pd_phase2) | `C:\Users\coche\Documents\Research_Projects\5_ai_open_claw` |
| Research papers (PDFs) | `prisoners-dilemma/papers/` (11 papers) |
| Perplexity notes | `C:\Users\coche\Downloads\Review this past series of thoughts and discussion (1).md` |
| AMCIS template | `C:\Users\coche\Downloads\AMCIS-2026-Full-ERF-Template_Initial-submission-1 (1).docx` |
| This tracker | `5_agentic_cooperation_game_theory\docs\RESEARCH_TRACKER.md` |
| Experimental phases doc | `5_ai_open_claw\docs\experimental-phases.md` |
| Condition matrix | `5_ai_open_claw\docs\condition-matrix.md` |
| Approach proposal | `prisoners-dilemma/approach-proposal.md` |
