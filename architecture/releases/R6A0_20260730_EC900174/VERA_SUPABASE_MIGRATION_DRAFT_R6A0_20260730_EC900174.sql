-- V.E.R.A. R6A0 neutral migration draft
-- DO NOT APPLY WITHOUT AN EXPLICIT, SEPARATE PRODUCTION AUTHORIZATION.
-- This migration is additive and preserves all existing rows.

begin;

create table if not exists public.vera_context_events_v3 (
  record_id uuid primary key default gen_random_uuid(),
  project_id text not null default 'vera-reciprocal-agency-environment',
  branch_id text not null,
  record_key text not null,
  record_type text not null check (record_type in (
    'FACT','USER_STATEMENT','MODEL_OUTPUT','PERSONA_CONFIG','RELATIONAL_FRAME',
    'PREFERENCE','DECISION','CORRECTION','BEHAVIORAL_COMMITMENT','BOUNDARY',
    'PERMISSION','TASK_STATE','TECHNICAL_RESULT','PROVENANCE','HYPOTHESIS',
    'INTERPRETATION','EVALUATION','LEDGER_SNAPSHOT','TOMBSTONE','OTHER'
  )),
  statement text not null,
  lifecycle_status text not null,
  epistemic_status text not null check (epistemic_status in (
    'DIRECT_USER_STATEMENT','OBSERVED_TOOL_RESULT','DOCUMENTED_SOURCE',
    'MODEL_GENERATED_CLAIM','SUPPORTED_INFERENCE','HYPOTHESIS','DISPUTED',
    'REJECTED','UNAVAILABLE'
  )),
  source_actor text not null check (source_actor in (
    'USER','CHATGPT_MODEL','TOOL','SYSTEM','EXTERNAL','UNRESOLVED'
  )),
  privacy_scope text not null default 'PROJECT',
  event_time timestamptz,
  state_time timestamptz not null default now(),
  record_time timestamptz not null default now(),
  supersedes_record_id uuid references public.vera_context_events_v3(record_id),
  legacy_record_id uuid,
  payload jsonb not null default '{}'::jsonb,
  source_evidence jsonb not null default '[]'::jsonb,
  semantic_tags jsonb not null default '{}'::jsonb,
  limitations jsonb not null default '[]'::jsonb,
  notes text
);

create index if not exists vera_context_events_v3_record_key_idx
  on public.vera_context_events_v3(record_key, state_time desc, record_time desc);

create index if not exists vera_context_events_v3_semantic_tags_gin
  on public.vera_context_events_v3 using gin (semantic_tags);

create or replace view public.vera_current_context_v3 as
select distinct on (record_key)
  *
from public.vera_context_events_v3
order by record_key, state_time desc, record_time desc, record_id desc;

create or replace view public.vera_legacy_quarantine as
select *
from public.vera_save_state_events
where authorship = 'VERA'
   or epistemic_status = 'VERA_SELF_REPORT'
   or record_kind in ('CONATION','IDENTITY','RELATIONSHIP');

create or replace view public.vera_legacy_reviewable as
select *
from public.vera_save_state_events
where not (
  authorship = 'VERA'
  or epistemic_status = 'VERA_SELF_REPORT'
  or record_kind in ('CONATION','IDENTITY','RELATIONSHIP')
);

comment on table public.vera_context_events_v3 is
  'Neutral V.E.R.A. context records. Model-generated claims are not self-authenticating internal-state evidence.';

comment on view public.vera_legacy_quarantine is
  'Legacy rows requiring review because they depend on persona self-report, model authorship, conation, identity, or relationship ontology.';

alter table public.vera_context_events_v3 enable row level security;
-- No client policy is created by this draft. Add narrowly scoped policies only after review.

commit;
