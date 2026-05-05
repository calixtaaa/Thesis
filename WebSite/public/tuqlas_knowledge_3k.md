Smart Hygiene Vending Machine (TUP Manila – BET Computer Engineering Tech).
Adviser: Prof. Gemma D. Belga - Robles.
Members: Asriel Romulo (Leader), Jonamae Tiu (Papers), Zharie Ann R. Valero (Papers), John Renzo G. Dacer (Lead UX/UI), Gideon Soberano (Lead Programmer), Jose Angelo F. Lacerna (Lead Programmer).

Overview: Hygiene-products vending machine + Admin Dashboard website. Machine runs Python and stores inventory/sales in SQLite (`vending.db`). Website is Vue/Vite and reads from Supabase. Optional bridge syncs `products`, `transactions`, and events so the dashboard can update realtime/near-realtime. Security: never expose Supabase service_role key in the website.

Products (slot • item • price • capacity):
1 Alcohol ₱25 cap3; 2 Soap ₱5 cap7; 3 Deodorant/Deo ₱10 cap8; 4 Mouthwash ₱8 cap7; 5 Wet Wipes ₱18 cap3;
6 Tissues ₱8 cap3; 7 All Night Pads ₱10 cap5; 8 Panty Liners ₱5 cap6; 9 Regular w/ Wings ₱7 cap5; 10 Non‑Wing Pads ₱7 cap5.

Low-stock thresholds (≤ = Low): Alcohol 1, Soap 3, Deodorant 3, Mouthwash 3, Wet Wipes 1, Tissue 1, Panty Liner 3, All Night Pads 2, Regular w/ Wings 3, Non‑Wing 3.
Status: Full if stock≥capacity; In Stock if threshold<stock<capacity; Low if 0<stock≤threshold; Empty if stock≤0.

Buying flow: select product → pay (coin acceptor) → dispense → record sale in `transactions` → update `products.current_stock` (normal mode).
After a synced purchase, dashboard should show: new Recent Transaction row, charts update, Live feed entry, and stock decrease (unless demo/full-stock mode is enabled).

Demo/full-stock mode: can force all stocks to full (current_stock=capacity) for thesis presentation. Transactions still record. This does not change RFID/GPIO/Coin logic—only inventory counts.

Dashboard data (Supabase): `public.products`, `public.transactions`, `public.live_feed`, `public.bug_reports`. Live feed may merge sales/events; duplicates should be avoided. Sidebar badges: Live feed badge counts unseen new events; Reports badge counts new OPEN bug reports; opening the page clears the badge.

Troubleshooting:
- Website stale: bridge not running or realtime not enabled → restart bridge; enable realtime publication for tables.
- Live feed empty: ensure `live_feed` exists + realtime-enabled; ensure new transactions/events are inserted to Supabase.
- Reports badge missing: ensure there are OPEN bug reports and the dashboard is updating; reload if needed.

