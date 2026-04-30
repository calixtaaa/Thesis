-- Run in Supabase → SQL Editor.
-- Creates a config table for capacity + low-stock thresholds, a REAL table for low-stock products,
-- and an optional trigger to decrement `products.current_stock` whenever a sale is INSERTed into `transactions`.
--
-- IMPORTANT:
-- - Supabase Realtime publications DO NOT support views.
-- - This script uses a TABLE (`public.low_stock_products`) so you can toggle Realtime for it.

-- ---------- 1) Config table (source of truth for capacity + low stock thresholds) ----------
create table if not exists public.product_stock_rules (
  product_key text primary key,
  display_name text not null,
  capacity integer not null check (capacity > 0),
  low_threshold integer not null check (low_threshold >= 0)
);

insert into public.product_stock_rules (product_key, display_name, capacity, low_threshold)
values
  ('alcohol', 'Alcohol', 3, 1),
  ('soap', 'Soap', 7, 3),
  ('deodorant', 'Deodorant', 9, 3),
  ('mouthwash', 'Mouthwash', 7, 3),
  ('wet_wipes', 'Wet Wipes', 3, 1),
  ('tissue', 'Tissue', 3, 1),
  ('panty_liner', 'Panty Liner', 8, 3),
  ('all_night_pads', 'All Night Pads', 6, 2),
  ('regular_with_wings', 'Regular with Wings', 7, 3),
  ('non_wing_pad', 'Non Wings Pad', 7, 3)
on conflict (product_key) do update set
  display_name = excluded.display_name,
  capacity = excluded.capacity,
  low_threshold = excluded.low_threshold;

-- Realtime (optional): replicate changes if you want to watch rule edits live
do $$
begin
  if not exists (
    select 1 from pg_publication_tables
    where pubname = 'supabase_realtime' and schemaname = 'public' and tablename = 'product_stock_rules'
  ) then
    alter publication supabase_realtime add table public.product_stock_rules;
  end if;
end $$;

-- Ensure underlying tables are in Realtime publication (safe to re-run).
-- (These are tables, so supported.)
do $$
begin
  if not exists (
    select 1 from pg_publication_tables
    where pubname = 'supabase_realtime' and schemaname = 'public' and tablename = 'products'
  ) then
    alter publication supabase_realtime add table public.products;
  end if;
  if not exists (
    select 1 from pg_publication_tables
    where pubname = 'supabase_realtime' and schemaname = 'public' and tablename = 'transactions'
  ) then
    alter publication supabase_realtime add table public.transactions;
  end if;
end $$;

-- ---------- 2) Normalize product names to keys (handles plural/variants) ----------
create or replace function public.product_key_from_name(raw text)
returns text
language sql
immutable
as $$
  with n as (
    select trim(regexp_replace(lower(coalesce(raw, '')), '[^a-z0-9]+', ' ', 'g')) as v
  )
  select
    case
      when (select v from n) = 'alcohol' then 'alcohol'
      when (select v from n) = 'soap' then 'soap'
      when (select v from n) in ('deodorant', 'deo') then 'deodorant'
      when (select v from n) in ('mouthwash', 'mouth wash') then 'mouthwash'
      when (select v from n) in ('wet wipes', 'wetwipes', 'wipes') then 'wet_wipes'
      when (select v from n) in ('tissue', 'tissues') then 'tissue'
      when (select v from n) in ('panty liner', 'panty liners', 'pantyliners', 'panti liner') then 'panty_liner'
      when (select v from n) in ('all night pads', 'all night pad', 'all nightpads') then 'all_night_pads'
      when (select v from n) in ('regular with wings', 'regular with wings pads', 'regular w wings pads') then 'regular_with_wings'
      when (select v from n) in ('non wing pad', 'non wing pads', 'non wings pad', 'non wings pads') then 'non_wing_pad'

      -- fuzzy fallbacks
      when (select v from n) like '%panty%liner%' then 'panty_liner'
      when (select v from n) like '%all%night%pad%' then 'all_night_pads'
      when (select v from n) like '%mouth%wash%' then 'mouthwash'
      when (select v from n) like '%wet%wipe%' then 'wet_wipes'
      when (select v from n) like '%tissue%' then 'tissue'
      when (select v from n) like '%deodor%' then 'deodorant'
      when (select v from n) like '%regular%wing%' then 'regular_with_wings'
      when (select v from n) like '%non%wing%pad%' then 'non_wing_pad'
      else ''
    end;
$$;

