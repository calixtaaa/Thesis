-- Run in Supabase → SQL Editor.
--
-- Why live_feed looks empty: nothing has INSERTed rows yet. This script:
--   (A) adds a few demo rows so the admin dashboard shows data immediately
--   (B) optionally attaches a trigger so each new row in `transactions` also appends to `live_feed`

-- ---------- (A) Seed rows (safe to delete later) ----------
insert into public.live_feed (event_type, message, payload)
values
  ('info', 'Feed ready — connect the machine or insert transactions to see sales here.', '{"source":"seed"}'::jsonb),
  ('test', 'Sample event (you may delete seed rows anytime)', '{"demo":true}'::jsonb),
  ('machine', 'Example: restock slot 2 completed', '{"slot":2,"action":"restock"}'::jsonb);

-- ---------- (B) Auto-append feed line when a sale is inserted into `transactions` ----------
-- Adjust column names if your table differs (check Table Editor → Definition).

create or replace function public.tr_append_live_feed_from_transaction()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
  msg text;
begin
  msg :=
    'Sale: ' ||
    coalesce(nullif(trim(new.product_name::text), ''), 'Product #' || coalesce(new.product_id::text, '?')) ||
    ' · slot ' || coalesce(new.slot_number::text, '?') ||
    ' · ₱' || coalesce(new.total_amount::text, '0');

  insert into public.live_feed (event_type, message, quantity, total_amount, payload)
  values (
    'sale',
    msg,
    new.quantity,
    new.total_amount,
    jsonb_strip_nulls(
      jsonb_build_object(
        'transaction_id', new.id,
        'product_id', new.product_id,
        'product_name', new.product_name,
        'slot_number', new.slot_number,
        'quantity', new.quantity,
        'total_amount', new.total_amount
      )
    )
  );

  return new;
end;
$$;

drop trigger if exists tr_transactions_append_live_feed on public.transactions;

create trigger tr_transactions_append_live_feed
  after insert on public.transactions
  for each row
  execute function public.tr_append_live_feed_from_transaction();

-- Note: new INSERTs into `transactions` (from your Pi/sync) will populate `live_feed` automatically.
-- Existing old transaction rows are not backfilled — only new sales after this trigger exists.
