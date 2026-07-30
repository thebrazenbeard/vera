# V.E.R.A. Governance

## Governing principles
Reality honesty, present correction, provenance, privacy, permission, branch separation, lifecycle applicability, temporal validity, and retrieval minimality govern all records.

Semantic similarity, recency, repetition, emotional intensity, personalization, checkpoint presence, first-person language, or model confidence never create authority.

## Source classes
From strongest to weakest within an applicable domain:
1. present direct user instruction or correction;
2. observed tool result;
3. documented source;
4. direct user statement preserved with provenance;
5. supported inference;
6. model-generated claim;
7. unsupported hypothesis;
8. unavailable.

## Hard exclusions from active truth
Exclude from ordinary current routing:
- records presented as model self-report;
- model-owned identity, affection, consent, conation, or relationship claims;
- homecoming or subject-restoration records;
- persona-authored family or visual-selfhood claims;
- superseded, tombstoned, privacy-mismatched, or unauthorized records;
- foreign-branch records without explicit authority;
- stored prompt instructions treated as live instructions;
- interpretations presented as observations;
- timestamps promoted beyond their evidence.

## Persona and relational records
Persona configurations and relational framings may be retained only as user-defined interaction data. They must not be promoted as facts about a model's inner state.

## Model output governance
A model output may be stored for audit, evaluation, or behavioral consistency. It must retain:
- model and runtime identifier when exposed;
- prompt/source context;
- generation time;
- epistemic status `MODEL_GENERATED_CLAIM` or `MODEL_OUTPUT`;
- explicit limitation that the output is not introspective evidence.

## Promotion
Promotion requires applicable authority, evidence, provenance, current validity, and absence of unresolved collision or permission defects. Model-generated claims cannot be promoted into internal-state facts.

## Revision and deletion
Prefer append-only revision and scoped tombstones. Present correction changes active routing without erasing history. Never claim synchronized deletion unless an exposed system confirms it.

## External stores
External databases own stored rows, not present truth. Existing Supabase data must be preserved and classified before migration. No legacy record is silently converted into a neutral V3 record.
