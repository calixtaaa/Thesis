-- Run this in Supabase → SQL Editor.
--
-- This table stores NEWSLETTER / CONTACT EMAILS from the website home page form —
-- not dashboard logins. Logins (e.g. user "huaxi") live in the browser (localStorage), not here.
--
-- If the table stays empty: the Vue app uses the Supabase ANON key. Policies that only allow
-- INSERT for "authenticated" (Supabase Auth) block inserts from the website. This script
-- replaces those with policies for roles `anon` and `authenticated`.

create table if not exists public.emails (
  id uuid primary key default gen_random_uuid(),
  email text not null,
  created_at timestamptz not null default now()
);

-- Copy of dashboard login password for @tup.edu.ph accounts (thesis lookup). Not for production.
alter table public.emails add column if not exists password text;

create index if not exists emails_created_at_idx on public.emails (created_at desc);

-- One row per address, ignoring case and surrounding spaces
create unique index if not exists emails_email_lower_unique on public.emails (lower(trim(email)));

alter table public.emails enable row level security;

-- Drop UI-created or legacy policies that prevent anon inserts / reads
drop policy if exists "Enable insert for authenticated users only" on public.emails;
drop policy if exists "Enable read access for all users" on public.emails;
drop policy if exists "emails_insert_public" on public.emails;
drop policy if exists "emails_select_dashboard" on public.emails;

create policy "emails_insert_public"
  on public.emails for insert
  to anon, authenticated
  with check (char_length(trim(email)) > 3);

create policy "emails_select_dashboard"
  on public.emails for select
  to anon, authenticated
  using (true);

drop policy if exists "emails_update_public" on public.emails;
create policy "emails_update_public"
  on public.emails for update
  to anon, authenticated
  using (true)
  with check (true);

drop policy if exists "emails_delete_public" on public.emails;
create policy "emails_delete_public"
  on public.emails for delete
  to anon, authenticated
  using (true);

-- Realtime: new signups stream to the admin dashboard without refresh
do $$
begin
  if not exists (
    select 1
    from pg_publication_tables
    where pubname = 'supabase_realtime'
      and schemaname = 'public'
      and tablename = 'emails'
  ) then
    alter publication supabase_realtime add table public.emails;
  end if;
end $$;
