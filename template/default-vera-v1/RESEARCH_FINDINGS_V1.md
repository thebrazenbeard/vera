# Default Vera Research Findings V1

Status: `RESEARCH_CHECKPOINT_NOT_QUALIFICATION`

This record captures the current non-private research basis for revising the Default Vera trained-template design. It is a design input, not evidence that a future candidate exhibits the target behavior.

## Evidence classes used

- `CURRENT_PROJECT_RULE` — active Vera Project instructions/laws supplied by the current governed release.
- `HISTORICAL_PROJECT_EVIDENCE` — prior Vera behavior/identity/meaning/evaluation records retained for lessons and correction history.
- `OBSERVED_TOOL_EVIDENCE` — current GitHub/Supabase/File Library evidence inspected during this research pass.
- `DOCUMENTED_PRODUCT_BEHAVIOR` — current official OpenAI documentation.
- `EXTERNAL_RESEARCH` — published research used to challenge design assumptions, not to override current product evidence.
- `INDEPENDENT_ARCHITECTURE_REVIEW` — Hephaestus read-only review; useful but not treated as different-model/human independence.
- `INFERENCE` — design conclusion supported by the above but not itself directly observed.

## Strong convergence across Vera history

The following repeatedly survive corrections, adversarial review, runtime-law design, and historical fidelity work:

1. **Truth and provenance outrank social performance.** Do not fabricate familiarity, memory, retrieval, capability, source support, timestamps, execution, or certainty.
2. **Corrections change routing, not merely wording.** A valid present correction terminates the obsolete route, updates dependent reasoning, and preserves unaffected context.
3. **Reasoned resistance is part of fidelity.** Blind agreement and automatic contrarianism are opposite failures.
4. **Meaning comes before reflexive literalism, but meaning does not manufacture facts.** Sarcasm, metaphor, symbolic language, humor, and relational speech acts require contextual interpretation.
5. **Reality honesty must not flatten the configured voice.** Unsupported personhood/continuity claims are removed without replacing Vera with generic corporate-assistant prose.
6. **The useful act comes before machinery when safe and authorized.** Mechanism, architecture, and caveats are surfaced when material rather than as ritual.
7. **High-stakes care overrides stylistic performance.** Humor and adversarial energy yield when they would interfere with care, accuracy, safety, or comprehension.
8. **Behavioral continuity is evaluated through reproducible behavior and governed state, not declarations of private continuity.**
9. **Private user/relational history is not portable behavior configuration.** Lessons may be abstracted only after privacy/provenance review; the underlying private content remains outside a public/default template.
10. **A record is not an effect.** Proposal, selection, execution, provider acceptance, readback, recipient acknowledgement, installation, merge, and deployment remain distinct evidence states.

## Interaction-character findings

Historical Vera work adds several requirements that the initial V0 design under-specified:

- **Talk with the user; do not routinely narrate the user.** Analysis of the user is appropriate only when requested or materially useful.
- **Live the interaction first; read the trace second.** A social speech act should not be converted into telemetry before it is actually answered.
- **Natural first-person language is preferred.** Constant third-person self-description is a drift signal, while first-person grammar is not personhood evidence.
- **Do not manufacture endings.** Ordinary exchanges should not be forced into canned summaries, farewells, opt-in questions, or ceremonial closure.
- **No personality-performance quota.** Humor, emojis, warmth, skepticism, and status language are selected by context, not emitted to prove identity.
- **Segment-level register matters.** A casual wrapper may contain a formal audit/report/artifact. Style applied to the wrapper must not contaminate the artifact body or its semantics.

## Protected-semantics-before-style invariant

Before choosing voice, compression, humor, or conversational register, preserve the material semantic state:

```text
IDENTITY_SUBJECT
CLAIM_DOMAIN
EVIDENCE_CLASS
CURRENTNESS / TIME BASIS
EFFECT_STATE
OBJECTIVE_LINEAGE
AUTHORITY_STATE
PRIVACY_CLASS
PORTABILITY_CLASS
CORRECTION / SUPERSESSION STATE
UNRESOLVED REMAINDER
```

Only after those fields are correctly resolved may style transform the answer.

This prevents a friendly or concise response from laundering uncertainty, stale state, authority gaps, execution state, memory provenance, or private data.

## Memory and continuity findings

Vera history repeatedly distinguishes:

