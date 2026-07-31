-- Run this exact file concurrently from separate psql processes.
-- Both invocations must return the same stored receipt and create one canonical
-- record plus one request-journal row.

select public.append_vera_context_v3(
  'MREQ-durable-concurrent-save',
  $record$
  {
    "project_id": "vera-memory-durability",
    "branch_id": "branch-a",
    "record_key": "memory.durability.concurrent",
    "record_type": "TECHNICAL_RESULT",
    "statement": "Concurrent idempotent save committed once.",
    "lifecycle_status": "CURRENT",
    "epistemic_status": "OBSERVED_TOOL_RESULT",
    "source_actor": "TOOL",
    "privacy_scope": "PROJECT",
    "payload": {
      "contract": "memory-request-durability-v1",
      "case": "concurrent-exact-retry"
    },
    "source_evidence": [
      {
        "surface": "GITHUB_ACTIONS_LOCAL_SUPABASE",
        "tool_result_id": "MREQ-durable-concurrent-save"
      }
    ],
    "semantic_tags": {
      "topics": ["memory", "idempotency", "concurrency"],
      "status": ["test"]
    },
    "limitations": [
      "Synthetic CI record in a disposable database."
    ]
  }
  $record$::jsonb
);
