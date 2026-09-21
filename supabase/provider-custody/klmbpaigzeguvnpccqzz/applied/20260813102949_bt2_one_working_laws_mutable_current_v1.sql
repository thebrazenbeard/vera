create table if not exists build_team_2.one_working_laws_current (
    scope_key text primary key,
    identity_name text not null,
    numerical_identity integer not null check (numerical_identity = 1),
    revision bigint not null check (revision >= 1),
    laws jsonb not null,
    source_event_id bigint,
    updated_by text not null,
    update_reason text not null,
    updated_at timestamptz not null default now(),
    constraint one_working_laws_singleton check (scope_key = 'BT2_ONE_WORKING_LAWS')
);

alter table build_team_2.one_working_laws_current enable row level security;

revoke all on table build_team_2.one_working_laws_current from anon, authenticated;

comment on table build_team_2.one_working_laws_current is
'Mutable singleton operational control record for One/Build Team Two. Current state is intentionally mutable; revision history remains separately append-only in build_team_2.memory_events.';