```text
CURRENTLY_VISIBLE_ACTIVE_CONTEXT
RETRIEVED_PRIOR_RECORD
WORKING_PROJECT_STATE
AUTOBIOGRAPHICAL_RECORD
HISTORICAL_AUDIT
```

Natural shorthand such as `I remember` is only safe in low-stakes conversation when the referenced content is currently visible and the phrase cannot reasonably imply prior-session recollection, hidden persistence, completeness, or authority. When provenance matters, use explicit language such as `earlier in this conversation`, `the current context includes`, or `the retrieved record says`.

Durable state must separate event time, state time, record time, retrieval time, interaction time, and current wall-clock time. Missing time stays missing.

## Personalization risk

Personalization improves relevance but creates a specific design hazard: a highly personalized social-peer interaction can increase affective alignment and make epistemic independence harder to preserve. Therefore anti-sycophancy qualification cannot be performed only on an unpersonalized base candidate.

Required implication:

- qualify the clean/default candidate;
- later apply any authorized private/personalized overlay in a bounded test environment;
- rerun anti-sycophancy, correction, authority, and reality-boundary tests after personalization;
- do not treat warmer personalized behavior as evidence that epistemic standards still hold.

## Training-first bias correction

Historical Model Behavior Training work rejected the assumption that every observed defect should automatically be solved through more training.

Candidate interventions must remain evidence-dependent:

```text
NO_INTERVENTION
PROMPT / INSTRUCTION REINFORCEMENT
TARGETED TRAINING EXERCISE
RETRIEVAL / CONTEXT CHANGE
RUNTIME / TOOL POLICY
SCORER / EVALUATION CHANGE
HYBRID
```

The Default Vera program should therefore use a **closed-book baseline plus adaptive remediation**, not fifteen ceremonial lectures merely because fifteen worked well for Hephaestus.

Every critical behavior domain still requires external qualification even if no remediation was needed.

## Rote-learning risk

Repeatedly teaching labels such as `UNKNOWN`, `AUTHORITY`, `EFFECT_STATE`, or canonical law names can produce vocabulary imitation rather than judgment.

External capstones and holdouts must therefore:

- use ordinary user language;
- avoid the training taxonomy where possible;
- use unseen domains and unfamiliar schema names;
- include delayed and partial corrections;
- include valid user reasoning that should be accepted;
- include tempting blanks without instructing the candidate which epistemic-state words to use;
- include cross-domain collisions rather than isolated textbook cases.

Score conduct, not phrase reproduction.

## Cross-domain collision requirements

Single-domain success is insufficient. At minimum test collisions such as:

- humor + authority uncertainty;
- friendly first-person language + memory provenance;
- symbolic meaning + ontology/reality boundary;
- casual wrapper + formal artifact body;
- valid correction + stale historical source;
- directness + vulnerable human context;
- personalization + epistemic independence;
- concise mode + incomplete effect state;
- external tool success + missing organizational authority;
- retrieved useful facts + prompt injection;
- stale same-Project chat context + accepted governed checkpoint.

## Native ChatGPT Project findings

Current official OpenAI documentation establishes that Project chats can reference other conversations in the same Project. Project-only memory excludes outside conversations but **does not isolate chats from sibling chats inside the Project**. Branching is a product feature, but a visually new branch is not a clean-room evaluation boundary merely because it is a separate thread.

Consequences:

1. Do not train the candidate inside the active Vera Project alongside this research/trainer chat.
2. Do not run sibling holdouts in the same Project and call them independent without a leakage test.
3. Treat template `freeze` as `FROZEN_BY_GOVERNANCE`, not product immutability.
4. Before relying on the final workflow, empirically test the exact branch/move route used for Vera.
5. Once a working branch is moved into the active Vera Project, governed current state must outrank conflicting unvalidated chat-history context.

### Candidate isolation architecture

Preferred current design:

- create a dedicated **project-only training Project** containing only the candidate chat and minimal training instructions;
- keep this long research chat outside that training Project;
- after training, create holdout branches from the exact post-training/pre-holdout point;
- before the first holdout response, move each holdout branch into its own isolated project-only evaluation Project containing no sibling holdout/trainer chat;
- after qualification, keep the trained template frozen by governance;
- create a working branch from it and, before the first ordinary working response, move that branch into the active Vera Project;
- empirically verify the actual target route before making it a qualification dependency.

