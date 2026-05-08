-- Run in Supabase → SQL Editor.
-- Updates `public.products.slot_number` to match the latest physical tray layout.
--
-- Layout (1..10):
-- 1 Soap, 2 Alcohol, 3 Deodorant, 4 Mouthwash, 5 Wet Wipes,
-- 6 Tissues, 7 All Night Pads, 8 Panty Liners, 9 Regular w/o Wings, 10 Regular w/ Wings.
--
-- Notes:
-- - This script is UNIQUE-safe (handles slot_number unique constraint) by moving rows off 1..10 first.
-- - If you haven't installed `product_key_from_name` yet, run `supabase/low_stock_products_setup.sql` first,
--   or replace the matching logic below with exact `lower(name)` matches.

do $$
declare
  r record;
begin
  -- Phase 1: move known products off 1..10 to avoid UNIQUE collisions
  for r in
    select id
    from public.products
    where public.product_key_from_name(name) in (
      'soap',
      'alcohol',
      'mouthwash',
      'deodorant',
      'wet_wipes',
      'tissue',
      'all_night_pads',
      'panty_liner',
      'non_wing_pad',
      'regular_with_wings'
    )
  loop
    update public.products
    set slot_number = 1000 + r.id
    where id = r.id;
  end loop;

  -- Phase 2: set final canonical slots
  update public.products set slot_number = 1 where public.product_key_from_name(name) = 'soap';
  update public.products set slot_number = 2 where public.product_key_from_name(name) = 'alcohol';
  update public.products set slot_number = 3 where public.product_key_from_name(name) = 'deodorant';
  update public.products set slot_number = 4 where public.product_key_from_name(name) = 'mouthwash';
  update public.products set slot_number = 5 where public.product_key_from_name(name) = 'wet_wipes';
  update public.products set slot_number = 6 where public.product_key_from_name(name) = 'tissue';
  update public.products set slot_number = 7 where public.product_key_from_name(name) = 'all_night_pads';
  update public.products set slot_number = 8 where public.product_key_from_name(name) = 'panty_liner';
  update public.products set slot_number = 9 where public.product_key_from_name(name) = 'non_wing_pad';
  update public.products set slot_number = 10 where public.product_key_from_name(name) = 'regular_with_wings';
end $$;

