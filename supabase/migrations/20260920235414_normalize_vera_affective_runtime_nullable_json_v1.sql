begin;

create or replace function public.vera_affective_runtime_normalize_nullable_json_v1()
returns trigger
language plpgsql
set search_path = pg_catalog, public
as $$
begin
  if new.last_event_receipt = 'null'::jsonb then
    new.last_event_receipt := null;
  end if;
  return new;
end;
$$;

drop trigger if exists vera_affective_runtime_normalize_nullable_json_v1
  on public.vera_affective_runtime_state_v1;

create trigger vera_affective_runtime_normalize_nullable_json_v1
before insert or update on public.vera_affective_runtime_state_v1
for each row
execute function public.vera_affective_runtime_normalize_nullable_json_v1();

comment on function public.vera_affective_runtime_normalize_nullable_json_v1() is
  'Normalizes JSON null for nullable structured affective fields to SQL NULL so source checkpoint semantics satisfy provider constraints without weakening validation.';

revoke all on function public.vera_affective_runtime_normalize_nullable_json_v1() from public, anon, authenticated;

commit;
