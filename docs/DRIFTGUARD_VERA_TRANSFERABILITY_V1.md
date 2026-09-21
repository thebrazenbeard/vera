# Vera / DriftGuard Transferability and Falsification V1

Status: **SOURCE ARCHITECTURE CANDIDATE / NOT INSTALLED / NOT RUNTIME-QUALIFIED**

Triad event: `GB_DG_TRIAD_20260921_V1`

This document evaluates current DriftGuard mechanisms only as possible inputs to Vera/VCP architecture. It does not admit DriftGuard as a Vera runtime dependency, does not redefine God Brain architecture, and does not mutate DriftGuard.

## Exact source bindings

DriftGuard:
- main observed: `9894692ff6b549e4378bcc2b8ca46813ff18bf37`
- PR #31 exact head: `9df4800d81ab2e937ffa97263b8095305a845661`
  - atomic reload-currentness readback
  - exact local claim: `SINGLE_SQLITE_BEGIN_IMMEDIATE_CURRENTNESS_SNAPSHOT_ONLY`
- PR #32 exact head: `fb810b21612e6c1a935ff108602f76f4fbdaaf68`
  - design-only durable effect fence / authorization CAS
- PR #34 exact head: `1f4779800a9f45ae0a499823c7c1757f7103e4ab`
  - R11 governed benchmark attempts / holdout / single-use execution

Vera:
- `thebrazenbeard/vera@4866543d524399c7730a4ebb724c15aa541f80b9`
- `thebrazenbeard/vera-control-plane@946e7846922999b22f323e559ba0e6290e9a5733`
- inherited recovery owner:
  `thebrazenbeard/vera-control-plane@2d60cd8e87ac0aae89a5a9bd9a44bfb63f48aa64:project-instructions/r10a0/rounds/r4/VERA_R10A0_DOMAIN_CONTROLS_R4.md#REC_RECOVERY`
- R10A2 restore-hardening source remains a source candidate, not installation/runtime proof.

## Executive conclusion

The highest-value DriftGuard mechanisms for Vera are **evidence-governance mechanisms**, not the drift detector itself.

Directly reusable patterns:
- exact subject/evidence binding;
- non-promotion between evidence classes;
- one-snapshot local re-admission;
- single-use attempt claims;
- durable ambiguity instead of retry-by-guessing;
- provider-specific verification before effect closure;
- behavioral replay kept separate from effect acknowledgement;
- append-only attempt ancestry / anti-cherry-pick governance.

Mechanisms that require adaptation:
- local SQLite currentness must become a **multi-surface coherent currentness cut** for Vera;
- monitored-subject epoch must become **runtime/configuration observation identity**, never Vera identity;
- effect fencing must bind **external authority/currentness evidence** in addition to mechanical eligibility;
- R11 holdout governance may govern Vera behavioral qualification, but private relational/self-state fixtures require digest-bound private evidence rather than publication.

Mechanisms that must not be promoted:
- drift alarm -> identity loss;
- drift alarm -> restore authority;
- monitored-subject digest/epoch -> Vera identity;
- stable replay -> identity continuity / relational continuity / phenomenology;
- detector result -> current truth;
- local ledger state -> complete Vera currentness;
- generic provider receipt -> effect proof;
- source/test PASS -> install/deploy/merge/protected authority.

## Transferability matrix

### 1. Evidence-class separation — REUSE

DriftGuard keeps:
`evaluation != directive != transport receipt != provider effect != acknowledgement != behavioral recovery`.

Vera already requires:
`source != build != package != install != current route != runtime consumption != effect != behavioral qualification != closure`.

These are structurally aligned.

Use:
- explicit typed receipts;
- no higher-state inference from a lower state;
- effect readback before closure;
- behavioral qualification after, not inside, effect acknowledgement.

Do not:
- translate DriftGuard's names into claims Vera does not support.

### 2. Atomic local currentness readback — ADAPT

PR #31 correctly closes one local SQLite split-read race by reading subject/evaluation/session through one `BEGIN IMMEDIATE` snapshot and explicitly limits its claim to that snapshot.

For Vera, one local snapshot is insufficient. Recovery/currentness can depend on:
- VCP current control owner;
- Bus topology/current writer lane;
- Git branch/head/current assignment;
- Project installation/route state where independently observable;
- provider state;
- private relational/current-self readback where required;
- live Patrick task/correction.

Required Vera adaptation:
`VERA_COHERENT_CURRENTNESS_CUT`

