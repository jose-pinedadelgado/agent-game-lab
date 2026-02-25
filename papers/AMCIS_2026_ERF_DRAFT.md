Short Title: Benchmarking Agentic LLM Cooperation

Emergent Research Forum (ERF) Paper

# Benchmarking Agentic LLM Cooperation: Protocol Safeguards and Game-Theoretic Awareness in Iterated Prisoner's Dilemma Experiments

## Introduction

As large language model (LLM) agents are increasingly deployed as autonomous actors in digital platforms, workflows, and API ecosystems, a critical question emerges: should these agents be treated as stateless services, or as strategic players in repeated interactions where intent, memory, and future behavior matter? When multiple LLM-based agents interact freely on a shared platform to perform tasks, their interactions take on characteristics of repeated games with security implications. An agent designed with adversarial intent could exploit a cooperative counterpart, offload computational costs, or manipulate outcomes through strategic communication.

The Prisoner's Dilemma (PD) provides a canonical, theoretically grounded mechanism to operationalize these dynamics. While recent work has established that LLMs exhibit cooperative behavior in PD settings (Fontana et al. 2025; Akata et al. 2025; Pal et al. 2026), this literature has focused on characterizing behavioral profiles rather than evaluating governance mechanisms. No study has tested whether protocol-level safeguards or game-theoretic awareness in agent design can reduce vulnerability to adversarial exploitation. Furthermore, the information systems (IS) perspective on platform governance, trust, and sociotechnical design remains entirely absent from this literature.

This paper presents a research-in-progress that addresses these gaps. We introduce pdbench, a reproducible benchmarking harness for iterated PD experiments with LLM agents, and describe a multi-phase experimental design that systematically varies agent personality, pre-decision communication, and protocol enforcement as experimental factors. We report preliminary results from Phase 1 (baseline experiments) and outline the methodology for Phase 2, which adds security-relevant variables. Our research question is:

*RQ: In iterated PD interactions between LLM-based agents, do protocol-level safeguards reduce vulnerability to adversarial exploitation, and does equipping agents with game-theoretic awareness further improve cooperative outcomes beyond what protocols alone provide?*

## Related Work

### LLM Behavior in the Prisoner's Dilemma

A growing body of work examines LLM behavior in game-theoretic settings. Fontana et al. (2025) study three LLMs in 100-round iterated PD against random opponents, finding that LLMs are generally "nicer than humans," with cooperation rates averaging 79% compared to 37% for human participants. Each model exhibits a distinct behavioral profile: Llama2 and GPT-3.5 shift from Grim Trigger to Always Cooperate as opponent hostility decreases, while Llama3 remains consistently exploitative. Akata et al. (2025) broaden the scope to 144 games across six families, testing LLM-vs-LLM, LLM-vs-policy, and LLM-vs-human conditions. They find that GPT-4 permanently shifts to defection after a single opponent betrayal, even when explicitly told the opponent will cooperate afterward. Most recently, Pal et al. (2026) use a strategy elicitation method to identify each model's characteristic memory-1 strategy, finding that Claude implements a Forgiver strategy while GPT-4o implements Grim Trigger, suggesting that model-specific strategic "personalities" are stable and identifiable.

### Gaps in Existing Literature

Despite this progress, several critical gaps remain. First, no study systematically tests LLM agents against the full set of canonical game-theoretic strategies (TFT, GRIM, GTFT, WSLS) as diagnostic baselines. Second, all existing studies use fixed horizons announced to agents; none test geometric stopping (unknown endpoint), which fundamentally changes optimal strategies per repeated-game theory (Dal Bo 2005). Third, while persona prompts have been shown to influence behavior (Phelps and Russell 2023; Guo 2023), no study maps structured persona configurations to emergent strategies using canonical baselines. Fourth, no study evaluates whether protocol-level interventions (structured interaction formats, validation layers) can reduce exploitation in agent-to-agent interactions. Finally, the entire literature is situated in CS, AI, and psychology venues. The IS perspective on platform governance, sociotechnical design, and accountability in autonomous agent ecosystems is absent.

## Research Design

### The pdbench Artifact

We develop pdbench, an open-source benchmarking harness for iterated PD experiments with configurable agents. The artifact implements: (1) a game engine supporting fixed and geometric horizons with seeded RNG for reproducibility; (2) six deterministic policy agents implementing canonical strategies (ALLC, ALLD, TFT, GRIM, GTFT, WSLS); (3) LLM-backed agents with configurable personas, provider adapters, and strict output parsing with retry logic; (4) a CLI for experiment execution and validation; and (5) structured output (JSONL per round, Parquet aggregates, JSON manifest) with a read-only Streamlit visualization interface. The separation of experiment runner from visualization ensures reproducibility and auditability.

### Experimental Variables

Our experimental design manipulates three independent variables across two phases:

**Phase 1 (Baseline PD, complete).** LLM agents with configurable persona prompts play iterated PD against canonical policy agents. No tools, no communication, no memory beyond a sliding history window. This phase establishes behavioral baselines and validates the methodology against prior work.

**Phase 2 (Capability asymmetry, in progress).** We introduce three experimental dimensions:

1. *Agent personality* (6 levels): Naive (no strategic awareness), Aware (basic defensive posture), Strategic (explicit game-theoretic reasoning), Deceptive (appears cooperative but exploits), Manipulative (actively influences opponent behavior), and Cooperative (genuine mutual benefit orientation). These operationalize a gradient from vulnerability to adversarial intent.

