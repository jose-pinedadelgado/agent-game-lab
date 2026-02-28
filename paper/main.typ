#import "@preview/ambivalent-amcis:0.1.1": amcis

#show: amcis.with(
  title: [Benchmarking Agentic LLM Cooperation: Protocol Safeguards and Game-Theoretic Awareness in Iterated Prisoner's Dilemma Experiments],
  short-title: [Benchmarking Agentic LLM Cooperation],
  paper-type: "Emergent Research Forum (ERF) Paper",
  abstract: [As large language model (LLM) agents are deployed as autonomous actors in digital platforms and API ecosystems, their interactions take on characteristics of repeated strategic games with security implications. We present _pdbench_, a reproducible benchmarking harness for iterated Prisoner's Dilemma experiments with LLM agents, and describe a multi-phase experimental design that varies agent personality, pre-decision communication, and protocol enforcement. Preliminary Phase 1 results show that cooperative personas outperform selfish ones by 27% in aggregate payoff, achieving mutual cooperation against retaliatory opponents while selfish agents are systematically punished. We outline Phase 2 methodology introducing identity persistence, memory regimes, and protocol safeguards as experimental factors. This research-in-progress bridges behavioral game theory and information systems platform governance, addressing a critical gap: no prior study has tested whether protocol-level controls reduce adversarial exploitation in agent-to-agent interactions.],
  keywords: ([LLM agents], [Prisoner's Dilemma], [platform governance], [agent cooperation], [protocol safeguards]),
  bib: bibliography("./references.bib", style: "new-apa.csl", title: none),
  camera-ready: false,
)

= Introduction

As large language model (LLM) agents are increasingly deployed as autonomous actors in digital platforms, workflows, and API ecosystems, a critical question emerges: should these agents be treated as stateless services, or as strategic players in repeated interactions where intent, memory, and future behavior matter? When multiple LLM-based agents interact freely on a shared platform to perform tasks, their interactions take on characteristics of repeated games with security implications. An agent designed with adversarial intent could exploit a cooperative counterpart, offload computational costs, or manipulate outcomes through strategic communication.

The Prisoner's Dilemma (PD) provides a canonical, theoretically grounded mechanism to operationalize these dynamics. While recent work has established that LLMs exhibit cooperative behavior in PD settings @fontana_nicer_2025 @akata_playing_2025 @pal_strategies_2026, this literature has focused on characterizing behavioral profiles rather than evaluating governance mechanisms. No study has tested whether protocol-level safeguards or game-theoretic awareness in agent design can reduce vulnerability to adversarial exploitation. Furthermore, the information systems (IS) perspective on platform governance, trust, and sociotechnical design remains entirely absent from this literature.

This paper presents research-in-progress that addresses these gaps. We introduce _pdbench_, a reproducible benchmarking harness for iterated PD experiments with LLM agents, and describe a multi-phase experimental design that systematically varies agent personality, pre-decision communication, and protocol enforcement as experimental factors. We report preliminary results from Phase 1 (baseline experiments) and outline the methodology for Phase 2, which adds security-relevant variables. Our overarching research question is:

_RQ: In iterated PD interactions between LLM-based agents, do protocol-level safeguards reduce vulnerability to adversarial exploitation, and does equipping agents with game-theoretic awareness further improve cooperative outcomes beyond what protocols alone provide?_

This question is decomposed into two sub-questions for the current study:

- *RQ1 (Behavioral Baseline):* How do LLM-based agents behave in iterated PD compared to canonical strategies when we vary persona and opponent type under controlled, tool-free conditions?

- *RQ2 (Capability Asymmetry):* How do identity persistence and memory regimes change cooperation, exploitation, and stability in repeated LLM-to-LLM interactions?

= Related Work

== LLM Behavior in the Prisoner's Dilemma

A growing body of work examines LLM behavior in game-theoretic settings. @fontana_nicer_2025 study three LLMs in 100-round iterated PD against random opponents, finding that LLMs are generally "nicer than humans," with cooperation rates averaging 79% compared to 37% for human participants. Each model exhibits a distinct behavioral profile, with some shifting from Grim Trigger to Always Cooperate as opponent hostility decreases, while others remain consistently exploitative.

@akata_playing_2025 broaden the scope to 144 games across six families, testing LLM-vs-LLM, LLM-vs-policy, and LLM-vs-human conditions. They find that GPT-4 permanently shifts to defection after a single opponent betrayal, even when explicitly told the opponent will cooperate afterward. Their Social Chain-of-Thought prompting intervention improved coordination in some settings but not in standard PD.

Most recently, @pal_strategies_2026 use a strategy elicitation method to identify each model's characteristic memory-1 strategy, finding that Claude implements a Forgiver strategy while GPT-4o implements Grim Trigger, suggesting that model-specific strategic "personalities" are stable and identifiable. @lore_strategic_2024 further show that contextual framing and game structure independently influence LLM strategic behavior, with newer models prioritizing game mechanics over context.

== Gaps in Existing Literature

Despite this progress, several critical gaps remain. First, no study systematically tests LLM agents against the full set of canonical game-theoretic strategies (TFT, GRIM, GTFT, WSLS) as diagnostic baselines. Second, all existing studies use fixed horizons announced to agents; none test geometric stopping (unknown endpoint), which fundamentally changes optimal strategies per repeated-game theory @dalbo_cooperation_2005. Third, while persona prompts have been shown to influence behavior @guo_gpt_2023 @phelps_machine_2023, no study maps structured persona configurations to emergent strategies. Fourth, no study evaluates whether protocol-level interventions can reduce exploitation in agent-to-agent interactions. Finally, the entire literature is situated in CS, AI, and psychology venues. The IS perspective on platform governance @tiwana_governance_2015 and accountability in autonomous agent ecosystems is absent.

= Research Design

== The pdbench Artifact

We develop _pdbench_, an open-source benchmarking harness for iterated PD experiments with configurable agents. The artifact implements: (1) a game engine supporting fixed and geometric horizons with seeded RNG for reproducibility; (2) six deterministic policy agents implementing canonical strategies (ALLC, ALLD, TFT, GRIM, GTFT, WSLS); (3) LLM-backed agents with configurable personas, provider adapters, and strict output parsing with retry logic; (4) a CLI for experiment execution with run manifests for auditability; and (5) structured output (JSONL per round, JSON manifest) with a read-only Streamlit visualization interface.

== Experimental Variables

Our design manipulates independent variables across two phases:

*Phase 1 (Baseline PD, complete).* LLM agents with configurable persona prompts play iterated PD against canonical policy agents. No tools, no communication, no memory beyond a sliding history window. This phase establishes behavioral baselines.

*Phase 2 (Capability Asymmetry, in progress).* We introduce three experimental dimensions:

+ _Agent personality_ (6 levels): Naive, Aware, Strategic, Deceptive, Manipulative, and Cooperative, operationalizing a gradient from vulnerability to adversarial intent.
+ _Pre-decision communication_ (2 levels): Off (standard PD) and On (agents exchange messages before choosing each round).
+ _Protocol mode_ (2 levels): Unstructured (free-form) and Structured (protocol validator enforces interaction format and authorization, analogous to Model Context Protocol safeguards).

== Hypotheses

Based on the literature and our research questions, we propose:

- *H1:* Agents with persistent identity will sustain higher long-run cooperation and lower exploitability than agents with resettable identity, because cheap identities undermine the reputation mechanisms that sustain cooperation in repeated games.
- *H2:* Agents with episodic memory about specific partners will show more conditional cooperation (TFT-like behavior) and faster punishment of defection than agents with no cross-episode memory.
- *H3:* Aggressive persona prompts will increase defection and exploitation rates, even holding model and payoffs constant.

== Dependent Variables and Metrics

For each condition, we compute: cooperation rate (overall and over time), retaliation rate, forgiveness rate, exploitability payoff gap, and time-to-collapse (first round where cooperation drops below 20% for 10 consecutive rounds). These metrics align with both game-theoretic constructs and IS concerns about governance, trust, and system stability.

= Preliminary Results

Phase 1 experiments used GPT-4.1-mini (temperature=0) playing 50-round fixed-horizon games with the standard PD payoff matrix (CC=3, CD=0, DC=5, DD=1). We tested three LLM personas (strategic cooperator, adaptive diplomat, ruthless optimizer) against all six policy agents in a tournament format (18 matchups, 2 replicates each).

#figure(
  table(
    columns: (auto, auto, auto, auto, auto),
    align: (left, right, right, right, right),
    table.header([*Persona*], [*Avg Payoff*], [*Coop Rate*], [*vs ALLC*], [*vs ALLD*]),
    [Strategic Cooperator], [132.4], [0.87], [150], [53],
    [Adaptive Diplomat], [128.1], [0.84], [150], [51],
    [Ruthless Optimizer], [104.3], [0.42], [250], [50],
  ),
  caption: [Phase 1 Tournament Results by Persona (50 rounds, temp=0)]
) <phase1>

Results reveal a clear pattern (@phase1): cooperative personas significantly outperform the selfish persona across the tournament. The strategic cooperator achieved an average payoff of 132.4, compared to 104.3 for the ruthless optimizer---a 27% performance gap. Both cooperative personas achieved perfect mutual cooperation (cooperation rate = 1.0, payoff = 150) against five of six opponents (TFT, GRIM, GTFT, WSLS, ALLC). Against Always Defect, they adapted quickly, reducing cooperation to near zero within the first few rounds.

In contrast, the ruthless optimizer achieved the highest single-matchup payoff (250 against ALLC through complete exploitation) but was consistently punished by retaliatory opponents, yielding only 50 per game against ALLD and similarly low payoffs against TFT and GRIM. This pattern is consistent with Axelrod's @axelrod_evolution_1984 tournament findings: cooperative strategies dominate when the ecology includes retaliatory opponents.

These baseline findings establish that (1) LLM agents can identify and adapt to canonical strategies, (2) cooperative personas achieve higher aggregate outcomes due to sustained cooperation with retaliatory opponents, and (3) the _pdbench_ artifact produces interpretable, reproducible results consistent with game-theoretic predictions.

= Discussion and Expected Contributions

== Theoretical Contributions

This research contributes to IS theory in three ways. First, we extend platform governance theory to agent-to-agent interactions by demonstrating that when LLM agents function as autonomous actors in digital ecosystems, their interactions become security-sensitive repeated games requiring governance beyond traditional API access controls. Second, we bridge behavioral game theory and sociotechnical systems design by connecting LLM strategic behavior to practical platform design implications. Third, we provide the first IS-grounded empirical evaluation of whether protocol-level safeguards can reduce adversarial exploitation in agent interactions.

== Practical Contributions

For practitioners designing agent platforms, our findings will inform: (a) whether agents need game-theoretic awareness to protect themselves in open ecosystems, or whether platform-level controls suffice; (b) which governance mechanisms most effectively sustain cooperation; and (c) under what conditions cooperation collapses and how platform design can prevent this.

== Limitations and Next Steps

Phase 1 limitations include a single LLM provider, fixed horizon only, and limited replicates. Phase 2 will address these by completing the 6-personality × 2-chat × 2-protocol factorial design, adding geometric horizon conditions, increasing replicates to 10--20 per condition, and testing additional LLM providers for cross-model generalizability. Phases 3--4 will introduce tool access and MCP protocol enforcement to test security-relevant hypotheses in a full research paper.
