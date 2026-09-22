alter table semantic_atlas.runtime_snapshots
  add column if not exists authority_scope text not null default 'CANONICAL_LEDGER'
  check (authority_scope in ('CANONICAL_LEDGER','RESEARCH_STAGING'));

comment on column semantic_atlas.runtime_snapshots.authority_scope is 'Separates canonical-ledger materialization from research-staging materialization. ACTIVE in one scope does not imply authority in the other.';

drop index if exists semantic_atlas.semantic_atlas_one_active_snapshot;
create unique index semantic_atlas_one_active_snapshot_per_scope
  on semantic_atlas.runtime_snapshots (authority_scope)
  where state = 'ACTIVE';

drop view if exists semantic_atlas.canonical_runtime_objects;
drop view if exists semantic_atlas.research_runtime_objects;
drop view if exists semantic_atlas.active_runtime_objects;

create view semantic_atlas.active_runtime_objects as
select o.snapshot_id, s.git_commit_sha, s.source_branch, s.authority_scope, s.loaded_at,
       o.object_id, o.object_type, o.source_path, o.payload_sha256, o.payload
from semantic_atlas.runtime_objects o
join semantic_atlas.runtime_snapshots s using (snapshot_id)
where s.state = 'ACTIVE';

create view semantic_atlas.canonical_runtime_objects as
select * from semantic_atlas.active_runtime_objects
where authority_scope = 'CANONICAL_LEDGER';

create view semantic_atlas.research_runtime_objects as
select * from semantic_atlas.active_runtime_objects
where authority_scope = 'RESEARCH_STAGING';

comment on view semantic_atlas.canonical_runtime_objects is 'Preferred live semantic runtime surface. Includes only an ACTIVE snapshot explicitly materialized from the canonical Git ledger scope.';
comment on view semantic_atlas.research_runtime_objects is 'Research-only runtime surface. Must never be substituted for canonical semantic runtime.';

revoke all on all tables in schema semantic_atlas from public, anon, authenticated;
grant select, insert, update, delete on all tables in schema semantic_atlas to service_role;