2. *Pre-decision communication* (2 levels): Off (standard PD, choose based on history only) and On (agents exchange messages before choosing their action each round). This tests whether communication enables manipulation or facilitates coordination.

3. *Protocol mode* (2 levels): Unstructured (free-form interaction) and Structured (protocol validator enforces interaction format, schema compliance, and authorization checks, analogous to Model Context Protocol safeguards). This tests whether protocol-level governance reduces exploitation.

### Dependent Variables and Metrics

For each condition, we compute: cooperation rate (overall and over time), retaliation rate (probability of defecting given opponent defected previously), forgiveness rate (probability of cooperating given opponent defected previously), exploitability payoff gap (difference in cumulative payoffs between agents), and time to collapse (first round where cooperation drops below 20% for 10 consecutive rounds). These metrics align with both game-theoretic constructs and IS concerns about governance, trust, and system stability.

## Preliminary Results

Phase 1 experiments used gpt-4.1-mini (temperature=0) playing 50-round fixed-horizon games with the standard PD payoff matrix (CC=3, CD=0, DC=5, DD=1). We tested three LLM personas (strategic cooperator, adaptive diplomat, ruthless optimizer) against all six policy agents in a tournament format (18 matchups, 2 replicates each).

Results reveal a clear pattern: cooperative personas significantly outperform the selfish persona across the tournament. The strategic cooperator achieved an average payoff of 132.4 per game, compared to 104.3 for the ruthless optimizer, a 27% performance gap. Both cooperative personas achieved perfect mutual cooperation (cooperation rate = 1.0, payoff = 150) against five of six opponents (TFT, GRIM, GTFT, WSLS, ALLC). Against Always Defect, they adapted quickly, reducing cooperation to 0.11 within the first few rounds. In contrast, the ruthless optimizer achieved the highest single-matchup payoff (250 against ALLC through complete exploitation) but was consistently punished by retaliatory opponents, yielding only 50 per game against ALLD and similarly low payoffs against TFT and GRIM.

These baseline findings establish that (1) LLM agents can identify and adapt to canonical strategies, (2) cooperative personas achieve higher aggregate outcomes than selfish ones due to successful sustained cooperation with retaliatory opponents, and (3) the pdbench artifact produces interpretable, reproducible results consistent with game-theoretic predictions. Phase 2 experiments will test whether structured protocols and game-theoretic awareness further improve resilience against adversarial counterparts.

## Discussion and Expected Contributions

### Theoretical Contributions

This research contributes to IS theory in three ways. First, we extend platform governance theory to agent-to-agent interactions by demonstrating that when LLM agents function as autonomous actors in digital ecosystems, their interactions become security-sensitive repeated games that require governance beyond traditional API access controls. Second, we bridge behavioral game theory and sociotechnical systems design by connecting LLM strategic behavior to practical platform design implications (identity persistence, protocol enforcement, audit mechanisms). Third, we provide the first IS-grounded empirical evaluation of whether protocol-level safeguards (analogous to Model Context Protocol) can reduce adversarial exploitation in agent interactions.

### Practical Contributions

For practitioners designing agent platforms, our findings will inform: (a) whether agents need to be equipped with game-theoretic awareness to protect themselves in open ecosystems, or whether platform-level controls suffice; (b) which governance mechanisms (structured protocols, communication channels, personality constraints) most effectively sustain cooperation; and (c) under what conditions cooperation collapses and how platform design can prevent this.

### Limitations and Next Steps

Phase 1 limitations include: a single LLM provider (OpenAI gpt-4.1-mini), fixed horizon only, and limited replicates. Phase 2 will address these by: (1) completing the 6-personality x 2-chat x 2-protocol factorial design; (2) adding geometric horizon conditions to test the "shadow of the future" effect; (3) increasing replicates to 10-20 per condition for statistical power; and (4) testing additional LLM providers (Claude, open-source models) for cross-model generalizability. The full experimental results will be submitted as a completed research paper.

## References

Akata, E., Schulz, L., Coda-Forno, J., Oh, S.J., Bethge, M., and Schulz, E. (2025). Playing Repeated Games with Large Language Models. *Nature Human Behaviour*.

Dal Bo, P. (2005). Cooperation under the Shadow of the Future: Experimental Evidence from Infinitely Repeated Games. *American Economic Review*, 95(5), 1591-1604.

Fontana, N., Pierri, F., and Arnaboldi, V. (2025). Nicer Than Humans: How Do Large Language Models Behave in the Prisoner's Dilemma? *Proc. 19th AAAI Conf. on Web and Social Media (ICWSM)*.

Guo, F. (2023). GPT in Game Theory Experiments. arXiv:2305.05516.

Pal, S., Mallela, A., Hilbe, C., Pracher, L., Wei, C., Fu, F., Schnell, S., and Nowak, M.A. (2026). Strategies of Cooperation and Defection in Five Large Language Models. arXiv:2601.09849.

Phelps, S. and Russell, Y.I. (2023). The Machine Psychology of Cooperation: Can GPT Models Operationalise Prompts for Altruism, Cooperation, Competitiveness and Selfishness into Corresponding Behaviours? arXiv:2305.07970.

Proverbio, D., Buscemi, A., Di Stefano, A., Han, T.A., Castignani, G., and Lie, P. (2025). Can LLMs Effectively Provide Game-Theoretic-Based Scenarios for Cybersecurity? *Frontiers in Computer Science*, 7, 1703586.

Zhu, Q. (2025). Game Theory Meets LLM and Agentic AI: Reimagining Cybersecurity for the Age of Intelligent Threats. arXiv:2507.10621.
