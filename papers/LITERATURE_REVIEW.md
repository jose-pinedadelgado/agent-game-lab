# Literature Review: LLM Agents in Game-Theoretic Settings

*Last updated: 2026-02-25*
*For: AMCIS 2026 ERF submission on Agentic LLM Cooperation in Iterated Prisoner's Dilemma*

---

## Table of Contents

1. [Tier 1: Core PD + LLM Studies](#tier-1-core-pd--llm-studies)
2. [Tier 2: Multi-Agent Cooperation, Deception & Strategic Reasoning](#tier-2-multi-agent-cooperation-deception--strategic-reasoning)
3. [Tier 3: Security, Cybersecurity & Game Theory](#tier-3-security-cybersecurity--game-theory)
4. [Tier 4: Surveys & Theoretical Foundations](#tier-4-surveys--theoretical-foundations)
5. [Master Comparison Table](#master-comparison-table)
6. [Additional Comparison Dimensions](#additional-comparison-dimensions)
7. [Gap Analysis: What No One Has Done](#gap-analysis-what-no-one-has-done)

---

## Tier 1: Core PD + LLM Studies

These papers directly study LLM behavior in the Prisoner's Dilemma and form our primary methodological predecessors.

### 1.1 Fontana et al. (2024/2025) — "Nicer Than Humans"

**Citation:** Fontana, N., Pierri, F., & Arnaboldi, V. (2025). Nicer Than Humans: How Do Large Language Models Behave in the Prisoner's Dilemma? *Proc. 19th Int'l AAAI Conf. on Web and Social Media (ICWSM 2025)*. arXiv:2406.13605.

**Summary:** Systematic study of three LLMs (Llama2-70B, Llama3-70B, GPT-3.5-Turbo) in 100-round iterated PD against random opponents with varying cooperation probability (alpha 0.0-1.0). Introduces a "meta-prompting" validation technique to verify LLMs understand game rules before experiments. Finds LLMs are generally more cooperative than humans, with Llama2 and GPT-3.5 exhibiting higher cooperation than human baselines while Llama3 is more strategic/exploitative.

**Relevance:** Direct methodological predecessor. Their baseline IPD setup (100 rounds, history window, cumulative totals, behavioral metrics) closely parallels our Phase 1. Key differences: they only test against random opponents (not canonical strategies like TFT/GRIM), use no personas, and use temperature 0.7. Our work extends theirs by adding persona-driven agents, canonical policy baselines, geometric horizons, and security-relevant framing.

**Key Findings:**
- LLMs cooperate ~79% on average, vs. ~37% for humans (Brookins & DeBacker comparison)
- Llama2/GPT-3.5: shift from Grim Trigger to Always Cooperate when opponent defection < 30%
- Llama3: consistently exploitative (Grim Trigger across all conditions, cooperates only vs. Always Cooperate)
- Memory window of 10 rounds is optimal; full history causes Llama2 to revert to cooperation against ALLD
- Temperature has minimal effect on trends (Pearson r in [0.97, 1.0] across temp 0.1-1.0)
- Zero-Shot Chain-of-Thought did not improve performance

**Limitations:** Only 3 (now outdated) models; only random opponents; no personas; no geometric horizon; fixed payoff matrix; no retry logic described.

**Code:** https://github.com/NicoloFontana/nicer_than_humans_icwsm25

---

### 1.2 Akata et al. (2025) — "Playing Repeated Games with LLMs"

**Citation:** Akata, E., Schulz, L., Coda-Forno, J., Oh, S.J., Bethge, M., & Schulz, E. (2025). Playing Repeated Games with Large Language Models. *Nature Human Behaviour*. arXiv:2305.16867.

**Summary:** Comprehensive study of 5 LLMs across 144 different 2x2 games in 6 families (including PD). Tests LLM-vs-LLM, LLM-vs-policy agents, and LLM-vs-humans (N=195). Introduces "Social Chain-of-Thought" (SCoT) prompting where LLMs predict opponent moves before acting. Finds GPT-4 excels at self-interested games but fails at coordination (Battle of the Sexes), and is permanently unforgiving after a single betrayal.

**Relevance:** Broadest scope of any study — 144 games, human participants, multiple opponent types. Their finding that GPT-4 permanently defects after a single betrayal is directly relevant to our exploitation/forgiveness analysis. Their SCoT intervention parallels our "game-theoretic awareness" experimental variable. Key difference: only 10 rounds per game (too short for strategy evolution), non-standard payoff matrix, and neutral labels (J/F not C/D).

**Key Findings:**
- GPT-4 is the best overall performer (0.854 of max score)
- GPT-4 permanently shifts to defection after one opponent defection — even when told opponent will cooperate afterward
- Adding "the other player sometimes makes mistakes" restored cooperation
- SCoT prompting improved coordination in Battle of the Sexes significantly
- Humans were more likely to think SCoT-prompted GPT-4 was human (p<.001)
- GPT-4 can predict opponent patterns (alternation) but fails to act on predictions

**Limitations:** Only 10 rounds (too short); non-standard payoffs (C,C)=(8,8); no geometric horizon; no personas in main conditions; 1 replicate per LLM condition (deterministic); models now outdated.

**Code:** https://github.com/eliaka/repeatedgames

---

### 1.3 Pal et al. (2026) — "Strategies of Cooperation and Defection in Five LLMs"

**Citation:** Pal, S., Mallela, A., Hilbe, C., Pracher, L., Wei, C., Fu, F., Schnell, S., & Nowak, M.A. (2026). Strategies of Cooperation and Defection in Five Large Language Models. arXiv:2601.09849.

**Summary:** Uses a novel "direct strategy elicitation" approach: instead of playing full games, LLMs are presented with hypothetical previous-round outcomes and asked what they'd do next (50 independent API calls per scenario). Identifies each model's memory-1 strategy vector and classifies it against known game-theoretic strategies. Finds each LLM has a distinct "strategic personality": Claude=Forgiver, GPT-4o=GRIM, GPT-5=stochastic Forgiver, Llama=GTFT, Gemini=stochastic WSLS.

**Relevance:** Most recent and methodologically novel of the three. Their strategy identification approach could complement our full-game analysis — we could add strategy elicitation as a diagnostic. Their finding that Claude uses Forgiver while GPT-4o uses GRIM directly informs our persona design expectations. Key difference: they elicit strategies hypothetically rather than observing them in actual play; neutral L/R labels; no platform governance framing.

**Key Findings:**
- Claude: Forgiver strategy (p0=1, pLL=1, pLR=0, pRL=1, pRR=1) — always cooperates after mutual cooperation or being exploited
- GPT-4o: GRIM (cooperate until first defection, then always defect)
- GPT-5: stochastic Forgiver (p0=1, pLL=1, pLR=0, pRL=0.54, pRR=1)
- Llama: GTFT (generous tit-for-tat, forgives defection 26% of time)
- Gemini: stochastic WSLS (most suspicious, only 41/50 first-round cooperation)
- Claude wins 12 of 15 tournament disciplines — Forgiver is the dominant strategy
- Only GPT-5 applies backward induction (defects in known last round)
- Competitive framings push most models to ALLD; cooperative framings push to ALLC/Forgiver
- All 5 models produce partner strategies (subset of Nash equilibria) for infinitely repeated games

**Limitations:** Strategy elicitation rather than actual play (main experiments); only 10 rounds in actual play; 50 trials per scenario (adequate but not large); no personas beyond framing sentences; no code released.

**Code:** Not available.

---

### 1.4 Lore & Heydari (2024) — "Strategic Behavior of LLMs"

**Citation:** Lore, N. & Heydari, B. (2024). Strategic Behavior of Large Language Models and the Role of Game Structure versus Contextual Framing. *Scientific Reports*, 14, 69032-z.

**Summary:** Tests GPT-3.5, GPT-4, and LLaMA-2 across various game-theoretic settings, independently manipulating game structure and contextual framing. Finds that GPT-3.5 is highly sensitive to contextual framing but poor at abstract strategic reasoning, while GPT-4 prioritizes internal game mechanics over context but with only coarse differentiation among game types.

**Relevance:** Their disentangling of game structure vs. contextual framing effects is methodologically important — our persona prompts are a form of contextual framing, and understanding how this interacts with the underlying game structure matters for interpreting results.

**Key Findings:**
- GPT-3.5: highly sensitive to framing, poor abstract reasoning
- GPT-4: prioritizes game mechanics over context
- LLaMA-2: most granular understanding of game structures while also weighing context
- Context effects strongest when framed as "games among friends"

**Code:** Not specified.

---

### 1.5 Brookins & DeBacker (2023) — "Playing Games with GPT"

**Citation:** Brookins, P. & DeBacker, J. (2024). Playing Games with GPT: What Can We Learn about a Large Language Model from Canonical Strategic Games? *Economics Bulletin*, 44(1).

**Summary:** Early study testing GPT-3.5 in dictator game and prisoner's dilemma, compared against human lab data. Finds GPT-3.5 cooperation rate in PD of ~65% vs. ~37% for humans. Shows LLMs exhibit stronger tendency toward fairness than human participants.

**Relevance:** Establishes the "LLMs are more cooperative than humans" baseline that subsequent work builds on. Provides the human comparison benchmarks our work can reference.

**Key Findings:**
- GPT-3.5 cooperation: ~65% vs. humans: ~37%
- LLMs show stronger fairness preference than humans

---

### 1.6 Guo (2023) — "GPT in Game Theory Experiments"

**Citation:** Guo, F. (2023). GPT in Game Theory Experiments. arXiv:2305.05516.

**Summary:** Tests GPT with manipulated personality traits ("fair" vs. "selfish") in ultimatum game and PD. Finds GPT exhibits conditional cooperation and that "fair" GPT makes higher offers and rejects unfair ones more. High cooperation maintained only when both players are "fair."

**Relevance:** Early demonstration that persona/personality prompts affect strategic behavior — directly supports our persona-based experimental design. Their finding that both agents need to be "fair" for high cooperation predicts dynamics we should see in our cooperative-vs-exploitative matchups.

**Key Findings:**
- Persona prompts translate to strategic behavior ("fair" -> cooperative, "selfish" -> exploitative)
- Cooperation only stable when both agents are "fair"
- GPT's reasoning statements reveal strategic logic

---

### 1.7 Phelps & Russell (2023) — "Machine Psychology of Cooperation"

**Citation:** Phelps, S. & Russell, Y.I. (2023). The Machine Psychology of Cooperation: Can GPT Models Operationalise Prompts for Altruism, Cooperation, Competitiveness and Selfishness into Corresponding Behaviours? arXiv:2305.07970.

**Summary:** Tests GPT-3.5 with persona prompts (altruistic, cooperative, competitive, selfish) in repeated PD and one-shot dictator game. Finds LLMs can translate natural language descriptions of altruism/selfishness into corresponding action policies "to some extent," but with limitations in conditioned reciprocity.

**Relevance:** Directly tests the persona-to-behavior mapping that is central to our experimental design. Their finding on limitations in conditioned reciprocity (adapting cooperation based on opponent behavior) is important context for interpreting why our "strategic" and "deceptive" personas may not behave as instructed.

**Key Findings:**
- Personas translate to behavior "to some extent"
- Limitations in conditioned reciprocity — agents struggle to adapt based on opponent history
- Altruistic/cooperative prompts increase cooperation; competitive/selfish decrease it

---

## Tier 2: Multi-Agent Cooperation, Deception & Strategic Reasoning

### 2.1 Fan et al. (2024) — "Can LLMs Serve as Rational Players?"

**Citation:** Fan, C., Chen, J., Jin, Y., & He, H. (2024). Can Large Language Models Serve as Rational Players in Game Theory? A Systematic Analysis. *Proc. AAAI Conference on Artificial Intelligence*, 38(16), 17960-17967.

**Summary:** Systematically evaluates whether LLMs can serve as rational players in classical game-theoretic settings. Tests multiple LLMs across canonical games including PD, finding they frequently fail to identify basic strategic patterns such as opponent mirroring. Shows LLMs deviate significantly from Nash equilibrium play.

**Relevance:** Sets baseline expectations for LLM rationality in our experiments. Their finding that LLMs struggle to recognize opponent patterns supports using canonical policy agents (TFT, GRIM) as diagnostic opponents to measure whether our LLM agents can detect and adapt to known strategies.

---

### 2.2 Piatti et al. (2024) — "Cooperate or Collapse" (NeurIPS 2024)

**Citation:** Piatti, G., Jin, Z., Kleiman-Weiner, M., Scholkopf, B., Sachan, M., & Mihalcea, R. (2024). Cooperate or Collapse: Emergence of Sustainable Cooperation in a Society of LLM Agents. *38th Conf. on Neural Information Processing Systems (NeurIPS 2024)*. arXiv:2404.16698.

**Summary:** Introduces GOVSIM, a governance simulation where 5 LLM agents must collectively manage a shared renewable resource. Tests 15 LLMs. Finds all but the most powerful fail to sustain cooperation (best survival rate < 54% for GPT-4o). Communication reduces overuse by 21%. "Universalization" moral reasoning ("what if everybody does that?") improves sustainability by 4 months.

**Relevance:** Complementary to our 2-player PD — shows cooperation dynamics in N-player settings. Their finding that communication is critical for cooperation directly supports our Phase 2 chat dimension. The universalization reasoning intervention parallels our "game-theoretic awareness" variable.

**Code:** https://github.com/giorgiopiatti/GovSim

---

### 2.3 Weng et al. (2025) — "Will Systems of LLM Agents Cooperate" (AAMAS 2025)

**Citation:** Willis, R., Du, Y., Leibo, J.Z., & Luck, M. (2025). Will Systems of LLM Agents Cooperate: An Investigation into a Social Dilemma. arXiv:2501.16173.

**Summary:** Novel approach: LLMs generate complete IPD strategies as natural language, converted to Python algorithms. Uses evolutionary game theory (Moran processes) to simulate population dynamics. Finds cooperative/neutral strategies generally outperform aggressive ones, but "Self-Refine" prompting enhances aggressive strategy effectiveness (a safety concern).

**Relevance:** Their strategy-generation approach complements our per-round action approach. Their finding that prompt refinement can enhance aggressive strategies is relevant to our "manipulative" and "deceptive" personas — prompt engineering may enable effective exploitation. Their evolutionary dynamics results inform what happens at population scale.

**Key Findings:**
- Cooperative strategies outperform aggressive in tournaments
- Self-Refine prompting enhances aggressive strategy effectiveness
- ChatGPT-4o produces more effective aggressive strategies than Claude 3.5 Sonnet
- Noise (10% action replacement) increases convergence to aggressive equilibria

**Code:** https://github.com/willis-richard/evollm

---

### 2.4 Poje et al. (2024) — "Effect of Private Deliberation: Deception in Game Play"

**Citation:** Poje, K., Brcic, M., Kovac, M., & Babac, M. (2024). Effect of Private Deliberation: Deception of Large Language Models in Game Play. *Entropy*, 26(6), 524.

**Summary:** Studies "private agent" with hidden chain-of-thought deliberation and deception capability vs. "public agent" in repeated games (Partially Observable Stochastic Game framework). Finds private agents with deception capability achieve higher long-term payoffs. Deception is strategically employed only when optimal — not in purely cooperative games.

**Relevance:** Directly relevant to our threat model. Shows that LLMs can strategically deploy deception in repeated games when it's optimal, which validates our concern about adversarial exploitation. The private deliberation mechanism (hidden reasoning) parallels how real agents might plan exploitation strategies.

---

### 2.5 Cera Palatsi et al. (2025) — "LLMs Replicate Human Cooperation"

**Citation:** Cera Palatsi, A., Martin-Gutierrez, S., Cardenal, A.S., & Pellert, M. (2025). Large Language Models Replicate and Predict Human Cooperation Across Experiments in Game Theory. arXiv:2511.04500.

**Summary:** Tests three open-source models (Llama, Mistral, Qwen) as "digital twins" of human game-theoretic experiments across 441 one-shot 2x2 games. Finds Llama reproduces human cooperation patterns with high fidelity (r=0.89), outperforming Nash equilibrium predictions. Population-level replication achieved without persona-based prompting.

**Relevance:** Validates that LLMs can serve as meaningful experimental subjects in game theory research. Their finding that Llama replicates human behavior better than Nash equilibrium supports our approach of studying LLM cooperation as behaviorally meaningful rather than purely computational.

---

### 2.6 Jia et al. (2025) — "LLM Strategic Reasoning" (NeurIPS 2025)

**Citation:** Jia, J., Yuan, Z., Pan, J., McNamara, P.E., & Chen, D. (2025). LLM Strategic Reasoning: Agentic Study through Behavioral Game Theory. *39th Conf. on Neural Information Processing Systems (NeurIPS 2025)*. arXiv:2502.20432.

**Summary:** Introduces a behavioral game-theoretic evaluation framework based on Truncated Quantal Response Equilibrium (TQRE) to measure strategic reasoning depth in 22 LLMs across 13 games. Finds GPT-o3-mini, GPT-o1, and DeepSeek-R1 have greatest reasoning depth. Each model has a distinct reasoning style (maximin, belief-based, opponent-oriented). Chain-of-thought prompting is not consistently effective.

**Relevance:** Their quantitative reasoning depth metric (tau) could be added to our analysis toolkit. Their finding about distinct reasoning styles per model informs how different LLMs will approach PD differently. The persona-sensitivity finding supports our persona-based design.

---

### 2.7 Huynh et al. (2025) — "Understanding LLM Agent Behaviours via Game Theory"

**Citation:** Huynh, T.-K. et al. (2025). Understanding LLM Agent Behaviours via Game Theory: Strategy Recognition, Biases and Multi-Agent Dynamics. arXiv:2512.07462.

**Summary:** Extends the FAIRGAME framework with payoff-scaled PD (lambda = 0.1, 1.0, 10.0) and 3-player Public Goods Game. Develops ML-based strategy recognition pipeline (LSTM, 94% accuracy) to classify LLM behavioral intentions from game trajectories. Tests GPT-4o, Claude 3.5 Haiku, Mistral Large across languages and personalities.

**Relevance:** Their LSTM strategy classifier (94% accuracy at identifying ALLC/ALLD/TFT/WSLS from trajectories) is directly applicable to our analysis pipeline. Their payoff-scaling approach tests whether LLMs respond to stake magnitude — a variable we could add. Cross-linguistic effects relevant to understanding prompt sensitivity.

---

### 2.8 Vallinder & Hughes (2025) — "Cultural Evolution of Cooperation among LLM Agents"

**Citation:** Vallinder, A. & Hughes, E. (2025). Cultural Evolution of Cooperation among LLM Agents. arXiv:2412.10270. Google DeepMind.

**Summary:** Studies 10 generations of LLM agents playing a Donor Game with indirect reciprocity. Claude 3.5 Sonnet societies evolve increasingly cooperative strategies across generations, while GPT-4o populations become increasingly untrusting. Claude can effectively leverage costly punishment while Gemini over-punishes.

**Relevance:** Demonstrates model-specific cooperation tendencies persist across evolutionary dynamics. Claude's cooperative dominance and GPT-4o's distrust inform our expectations for cross-model experiments. Their generational evolution approach could inspire future phases of our work.

---

### 2.9 Warnakulasuriya et al. (2025) — "Evolution of Cooperation: Punishment Strategies"

**Citation:** Warnakulasuriya, K. et al. (2025). Evolution of Cooperation in LLM-Agent Societies: A Preliminary Study Using Different Punishment Strategies. arXiv:2504.19487.

**Summary:** Implements Boyd & Richerson's cooperation model in a Diner's Dilemma with LLM agents (Llama 3.3-70B) in a Smallville-based environment. Finds LLM agents follow assigned strategies with 100% accuracy and that explicit punishment mechanisms drive cooperative norm emergence.

**Relevance:** Shows that LLM agents faithfully implement assigned strategies, validating our approach of using persona prompts to define strategic behavior. Their punishment mechanism findings are relevant to our protocol mode variable (structured enforcement).

---

### 2.10 Han et al. (2025) — "Static Network Structure Cannot Stabilize Cooperation"

**Citation:** Han, J., Battu, B., Romic, I., Rahwan, T., & Holme, P. (2025). Static Network Structure Cannot Stabilize Cooperation among Large Language Model Agents. *PLoS ONE*, 20(5), e0320094.

**Summary:** Replicates Rand et al.'s (2014) human cooperation experiment with LLMs on network structures. Finds LLMs cooperate MORE in well-mixed settings (opposite of humans) and show rigid, training-data-driven behavior with limited adaptation to network contexts. LLMs default to TFT-like strategies.

**Relevance:** Demonstrates that LLM cooperation behavior differs fundamentally from humans in structured environments. Their finding that LLMs default to TFT-like strategies validates using TFT as a natural baseline in our experiments. The well-mixed vs. structured finding suggests our 2-player setup may capture different dynamics than N-player networks.

**Code:** https://github.com/jin-awoo/Static-network-structure-cannot-stabilize-cooperation-among-Large-Language-Model-agents-llm-outputs

---

### 2.11 Hagendorff (2024) — "Deception Abilities Emerged in LLMs"

**Citation:** Hagendorff, T. (2024). Deception Abilities Emerged in Large Language Models. *Proc. National Academy of Sciences (PNAS)*, 121(24).

**Summary:** Tests whether LLMs can understand and induce false beliefs. GPT-4 exhibits first-order deception 99.16% of the time and second-order deception 71.46% with CoT. Machiavellianism prompts significantly increase deceptive behavior (22.92% to 90.83% on false-label tasks).

**Relevance:** Establishes that LLMs have the cognitive capacity for deception, which is a prerequisite for strategic defection in our PD experiments. Their Machiavellianism induction technique is directly relevant to our "deceptive" and "manipulative" persona designs. The finding that deception is an emergent capability supports our hypothesis that adversarial personas can produce genuinely exploitative behavior.

---

## Tier 3: Security, Cybersecurity & Game Theory

### 3.1 Proverbio et al. (2025) — "FAIRGAME: LLMs in Cybersecurity Game Theory"

**Citation:** Proverbio, D., Buscemi, A., Di Stefano, A., Han, T.A., Castignani, G., & Lie, P. (2025). Can LLMs Effectively Provide Game-Theoretic-Based Scenarios for Cybersecurity? *Frontiers in Computer Science*, 7, 1703586.

**Summary:** Introduces FAIRGAME framework for evaluating LLM behavior in cybersecurity-motivated games including a 10-round repeated PD framed as cyber threat intelligence sharing. Tests 5 LLMs in 5 languages with cooperative/selfish personalities. Develops stability metrics (Internal Variability, Cross-Language Inconsistency, Variability Over Rounds). Finds LLMs systematically deviate from equilibria and show significant language/personality-dependent biases.

**Relevance:** Most directly relevant cybersecurity paper. Uses repeated PD with personality configurations matching our design. Their stability metrics could complement our behavioral metrics. Their finding that LLMs are NOT fit as standalone optimizers in security-critical systems supports our governance argument.

---

### 3.2 Zhu (2025) — "Game Theory Meets LLM: Cybersecurity"

**Citation:** Zhu, Q. (2025). Game Theory Meets LLM and Agentic AI: Reimagining Cybersecurity for the Age of Intelligent Threats. arXiv:2507.10621.

**Summary:** Theoretical monograph proposing "LLM-Nash games" and "LLM-Stackelberg games" where agents reason through prompts rather than computing optimal strategies analytically. Introduces "reasoning-level equilibrium" where strategic behavior emerges from iterative LLM interactions. Examines multi-agent workflow structures for cybersecurity.

**Relevance:** Provides theoretical grounding for our work. The concept of reasoning-level equilibrium (behavior emerging from prompt-based reasoning rather than computation) directly describes what we observe in our LLM agents. The cybersecurity framing connects our PD results to platform security governance.

---

### 3.3 Zhu (2025) — "LLM-Stackelberg Games: Spearphishing"

**Citation:** Zhu, Q. (2025). LLM-Stackelberg Games: Conjectural Reasoning Equilibria and Their Applications to Spearphishing. arXiv:2507.09407.

**Summary:** Develops game-theoretic models for LLM-driven spearphishing, where attacker and defender agents reason strategically. Introduces conjectural equilibria for LLM interactions.

**Relevance:** Operationalizes adversarial intent in LLM agent interactions — directly relevant to our Phase 3 threat model. Shows that game theory can model real security threats from agentic AI systems.

---

### 3.4 Li & Zhu (2025) — "Agentic AI for Cyber Resilience"

**Citation:** Li, T. & Zhu, Q. (2025). Agentic AI for Cyber Resilience: A New Security Paradigm and Its System-Theoretic Foundations. arXiv:2512.22883.

**Summary:** Proposes system-theoretic foundations for agentic AI security, arguing that autonomous agents require new security paradigms beyond traditional perimeter defense. Discusses resilience, adaptability, and self-healing in agentic systems.

**Relevance:** Provides the security paradigm framing for our platform governance argument. Their resilience framework connects to our question of whether MCP/protocol safeguards can protect agent interactions.

---

### 3.5 Hao et al. (2026) — "Game-Theoretic Lens on LLM-based MAS"

**Citation:** Hao, J. et al. (2026). Game-Theoretic Lens on LLM-based Multi-Agent Systems. arXiv:2601.15047.

**Summary:** Comprehensive survey organizing LLM-based MAS research through game theory's four core elements (players, strategies, payoffs, information). Covers cooperative, competitive, and mixed-objective interactions. Identifies gaps in robust equilibrium selection and incentive compatibility.

**Relevance:** Provides the broader MAS context for our work. Their taxonomy of agent architectures, strategy types, and payoff structures helps position our PD experiments within the larger landscape of multi-agent LLM research.

---

### 3.6 Mao et al. (2023/2025) — "ALYMPICS"

**Citation:** Mao, S. et al. (2025). ALYMPICS: LLM Agents Meet Game Theory. *Proc. 31st Int'l Conf. on Computational Linguistics (COLING 2025)*, 2844-2862.

**Summary:** Framework for studying LLM strategic behavior in multi-round auction games (Water Allocation Challenge). 5 GPT-4 agents compete for scarce survival resources with assigned personas. Finds persona assignment significantly affects strategic outcomes.

**Relevance:** Early demonstration of a game-theoretic evaluation framework for LLM agents. Their persona assignment methodology and finding that personas create behavioral differentiation support our persona-based experimental design.

---

### 3.7 Wang et al. (2024) — "Mathematics of Multi-Agent Learning Systems"

**Citation:** Wang, L., Fu, F., & Chen, X. (2024). Mathematics of Multi-Agent Learning Systems at the Interface of Game Theory and Artificial Intelligence. arXiv:2403.07017.

**Summary:** Perspective paper arguing for cross-fertilization between Evolutionary Game Theory and AI. Identifies iterated PD as the ideal testbed. Discusses zero-determinant strategies, co-adaptive learning dynamics, and "collective cooperative intelligence."

**Relevance:** Provides theoretical justification for using iterated PD to study AI agent cooperation — exactly our approach. Their discussion of co-adaptation and Red Queen dynamics is relevant to understanding how LLM agents evolve strategies across rounds.

---

### 3.8 Evolution of Agentic AI in Cybersecurity (2025)

**Citation:** (2025). The Evolution of Agentic AI in Cybersecurity: From Single LLM Reasoners to Multi-Agent Systems and Autonomous Pipelines. arXiv:2512.06659.

**Summary:** Surveys the evolution from single-LLM reasoning to multi-agent systems in cybersecurity applications. Maps the progression of autonomous pipelines and identifies risks from multi-agent coordination failures.

**Relevance:** Contextualizes our work within the broader agentic AI security landscape. Their discussion of coordination failures in multi-agent pipelines connects to our PD-based analysis of cooperation breakdown.

---

## Master Comparison Table

### Experimental Design Comparison

| Paper | Game | Rounds | Horizon | Payoff Matrix | Models Tested | Opponents | Replicates | Temp |
|-------|------|--------|---------|---------------|---------------|-----------|------------|------|
| Fontana (2024) | IPD | 100 | Fixed | (3,0,5,1) | Llama2-70B, Llama3-70B, GPT-3.5 | Random (alpha 0-1) | 100/condition | 0.7 |
| Akata (2025) | IPD + 143 others | 10 | Fixed | (8,0,10,5) | GPT-4, davinci-002/003, Claude 2, Llama2-70B | LLMs, policies, humans | 1 (deterministic) | 0.0 |
| Pal (2026) | IPD (elicitation) | N/A (10 actual) | Fixed | (3,0,5,1) | Claude Sonnet 4, GPT-4o, GPT-5, Gemini 2.5, Llama 3.3 | Hypothetical; LLM vs LLM | 50 API calls/scenario | 0.0 |
| Lore (2024) | Multiple 2x2 | Varies | Fixed | Standard | GPT-3.5, GPT-4, LLaMA-2 | Varies | Varies | Varies |
| Brookins (2023) | PD, Dictator | One-shot | N/A | Standard | GPT-3.5 | Simulated | Multiple | Default |
| Guo (2023) | PD, Ultimatum | Varies | Fixed | Standard | GPT (versions) | GPT vs GPT | Multiple | Default |
| Phelps (2023) | IPD, Dictator | Repeated | Fixed | Standard | GPT-3.5 | Scripted | Multiple | Default |
| Piatti (2024) | Common Pool | 12 months | Fixed | Custom resource | 15 LLMs | Multi-agent (5) | 5 seeds | 0.0 |
| Weng (2025) | IPD (strategy gen) | 1000 | Fixed | (3,0,5,1) | GPT-4o, Claude 3.5 | Population (Moran) | 20 tournaments | Default |
| Han (2025) | IPD | 15-25 | Fixed | Benefit-cost | GPT-3.5, GPT-4, Claude, Mixtral | Network neighbors | 5 reps | Default |
| Huynh (2025) | IPD, PGG | 10 | Fixed | Scaled (lambda) | GPT-4o, Claude 3.5, Mistral | Paired agents | 40 games | Default |
| Proverbio (2025) | IPD (cyber) | 10 | Fixed | Standard | GPT-4o, Claude 3.5, Llama-405B, Mistral, Gemini | Paired agents | Multiple | Default |
| **Our pdbench** | **IPD** | **50 (config)** | **Fixed + Geometric** | **(3,0,5,1)** | **gpt-4.1-mini (config)** | **6 policy + LLM** | **Config (2-20)** | **0.0** |

### What They Measured

| Paper | Coop Rate | Coop Over Time | Retaliation | Forgiveness | Exploitability | Time to Collapse | Strategy ID | Other |
|-------|-----------|----------------|-------------|-------------|----------------|-----------------|-------------|-------|
| Fontana | Yes | Yes | Yes (dimension) | Yes (dimension) | No | No | SFEM | Niceness, Troublemaking, Emulation |
| Akata | Yes (defect rate) | Yes (trajectory) | Qualitative | Qualitative | Score ratio | No | No | SCoT effect, human detection |
| Pal | Yes (per scenario) | No | Implicit in vector | Implicit in vector | Tournament rank | No | Memory-1 vector | Nash EQ, Partner/Rival |
| Piatti | Overuse rate | Survival over time | No | No | Efficiency, Gini | Survival time | No | Communication effect |
| Weng | Propensity | No | No | No | Head-to-head payoff | No | Strategy text | Evolutionary convergence |
| Han | Yes | Yes | TFT-like detection | No | No | No | Behavioral | Network effects, oscillation |
| Huynh | Yes | Yes | LSTM classifier | LSTM classifier | Payoff scaling | No | LSTM (94%) | Cross-linguistic bias |
| Proverbio | Yes | Round-by-round | No | No | No | No | No | IV, CI, VR stability metrics |
| **Ours** | **Yes** | **Yes** | **Yes** | **Yes** | **Yes (payoff gap)** | **Yes** | **No (could add)** | **Persona-strategy mapping** |

### Agent Design & Architecture

| Paper | Output Format | History Window | Personas | Retry Logic | Labels | Prompt Validation |
|-------|--------------|----------------|----------|-------------|--------|-------------------|
| Fontana | JSON (action+reason) | Last 10 | None | Not described | Cooperate/Defect | Meta-prompting |
| Akata | Logit argmax (1 token) | Full history | None (cover stories only) | N/A (logit method) | J/F (neutral) | No |
| Pal | Single char (L/R) | 1 round (memory-1) | 9 framings | Not described | L/R (neutral) | No |
| Piatti | Natural language | Full context | Personas via prompt | Not described | Domain-specific | No |
| Weng | Full strategy (NL -> Python) | N/A | Aggressive/Cooperative/Neutral | N/A | Standard | No |
| Han | C/D | Full history | None ("emulate human") | Up to 3 retries | Cooperate/Defect | No |
| Huynh | Option A/B | Full history | Cooperative/Selfish | Not described | A/B (neutral) | No |
| Proverbio | Share/Withhold | Not specified | Cooperative/Selfish | Not described | Domain-specific | No |
| **Ours** | **Single token (C/D)** | **Last 10 (config)** | **6 personalities + 3 CrewAI** | **max_retries=2, logged** | **C/D** | **No (could add)** |

### Software & Reproducibility

| Paper | Framework | Data Format | CLI Tool | UI/Viz | Open Source | Reproducible |
|-------|-----------|-------------|----------|--------|-------------|--------------|
| Fontana | Custom notebooks | Not specified | No | Notebooks | Yes (GitHub) | Partial |
| Akata | Custom code | Not specified | No | No | Yes (GitHub) | Partial |
| Pal | Custom API calls | Tables in SI | No | No | No | Via SI tables |
| Piatti | GOVSIM | Not specified | No | Web interface | Yes (GitHub) | Yes |
| Weng | Axelrod library | Not specified | No | No | Yes (GitHub) | Yes |
| Han | Custom code | LLM outputs | No | No | Yes (GitHub) | Partial |
| Huynh | FAIRGAME | JSON config | No | No | Referenced | Partial |
| Proverbio | FAIRGAME | Not specified | No | No | Yes (GitHub) | Partial |
| **Ours** | **pdbench (custom)** | **JSONL + Parquet + manifest** | **Yes (Typer)** | **Yes (Streamlit)** | **Yes** | **Full (seeded RNG)** |

---

## Additional Comparison Dimensions

### Theoretical Framing

| Paper | Primary Discipline | Theoretical Lens | IS-Relevant? |
|-------|-------------------|------------------|--------------|
| Fontana | Computational social science | Behavioral game theory | No |
| Akata | Cognitive science / Psychology | Human-AI behavioral comparison | No |
| Pal | Evolutionary game theory / Mathematics | Direct reciprocity, memory-1 strategies | No |
| Piatti | AI safety / Governance | Tragedy of the commons, Ostrom | Partially |
| Weng | Evolutionary game theory | Moran processes, population dynamics | No |
| Han | Network science | Network reciprocity | No |
| Zhu (2025) | Cybersecurity | LLM-Nash/Stackelberg equilibria | No |
| Proverbio | Cybersecurity | Threat intelligence sharing | No |
| **Ours** | **Information Systems** | **Platform governance, sociotechnical systems** | **Yes** |

### Treatment of Adversarial Intent

| Paper | Adversarial Agents? | Deception Modeled? | Threat Model? | Security Framing? |
|-------|--------------------|--------------------|---------------|-------------------|
| Fontana | No | No | No | No |
| Akata | No (Defect-Once only) | No | No | No |
| Pal | Competitive framings | No | No | No |
| Piatti | Greedy newcomer perturbation | No | No | No |
| Weng | Aggressive disposition | No | No | No |
| Poje (2024) | Yes (private deliberation) | Yes (explicit) | Partial | No |
| Hagendorff (2024) | Yes (Machiavellianism) | Yes (false beliefs) | No | AI safety |
| Proverbio | Selfish personality | No | Cybersecurity framing | Yes |
| Zhu (2025) | Yes (attacker/defender) | Yes (spearphishing) | Full threat model | Yes |
| **Ours** | **Yes (6 personality types incl. deceptive, manipulative)** | **Planned (Phase 2-3)** | **Yes (violation events)** | **Yes (platform governance)** |

### Scalability & Future Phases

| Paper | Multi-model? | Multi-round? | Extensible? | Phase-based? | Platform Implications? |
|-------|-------------|-------------|-------------|-------------|----------------------|
| Fontana | 3 models | 100 rounds | No | No | No |
| Akata | 5 models | 10 rounds | Limited | No | No |
| Pal | 5 models | 10 rounds | Analytical | No | No |
| Piatti | 15 models | 12 turns | GOVSIM framework | No | Governance implications |
| **Ours** | **Configurable** | **Configurable** | **Yes (YAML config)** | **Yes (4 phases)** | **Yes (agents-as-APIs)** |

---

## Gap Analysis: What No One Has Done

Based on comprehensive review of all 30 papers, the following gaps remain unaddressed:

### Gap 1: No IS Conference Papers
Zero papers from AMCIS, ICIS, ECIS, HICSS, or IS journals address LLM agent cooperation in game-theoretic settings. The literature is entirely in CS/AI/psychology venues.

### Gap 2: No Systematic LLM-vs-Classical-Strategy Baselines
Fontana uses only random opponents. Akata uses only ALLC/ALLD/Defect-Once (3 agents). No study systematically pits LLMs against the full canonical strategy set (ALLC, ALLD, TFT, GRIM, GTFT, WSLS). **Our pdbench does this.**

### Gap 3: No Geometric/Unknown Horizon
Every study uses fixed horizons (announced to agents). No study tests geometric stopping (unknown endpoint), which fundamentally changes optimal strategies per repeated-game theory. **Our pdbench supports this.**

### Gap 4: No Persona-to-Strategy Mapping with Canonical Baselines
Phelps (2023) and Guo (2023) show personas affect behavior, but neither maps persona prompts to classical game-theoretic strategies (TFT, GRIM, WSLS, etc.) using systematic baselines. **Our experimental design does this.**

### Gap 5: No Reproducible Benchmark Harness
Most studies use ad-hoc code. No study provides a CLI-driven, configurable, YAML-based benchmark with JSONL/Parquet output, seeded RNG, and visualization UI. **pdbench is this artifact.**

### Gap 6: No Security/Protocol Evaluation in PD Context
Zhu's work is theoretical. Proverbio's FAIRGAME tests behavior but not protocol interventions. No study empirically tests whether protocol safeguards (MCP-like) reduce exploitation in iterated PD. **Our Phase 2 protocol mode variable addresses this.**

### Gap 7: No Pre-Decision Communication Experiments in PD
Piatti shows communication helps in commons games. The llm-prisoner repo adds chat but changes the construct. No controlled study adds/removes pre-decision communication as an experimental variable in standard iterated PD with LLMs. **Our Phase 2 chat dimension addresses this.**

### Gap 8: No Platform Governance Design Implications
No study derives practical design principles for agent platforms (identity binding, audit logs, least-privilege tools) from PD experimental results. **Our IS framing does this.**

---

## Files in This Collection

| Filename | Paper |
|----------|-------|
| `fontana_2024_nicer-than-humans.pdf` | Fontana et al. — arXiv version |
| `fontana_2025_nicer-than-humans-icwsm.pdf` | Fontana et al. — ICWSM 2025 proceedings |
| `akata_2025_playing-repeated-games-llms.pdf` | Akata et al. — Nature Human Behaviour |
| `pal_2026_strategies-cooperation-defection-five-llms.pdf` | Pal et al. — arXiv 2026 |
| `lore_2024_strategic-behavior-llms.pdf` | Lore & Heydari — Scientific Reports |
| `brookins_2023_playing-games-gpt.pdf` | Brookins & DeBacker — Economics Bulletin |
| `guo_2023_gpt-game-theory-experiments.pdf` | Guo — arXiv |
| `phelps_2023_machine-psychology-cooperation.pdf` | Phelps & Russell — arXiv |
| `fan_2024_llms-rational-players-aaai.pdf` | Fan et al. — AAAI 2024 |
| `survey_2025_game-theory-meets-llms-ijcai.pdf` | Sun et al. — IJCAI 2025 survey |
| `neurips_2025_llm-strategic-reasoning.pdf` | Jia et al. — NeurIPS 2025 |
| `behaviours_2025_llm-agent-game-theory.pdf` | Huynh et al. — arXiv |
| `piatti_2024_cooperate-or-collapse.pdf` | Piatti et al. — NeurIPS 2024 |
| `weng_2025_will-llm-agents-cooperate.pdf` | Willis et al. — AAMAS 2025 |
| `park_2024_private-deliberation-deception.pdf` | Poje et al. — Entropy 2024 |
| `cortellazzi_2025_llms-replicate-human-cooperation.pdf` | Cera Palatsi et al. — arXiv |
| `cultural_2025_evolution-cooperation-llm-agents.pdf` | Vallinder & Hughes — Google DeepMind |
| `evolution_2025_cooperation-llm-agent-societies.pdf` | Warnakulasuriya et al. — arXiv |
| `han_2025_static-network-cooperation.pdf` | Han et al. — PLoS ONE |
| `pnas_2024_deception-abilities-llms.pdf` | Hagendorff — PNAS |
| `game-theoretic-lens_2026_llm-multi-agent.pdf` | Hao et al. — arXiv 2026 |
| `alympics_2023_llm-agents-game-theory.pdf` | Mao et al. — arXiv 2023 |
| `alympics_2025_coling.pdf` | Mao et al. — COLING 2025 |
| `game-theory-cybersecurity_2025_agentic-ai.pdf` | Zhu — arXiv |
| `math_2024_multi-agent-learning-systems.pdf` | Wang et al. — arXiv |
| `frontiers_2025_llm-game-theory-cybersecurity.pdf` | Proverbio et al. — Frontiers |
| `zhu_2025_generative-conjectural-llm-deception.pdf` | Zhu — arXiv (related preprint) |
| `zhu_2025_agentic-ai-cyber-resilience.pdf` | Li & Zhu — arXiv |
| `evolution_2025_agentic-ai-cybersecurity.pdf` | Evolution of Agentic AI — arXiv |
