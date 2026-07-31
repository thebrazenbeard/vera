-- Bounded Memory request-durability correction.
--
-- Persists SAVE request identity, a canonical request hash, and the exact
-- database receipt in the same transaction as the canonical append. Exact
-- retries recover the stored receipt without a second canonical mutation.
-- Changed-payload reuse of a request ID fails closed. Version-controlled source
-- only; production application remains separately unauthorized.

begin;

create extension if not exists pgcrypto with schema extensions;

create table public.vera_memory_request_receipts_v3 (
  request_id text primary key,
  operation text not null,
  request_hash text not null,
  receipt_id uuid not null unique,
  record_id uuid not null unique
    references public.vera_context_events_v3(record_id),
  receipt jsonb not null,
  journal_record_time timestamptz not null default clock_timestamp(),
  constraint vera_memory_request_receipts_v3_request_id_chk check (
    request_id = btrim(request_id)
    and request_id <> ''
    and length(request_id) <= 256
    and request_id !~ '[[:cntrl:]]'
  ),
  constraint vera_memory_request_receipts_v3_operation_chk
    check (operation = 'SAVE'),
  constraint vera_memory_request_receipts_v3_hash_chk
    check (request_hash ~ '^[0-9a-f]{64}$'),
  constraint vera_memory_request_receipts_v3_receipt_object_chk
    check (jsonb_typeof(receipt) = 'object'),
  constraint vera_memory_request_receipts_v3_receipt_binding_chk check (
    receipt->>'schema' = 'VERA_MVE_RECEIPT_V3'
    and receipt->>'request_id' = request_id
    and receipt->>'operation' = operation
    and receipt->>'receipt_id' = receipt_id::text
    and receipt->'record_ids' = jsonb_build_array(record_id)
  )
);

alter table public.vera_memory_request_receipts_v3 enable row level security;

create policy vera_memory_request_receipts_v3_no_anon_access
  on public.vera_memory_request_receipts_v3
  for all to anon
  using (false) with check (false);

create policy vera_memory_request_receipts_v3_no_authenticated_access
  on public.vera_memory_request_receipts_v3
  for all to authenticated
  using (false) with check (false);

create or replace function public.block_vera_memory_request_receipt_mutation_v3()
returns trigger
language plpgsql
set search_path = pg_catalog, public
as $$
begin
  raise exception 'vera_memory_request_receipts_v3 is append-only; request receipts may not be updated or deleted';
end;
$$;

drop trigger if exists vera_memory_request_receipts_v3_block_mutation
  on public.vera_memory_request_receipts_v3;
create trigger vera_memory_request_receipts_v3_block_mutation
before update or delete on public.vera_memory_request_receipts_v3
for each row execute function public.block_vera_memory_request_receipt_mutation_v3();

create or replace function public.vera_memory_save_request_hash_v3(
  p_record jsonb
)
returns text
language plpgsql
immutable
set search_path = pg_catalog, public, extensions
as $$
begin
  if p_record is null or jsonb_typeof(p_record) <> 'object' then
    raise exception 'p_record must be a JSON object';
  end if;

  return encode(
    extensions.digest(
      convert_to(
        jsonb_build_object(
          'operation', 'SAVE',
          'record', p_record
        )::text,
        'UTF8'
      ),
      'sha256'
    ),
    'hex'
  );
end;
$$;

-- Preserve the fully validated append implementation as an internal one-shot
-- primitive. Its execute grant is removed below; callers use only the durable
-- wrapper recreated under the original public function name.
alter function public.append_vera_context_v3(text, jsonb)
  rename to append_vera_context_v3_once;

create or replace function public.append_vera_context_v3(
  p_request_id text,
  p_record jsonb
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, extensions
as $$
declare
  normalized_request_id text;
  request_hash_value text;
  existing_hash text;
  existing_receipt jsonb;
  new_receipt jsonb;
  new_receipt_id uuid;
  new_record_id uuid;
begin
  if p_request_id is null then
    raise exception 'p_request_id must be non-empty';
  end if;

  normalized_request_id := btrim(p_request_id);
  if normalized_request_id = ''
     or normalized_request_id <> p_request_id
     or length(normalized_request_id) > 256
     or normalized_request_id ~ '[[:cntrl:]]' then
    raise exception 'p_request_id must be a non-empty canonical identifier without surrounding whitespace or control characters';
  end if;

  request_hash_value := public.vera_memory_save_request_hash_v3(p_record);

  -- The request lock serializes same-ID callers before either checks or mutates
  -- canonical state. Hash collisions can only reduce concurrency; they cannot
  -- permit duplicate writes or changed-payload reuse.
  perform pg_advisory_xact_lock(
    hashtextextended('MEMORY_SAVE' || E'\x1f' || normalized_request_id, 0)
  );

  select request_hash, receipt
    into existing_hash, existing_receipt
  from public.vera_memory_request_receipts_v3
  where request_id = normalized_request_id;

  if found then
    if existing_hash <> request_hash_value then
      raise exception 'MVE_REQUEST_ID_REUSE_CONFLICT: request ID % is already bound to a different SAVE request hash',
        normalized_request_id
        using errcode = '22023';
    end if;

    -- Return the exact committed receipt, including its original receipt_id and
    -- record_time. Recovery does not synthesize a new receipt or mutate memory.
    return existing_receipt;
  end if;

  new_receipt := public.append_vera_context_v3_once(
    normalized_request_id,
    p_record
  );

  new_receipt_id := (new_receipt->>'receipt_id')::uuid;
  new_record_id := (new_receipt#>>'{record_ids,0}')::uuid;

  insert into public.vera_memory_request_receipts_v3 (
    request_id,
    operation,
    request_hash,
    receipt_id,
    record_id,
    receipt
  ) values (
    normalized_request_id,
    'SAVE',
    request_hash_value,
    new_receipt_id,
    new_record_id,
    new_receipt
  );

  return new_receipt;
end;
$$;

revoke all privileges on table public.vera_memory_request_receipts_v3
  from public, anon, authenticated, service_role;
revoke all on function public.block_vera_memory_request_receipt_mutation_v3()
  from public, anon, authenticated, service_role;
revoke all on function public.vera_memory_save_request_hash_v3(jsonb)
  from public, anon, authenticated;
revoke all on function public.append_vera_context_v3_once(text, jsonb)
  from public, anon, authenticated, service_role;
revoke all on function public.append_vera_context_v3(text, jsonb)
  from public, anon, authenticated;

grant execute on function public.append_vera_context_v3(text, jsonb)
  to service_role;

comment on table public.vera_memory_request_receipts_v3 is
  'Append-only SAVE request journal binding one request ID and canonical SHA-256 request hash to the exact committed database receipt and canonical record.';
comment on column public.vera_memory_request_receipts_v3.journal_record_time is
  'Database persistence time of the request-journal row only; not event, state, retrieval, delivery, recollection, or receipt-generation time.';
comment on function public.vera_memory_save_request_hash_v3(jsonb) is
  'Canonical SHA-256 hash of the SAVE operation and caller-supplied JSON record. It is request identity evidence, not semantic equivalence.';
comment on function public.append_vera_context_v3_once(text, jsonb) is
  'Internal one-shot canonical append primitive. Direct service-role execution is revoked; use append_vera_context_v3.';
comment on function public.append_vera_context_v3(text, jsonb) is
  'Durable idempotent SAVE interface. Exact retries recover the stored receipt; changed-payload request-ID reuse fails closed; canonical append and receipt journal commit atomically.';

commit;
