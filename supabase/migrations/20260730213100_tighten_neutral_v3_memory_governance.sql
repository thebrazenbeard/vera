-- Companion Memory workstream migration.
--
-- Tightens save-time provenance and classification rules after the live baseline
-- was verified to satisfy them. Production application remains separately gated.

begin;

do $$
begin
  if exists (
    select 1
    from public.vera_context_events_v3
    where jsonb_array_length(source_evidence) = 0
  ) then
    raise exception 'neutral V3 baseline contains records without source evidence';
  end if;

  if exists (
    select 1
    from public.vera_context_events_v3
    where semantic_tags = '{}'::jsonb
  ) then
    raise exception 'neutral V3 baseline contains records without semantic tags';
  end if;

  if exists (
    select 1
    from public.vera_context_events_v3
    where privacy_scope not in ('PROJECT', 'PRIVATE', 'TECHNICAL')
  ) then
    raise exception 'neutral V3 baseline contains unsupported privacy scope';
  end if;

  if exists (
    select 1
    from public.vera_context_events_v3
    where source_actor = 'CHATGPT_MODEL'
      and (
        epistemic_status <> 'MODEL_GENERATED_CLAIM'
        or record_type <> 'MODEL_OUTPUT'
      )
  ) then
    raise exception 'neutral V3 baseline misclassifies ChatGPT model output';
  end if;

  if exists (
    select 1
    from public.vera_context_events_v3
    where record_type = 'MODEL_OUTPUT'
      and epistemic_status <> 'MODEL_GENERATED_CLAIM'
  ) then
    raise exception 'neutral V3 baseline promotes model output beyond MODEL_GENERATED_CLAIM';
  end if;
end;
$$;

do $$
begin
  if not exists (
    select 1 from pg_constraint
    where conrelid = 'public.vera_context_events_v3'::regclass
      and conname = 'vera_context_events_v3_source_evidence_nonempty_chk'
  ) then
    alter table public.vera_context_events_v3
      add constraint vera_context_events_v3_source_evidence_nonempty_chk
      check (jsonb_array_length(source_evidence) > 0);
  end if;

  if not exists (
    select 1 from pg_constraint
    where conrelid = 'public.vera_context_events_v3'::regclass
      and conname = 'vera_context_events_v3_semantic_tags_nonempty_chk'
  ) then
    alter table public.vera_context_events_v3
      add constraint vera_context_events_v3_semantic_tags_nonempty_chk
      check (semantic_tags <> '{}'::jsonb);
  end if;

  if not exists (
    select 1 from pg_constraint
    where conrelid = 'public.vera_context_events_v3'::regclass
      and conname = 'vera_context_events_v3_privacy_scope_chk'
  ) then
    alter table public.vera_context_events_v3
      add constraint vera_context_events_v3_privacy_scope_chk
      check (privacy_scope in ('PROJECT', 'PRIVATE', 'TECHNICAL'));
  end if;

  if not exists (
    select 1 from pg_constraint
    where conrelid = 'public.vera_context_events_v3'::regclass
      and conname = 'vera_context_events_v3_model_actor_classification_chk'
  ) then
    alter table public.vera_context_events_v3
      add constraint vera_context_events_v3_model_actor_classification_chk
      check (
        source_actor <> 'CHATGPT_MODEL'
        or (
          epistemic_status = 'MODEL_GENERATED_CLAIM'
          and record_type = 'MODEL_OUTPUT'
        )
      );
  end if;

  if not exists (
    select 1 from pg_constraint
    where conrelid = 'public.vera_context_events_v3'::regclass
      and conname = 'vera_context_events_v3_model_output_epistemic_chk'
  ) then
    alter table public.vera_context_events_v3
      add constraint vera_context_events_v3_model_output_epistemic_chk
      check (
        record_type <> 'MODEL_OUTPUT'
        or epistemic_status = 'MODEL_GENERATED_CLAIM'
      );
  end if;
end;
$$;

comment on constraint vera_context_events_v3_source_evidence_nonempty_chk
  on public.vera_context_events_v3 is
  'Every neutral V3 memory record must retain at least one source-evidence entry.';
comment on constraint vera_context_events_v3_semantic_tags_nonempty_chk
  on public.vera_context_events_v3 is
  'Every neutral V3 memory record must retain a non-empty semantic index object.';
comment on constraint vera_context_events_v3_privacy_scope_chk
  on public.vera_context_events_v3 is
  'Memory privacy scope is explicitly bounded to PROJECT, PRIVATE, or TECHNICAL.';
comment on constraint vera_context_events_v3_model_actor_classification_chk
  on public.vera_context_events_v3 is
  'ChatGPT-authored content is stored only as MODEL_OUTPUT with MODEL_GENERATED_CLAIM epistemic status.';
comment on constraint vera_context_events_v3_model_output_epistemic_chk
  on public.vera_context_events_v3 is
  'MODEL_OUTPUT cannot be promoted beyond MODEL_GENERATED_CLAIM through record insertion.';

commit;
