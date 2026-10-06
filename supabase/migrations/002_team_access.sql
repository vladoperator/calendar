-- Controlul accesului pentru echipa clinicii.
-- Rulează după 001_clinic_state.sql, o singură dată, în Supabase SQL Editor.

create table if not exists public.clinic_users (
  id uuid primary key references auth.users(id) on delete cascade,
  email text not null,
  role text not null default 'staff' check (role in ('admin', 'staff')),
  approved boolean not null default false,
  created_at timestamptz not null default now()
);

alter table public.clinic_users enable row level security;

create or replace function public.create_clinic_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
  first_account boolean;
begin
  select not exists (select 1 from public.clinic_users) into first_account;
  insert into public.clinic_users (id, email, role, approved)
  values (
    new.id,
    coalesce(new.email, ''),
    case when first_account then 'admin' else 'staff' end,
    first_account
  );
  return new;
end;
$$;

drop trigger if exists on_auth_user_created_for_clinic on auth.users;
create trigger on_auth_user_created_for_clinic
  after insert on auth.users
  for each row execute procedure public.create_clinic_user();

-- Conturile existente sunt preluate; primul devine administrator.
insert into public.clinic_users (id, email, role, approved)
select id, coalesce(email, ''), 'staff', false from auth.users
on conflict (id) do nothing;

with first_user as (
  select id from public.clinic_users order by created_at asc, id asc limit 1
)
update public.clinic_users
set role = 'admin', approved = true
where id in (select id from first_user)
  and not exists (select 1 from public.clinic_users where role = 'admin');

create or replace function public.is_clinic_admin()
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists (
    select 1 from public.clinic_users
    where id = auth.uid() and role = 'admin' and approved = true
  );
$$;

create or replace function public.is_clinic_approved()
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists (
    select 1 from public.clinic_users
    where id = auth.uid() and approved = true
  );
$$;

drop policy if exists "clinic_users_read_self_or_admin" on public.clinic_users;
create policy "clinic_users_read_self_or_admin" on public.clinic_users
  for select to authenticated
  using (id = (select auth.uid()) or (select public.is_clinic_admin()));

drop policy if exists "clinic_users_admin_update" on public.clinic_users;
create policy "clinic_users_admin_update" on public.clinic_users
  for update to authenticated
  using ((select public.is_clinic_admin()))
  with check ((select public.is_clinic_admin()));

-- Un singur spațiu de lucru comun pentru toți membrii aprobați ai clinicii.
drop policy if exists "clinic_state_select_own" on public.clinic_state;
drop policy if exists "clinic_state_insert_own" on public.clinic_state;
drop policy if exists "clinic_state_update_own" on public.clinic_state;
drop policy if exists "clinic_state_delete_own" on public.clinic_state;

create policy "clinic_state_read_approved" on public.clinic_state
  for select to authenticated using ((select public.is_clinic_approved()));

create policy "clinic_state_insert_admin" on public.clinic_state
  for insert to authenticated with check ((select public.is_clinic_admin()));

create policy "clinic_state_update_approved" on public.clinic_state
  for update to authenticated using ((select public.is_clinic_approved()))
  with check ((select public.is_clinic_approved()));

create policy "clinic_state_delete_admin" on public.clinic_state
  for delete to authenticated using ((select public.is_clinic_admin()));
