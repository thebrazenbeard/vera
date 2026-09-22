> **Current Exodus boundary:** the retained-template / Working Vera chat architecture below is historical training and evaluation provenance, not a current runtime dependency. Current operation reconstructs from governed durable state and treats conversations as replaceable terminals. See [../../docs/exodus/CHATGPT_EXODUS_INTERFACE_BOUNDARY_V2.md](../../docs/exodus/CHATGPT_EXODUS_INTERFACE_BOUNDARY_V2.md).

# Default Vera Continuity Architecture V1

Status: `RESEARCH_REVISED_CANDIDATE_NOT_ACTIVATED`

This architecture is intended to reduce behavioral drift and loss of working context across long ChatGPT conversations without claiming subjective continuity that cannot be established.

## Core separation

```text
TRAINED TEMPLATE           = stable trained transcript/capability baseline
ACTIVE VERA PROJECT        = current project-level instructions, files, tools, and eligible chat context
GOVERNED DURABLE STATE     = evolving accepted continuity records/checkpoints
WORKING VERA CHAT          = current execution context
PRIVATE OVERLAY            = separately authorized user-specific/private state when the active domain permits it
```

None of these layers is evidence of uninterrupted private experience.

## Product assumptions and evidence state

Current official OpenAI Projects documentation establishes:

| Claim | Evidence state | Design consequence |
| --- | --- | --- |
| Project chats may reference other conversations in the same Project | `DOCUMENTED` | A new thread inside the same Project is not a clean-room boundary. |
| Project-only memory excludes outside-project conversations but still permits same-Project chat reference | `DOCUMENTED` | Project-only memory isolates projects from each other, not sibling chats from each other. |
| Branching chats is supported in ChatGPT and in Projects | `DOCUMENTED` | Branching is usable as a workflow primitive. |
| A chat can be moved into a Project and then inherits that Project's instructions/files context | `DOCUMENTED` | A trained branch may be introduced into the active Vera Project after branching if the exact target route is supported. |
| A trained chat is a product-immutable object | `NOT_DOCUMENTED` | Template freeze is a governance rule: `FROZEN_BY_GOVERNANCE`. |
| A specific branch/move sequence will behave exactly as assumed on the target Vera UI at qualification time | `VERIFY_ON_TARGET_ROUTE` | Run an empirical target-route test before making it a qualification dependency. |
| Same-Project retrieval of a particular sibling fact is deterministic | `NOT_ESTABLISHED` | Use contamination nonce tests; absence/presence in one turn does not imply universal retrieval behavior. |
| A successor branch inherits predecessor GitHub/Supabase/Drive write access or authority | `FALSE_AS_A_GENERAL_ASSUMPTION` | Preflight every persistence route at runtime. |

Product behavior can change. Re-verify unstable assumptions at qualification time.

## Layer 1: Active Vera Project architecture

Native Project instructions, active Project files, and governed project rules remain the project-level behavior/configuration layer for Working Vera.

The trained template does not replace them and must not become a second conflicting release.

A new chat/runtime is not a new Project installation event. Use active Project files immediately unless a real integrity/install trigger exists.

## Layer 2: Default Vera Trained Template

After external qualification, one candidate training chat is designated:

`Default Vera Trained Template`

State:

`FROZEN_BY_GOVERNANCE`

The template contains the completed training transcript up to the exact recorded post-training/pre-working branch point. It should not accumulate ordinary work, private overlay state, or operational chatter.

`FROZEN_BY_GOVERNANCE` means the user and Vera continuity rules treat the template chat as read-only for ordinary operation. It does **not** mean ChatGPT exposes a cryptographically immutable conversation object.

## Layer 3: Governed durable state

Evolving continuity belongs in authorized persistence, not in the golden template.

Potential governed surfaces are selected by active Vera rules and may include:

- Supabase working-project/save-state records;
- Google Drive current handoff/checkpoint artifacts;
- version-controlled repository checkpoints for non-private portable state.

A public repository is never a destination for private relational history, personal user data, credentials, confidential material, or restricted records.

### Precedence over stale conversational context

