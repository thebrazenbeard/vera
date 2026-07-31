-- Remove only the malformed test fixture after the expected migration refusal.

drop table if exists public.vera_context_events_v3 cascade;
