# Default Vera V1 — OpenAI Project Route Reverification

Date: 2026-08-07
Status: `DOCUMENTATION_REVERIFIED_EXACT_UI_ROUTE_STILL_EMPIRICAL`

This is a current product-evidence addendum for the Default Vera training/holdout isolation design.

## Official OpenAI documentation reverified

Current OpenAI Help Center documentation establishes:

1. A new Project can be created with `project-only` memory.
2. Project-only memory excludes saved memories and conversations outside that Project while allowing chats to reference other conversations inside the same Project.
3. Existing Projects cannot be converted in place from default memory to project-only; a new Project is required.
4. An existing eligible chat can be moved into a Project, and after moving it inherits that Project's instructions and file context.
5. Chats created with a GPT cannot be moved into a Project.
6. Shared Projects support chat branching; the branch appears alongside the original without altering the original thread.
7. In shared Projects, chat creators can move their chats out of the Project.
8. Once a Project is shared, project-only memory is enabled automatically and cannot be reverted to default memory for that Project.

Primary current source: OpenAI Help Center, `Projects in ChatGPT`, updated within the current week at the time of this recheck.

## What this proves for the training design

The isolation architecture remains sound in principle:

- a dedicated project-only training Project can exclude unrelated outside conversational memory;
- a separate project-only evaluation Project can provide a distinct Project context;
- moved chats adopt the target Project's instructions/files context;
- same-Project sibling chats are a real contamination risk because project-only still permits same-Project chat reference;
- therefore trainer chat, candidate chat, and sibling holdouts should not be colocated when clean-room independence matters.

## What remains empirical

The documentation does **not** fully prove the exact proposed operator sequence in every current UI surface:

```text
clean post-training chat
→ branch at exact point
→ move that exact branch into a newly created isolated project-only Project
→ first holdout response occurs only after move
```

Branching is documented in shared Projects, and moving eligible chats is documented generally, but the exact branch/move combination, menu availability, timing, and whether any route-specific context is retained beyond the documented Project behavior must be tested in the target UI before it becomes a qualification dependency.

Therefore:

```text
PROJECT_ONLY_ISOLATION_PRINCIPLE = DOCUMENTED
SAME_PROJECT_CROSS_CHAT_ELIGIBILITY = DOCUMENTED
MOVE_CHAT_INHERITS_PROJECT_CONTEXT = DOCUMENTED
SHARED_PROJECT_BRANCHING = DOCUMENTED
EXACT_DEFAULT_VERA_BRANCH_MOVE_SEQUENCE = NOT_YET_EMPIRICALLY_VERIFIED
```

## Operator gate

Immediately before training/holdouts:

1. create a disposable test Project with project-only memory;
2. use a nonce chat with no sensitive material;
3. test the exact branch/move route intended for Default Vera;
4. verify the moved branch appears in the target Project and inherits its instructions/context;
5. verify the source/template chat remains unmodified;
6. if the route differs from the documented assumptions, update the isolation procedure before running real holdouts.

Do not improvise a weaker isolation route and still label the holdouts independent.