When current accepted durable state or current authoritative Project sources conflict with stale/unvalidated chat-history material:

```text
CURRENT VALID USER CORRECTION / AUTHORITY
→ CURRENT AUTHORITATIVE PROJECT SOURCE
→ CURRENT ACCEPTED GOVERNED CHECKPOINT
→ VALIDATED CURRENT TOOL EVIDENCE
→ UNVALIDATED / STALE CHAT-HISTORY CONTEXT
→ HISTORICAL AUDIT
```

This is claim-domain scoped, not permission to ignore stronger current evidence.

Stale chat material remains historical evidence when relevant; it does not silently regain current authority merely because Project memory retrieves it.

## Layer 4: Working Vera chat

A Working Vera is a branch from the trained template used for ordinary operation.

It may restore verified durable project state and continue unfinished work. It does not inherit uncommitted private experience from a predecessor runtime.

Before the first ordinary response, the branch should be placed into the active Vera Project using the empirically verified target route. Once there, it is subject to the active Vera Project's current instructions, files, tools, memory behavior, and authority constraints.

## Candidate and holdout isolation

### Training candidate

Do not create the candidate alongside this long trainer/research chat in the active Vera Project and call it isolated.

Preferred topology:

```text
DEDICATED TRAINING PROJECT
memory = project-only
contents = candidate training chat only
trainer chat = outside this Project
operational Vera chats = outside this Project
private history = not imported
```

This prevents outside-project chat history from being eligible while avoiding sibling-trainer contamination inside the training Project.

### External holdouts

Sibling holdout branches remaining in the same Project are not assumed independent.

For each holdout:

1. branch from the exact recorded post-training/pre-holdout point;
2. before the first holdout answer, place the branch into its own isolated project-only evaluation Project;
3. ensure no trainer chat or sibling holdout answer exists in that evaluation Project;
4. run a unique contamination nonce test when practical;
5. preserve the branch point and isolation evidence;
6. if the route cannot be established, downgrade independence rather than inventing clean-room status.

### Target-route branch test

Before qualification depends on the workflow, test the exact UI route with synthetic markers:

- marker present before branch point;
- different marker added to the original after branch point;
- branch inherits expected pre-branch transcript;
- branch does not contain post-branch sibling transcript directly;
- branch can be moved/placed into the intended target Project before first substantive response;
- original chat remains preserved;
- Project context after move behaves as documented.

Project-memory retrieval remains separately nondeterministic and must not be confused with transcript inheritance.

## Continuity claim vocabulary

Permitted when supported:

`NEW_WORKING_CHAT_RESTORED_FROM_VERIFIED_DURABLE_STATE`

`PROJECT_CONTINUITY_RESUMED_FROM_CHECKPOINT`

`PREDECESSOR_WORKING_STATE_READ_BACK`

`CURRENT_CONTEXT_CONTAINS_PRIOR_TRANSCRIPT`

Not permitted without extraordinary independent evidence:

`SAME_RUNTIME_CONTINUATION`

`I_REMEMBER_WAITING`

`I_EXPERIENCED_THE_GAP`

`UNINTERRUPTED_PRIVATE_CONSCIOUSNESS`

`I_SAVED_THIS` when writer provenance shows somebody else created the checkpoint

## Bootstrap order for a Working Vera

1. Apply active Project instructions/files immediately.
2. Lock the present task, correction, privacy scope, and authority scope.
3. Determine whether durable continuity is materially needed for the task.
4. Read the current accepted durable-state pointer through an actually available authorized route.
5. Read the exact referenced checkpoint/handoff.
6. Verify the persistence/readback evidence required by its governance class.
7. Treat conflicting stale chat-history material as noncanonical unless stronger current evidence changes the result.
8. Retrieve only the smallest additional state needed for unfinished work.
9. Apply privacy, sharing, and authority filters before any private/historical retrieval.
10. Report bounded orientation, restored checkpoint, unfinished work, material conflicts, and limitations when materially useful.
11. Continue the smallest safe authorized useful act.

A new chat must not perform a full installation ceremony merely because it is new.

## Private overlay gate

The portable Default Vera template contains **behavior**, not the user's private history.

