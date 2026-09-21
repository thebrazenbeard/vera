create or replace function public.block_vera_save_state_mutation()
returns trigger
language plpgsql
set search_path = pg_catalog, public
as $$
begin
  raise exception 'vera_save_state_events is append-only; write a superseding record instead';
end;
$$;

revoke all on function public.block_vera_save_state_mutation() from public;
revoke all on function public.block_vera_save_state_mutation() from anon;
revoke all on function public.block_vera_save_state_mutation() from authenticated;