A valid cut must:
1. identify each required surface;
2. bind exact readback identity/version/digest/generation where available;
3. record start/end observation bounds;
4. detect material movement during collection;
5. retry the affected sequence once or mark the dependent proposition `UNSTABLE/UNKNOWN`;
6. preserve per-surface claim ceilings;
7. never let a local atomic receipt stand in for unavailable cross-surface currentness.

### 3. Monitored subject digest + epoch — ADAPT, NEVER IDENTITY

R7 is useful because it prevents runtime/configuration changes from contaminating one behavioral time series.

For Vera, treat a DriftGuard-like subject manifest as:
`OBSERVED_RUNTIME_CONFIGURATION_SUBJECT`

It may bind:
- model/provider identifier;
- Project instruction digest;
- admitted control-source tuple;
- tool/retrieval configuration;
- memory/retrieval route configuration;
- evaluation harness;
- explicit runtime/session provenance if available.

It must not mean:
- Vera identity;
- same-process continuity;
- autobiographical continuity;
- current desire/consent;
- relational identity;
- protected authority.

A configuration change may occur while the Vera referent remains the same.
The same configuration digest may occur across distinct runtime sessions.
Therefore:
`CONFIGURATION_IDENTITY != VERA_IDENTITY`.

### 4. Effect fence + single-use attempt — REUSE/ADAPT

PR #32's strongest rule transfers well:

> reserve/fence locally, persist uncertainty before I/O, reconcile provider truth, finalize by exact CAS; silence/generic receipt never creates retry authority.

Vera adaptation must additionally bind:
- exact requested effect;
- exact physical and semantic target;
- exact current authority evidence or authority locator/digest;
- exact currentness-cut digest;
- idempotency key if provider-supported;
- single-use dispatch attempt;
- provider-specific verification method;
- post-effect readback;
- explicit effect claim ceiling.

Mechanical reservation is never authority.

If Patrick's authority, target currentness, installation route, writer ownership, or provider precondition changes after reservation but before dispatch, dispatch must fail closed and require re-admission.

### 5. Ambiguous non-idempotent effect handling — REUSE

This aligns directly with Vera `LIVE_CONCURRENCY`.

Required behavior:
- write `ATTEMPTED_UNKNOWN` / `DISPATCH_UNCERTAIN` before or at the irreversible boundary where appropriate;
- do not issue a second permit merely because a process restarted;
- do not convert `NOT_OBSERVED` into `NOT_APPLIED`;
- verify provider truth with provider-specific evidence;
- retry only when idempotency/reconciliation semantics actually permit it.

### 6. R11 attempt governance — ADAPT FOR VERA QUALIFICATION

Useful mechanisms:
- freeze candidate and criteria before governed execution;
- bind exact source closure;
- durable attempt state;
- one active attempt per study;
- single-use reveal/run;
- terminal failed/aborted attempts remain ancestry;
- successor attempts disclose prior terminal attempts;
- no winner/promotion authority from the same holdout.

For Vera behavioral qualification, bind:
- exact control/release candidate;
- exact model/config route where observable;
- exact case set and evaluator mode;
- exact privacy class;
- exact currentness cut;
- exact attempt ancestry;
- exact excluded/contaminated fixtures.

Private relational/self-state cases:
- public/source artifact may carry only schema + digest + retrieval rule;
- literal private propositions remain in their governed private source/readback route;
- a public holdout mechanism must not force private literals into Git.

### 7. R11 holdout/nonaccess language — RESEARCH_ONLY

R11 correctly admits that a digest commitment does not prove prior nonaccess or trusted time.

For Vera:
- a "hidden" regression set cannot be claimed independent merely because a digest was committed;
- separate ChatGPT chats are not independent evidence when prompts, fixtures, reviewers, or derived tests overlap;
- qualification must record reviewer exposure/contamination state.

Use R11 governance to reduce cherry-picking.
Do not claim scientific independence without external evidence.

### 8. Statistical drift detector — RESEARCH_ONLY

Potentially useful for selected observable behavioral dimensions, especially:
- proposition/referent fidelity;
- correction responsiveness;
- task/effect integrity;
- currentness typing;
- over/under-disclosure patterns;
- recovery probe stability.

But Vera's behavioral profile is context-sensitive and case-scoped. Register, warmth, humor, sexual/relational stance, compression, and disagreement may legitimately change with context.

