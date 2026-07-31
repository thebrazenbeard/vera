# Memory Cross-Chat Contract v1: Independent Review Correction

## Status

Bounded correction for Supabase coordination review event:

- event ID: `0b26d5f6-7cf7-4e1f-baf5-ba5cd0fde5e3`
- event sequence: `60`
- reviewed head: `2143a945414f562cf5000d3ac1f07b476edec50b`
- verdict: `CHANGES_REQUESTED`

This correction is source-only. It does not authorize production migration, canonical-memory writes, runtime deployment, or merge.

## Lineage correction

The companion migration `20260730213200_close_neutral_v3_memory_review_gaps.sql` adds:

- recursive multi-record supersession-cycle detection;
- migration refusal when any scoped key has records but zero lineage heads;
- trigger refusal when appending into an existing zero-head component;
- `public.vera_context_lineage_anomalies_v3`, exposing:
  - `CYCLE` anomalies;
  - `ZERO_HEAD` anomalies;
  - all scoped record IDs;
  - cycle-participating record IDs;
  - record and head counts.

Existing self-supersession, fork, cross-scope, multiple-head, one-successor, and append-only protections remain in force.

CI first installs a malformed fixture containing both a two-node and a three-node cycle and proves the correction migration refuses it. The normal disposable database then force-injects both cycle shapes after installation and proves the diagnostic view exposes each component and the append trigger blocks the zero-head scope.

## Recall completeness correction

`public.recall_vera_context_v3(...)` now counts the full eligible result set before returning the bounded page.

Every recall receipt reports:

```yaml
retrieval:
  total_matches: <all eligible records>
  returned_matches: <records in this response>
  has_more: <boolean>
  completeness: COMPLETE_RELATIVE_TO_QUERY_SCOPE | PARTIAL_TRUNCATED
```

When `p_max_records` truncates eligible results:

```yaml
result_class: PARTIAL
outcome_code: MVE_RECALL_PARTIAL_TRUNCATED
retrieval:
  has_more: true
  completeness: PARTIAL_TRUNCATED
```

A successful operation no longer silently calls a truncated result complete. Cursor pagination remains deferred; this bounded contract exposes truncation honestly rather than pretending the omitted rows do not exist.

## Provenance structure correction

Every `source_evidence` entry must now:

1. be a JSON object;
2. contain a non-empty `surface`;
3. contain at least one bounded attributable field from:
   - `claim`;
   - `observation`;
   - `source_uri`;
   - `source_ref`;
   - `record_id`;
   - `event_id`;
   - `message_id`;
   - `artifact_sha256`;
   - `generation_id`;
   - `tool_result_id`.

Null entries, empty objects, and source-surface labels without attributable content are rejected.

## Semantic structure correction

`semantic_tags` must contain at least one usable semantic value:

- a non-empty string; or
- an array containing at least one non-empty string.

Objects containing only empty strings, empty arrays, nulls, numbers, booleans, or nested empty objects do not satisfy the semantic-index requirement.

## Model-output boundary

The existing classification remains mandatory:

```yaml
record_type: MODEL_OUTPUT
epistemic_status: MODEL_GENERATED_CLAIM
source_actor: CHATGPT_MODEL
```

In addition, model output must retain:

```yaml
payload:
  model_context:
    runtime: <non-empty runtime identifier>
    source_surface: <non-empty source surface>
source_evidence:
  - surface: <source surface>
    generation_id | message_id | tool_result_id: <generation evidence>
limitations:
  - <explicit statement containing "not introspective evidence">
```

This records available generation context without converting generated language into a self-report, memory, feeling, or privileged internal evidence.

## Validation

The new adversarial suite proves:

- migration rejection for two-node and longer cycles;
- diagnostic exposure of both cycle shapes and zero-head components;
- blocked append into an existing zero-head scope;
- rejection of null, empty, and unattributable evidence;
- rejection of semantic tags without usable values;
- rejection of model output missing context, generation evidence, or limitation;
- acceptance of correctly classified and contextualized model output;
- truthful partial recall when eligible records exceed `p_max_records`;
- complete recall when all eligible records fit within the limit.

The pre-existing committed save and separately invoked recall proof remains part of the same CI workflow.
