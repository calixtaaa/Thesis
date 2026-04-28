-- Run in Supabase → SQL Editor.
-- Sets product capacity (total slots/stock per product) based on your final machine layout.
-- Safe to re-run; it only updates matching product names.

-- Tip: If some names don't match your `products.name` exactly, adjust the WHERE clauses.

update public.products set capacity = 3
where lower(name) in ('alcohol');

update public.products set capacity = 7
where lower(name) in ('soap');

update public.products set capacity = 9
where lower(name) in ('deo', 'deodorant');

update public.products set capacity = 7
where lower(name) in ('mouth wash', 'mouthwash');

update public.products set capacity = 3
where lower(name) in ('wipes', 'wet wipes', 'wetwipes');

update public.products set capacity = 3
where lower(name) in ('tissue', 'tissues');

update public.products set capacity = 8
where lower(name) in ('panti liner', 'panty liner', 'panty liners', 'pantyliners');

update public.products set capacity = 6
where lower(name) in ('all night pads', 'all-night pads');

update public.products set capacity = 7
where lower(name) in ('regular with wings', 'regular w/ wings pads', 'regular with wings pads');

update public.products set capacity = 7
where lower(name) in ('non wing pad', 'non-wing pads', 'non wing pads', 'non-wing pad');

-- Optional: normalize any over-cap stock down to capacity
update public.products
set current_stock = capacity
where capacity is not null and current_stock > capacity;