-- ---------- 3) View: low-stock products (joins products with rules) ----------
-- ---------- 3) Table: low-stock products (materialized + kept fresh by triggers) ----------
drop view if exists public.low_stock_products;

create table if not exists public.low_stock_products (
  product_id bigint primary key,
  slot_number integer,
  name text,
  price numeric,
  current_stock integer,
  capacity integer,
  low_threshold integer,
  ratio numeric,
  status text,
  updated_at timestamptz not null default now()
);

create index if not exists low_stock_products_slot_idx on public.low_stock_products (slot_number);

create or replace function public.refresh_low_stock_products()
returns void
language plpgsql
security definer
set search_path = public
as $$
begin
  -- Upsert ALL products with computed status
  insert into public.low_stock_products (
    product_id, slot_number, name, price, current_stock, capacity, low_threshold, ratio, status, updated_at
  )
  select
    p.id as product_id,
    p.slot_number,
    p.name,
    p.price,
    p.current_stock,
    r.capacity,
    r.low_threshold,
    (p.current_stock::numeric / nullif(r.capacity, 0)) as ratio,
    case
      when p.current_stock <= 0 then 'Empty'
      when p.current_stock <= r.low_threshold then 'Low'
      when p.current_stock >= r.capacity then 'Full'
      else 'In Stock'
    end as status,
    now() as updated_at
  from public.products p
  join public.product_stock_rules r
    on r.product_key = public.product_key_from_name(p.name)
  on conflict (product_id) do update set
    slot_number = excluded.slot_number,
    name = excluded.name,
    price = excluded.price,
    current_stock = excluded.current_stock,
    capacity = excluded.capacity,
    low_threshold = excluded.low_threshold,
    ratio = excluded.ratio,
    status = excluded.status,
    updated_at = excluded.updated_at;

  -- Remove rows that no longer have a matching source product/rule
  delete from public.low_stock_products l
  where not exists (
    select 1
    from public.products p
    join public.product_stock_rules r
      on r.product_key = public.product_key_from_name(p.name)
    where p.id = l.product_id
  );
end;
$$;

-- Trigger wrapper (so we can attach to multiple tables)
create or replace function public.tr_refresh_low_stock_products()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  perform public.refresh_low_stock_products();
  return null;
end;
$$;

drop trigger if exists tr_products_refresh_low_stock on public.products;
create trigger tr_products_refresh_low_stock
  after insert or update or delete on public.products
  for each statement
  execute function public.tr_refresh_low_stock_products();

drop trigger if exists tr_rules_refresh_low_stock on public.product_stock_rules;
create trigger tr_rules_refresh_low_stock
  after insert or update or delete on public.product_stock_rules
  for each statement
  execute function public.tr_refresh_low_stock_products();

-- Initial build
select public.refresh_low_stock_products();

-- Realtime: now you CAN toggle realtime for this table
do $$
begin
  if not exists (
    select 1 from pg_publication_tables
    where pubname = 'supabase_realtime' and schemaname = 'public' and tablename = 'low_stock_products'
  ) then
    alter publication supabase_realtime add table public.low_stock_products;
  end if;
end $$;

-- ---------- 4) OPTIONAL: decrement stock automatically when a transaction is inserted ----------
-- This is the common reason you "buy alcohol but the stock stays the same":
-- inserting into `transactions` does NOT automatically update `products.current_stock` unless you add a trigger.
create or replace function public.tr_decrement_stock_on_transaction()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
  qty int := greatest(coalesce(new.quantity, 1), 1);
begin
  -- Prefer product_id, then slot_number, then product_name
  update public.products p
  set current_stock = greatest(p.current_stock - qty, 0),
      updated_at = now()
  where (new.product_id is not null and p.id = new.product_id)
     or (new.product_id is null and new.slot_number is not null and p.slot_number = new.slot_number)
     or (new.product_id is null and new.slot_number is null and new.product_name is not null and lower(p.name) = lower(new.product_name));

  return new;
end;
$$;

drop trigger if exists tr_transactions_decrement_stock on public.transactions;
create trigger tr_transactions_decrement_stock
  after insert on public.transactions
  for each row
  execute function public.tr_decrement_stock_on_transaction();

-- ---------- 5) (Recommended) One-time data cleanup if old stocks exceed real capacity ----------
-- clamps current_stock down to your configured capacity
update public.products p
set current_stock = least(p.current_stock, r.capacity),
    updated_at = now()
from public.product_stock_rules r
where r.product_key = public.product_key_from_name(p.name)
  and p.current_stock > r.capacity;

