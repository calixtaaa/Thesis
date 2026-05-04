Smart Hygiene Vending Machine (TUP Manila – BET Computer Engineering Tech).
Adviser: Prof. Gemma D. Belga - Robles.
Members: Asriel Romulo (Leader), Jonamae Tiu (Papers), Zharie Ann R. Valero (Papers), John Renzo G. Dacer (Lead UX/UI), Gideon Soberano (Lead Programmer), Jose Angelo F. Lacerna (Lead Programmer).

System: Machine app (Python + SQLite `vending.db`) + Admin Dashboard (Vue/Vite) using Supabase. Optional bridge syncs `products`, `transactions`, and events for realtime dashboard updates. Security: never expose Supabase service_role key in the website.

Products (slot • item • price • capacity):
1 Alcohol ₱25 cap3
2 Soap ₱5 cap7
3 Deodorant/Deo ₱10 cap8
4 Mouthwash ₱8 cap7
5 Tissues ₱8 cap3
6 Wet Wipes ₱18 cap3
7 Panty Liners ₱5 cap6
8 All Night Pads ₱10 cap5
9 Regular w/ Wings ₱7 cap5
10 Non‑Wing Pads ₱7 cap5

Low-stock thresholds (≤ = Low): Alcohol 1, Soap 3, Deodorant 3, Mouthwash 3, Wet Wipes 1, Tissue 1, Panty Liner 3, All Night Pads 2, Regular w/ Wings 3, Non‑Wing 3. Status: Full if stock≥capacity; Empty if stock≤0.

Buying flow: select product → pay (coin acceptor) → dispense → record `transactions` → update `products.current_stock` (normal mode). Website should show new Recent Transaction, updated charts, and a live feed entry (if synced).

Demo/full-stock mode: stocks can be forced to full (current_stock=capacity) for thesis presentation. Transactions still record, but inventory may not decrease. This does not change RFID/GPIO/Coin logic—only inventory counts.

Dashboard data (Supabase): `public.products`, `public.transactions`, `public.live_feed`, `public.bug_reports`. Live feed merges sales and events; duplicates are avoided when possible. Sidebar badges: Live feed badge counts unseen new events; Reports badge counts new OPEN bug reports; opening the page clears the badge.

Troubleshooting: website stale → restart bridge / enable realtime; live feed empty → ensure `live_feed` exists + realtime; reports badge missing → ensure OPEN bug reports and dashboard updating.

