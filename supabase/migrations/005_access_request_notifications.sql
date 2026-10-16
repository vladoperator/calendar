-- Run after 004. Configure denta_access_request_url and
-- denta_access_request_token in Supabase Vault before enabling notifications.
begin;

create extension if not exists pg_net with schema extensions;

create or replace function public.notify_clinic_access_request()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
  endpoint text;
  webhook_token text;
begin
  select decrypted_secret into endpoint
  from vault.decrypted_secrets where name = 'denta_access_request_url';
  select decrypted_secret into webhook_token
  from vault.decrypted_secrets where name = 'denta_access_request_token';

  if endpoint is null or webhook_token is null then
    raise warning 'Registration notification skipped: configure the Vault settings.';
    return new;
  end if;

  perform net.http_post(
    url := endpoint,
    headers := jsonb_build_object(
      'Content-Type', 'application/json',
      'Authorization', 'Bearer ' || webhook_token
    ),
    body := jsonb_build_object(
      'type', 'INSERT', 'schema', 'public', 'table', 'clinic_users',
      'record', jsonb_build_object(
        'id', new.id, 'email', new.email, 'approved', new.approved
      )
    ),
    timeout_milliseconds := 10000
  );
  return new;
exception when others then
  -- Notification problems must not prevent account creation. Do not log secrets.
  raise warning 'Registration notification could not be queued (SQLSTATE %).', sqlstate;
  return new;
end;
$$;

revoke all on function public.notify_clinic_access_request() from public, anon, authenticated;

drop trigger if exists on_clinic_access_requested on public.clinic_users;
create trigger on_clinic_access_requested
  after insert on public.clinic_users
  for each row when (new.approved = false)
  execute function public.notify_clinic_access_request();

commit;
