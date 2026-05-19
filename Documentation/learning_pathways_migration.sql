-- Migration: learning_pathways
-- For the Deep Researcher agent (backend/app/deep_researcher).
-- Apply via Supabase MCP `apply_migration` or `execute_sql`.
--
-- v1 design: a single row per (user_id, role_slug). Pathway and sources
-- live in JSONB so we can iterate on the Pydantic schema without ALTERs.
-- Normalize into pathway_milestones / pathway_resources only when the
-- frontend needs joins or partial updates.

create table if not exists learning_pathways (
  id               uuid primary key default gen_random_uuid(),
  user_id          uuid not null references auth.users(id) on delete cascade,
  role_slug        text not null,
  target_role      text not null,
  pathway          jsonb not null,
  sources          jsonb not null default '[]'::jsonb,
  iterations_used  int  not null default 0,
  created_at       timestamptz not null default now(),
  unique (user_id, role_slug)
);

create index if not exists learning_pathways_user_role_created_idx
  on learning_pathways (user_id, role_slug, created_at desc);

alter table learning_pathways enable row level security;

drop policy if exists "own pathways" on learning_pathways;
create policy "own pathways"
  on learning_pathways
  for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);
