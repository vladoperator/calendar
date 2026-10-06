-- Rulează o singură dată în Supabase: SQL Editor > New query > Run.
-- Fiecare cont vede şi modifică doar datele propriei clinici.
create table if not exists public.clinic_state (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  data jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (owner_id)
);

alter table public.clinic_state enable row level security;

drop policy if exists "clinic_state_select_own" on public.clinic_state;
create policy "clinic_state_select_own" on public.clinic_state
  for select to authenticated using ((select auth.uid()) = owner_id);

drop policy if exists "clinic_state_insert_own" on public.clinic_state;
create policy "clinic_state_insert_own" on public.clinic_state
  for insert to authenticated with check ((select auth.uid()) = owner_id);

drop policy if exists "clinic_state_update_own" on public.clinic_state;
create policy "clinic_state_update_own" on public.clinic_state
  for update to authenticated using ((select auth.uid()) = owner_id)
  with check ((select auth.uid()) = owner_id);

drop policy if exists "clinic_state_delete_own" on public.clinic_state;
create policy "clinic_state_delete_own" on public.clinic_state
  for delete to authenticated using ((select auth.uid()) = owner_id);

create or replace function public.set_clinic_state_updated_at()
returns trigger language plpgsql security invoker set search_path = '' as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists clinic_state_updated_at on public.clinic_state;
create trigger clinic_state_updated_at
  before update on public.clinic_state
  for each row execute function public.set_clinic_state_updated_at();
