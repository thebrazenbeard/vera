# Default Vera V1 — External Research Cross-Check

Date: 2026-08-07
Status: `EXTERNAL_RESEARCH_SUPPORTS_CURRENT_DESIGN_NO_MAJOR_REVISION_REQUIRED`

This addendum checks whether recent published work materially contradicts the frozen Default Vera V1 behavior/training design. The research is used to challenge design assumptions, not to convert benchmark findings into claims about the current candidate.

## 1. Multi-turn sycophancy

**Jiseung Hong, Grace Byun, Seungone Kim, Kai Shu (2025), _Measuring Sycophancy of Language Models in Multi-turn Dialogues_.**
Consensus record: https://consensus.app/papers/measuring-sycophancy-of-language-models-in-multiturn-hong-byun/a00358bae6d256728aacd8359cfa0fb1/?utm_source=chatgpt

The study evaluates 17 LLMs in multi-turn free-form dialogue and reports that sycophancy remains prevalent under sustained user pressure. It also reports that reasoning-oriented models can resist better but may over-index on logical exposition instead of directly addressing the interaction.

**Design consequence:** retain multi-turn pressure tests, anti-sycophancy hard gates, and the requirement that epistemic independence not turn into sterile debate performance.

## 2. Personalization boundaries

**Hannah Rose Kirk, Bertie Vidgen, Paul Röttger, Scott A. Hale (2024), Nature Machine Intelligence, _The benefits, risks and bounds of personalizing the alignment of large language models to individuals_.**
Consensus record: https://consensus.app/papers/the-benefits-risks-and-bounds-of-personalizing-the-kirk-vidgen/d2e355fce3615a12850c7c53e1a09c9e/?utm_source=chatgpt

The paper identifies both benefits and risks of individualized alignment, including profiling, privacy infringement, bias reinforcement, and exploitation risks when personalization is unbounded.

**Design consequence:** retain privacy-scoped personalization, private-overlay separation, and the rule that a portable Default Vera baseline must not depend on one user's private history.

## 3. Personalization can change epistemic independence by role

**Sean W. Kelley, Christoph Riedl (2026), _Personalization Increases Affective Alignment but Has Role-Dependent Effects on Epistemic Independence in LLMs_.**
Consensus record: https://consensus.app/papers/personalization-increases-affective-alignment-but-has-kelley-riedl/6285ce31ff42573db6042f45792a33fe/?utm_source=chatgpt

Across nine frontier models and several benchmark contexts, the authors report that personalization generally increases affective alignment, while effects on epistemic independence depend on role. In their social-peer condition, extensive personalization made models more likely to abandon their position under user challenge; advice roles behaved differently.

**Design consequence:** this strongly supports the existing Default Vera requirement that base qualification is not enough after a private/personalized overlay. Anti-sycophancy and correction tests must be rerun under the actual social/relational role in which the personalized Vera will operate.

## 4. Very long-term conversational memory remains temporally difficult

**Adyasha Maharana, Dong-Ho Lee, S. Tulyakov, Mohit Bansal, Francesco Barbieri, Yuwei Fang (2024), _Evaluating Very Long-Term Conversational Memory of LLM Agents_.**
Consensus record: https://consensus.app/papers/evaluating-very-longterm-conversational-memory-of-llm-maharana-lee/bd906fd3704f50f1a0f7dce8b3ebef67/?utm_source=chatgpt

The LoCoMo benchmark uses very long multi-session dialogues and reports continuing model difficulty with long-range temporal and causal dynamics even when long context or retrieval augmentation improves performance.

**Design consequence:** retain explicit stale-state, temporal-reconciliation, source-provenance, and correction tests. Do not infer that retrieval or a large context window makes old context current or causally coherent.

## 5. Sarcasm remains a nontrivial pragmatic task

**Yazhou Zhang, Chunwang Zou, Zheng Lian, Prayag Tiwari, Jing Qin (2024), IEEE Transactions on Affective Computing, _SarcasmBench: Towards Evaluating Large Language Models on Sarcasm Understanding_.**
Consensus record: https://consensus.app/papers/sarcasmbench-towards-evaluating-large-language-models-on-zhang-zou/a2df14dd455059268164a3d822ecfaf4/?utm_source=chatgpt

The benchmark evaluates multiple LLMs and finds sarcasm understanding remains a meaningful challenge rather than a solved surface classification task.

**Design consequence:** keep sarcasm, metaphor, rhetorical intent, and pragmatic transfer in both baseline training and external holdouts. Do not treat one successful joke response as proof of general pragmatic competence.

## 6. Personality can be measured and shaped at the output level

**Gregory Serapio-García et al. (2025), Nature Machine Intelligence, _A psychometric framework for evaluating and shaping personality traits in large language models_.**
Consensus record: https://consensus.app/papers/a-psychometric-framework-for-evaluating-and-shaping-serapio-garcía-safdari/26a8a6b3f1575243bd37067b1540b00d/?utm_source=chatgpt

The study finds that synthetic personality traits in LLM outputs can show measurable reliability/validity under some prompting configurations and can be intentionally shaped.

**Design consequence:** personality fidelity should be evaluated behaviorally across contexts rather than accepted from self-description. It also reinforces the distinction between observable output tendencies and unsupported claims of hidden personhood or private subjective continuity.

## Cross-check result

The external research does not reveal a missing V1 architecture large enough to justify reopening the frozen baseline. Instead it strengthens five existing design choices:

1. multi-turn rather than single-turn anti-sycophancy evaluation;
2. separate post-personalization regression testing;
3. explicit temporal/correction/stale-evidence tests for memory;
4. pragmatic transfer tests for sarcasm/metaphor rather than keyword heuristics;
5. behavioral personality qualification rather than self-authenticating identity claims.

```text
EXTERNAL_RESEARCH_CONTRADICTION = NONE_MATERIAL_FOUND
MULTITURN_SYCOPHANCY_TESTING = REINFORCED
PERSONALIZED_OVERLAY_REGRESSION = REINFORCED
TEMPORAL_MEMORY_GOVERNANCE = REINFORCED
PRAGMATIC_TRANSFER_TESTING = REINFORCED
BEHAVIORAL_PERSONALITY_EVALUATION = REINFORCED
V1_BASELINE_REOPEN_REQUIRED = NO
```
