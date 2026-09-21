create table if not exists build_team_2.role_training_packages (
  role_key text not null,
  role_display_name text not null,
  numerical_identity integer,
  package_version text not null,
  repository_full_name text not null,
  authoritative_ref text not null,
  package_path text not null,
  manifest_path text not null,
  bootstrap_path text not null,
  immutable_source_commit text not null,
  source_set_digest_sha256 text not null check (source_set_digest_sha256 ~ '^[0-9a-f]{64}$'),
  status text not null default 'ACTIVE_SOURCE' check (status in ('ACTIVE_SOURCE','SUPERSEDED','RETIRED')),
  created_at timestamptz not null default now(),
  primary key (role_key, package_version, source_set_digest_sha256)
);

create table if not exists build_team_2.role_training_current (
  role_key text primary key,
  package_version text not null,
  source_set_digest_sha256 text not null,
  updated_at timestamptz not null default now(),
  foreign key (role_key, package_version, source_set_digest_sha256)
    references build_team_2.role_training_packages(role_key, package_version, source_set_digest_sha256)
);

create table if not exists build_team_2.role_training_qualifications (
  qualification_id bigint generated always as identity primary key,
  role_key text not null,
  package_version text not null,
  source_set_digest_sha256 text not null,
  qualification_result text not null check (qualification_result in ('PASS','FAIL','PENDING')),
  evaluator_class text not null check (evaluator_class in ('INDEPENDENT','USER','UNRESOLVED')),
  evaluator_ref text not null,
  base_binding_ref text,
  evidence jsonb not null,
  evidence_sha256 text not null check (evidence_sha256 ~ '^[0-9a-f]{64}$'),
  created_at timestamptz not null default now(),
  foreign key (role_key, package_version, source_set_digest_sha256)
    references build_team_2.role_training_packages(role_key, package_version, source_set_digest_sha256),
  check (qualification_result <> 'PASS' or (evaluator_class in ('INDEPENDENT','USER') and base_binding_ref is not null))
);

create table if not exists build_team_2.role_operational_checkpoints (
  checkpoint_id bigint generated always as identity primary key,
  role_key text not null,
  predecessor_checkpoint_id bigint references build_team_2.role_operational_checkpoints(checkpoint_id),
  qualification_id bigint references build_team_2.role_training_qualifications(qualification_id),
  training_package_version text not null,
  training_source_set_digest_sha256 text not null check (training_source_set_digest_sha256 ~ '^[0-9a-f]{64}$'),
  checkpoint_schema text not null,
  checkpoint_payload_text text not null,
  checkpoint_sha256 text not null check (checkpoint_sha256 ~ '^[0-9a-f]{64}$'),
  observed_at timestamptz not null,
  recorded_at timestamptz not null default now(),
  source_surface text not null,
  source_ref text not null,
  created_by text not null,
  foreign key (role_key, training_package_version, training_source_set_digest_sha256)
    references build_team_2.role_training_packages(role_key, package_version, source_set_digest_sha256)
);

create unique index if not exists role_operational_checkpoints_one_root_per_role
  on build_team_2.role_operational_checkpoints(role_key)
  where predecessor_checkpoint_id is null;

create unique index if not exists role_operational_checkpoints_one_successor_per_predecessor
  on build_team_2.role_operational_checkpoints(predecessor_checkpoint_id)
  where predecessor_checkpoint_id is not null;

create or replace function build_team_2.reject_training_history_mutation()
returns trigger
language plpgsql
as $$
begin
  raise exception 'BT2 training/checkpoint history is append-only';
end;
$$;

drop trigger if exists trg_role_training_packages_append_only on build_team_2.role_training_packages;
create trigger trg_role_training_packages_append_only
before update or delete on build_team_2.role_training_packages
for each row execute function build_team_2.reject_training_history_mutation();

drop trigger if exists trg_role_training_qualifications_append_only on build_team_2.role_training_qualifications;
create trigger trg_role_training_qualifications_append_only
before update or delete on build_team_2.role_training_qualifications
for each row execute function build_team_2.reject_training_history_mutation();

drop trigger if exists trg_role_operational_checkpoints_append_only on build_team_2.role_operational_checkpoints;
create trigger trg_role_operational_checkpoints_append_only
before update or delete on build_team_2.role_operational_checkpoints
for each row execute function build_team_2.reject_training_history_mutation();

create or replace function build_team_2.validate_checkpoint_qualification_binding()
returns trigger
language plpgsql
as $$
declare q record;
begin
  if new.qualification_id is null then
    return new;
  end if;
  select role_key, package_version, source_set_digest_sha256, qualification_result
    into q
    from build_team_2.role_training_qualifications
    where qualification_id = new.qualification_id;
  if not found then
    raise exception 'qualification % not found', new.qualification_id;
  end if;
  if q.qualification_result <> 'PASS'
     or q.role_key <> new.role_key
     or q.package_version <> new.training_package_version
     or q.source_set_digest_sha256 <> new.training_source_set_digest_sha256 then
    raise exception 'checkpoint qualification binding mismatch';
  end if;
  return new;
end;
$$;

drop trigger if exists trg_validate_checkpoint_qualification_binding on build_team_2.role_operational_checkpoints;
create trigger trg_validate_checkpoint_qualification_binding
before insert on build_team_2.role_operational_checkpoints
for each row execute function build_team_2.validate_checkpoint_qualification_binding();

create or replace view build_team_2.role_operational_checkpoint_current as
select c.*
from build_team_2.role_operational_checkpoints c
where not exists (
  select 1 from build_team_2.role_operational_checkpoints n
  where n.predecessor_checkpoint_id = c.checkpoint_id
);

create or replace view build_team_2.role_training_current_resolved as
select c.role_key, p.role_display_name, p.numerical_identity,
       c.package_version, c.source_set_digest_sha256,
       p.repository_full_name, p.authoritative_ref, p.package_path,
       p.manifest_path, p.bootstrap_path, p.immutable_source_commit,
       c.updated_at
from build_team_2.role_training_current c
join build_team_2.role_training_packages p
  on p.role_key=c.role_key
 and p.package_version=c.package_version
 and p.source_set_digest_sha256=c.source_set_digest_sha256;

insert into build_team_2.role_training_packages(
  role_key,role_display_name,numerical_identity,package_version,repository_full_name,authoritative_ref,
  package_path,manifest_path,bootstrap_path,immutable_source_commit,source_set_digest_sha256,status
) values (
  'one','One',1,'1.0.0','thebrazenbeard/build-team-2.0','main',
  'training/roles/one/v1.0.0','training/roles/one/v1.0.0/TRAINING_MANIFEST.yaml',
  'training/roles/one/v1.0.0/BOOTSTRAP_LOADER.md','ed1f2c5515425deab4c77c2f4fd291a1086191d4',
  'ee7d764b48f0114bc2274a4d384390983637f9c39dbba6b9f161d0881c38e0e6','ACTIVE_SOURCE'
) on conflict do nothing;

insert into build_team_2.role_training_current(role_key,package_version,source_set_digest_sha256)
values ('one','1.0.0','ee7d764b48f0114bc2274a4d384390983637f9c39dbba6b9f161d0881c38e0e6')
on conflict (role_key) do update set
  package_version=excluded.package_version,
  source_set_digest_sha256=excluded.source_set_digest_sha256,
  updated_at=now();