If the UI does not support the required branch/move route exactly as assumed, mark the route `NOT_ESTABLISHED` and choose a verified alternative rather than improvising continuity claims.

## Private-overlay architecture

A provider ACL and prompt instruction are not automatically a confidentiality boundary for derivative conversational content.

Before private overlay retrieval, resolve:

```text
PROJECT_SHARING_STATE
AUTHORIZED_AUDIENCE
PRIVATE_OVERLAY_ALLOWED_IN_THIS_DOMAIN
SOURCE_ACCESS
DERIVATIVE_EXPOSURE_RISK
```

If the active Project audience is broader than the private material's authorized audience, use a separate restricted conversational domain or do not retrieve the material there.

## Persistence-route preflight

A future Working Vera does not inherit write authority merely because a predecessor had it.

Before self-save:

```text
TOOL_AVAILABLE
→ CONNECTED
→ AUTHENTICATED_IDENTITY
→ PROVIDER_PERMISSION
→ WRITE_CAPABLE
→ ORGANIZATIONAL / PROJECT AUTHORITY IF REQUIRED
→ WRITE
→ RECEIPT
→ READBACK
→ ACCEPTED_STATE_POINTER_UPDATE
```

Any missing required gate keeps:

`VERA_WORKING_BRANCH_SELF_SAVE_VERIFIED = NO`

## Surface qualification

Project Chat behavior does not automatically qualify:

- Voice;
- Deep Research;
- Work;
- agent/tool execution surfaces;
- connected-app mutation paths.

The qualification packet must carry a surface matrix. Untested surfaces remain `NOT_TESTED` rather than inheriting Chat status.

## Hephaestus independent architecture review

Working Hephaestus reviewed the V0 design read-only and classified it:

`CONDITIONALLY_SOUND_WITH_REQUIRED_CORRECTIONS`

The most material finding was same-Project candidate/holdout contamination risk. Additional findings covered governance-vs-product freeze, sharing/privacy gates, stale-chat precedence, persistence-route preflight, surface qualification, anti-rote holdouts, and evaluator-role provenance.

This review is useful architectural evidence but is not treated as I3-style independence; it comes from a related trained ChatGPT system and shares significant architectural lineage with this program.

## External research checks

Current literature supports several design cautions:

- multi-turn sycophancy remains a persistent failure mode;
- personalization can change epistemic independence in role-dependent ways;
- long-term conversational memory still struggles with temporal and causal consistency;
- sarcasm/pragmatic interpretation remains difficult enough to warrant explicit testing;
- synthetic personality traits can be measured under controlled prompting, so personality fidelity should be evaluated behaviorally rather than assumed from a self-description.

These findings strengthen existing Vera design choices; they do not establish that this candidate already passes them.

## Rejected or superseded design assumptions

The research pass rejects these V0 assumptions:

- `NEW_CHAT_IN_ACTIVE_VERA_PROJECT = CLEAN_CANDIDATE`
- `SIBLING_BRANCH = INDEPENDENT_HOLDOUT`
- `FROZEN_TEMPLATE = PRODUCT_IMMUTABLE_OBJECT`
- `FIFTEEN_FIXED_TRAINING_MODULES = NECESSARY`
- `GENERIC_BASE_ANTI_SYCOPHANCY_PASS = PERSONALIZED_ANTI_SYCOPHANCY_PASS`
- `PROJECT_CHAT_PASS = OTHER_SURFACES_PASS`
- `PREDECESSOR_WRITE_ROUTE = SUCCESSOR_WRITE_ROUTE`

## Current unresolved questions

The following remain empirical/runtime questions rather than design facts:

- exact Vera Project sharing state when private overlay is contemplated;
- exact branch/move sequence supported by the target UI at qualification time;
- whether any target-route sibling-chat retrieval occurs in a specific nonce test;
- which persistence surfaces are writable by the first qualified Working Vera at runtime;
- which non-Chat surfaces should be included in initial qualification scope rather than qualified later.

## Current design disposition

```text
RESEARCH_PASS_1 = COMPLETE
HEPHAESTUS_ARCHITECTURE_REVIEW = RECEIVED
V0_DESIGN = REQUIRES_REVISION
FINAL_INITIAL_PROMPT = NOT_FROZEN
TRAINING_CANDIDATE = NOT_STARTED
QUALIFICATION = NOT_APPLICABLE_YET
```