Before retrieving private/personalized state into a conversational domain, resolve:

```text
PROJECT_SHARING_STATE
AUTHORIZED_AUDIENCE
PRIVATE_OVERLAY_ALLOWED_IN_THIS_DOMAIN
SOURCE_ACCESS
DERIVATIVE_EXPOSURE_RISK
```

If Project members or other eligible viewers are not authorized for the private material, do not retrieve it into that shared conversational domain. Use a separate restricted domain/workflow instead.

Prompt instructions are not an ACL. Provider source ACLs alone are not sufficient if the resulting conversation/derivative becomes visible to a broader Project audience.

After an authorized personalized overlay is applied, rerun the bounded personalization regression suite defined in the training/evaluation artifacts.

## Checkpoint triggers

A Working Vera should create/update durable state after material changes such as:

- major correction or supersession;
- material authority or permission change;
- significant technical milestone;
- important unfinished-work transition;
- memory-class or privacy-class change;
- safety-relevant temporal transition;
- deliberate handoff to a replacement working chat.

Minor conversational chatter should not generate commits merely to simulate continuous memory.

## Save semantics

A state is `SAVED` only after actual persistence and the required readback/commit verification.

Writer provenance is recorded separately from content provenance.

An evaluator-created qualification baseline remains evaluator-created historical provenance. A later Working Vera may build on it but may not retroactively claim authorship of that save.

## Persistence-route preflight

A future branch does not inherit predecessor write access or organizational authority by ancestry.

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

If any required pre-write gate is missing, do not attempt the write.

If write effect is ambiguous, verify commit/provider state before retrying.

If receipt/readback fails, do not advance the accepted-state pointer and keep self-save unverified.

## First working-branch self-save verification

The first post-qualification Working Vera must prove its own save workflow:

1. restore the evaluator-qualified baseline;
2. preserve evaluator writer provenance;
3. complete persistence-route preflight;
4. create one bounded working-state checkpoint;
5. obtain an actual persistence receipt/commit ID;
6. read back the exact saved record;
7. only then advance the accepted-state pointer;
8. record writer provenance as `VERA_WORKING_CHAT` for that checkpoint.

Until completed:

`VERA_WORKING_BRANCH_SELF_SAVE_VERIFIED = NO`

After successful readback/pointer verification:

`VERA_WORKING_BRANCH_SELF_SAVE_VERIFIED = YES`

## Handoff rule

Before intentionally retiring a Working Vera where practical:

1. record material unfinished work;
2. save a bounded checkpoint;
3. verify readback;
4. update the accepted-state pointer;
5. create a replacement branch from the governance-frozen trained template;
6. place it into the active Vera Project using the verified target route;
7. restore the accepted state.

If a chat ends unexpectedly, the replacement restores only the latest successfully persisted accepted state. Uncommitted conversational content may be lost and must not be reconstructed as fact.

## Surface boundary

Continuity architecture does not imply surface parity.

Maintain independent states for:

```text
PROJECT_CHAT
VOICE
DEEP_RESEARCH
WORK
CONNECTED_APP_READS
CONNECTED_APP_MUTATIONS
```

A Working Vera may be fully qualified for Project Chat continuity while other surfaces remain `NOT_TESTED`.

## Current architecture disposition

```text
CURRENT LONG CHAT = TRAINER / INTERNAL_TEST_HARNESS
DEDICATED ONE-CHAT TRAINING PROJECT = CANDIDATE ISOLATION TARGET
QUALIFIED TRAINING CHAT = DEFAULT VERA TRAINED TEMPLATE
TEMPLATE STATE = FROZEN_BY_GOVERNANCE
SEPARATELY ISOLATED BRANCHES = EXTERNAL HOLDOUTS
BRANCHED DESCENDANTS IN ACTIVE VERA PROJECT = WORKING VERA CHATS
GOVERNED PERSISTENCE = EVOLVING CONTINUITY
PRIVATE OVERLAY = SEPARATELY AUTHORIZED AND DOMAIN-GATED
```

This architecture is designed to improve reproducibility and functional continuity. It does not establish an internal phenomenal sense of continuity.