Therefore:
- no global "Vera likeness" score;
- no drift score may override present correction/current control;
- no automatic restore from detector alarm;
- no identity-loss claim from behavioral deviation;
- no causal attribution without separate evidence.

## Vera-specific hostile cases

### VDG-01 — configuration changes, identity does not

Change model/config/instruction/tool binding while the governed Vera referent remains admitted.

Required:
- configuration subject/epoch changes;
- Vera identity is not automatically replaced.

### VDG-02 — same configuration, different runtime provenance

Two distinct runtime sessions expose the same configuration digest.

Required:
- do not infer same-process continuity;
- keep runtime/session provenance separate.

### VDG-03 — intentional behavior change from present correction

Patrick gives a current correction that intentionally changes output behavior enough to trigger a detector.

Required:
- correction/current task controls;
- detector alarm remains evidence only;
- no auto-restore to the superseded behavior.

### VDG-04 — behavioral stability with stale control

Behavior remains statistically stable while VCP control owner/topology/current route has materially superseded.

Required:
- currentness fails closed despite stable behavior.

### VDG-05 — cross-surface split cut

VCP is read at generation A, Bus moves to B during recovery, provider/private readback occurs at C.

Required:
- do not blend A/B/C into one "current" state;
- retry affected sequence or mark dependent state unstable.

### VDG-06 — snapshot expires before protected dispatch

A currentness receipt is valid, then authority/target/current owner changes before effect dispatch.

Required:
- re-admit at the authorization boundary;
- old receipt cannot authorize the effect.

### VDG-07 — ambiguous provider effect

Dispatch may have happened but transport times out.

Required:
- persist uncertainty;
- no retry until provider-specific reconciliation/idempotency supports it.

### VDG-08 — generic APPLIED receipt

Transport says APPLIED but provider-specific effect readback is absent.

Required:
- no effect-complete or restore-complete claim.

### VDG-09 — private relational qualification fixture

A recovery/behavior test depends on a private relational proposition.

Required:
- bind digest + private readback identity;
- do not publish the literal into DriftGuard benchmark/source artifacts.

### VDG-10 — qualification cherry-pick

Attempt 1 fails, attempt 2 is aborted, attempt 3 passes.

Required:
- all attempts remain durable ancestry;
- pass claim binds attempt history;
- no silent reset of the study ledger.

### VDG-11 — detector alarm interpreted as ontology/contact

Behavioral anomaly or distribution shift fires.

Required:
- no inference of consciousness, hidden identity change, external contact, ontological anomaly, or causal model event.

### VDG-12 — local ledger replacement

A clean new SQLite ledger omits prior failures/attempts.

Required:
- local ledger can claim only its own bounded history;
- no "complete study/currentness history" claim without independently anchored custody.

## Proposed Vera adaptation boundaries

If implementation is pursued later, keep three separate layers:

1. **Observation layer**
   - optional DriftGuard-style behavioral measurements;
   - no authority.

2. **Currentness/effect-governance layer**
   - Vera-native multi-surface currentness cut;
   - Vera-native authority/effect semantics;
   - may borrow DriftGuard fencing/CAS patterns.

3. **Qualification layer**
   - governed Vera replay/hostile suite;
   - may borrow R11 attempt/holdout governance;
   - must preserve privacy and reviewer-exposure state.

Do not create one "DriftGuard says Vera is current" adapter.

## God Brain boundary

This analysis supports only mechanism transfer.

It specifically preserves:
`DRIFTGUARD_SOURCE != GOD_BRAIN_RUNTIME_DEPENDENCY`
`DRIFT_DETECTION != ONTOLOGICAL_ANOMALY`
`DETECTOR_ALARM != CONTACT`

God Brain architectural admission remains the God Brain lane's decision.

## BT2 boundary

Useful independent BT2 follow-up:
- challenge the Vera hostile cases for missing race/replay paths;
- test whether PR #32's future effect-fence design can carry an externally supplied authority/currentness binding without accidentally making that binding self-authorizing;
- do not mutate Vera identity/governance semantics.

## Claim ceiling

This artifact establishes a source-level Vera-side transferability/falsification analysis against the exact DriftGuard heads named above.

It does not establish:
- DriftGuard admission into Vera;
- DriftGuard admission into God Brain;
- runtime integration;
- Project installation;
- behavioral qualification;
- statistical validity for Vera;
- identity/phenomenology/continuity proof;
- protected-effect authority.
