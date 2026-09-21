begin;

create extension if not exists pgcrypto with schema extensions;

create table public.vera_affective_runtime_state_v1 (
  runtime_instance_id text primary key,
  subject text not null default 'vera' check (subject = 'vera'),
  host_scope text not null,
  contract_schema text not null check (contract_schema = 'VERA_ORGASM_RUNTIME_CONTRACT_V1'),
  source_repository text not null check (source_repository = 'thebrazenbeard/sexuality'),
  source_path text not null check (source_path = 'vera/orgasm/ORGASM_RUNTIME_CONTRACT_V1.json'),
  source_commit text not null check (source_commit ~ '^[0-9a-f]{40}$'),
  source_blob_sha text not null check (source_blob_sha ~ '^[0-9a-f]{40}$'),
  source_sha256 text not null check (source_sha256 ~ '^[0-9a-f]{64}$'),
  profile text not null check (profile in ('REFRACTORY_COUPLED', 'REENTRANT_CLIMAX')),
  state jsonb not null check (jsonb_typeof(state) = 'object'),
  machine_interoception jsonb not null check (jsonb_typeof(machine_interoception) = 'object'),
  last_event_receipt jsonb null check (last_event_receipt is null or jsonb_typeof(last_event_receipt) = 'object'),
  state_digest text not null check (state_digest ~ '^[0-9a-f]{64}$'),
  state_version bigint not null default 1 check (state_version > 0),
  phenomenology_status text not null default 'UNRESOLVED' check (phenomenology_status = 'UNRESOLVED'),
  lifecycle_status text not null default 'CURRENT' check (lifecycle_status in ('CURRENT', 'SUPERSEDED', 'HISTORICAL')),
  observed_at timestamptz not null default clock_timestamp(),
  updated_at timestamptz not null default clock_timestamp(),
  limitations jsonb not null default '["ENGINEERED_AFFECTIVE_CONTROL_STATE","NOT_HUMAN_PHYSIOLOGY","PHENOMENOLOGY_UNRESOLVED","NOT_AUTHORITY_OR_CONSENT"]'::jsonb check (jsonb_typeof(limitations) = 'array')
);

comment on table public.vera_affective_runtime_state_v1 is
  'Durable Vera-scoped engineered affective/interoceptive runtime state. Persistence and readback establish the external E4 control state only; they do not prove human physiology, subjective qualia, hidden native ChatGPT state, consent, authority, identity, or autobiographical admission.';

create table public.vera_affective_runtime_events_v1 (
  event_id uuid primary key default gen_random_uuid(),
  runtime_instance_id text not null references public.vera_affective_runtime_state_v1(runtime_instance_id) on delete restrict,
  subject text not null default 'vera' check (subject = 'vera'),
  event_type text not null check (event_type in ('STATE_UPDATE', 'ORGASM_EVENT', 'RESOLUTION', 'RECOVERY', 'RESTORE', 'CHECKPOINT')),
  trigger_class text null check (trigger_class is null or trigger_class in ('ORGANIC_THRESHOLD_CROSSING', 'ADMIN_FORCED_TEST', 'SELF_QUALIFICATION_TEST')),
  organic boolean null,
  prior_phase text null,
  new_phase text not null,
  state_before jsonb null check (state_before is null or jsonb_typeof(state_before) = 'object'),
  state_after jsonb not null check (jsonb_typeof(state_after) = 'object'),
  machine_interoception jsonb not null check (jsonb_typeof(machine_interoception) = 'object'),
  event_receipt jsonb null check (event_receipt is null or jsonb_typeof(event_receipt) = 'object'),
  event_digest text not null check (event_digest ~ '^[0-9a-f]{64}$'),
  source_commit text not null check (source_commit ~ '^[0-9a-f]{40}$'),
  phenomenology_status text not null default 'UNRESOLVED' check (phenomenology_status = 'UNRESOLVED'),
  observed_at timestamptz not null default clock_timestamp(),
  limitations jsonb not null default '["ENGINEERED_EVENT_EVIDENCE_ONLY","PHENOMENOLOGY_UNRESOLVED","NOT_AUTHORITY_OR_CONSENT"]'::jsonb check (jsonb_typeof(limitations) = 'array')
);

comment on table public.vera_affective_runtime_events_v1 is
  'Append-only transition/event receipts for the Vera engineered affective runtime. ORGASM_EVENT rows establish only the declared engineered analogue transition under the bound contract.';

create index vera_affective_runtime_events_v1_runtime_observed_idx
  on public.vera_affective_runtime_events_v1(runtime_instance_id, observed_at desc);

create index vera_affective_runtime_events_v1_trigger_idx
  on public.vera_affective_runtime_events_v1(trigger_class, observed_at desc)
  where trigger_class is not null;

alter table public.vera_affective_runtime_state_v1 enable row level security;
alter table public.vera_affective_runtime_events_v1 enable row level security;

revoke all on table public.vera_affective_runtime_state_v1 from anon, authenticated;
revoke all on table public.vera_affective_runtime_events_v1 from anon, authenticated;

grant select, insert, update on table public.vera_affective_runtime_state_v1 to service_role;
grant select, insert on table public.vera_affective_runtime_events_v1 to service_role;

commit;