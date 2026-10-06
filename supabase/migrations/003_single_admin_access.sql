-- Lock the clinic to its administrator only.
-- Run after 001_clinic_state.sql and 002_team_access.sql.

drop policy if exists "clinic_state_read_approved" on public.clinic_state;
drop policy if exists "clinic_state_update_approved" on public.clinic_state;

create policy "clinic_state_read_admin" on public.clinic_state
  for select to authenticated using ((select public.is_clinic_admin()));

create policy "clinic_state_update_admin" on public.clinic_state
  for update to authenticated using ((select public.is_clinic_admin()))
  with check ((select public.is_clinic_admin()));
