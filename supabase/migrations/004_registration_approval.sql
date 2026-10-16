-- Run after 003_single_admin_access.sql. New accounts require admin approval.
begin;

-- Public registration must never give administrator rights to the first visitor.
-- Only the confirmed approval mailbox can bootstrap an administrator account.
-- Existing administrators are retained to avoid locking out the clinic.
create or replace function public.create_clinic_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
  is_owner boolean;
begin
  is_owner := lower(coalesce(new.email, '')) = 'chathot000@gmail.com'
    and new.email_confirmed_at is not null;
  insert into public.clinic_users (id, email, role, approved)
  values (new.id, coalesce(new.email, ''),
    case when is_owner then 'admin' else 'staff' end, is_owner);
  return new;
end;
$$;

create or replace function public.confirm_clinic_owner()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  if lower(coalesce(new.email, '')) = 'chathot000@gmail.com'
     and new.email_confirmed_at is not null then
    update public.clinic_users set role = 'admin', approved = true
    where id = new.id;
  end if;
  return new;
end;
$$;

drop trigger if exists on_clinic_owner_confirmed on auth.users;
create trigger on_clinic_owner_confirmed
  after update of email_confirmed_at on auth.users
  for each row execute function public.confirm_clinic_owner();

update public.clinic_users as profile set role = 'admin', approved = true
from auth.users as account
where profile.id = account.id
  and lower(account.email) = 'chathot000@gmail.com'
  and account.email_confirmed_at is not null;

-- Restore team access after migration 003's administrator-only policies.
drop policy if exists "clinic_state_read_admin" on public.clinic_state;
drop policy if exists "clinic_state_update_admin" on public.clinic_state;
drop policy if exists "clinic_state_read_approved" on public.clinic_state;
drop policy if exists "clinic_state_update_approved" on public.clinic_state;

create policy "clinic_state_read_approved" on public.clinic_state
  for select to authenticated using ((select public.is_clinic_approved()));
create policy "clinic_state_update_approved" on public.clinic_state
  for update to authenticated using ((select public.is_clinic_approved()))
  with check ((select public.is_clinic_approved()));

-- INSERT/DELETE of clinic data and approval of users remain admin-only (002).
commit;
