-- Run ONLY if the website shows empty products/transactions and Supabase logs show RLS blocking SELECT.
-- Adjust if you already use stricter policies.

alter table if exists public.products enable row level security;
alter table if exists public.transactions enable row level security;

drop policy if exists "products_select_dashboard" on public.products;
create policy "products_select_dashboard"
  on public.products for select
  to anon, authenticated
  using (true);

drop policy if exists "transactions_select_dashboard" on public.transactions;
create policy "transactions_select_dashboard"
  on public.transactions for select
  to anon, authenticated
  using (true);

-- Writers (machine / edge functions) often use service_role. If your Pi inserts with the anon key, add INSERT policies separately.
