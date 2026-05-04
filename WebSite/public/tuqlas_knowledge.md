Smart Hygiene Vending Machine (TUP Manila – BET Computer Engineering Tech).
Adviser: Prof. Gemma D. Belga - Robles.
Members: Asriel Romulo (Leader), Jonamae Tiu (Papers), Zharie Ann R. Valero (Papers), John Renzo G. Dacer (Lead UX/UI), Gideon Soberano (Lead Programmer), Jose Angelo F. Lacerna (Lead Programmer).

Overview: Hygiene-products vending machine + Admin Dashboard website. Machine runs Python and stores inventory/sales in SQLite (`vending.db`). Website is Vue/Vite and reads from Supabase. Optional bridge syncs `products`, `transactions`, and events so the dashboard can update realtime/near-realtime. Security: never expose Supabase service_role key in the website.

Products (slot • item • price • capacity):
1 Alcohol ₱25 cap3; 2 Soap ₱5 cap7; 3 Deodorant/Deo ₱10 cap8; 4 Mouthwash ₱8 cap7; 5 Tissues ₱8 cap3;
6 Wet Wipes ₱18 cap3; 7 Panty Liners ₱5 cap6; 8 All Night Pads ₱10 cap5; 9 Regular w/ Wings ₱7 cap5; 10 Non‑Wing Pads ₱7 cap5.

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

Smart Hygiene Vending Machine (TUP Manila – BET Computer Engineering Tech).
Adviser: Prof. Gemma D. Belga - Robles.
Members: Asriel Romulo (Leader), Jonamae Tiu (Papers), Zharie Ann R. Valero (Papers), John Renzo G. Dacer (Lead UX/UI), Gideon Soberano (Lead Programmer), Jose Angelo F. Lacerna (Lead Programmer).

Overview: This project is a hygiene-products vending machine with an Admin Dashboard website. The machine runs a Python app and stores data locally in SQLite (`vending.db`). The website is built with Vue/Vite and reads data from Supabase. A machine-to-Supabase bridge can sync `products` and `transactions` (and optionally events) so the dashboard updates in realtime or near-realtime.

Products (slot • item • price • capacity):
1 Alcohol ₱25 cap3
2 Soap ₱5 cap7
3 Deodorant/Deo ₱10 cap8
4 Mouthwash/Mouth wash ₱8 cap7
5 Tissues/Tissue ₱8 cap3
6 Wet Wipes/Wipes ₱18 cap3
7 Panty Liners/Panty liner/Panti liner ₱5 cap6
8 All Night Pads ₱10 cap5
9 Regular with Wings ₱7 cap5
10 Non‑Wing Pads ₱7 cap5

Low-stock thresholds (≤ = Low): Alcohol 1, Soap 3, Deodorant 3, Mouthwash 3, Wet Wipes 1, Tissue 1, Panty Liner 3, All Night Pads 2, Regular with Wings 3, Non‑Wing 3.
Status meaning: Full if stock≥capacity; In Stock if threshold<stock<capacity; Low if 0<stock≤threshold; Empty if stock≤0.

Buying flow (user): select product → pay (coin acceptor) → dispense → record sale in `transactions` → update `products.current_stock` (normal mode).
What the dashboard should show after a purchase (if synced): new Recent Transaction row, charts update, Live feed shows an event, and the product stock decreases (unless demo/full-stock mode is enabled).

Live feed: the dashboard can show a merged timeline from `transactions` (sales) and `live_feed` (non-sale machine events). Duplicates should be avoided when the same sale appears in both places.

Reports: bug reports come from Supabase `bug_reports`. The Reports sidebar badge counts new OPEN bug reports until the Reports page is opened.

Demo/full-stock mode: the machine can force all stocks to full (current_stock=capacity) for thesis presentation. Transactions still record, but inventory may not decrease on the website. This does not change RFID/GPIO/Coin logic—only inventory counts.

Security: never expose Supabase service_role keys in the website/browser. Use anon/public key only in the website.

Troubleshooting quick checks:
1) Website stale/not updating: bridge not running OR realtime not enabled for tables → restart the bridge; ensure tables are added to Supabase realtime publication; confirm internet access.
2) Live feed empty: ensure `live_feed` exists and is realtime-enabled; ensure the machine is inserting transactions/events to Supabase.
3) Reports badge not showing: confirm there are OPEN bug reports and the dashboard is receiving updates or refreshing.

## Smart Hygiene Vending Machine (Tuqlas KB – 3k–4k chars)

Project: Smart Hygiene Vending Machine (TUP Manila – BET Computer Engineering Tech).
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

Troubleshooting:
- Website stale: bridge not running / realtime not enabled → restart bridge and ensure tables are in realtime publication.
- Live feed empty: ensure `live_feed` exists + enabled for realtime; ensure new transactions/events are inserted.
- Reports badge missing: ensure there are OPEN bug reports and dashboard is updating; reload if needed.

## Smart Hygiene Vending Machine (Tuqlas KB – 3k–4k chars)

Project: Smart Hygiene Vending Machine (TUP Manila – BET Computer Engineering Tech).
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

Buying flow: select product → pay (coin acceptor) → dispense → record `transactions` → update `products.current_stock` (normal mode). Website should show new “Recent Transaction”, updated charts, and a live feed entry (if synced).

Demo/full-stock mode: stocks can be forced to full (current_stock=capacity) for thesis presentation. Transactions still record, but inventory may not decrease. This does not change RFID/GPIO/Coin logic—only inventory counts.

Dashboard data (Supabase): `public.products`, `public.transactions`, `public.live_feed`, `public.bug_reports`. Live feed merges sales and events; duplicates are avoided when possible. Sidebar badges: Live feed badge counts unseen new events; Reports badge counts new OPEN bug reports; opening the page clears the badge.

Troubleshooting:
- Website stale: bridge not running / realtime not enabled → restart bridge and ensure tables are in realtime publication.
- Live feed empty: ensure `live_feed` exists + enabled for realtime; ensure new transactions/events are inserted.
- Reports badge missing: ensure there are OPEN bug reports and dashboard is updating; reload if needed.

*** End of File

Project: Smart Hygiene Vending Machine (TUP Manila – BET Computer Engineering Tech).
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

Buying flow: select product → pay (coin acceptor) → dispense → record `transactions` → update `products.current_stock` (normal mode). Website should show new “Recent Transaction”, updated charts, and a live feed entry (if synced).

Demo/full-stock mode: stocks can be forced to full (current_stock=capacity) for thesis presentation. Transactions still record, but inventory may not decrease. This does not change RFID/GPIO/Coin logic—only inventory counts.

Dashboard data (Supabase): `public.products`, `public.transactions`, `public.live_feed`, `public.bug_reports`. Live feed merges sales and events; duplicates are avoided when possible. Sidebar badges: Live feed badge counts unseen new events; Reports badge counts new OPEN bug reports; opening the page clears the badge.

Troubleshooting:
- Website stale: bridge not running / realtime not enabled → restart bridge and ensure tables are in realtime publication.
- Live feed empty: ensure `live_feed` exists + enabled for realtime; ensure new transactions/events are inserted.
- Reports badge missing: ensure there are OPEN bug reports and dashboard is updating; reload if needed.

## Smart Hygiene Vending Machine (Tuqlas KB – 3k–4k chars)

Project: Smart Hygiene Vending Machine (TUP Manila – BET Computer Engineering Tech).
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

Buying flow: select product → pay (coin acceptor) → dispense → record `transactions` → update `products.current_stock` (normal mode). Website should show new “Recent Transaction”, updated charts, and live feed entry (if synced).

Demo/full-stock mode: stocks are forced to full (current_stock=capacity) for presentation. Transactions still record, but inventory may not decrease. This does not change RFID/GPIO/Coin logic—only inventory counts.

Dashboard data (Supabase): `public.products`, `public.transactions`, `public.live_feed`, `public.bug_reports`. Live feed merges sales and events; duplicates are avoided when possible. Sidebar badges: Live feed badge counts unseen new events; Reports badge counts new OPEN bug reports; opening the page clears the badge.

Troubleshooting:
- Website stale: bridge not running / realtime not enabled → restart bridge and ensure tables are in realtime publication.
- Live feed empty: ensure `live_feed` exists + enabled for realtime; ensure new transactions/events are inserted.
- Reports badge missing: ensure there are OPEN bug reports and dashboard is updating; reload if needed.


### 1.3 Thesis adviser (from the website)
**Prof. Gemma D. Belga - Robles**  
Role: **Thesis/Capstone Adviser**  
Additional title shown in the website: **College CIT Secretary**

If asked: “Who guided your thesis?”  
Answer: **Prof. Gemma D. Belga - Robles**.

### 1.4 Team members (from the website Team page)
These names and roles are the canonical team list:

1) **Asriel Romulo** — **Leader**  
2) **Jonamae Tiu** — **Papers**  
3) **Zharie Ann R. Valero** — **Papers**  
4) **John Renzo G. Dacer** — **Lead UX/UI**  
5) **Gideon Soberano** — **Lead Programmer**  
6) **Jose Angelo F. Lacerna** — **Lead Programmer**

If asked: “Who are the members?” or “Who built this machine?”  
Answer with the list above.

---

## 2) What is the system?

The system combines a physical vending machine and a web-based admin dashboard.

### 2.1 Vending Machine App (Python + SQLite)
The machine app runs locally and is responsible for:
- Displaying the machine UI and handling selection
- Accepting payment input (e.g., coin acceptor)
- Controlling dispensing hardware (motors/actuators)
- Optionally using sensors/IR confirmation
- Recording inventory and transactions in a local SQLite database

Local database file:
- **`vending.db`** (SQLite)

Key local tables (high-level):
- `products`: slot inventory (`capacity`, `current_stock`, etc.)
- `transactions`: sales history (`timestamp`, `quantity`, `total_amount`, etc.)
- optional user tables (RFID users, admin settings, hardware settings)

### 2.2 Admin Dashboard Website (Vue/Vite + Supabase)
The website is used to view and manage (depending on permissions):
- Inventory levels, low-stock list
- Recent transactions and sales charts
- A “machine live feed” timeline
- Bug reports (Reports page)
- Downloadable sales reports (CSV/XLSX)

The website uses Supabase as the central “cloud” database for the dashboard.

### 2.3 Machine → Supabase Sync (Bridge)
An optional bridge process pushes machine updates to Supabase so the dashboard can show data in near real time:
- Upserts `products` (inventory)
- Inserts `transactions` (sales)
- Optionally appends `live_feed` events

---

## 3) Product catalog (slot, price, and capacity)

The machine contains 10 primary product slots.

### 3.1 Official product list (slot → name → price → capacity)
1. Slot 1 — **Alcohol** — ₱25 — capacity **3**  
2. Slot 2 — **Soap** — ₱5 — capacity **7**  
3. Slot 3 — **Deodorant / Deo** — ₱10 — capacity **8**  
4. Slot 4 — **Mouthwash / Mouth wash** — ₱8 — capacity **7**  
5. Slot 5 — **Tissues / Tissue** — ₱8 — capacity **3**  
6. Slot 6 — **Wet Wipes / Wipes / Wetwipes** — ₱18 — capacity **3**  
7. Slot 7 — **Panty Liners / Panty liner / Panti liner / Pantyliners** — ₱5 — capacity **6**  
8. Slot 8 — **All Night Pads / All-night pads** — ₱10 — capacity **5**  
9. Slot 9 — **Regular with Wings Pads / Regular W/ Wings Pads** — ₱7 — capacity **5**  
10. Slot 10 — **Non-Wing Pads / Non wing pad / Non-wing pad** — ₱7 — capacity **5**

### 3.2 Name normalization (how the system recognizes variants)
Data sources can use different text:
- “Deo” should be treated as “Deodorant”
- “Mouth wash” should be treated as “Mouthwash”
- “Wetwipes” / “wipes” should be treated as “Wet Wipes”
- “Panti liner” / “pantyliners” should be treated as “Panty Liners”
- “Non wing pad” / “non-wing pad” should be treated as “Non-Wing Pads”

When a user asks for an item using a variant, respond using the canonical name above.

---

## 4) Stock status rules and low-stock thresholds

The machine uses two key values:
- **capacity**: max items that can fit in a slot
- **current_stock**: current count in the slot

### 4.1 Status definitions
- **Full**: `current_stock >= capacity`
- **In Stock**: `threshold < current_stock < capacity`
- **Low**: `0 < current_stock <= threshold`
- **Empty**: `current_stock <= 0`

### 4.2 Low-stock thresholds (official)
The dashboard marks a product “Low” when `current_stock <= threshold`:

- Alcohol: **1**
- Soap: **3**
- Deodorant: **3**
- Mouthwash: **3**
- Wet Wipes: **1**
- Tissue: **1**
- Panty Liner: **3**
- All Night Pads: **2**
- Regular with Wings: **3**
- Non Wings Pad: **3**

### 4.3 What to do when something is Low or Empty
For customers:
- Choose a different product if the desired product is Empty.
For restockers/admins:
- Restock the slot up to capacity.
- Ensure the database stock is updated to match reality.

---

## 5) How buying works (user-facing)

The exact UI can differ by version, but the buying flow is generally:

1) **Select product** (by slot or product name).  
2) **Pay** using the supported payment input (e.g., coin acceptor).  
3) Machine **dispenses** the item (motor/actuator).  
4) Machine may **confirm vend** (sensor/IR confirmation if enabled).  
5) Machine records the sale in SQLite `transactions`.  
6) Machine reduces stock in SQLite `products.current_stock` (unless demo/full-stock mode is enabled).  
7) If sync is enabled, the bridge posts the new transaction and updated products to Supabase.

What a successful purchase should produce:
- A new transaction record
- A stock decrement (normal mode)
- A new dashboard entry (if synced)

---

## 6) Restocking (admin/restocker)

Restocking is the act of refilling physical items and updating the database count.

Rules:
- Stock should not exceed capacity.
- If a slot is physically full, set `current_stock = capacity`.

If asked: “What is the max for Soap?” → 7.  
If asked: “What is the max for All Night Pads?” → 5.

---

## 7) Full-stock / demo mode (important for presentations)

In demo/thesis mode, inventory can be forced to remain full:
- `current_stock` is set to `capacity` for all products.

Why this exists:
- Keeps the UI stable during demos.
- Prevents the display from becoming “empty” after repeated purchases in a presentation.

Important:
- This changes **inventory counts only**.
- It does not change RFID/GPIO/coin acceptor logic or physical dispensing.

If asked: “Why is stock always full?”  
Answer: Demo/full-stock mode is enabled.

---

## 8) Where dashboard data comes from (Supabase)

The website uses Supabase tables (typical names):

- `public.products` — inventory snapshot used by the dashboard
- `public.transactions` — sales history used by charts and exports
- `public.live_feed` — append-only machine events
- `public.bug_reports` — bug reports shown in Reports section

### 8.1 Realtime updates
If Supabase Realtime is enabled:
- the dashboard can update live via `postgres_changes`.

If realtime is unavailable:
- the dashboard may use periodic refresh/fallback.

---

## 9) Dashboard sections (what they mean)

### 9.1 Overview
Purpose: quick “at a glance” status.
Shows:
- totals (sales/orders/customers, depending on configuration)
- low-stock list
- recent transactions
- live feed preview

### 9.2 Live feed
Purpose: a timeline of machine activity.
Shows:
- sales derived from transactions
- other events from live_feed
Supports:
- date filtering (calendar)
- range filtering (day/week/month)

### 9.3 Sales Reports
Purpose: export transactions for reporting.
Formats:
- CSV
- XLSX

### 9.4 Reports (bug reports)
Purpose: track issues submitted from the machine.
Tabs:
- Open
- Fixed
Admin actions:
- mark as fixed (if enabled)

---

## 10) Notifications / sidebar badges (how they work)

Badges are “unread counts”:

### 10.1 Live feed badge
- Counts new feed events since you last opened the Live feed page.
- Clears when Live feed is opened.

### 10.2 Reports badge
- Counts new OPEN bug reports since you last opened Reports.
- Clears when Reports is opened.

If asked: “Why did the badge disappear?”  
Answer: Opening the page marks items as seen.

---

## 11) Troubleshooting (step-by-step)

### 11.1 Website is blank / white screen
Most common cause:
- a runtime JavaScript error.

Steps:
1) Reload the page.
2) Open browser developer tools → Console.
3) Read the error and identify which component failed.
4) Rebuild and redeploy if a recent change introduced it.

### 11.2 Website is stale (not updating)
Causes:
- bridge not running
- realtime not configured
- network issue

Steps:
1) Confirm machine app is recording transactions locally.
2) Confirm bridge can push to Supabase (no lock/permission issues).
3) Confirm Realtime publication includes needed tables.
4) If realtime is down, rely on fallback refresh until fixed.

### 11.3 Live feed not updating
Steps:
1) Confirm `live_feed` table exists.
2) Confirm `live_feed` is enabled for Realtime publication.
3) Confirm machine is inserting transactions or events.

### 11.4 Reports badge not showing
Steps:
1) Ensure there is at least one OPEN bug report row.
2) Ensure dashboard is receiving updates or refreshing.
3) If “last seen” state is stuck, clear local storage (developer action) and reload.

---

## 12) FAQ templates (copy-paste friendly)

### “What products are available?”
We offer Alcohol, Soap, Deodorant, Mouthwash, Tissues, Wet Wipes, Panty Liners, All Night Pads, Regular with Wings Pads, and Non-Wing Pads.

### “What does Low stock mean?”
Low stock means the product is still available but its quantity is at or below its low-stock threshold (e.g., Alcohol is low at 1, Soap is low at 3).

### “Who is your adviser?”
Our thesis adviser is **Prof. Gemma D. Belga - Robles**.

### “Who are the members?”
Asriel Romulo (Leader), Jonamae Tiu (Papers), Zharie Ann R. Valero (Papers), John Renzo G. Dacer (Lead UX/UI), Gideon Soberano (Lead Programmer), and Jose Angelo F. Lacerna (Lead Programmer).

### “Why does stock not decrease after buying?”
The system may be running in demo/full-stock mode where inventory counts are forced to stay full for presentations.

---

## 13) Security and privacy
- Do not expose Supabase service-role keys in the browser.
- Only use public/anon keys client-side.
- Keep service-role keys server-side or on the machine in private env files.

---

## 14) Detailed architecture (for developers and technical users)

This section is more technical. It explains how data moves through the system and why certain design decisions exist.

### 14.1 The local machine database (`vending.db`)
The vending machine stores its operational data locally so it can function even if the internet is unavailable.

At a conceptual level:
- `products` holds the **current inventory state**.
- `transactions` holds the **history of purchases**.
- optional tables hold **RFID users**, **admin credentials**, and **hardware settings**.

Why SQLite?
- Lightweight and reliable.
- Easy to bundle with Python.
- Works offline.

### 14.2 The cloud database (Supabase)
Supabase is used by the website as the “single view” of machine activity. The website reads from Supabase and can subscribe to changes (realtime).

Supabase tables act like a “mirror” of key machine data:
- `public.products` mirrors inventory.
- `public.transactions` mirrors sales history.
- `public.live_feed` shows a readable timeline of events.
- `public.bug_reports` is an issue channel from the machine to admins.

### 14.3 The sync bridge (SQLite → Supabase)
The bridge exists because the machine’s primary source of truth is local SQLite. The website cannot directly access the machine’s local DB, so the bridge “uploads” changes.

Typical behavior:
- **Products** are upserted every few seconds (or on a schedule) so the website stock numbers stay current.
- **Transactions** are inserted when new local transactions appear.
- The bridge keeps a cursor (last synced id) to avoid re-sending all history.

Why bridge mode matters:
- If the bridge is not running, the website can only show old data.
- If the bridge runs twice (two instances), duplicates can happen.
- If the bridge gets stuck behind a stale lock file, syncing stops.

### 14.4 Realtime on the website
When realtime is enabled, the website listens to Supabase `postgres_changes` events:
- INSERT / UPDATE / DELETE on the key tables.

If realtime is not enabled for a table, the website may still show data via:
- initial fetch (page load)
- periodic refresh fallback

The dashboard may display a connection status (connected vs fallback refresh) depending on configuration.

---

## 15) Supabase setup and environment variables (no secrets included)

### 15.1 Website environment variables
The website needs:
- `VITE_SUPABASE_URL` (Project URL)
- `VITE_SUPABASE_PUBLISHABLE_KEY` (anon/public key)

These are placed in:
- `WebSite/.env.local` for local dev
- Hosting platform environment variables for production (Netlify/Vercel/etc.)

### 15.2 Machine/bridge environment variables
The bridge needs:
- `SUPABASE_URL` (Project URL)
- `SUPABASE_SERVICE_ROLE_KEY` (service_role key; **secret**)

These are placed in:
- `supabase.env` on the machine / server side

Security reminder:
- The service role key must never be committed or shipped to the browser.

---

## 16) Database and dashboard behavior details (what admins should expect)

### 16.1 Inventory truth
In normal mode:
- When a purchase occurs, the machine decreases `current_stock` in SQLite.
- The bridge upserts that new stock to Supabase.
- The website displays the Supabase stock (and can show “Low/Empty”).

In demo/full-stock mode:
- The machine forces `current_stock = capacity` during initialization or on a configured step.
- The website will display full stock even after purchases.
This is expected behavior during thesis demos.

### 16.2 Transactions truth
Transactions should always append; they form the sales history.

If the same transaction appears twice:
- It may indicate a duplicate insert due to:
  - bridge restart without a proper cursor
  - missing stable transaction identifier
  - duplicate bridge instances

The recommended approach is:
- Use a stable “source transaction id” from the machine (if supported)
- Ensure only one bridge instance is running

### 16.3 Live feed truth
Live feed is intended to be readable:
- “Sale: <product> · slot <n> · ₱<amount>”
- plus other non-sale messages (restock, maintenance, info)

Sales can be shown via transactions (preferred for stable reporting), while live_feed can be used for:
- non-sale operational events
- debugging and monitoring

---

## 17) Reports (bug reports) workflow

Bug reports are messages from the machine to admins. A bug report typically contains:
- timestamp
- category (type of issue)
- details (description)
- version/theme (optional)
- machine identifier (optional)

### 17.1 Open vs Fixed
Admins can set status:
- Open: needs attention
- Fixed: resolved

### 17.2 Reports badge meaning
The Reports badge counts:
- new OPEN bug reports since the last time Reports was opened

This helps admins focus on newly received issues.

If asked: “Why does the badge not count fixed reports?”
Answer:
- The badge is an alert for new unresolved items; fixed items are considered resolved.

---

## 18) Hardware overview (high level, without changing behavior)

This section describes hardware in general terms. It does not change or override your RFID/GPIO/Coin Acceptor logic.

### 18.1 Coin acceptor (payment pulses)
A coin acceptor usually outputs pulses:
- The machine software counts pulses to determine inserted value.

Common troubleshooting:
- If coins are not detected, check wiring and pulse calibration settings.
- If value is wrong, adjust coin pulse calibration (software setting).

### 18.2 RFID (roles and access)
RFID can be used to:
- identify users
- allow staff/admin access for restocking or maintenance

The system may store RFID users in a local table (e.g., `rfid_users`).

### 18.3 GPIO (sensors and actuators)
GPIO is used on Raspberry Pi setups for:
- sensors (IR beam confirmation, door sensors)
- actuators (relays, motors depending on design)

If asked: “Does the website control hardware directly?”
Answer:
- No. The website reads Supabase data; hardware control is local to the machine app.

---

## 19) Deployment and operation (practical instructions)

### 19.1 Running the machine app
General guidance:
- Start the machine application.
- Confirm it initializes the database.
- Confirm inventory is loaded.

If Supabase sync is configured:
- Confirm the bridge starts (or run it manually).

### 19.2 Running the website locally
Typical steps:
- Configure `WebSite/.env.local` with Supabase URL + anon key.
- Run `npm install` then `npm run dev`.

### 19.3 Building the website for production
Use:
- `npm run build`

Deploy the `dist/` folder to your hosting platform (Netlify, etc.) or use your configured deployment scripts.

---

## 20) “If this happens, do that” quick cheat sheet

### 20.1 Stock numbers look wrong
- Verify machine DB values in `products`.
- Verify bridge is pushing updates.
- Verify website is reading the correct Supabase project URL.

### 20.2 Recent transactions not updating
- Confirm the machine is inserting new `transactions`.
- Confirm the bridge cursor advanced (last synced id).
- Confirm realtime is enabled for `transactions` in Supabase.

### 20.3 Live feed shows duplicates
- Ensure the dashboard is not counting the same sale from both `transactions` and `live_feed`.
- Ensure stable identifiers exist (source transaction id).
- Ensure only one bridge instance is running.

### 20.4 Website loads but shows “no rows”
- Ensure Supabase tables exist and policies allow select.
- Ensure you are connected to the correct Supabase URL.

---

## 21) Glossary (terms users may ask about)

- **Capacity**: maximum number of items that fit in a slot.
- **Current stock**: current inventory count in the slot.
- **Low-stock threshold**: value at which an item is considered “Low”.
- **SQLite**: local database file used by the machine.
- **Supabase**: cloud database + realtime service used by the dashboard.
- **Realtime**: browser receives database change events automatically.
- **Bridge**: program that pushes machine SQLite data to Supabase.
- **Live feed**: timeline of machine events and sales messages.
- **Bug report**: message sent from machine to dashboard for admin review.

---

## 22) Extended FAQ (more detailed answers)

### 22.1 “Is the dashboard the source of truth?”
No. The source of truth for machine operations is the **machine’s local database**. Supabase and the dashboard are for monitoring and administration.

### 22.2 “What happens if the internet goes down?”
The machine can still operate using local SQLite:
- users can buy items
- transactions still record locally
When internet returns:
- the bridge can upload missed transactions and refresh inventory.

### 22.3 “Why does the dashboard sometimes show delayed updates?”
Possible reasons:
- realtime is down and the dashboard is using fallback refresh
- network delay between bridge and Supabase
- the bridge is throttled to reduce API usage

### 22.4 “How do I confirm the bridge is working?”
A working bridge results in:
- new `transactions` appearing in Supabase after a sale
- updated `products.current_stock` values appearing in Supabase
- live feed activity (if configured)

### 22.5 “Can we export reports for thesis documentation?”
Yes. The dashboard provides:
- CSV export
- XLSX export
These can be used for thesis analysis, charts, and documentation.

---

## 23) Product descriptions (helpful for users)

This section provides short, user-friendly descriptions. The chatbot can use these when someone asks “What is this product?” or “What is inside slot X?”

### 23.1 Alcohol (Slot 1)
- Purpose: quick hand sanitation / disinfection
- Typical usage: apply on hands, rub until dry
- Capacity: 3 items
- Low-stock threshold: 1

### 23.2 Soap (Slot 2)
- Purpose: hand washing and hygiene
- Capacity: 7 items
- Low-stock threshold: 3

### 23.3 Deodorant / Deo (Slot 3)
- Purpose: odor control and personal care
- Capacity: 8 items
- Low-stock threshold: 3

### 23.4 Mouthwash / Mouth wash (Slot 4)
- Purpose: oral hygiene and fresh breath
- Capacity: 7 items
- Low-stock threshold: 3

### 23.5 Tissues (Slot 5)
- Purpose: quick cleaning / wiping
- Capacity: 3 items
- Low-stock threshold: 1

### 23.6 Wet Wipes (Slot 6)
- Purpose: convenient cleaning when soap/water is not available
- Capacity: 3 items
- Low-stock threshold: 1

### 23.7 Panty Liners (Slot 7)
- Purpose: daily hygiene and comfort
- Capacity: 6 items
- Low-stock threshold: 3

### 23.8 All Night Pads (Slot 8)
- Purpose: overnight protection
- Capacity: 5 items
- Low-stock threshold: 2

### 23.9 Regular with Wings Pads (Slot 9)
- Purpose: regular protection with wings for better fit
- Capacity: 5 items
- Low-stock threshold: 3

### 23.10 Non-Wing Pads (Slot 10)
- Purpose: regular protection without wings
- Capacity: 5 items
- Low-stock threshold: 3

---

## 24) Admin operations and best practices

### 24.1 Daily admin checklist
Recommended daily routine:
1) Open dashboard **Overview** and check the Low-stock list.
2) Open **Live feed** and scan for recent sales and unusual events.
3) Check **Reports** (bug reports) for new open issues.
4) If any item is low/empty, schedule restocking.

### 24.2 Restocking checklist
Before restocking:
- Bring the correct items for the slot.
- Verify slot label and product type.

During restocking:
- Refill the slot physically up to capacity.
- Update the inventory count in the machine/admin tool if required.

After restocking:
- Confirm the dashboard shows stock updated (if sync is enabled).
- If the dashboard does not update, check bridge and Supabase connectivity.

### 24.3 Handling discrepancies (physical vs dashboard)
If the physical slot is full but the dashboard shows Low:
- The dashboard is likely stale or out of sync.
Actions:
- Confirm the machine database has correct `current_stock`.
- Confirm the bridge pushed products successfully.
- Confirm the dashboard is pointing to the correct Supabase project.

If the physical slot is empty but the dashboard shows Full:
- In demo/full-stock mode, this can happen intentionally.
- In normal mode, this indicates incorrect inventory tracking.
Actions:
- Check whether demo mode is enabled.
- Verify stock decrement logic after purchases.
- Ensure restock procedures update the DB correctly.

---

## 25) Supabase Realtime and RLS (high-level guidance)

This section helps explain why a dashboard might show “no rows” even when tables exist.

### 25.1 Realtime publication
For realtime subscriptions to work, Supabase must be configured to replicate the relevant tables in the `supabase_realtime` publication.

Common required tables:
- `public.products`
- `public.transactions`
- `public.live_feed`
- `public.bug_reports`

If asked: “How do we enable realtime?”
Answer (high-level):
- Enable the table for realtime replication in Supabase settings (Database replication / Realtime publication).

### 25.2 Row Level Security (RLS)
If RLS is enabled but policies are missing:
- The website can fail to read rows even if data exists.

Best practice:
- Allow `SELECT` for anon/authenticated users on read-only dashboard tables where appropriate.
- Keep `INSERT/UPDATE` restricted (service role on bridge/machine, or authenticated admin users).

---

## 26) Performance and reliability tips (what keeps the system stable)

### 26.1 Avoid duplicate bridge instances
Running the bridge twice can cause duplicate inserts and confusing dashboards.
Recommendation:
- Keep only one bridge process running per machine.

### 26.2 Prevent stale lock issues
If the bridge uses a lock file and the machine restarts unexpectedly:
- a stale lock can block the bridge.
Recommendation:
- Use stale-lock recovery logic or remove the lock when safe.

### 26.3 Keep transaction ordering stable
For accurate “Recent Transactions” and charts:
- Always sort by `created_at`/timestamp
- Use stable ids if possible

---

## 27) Tuqlas chatbot behavior guidelines (how it should answer)

When responding, the chatbot should:
- Prefer short, clear answers first, then offer steps.
- Ask clarifying questions only when necessary.
- Use the official product names and slot numbers.
- Be careful with security: never output service role keys.

Examples:

User: “Is Wet Wipes available?”
Bot:
- Check stock status: If current_stock > 0 → “Yes, Wet Wipes is available (Slot 6).”
- If 0 → “Wet Wipes is currently out of stock (Slot 6).”

User: “Why is the dashboard not updating?”
Bot:
- Provide likely causes (bridge down, realtime disabled).
- Give a short checklist to verify.

---

## 28) Additional FAQ (common real-world questions)

### 28.1 “What are your operating hours?”
This depends on deployment location. If not configured, answer:
- “Operating hours depend on where the machine is placed. Please ask the site administrator.”

### 28.2 “Can I buy multiple items at once?”
If the machine supports only one vend per transaction, answer:
- “Purchases are typically one product selection per transaction. You can repeat the process to buy multiple items.”

### 28.3 “Can I pay using e-wallet?”
If not supported, answer:
- “Payment methods depend on the machine configuration. The standard setup supports coin acceptor input.”

### 28.4 “Why do I see ‘fallback refresh active’?”
Answer:
- “It means Supabase realtime isn’t fully available right now, so the dashboard refreshes periodically instead of streaming instant updates.”

---

## 29) Testing and verification (for demos and defense)

This section helps answer questions like “How do you know it works?” and “How was it validated?”.

### 29.1 Functional checks (machine)
A simple functional test plan:

1) **Startup test**
   - Start the machine app.
   - Verify UI loads and products appear.
   - Verify database initializes without errors.

2) **Inventory test**
   - Confirm each slot displays correct capacity.
   - Confirm stock status (Full/In Stock/Low/Empty) follows the rules.

3) **Purchase test**
   - Select a product.
   - Insert payment (coin acceptor).
   - Verify dispensing happens.
   - Verify a transaction row is recorded.
   - Verify stock decreases in normal mode (or stays full in demo/full-stock mode).

4) **Edge cases**
   - Attempt to buy an Empty product (should block or warn).
   - Attempt to pay insufficient amount (should not vend).

### 29.2 Functional checks (website)

1) **Initial load**
   - Website loads without a blank/white screen.
   - Overview shows products and transactions.

2) **Realtime / refresh**
   - When a new transaction arrives in Supabase, “Recent Transactions” updates.
   - Live feed reflects new activity.
   - Reports badge appears for new open bug reports.

3) **Exports**
   - Sales Reports export CSV/XLSX successfully.

### 29.3 Data integrity checks
To validate correctness:
- `current_stock` should never exceed `capacity`.
- Transactions should be ordered by timestamp.
- Duplicates should be prevented or deduped.

---

## 30) Reliability and failure handling

### 30.1 What happens during power loss?
Because SQLite is local, the machine can:
- recover its inventory and transaction history after restart.
If a vend happened during the outage:
- the system may need manual reconciliation depending on exact timing.

### 30.2 What happens when the bridge fails?
If the bridge cannot post to Supabase:
- the machine still works offline.
- the website will show old data until connectivity is restored.

Best practice:
- Keep a clear log message for bridge failures (HTTP errors, timeouts).
- Ensure stale-lock recovery is enabled if a lock file is used.

---

## 31) Thesis-defense friendly explanation (non-technical)

If asked to explain the system simply:

“We built a hygiene vending machine that records inventory and purchases locally so it works even without internet. For administration, we created a web dashboard connected to Supabase. A bridge process synchronizes machine data to Supabase so the dashboard can show near real-time updates. The dashboard highlights low-stock items, shows recent transactions, and provides a live activity feed and bug reports for monitoring and maintenance.”

---

## 32) Ethical, safety, and privacy considerations

### 32.1 User privacy
The system should avoid storing unnecessary personal data.
If RFID is used:
- store only what is required for access/control
- protect role-based operations (admin vs customer)

### 32.2 Security
- Keep service keys private.
- Restrict write operations to trusted processes/users.
- Use Row Level Security (RLS) carefully.

### 32.3 Safety
Physical safety considerations:
- moving parts should be enclosed properly
- dispensing mechanism should not expose pinch points
- electrical wiring should be insulated and managed properly

---

## 33) Future improvements (what could be added later)

Possible enhancements:
- More payment options (e-wallet, QR code)
- Better telemetry (temperature/online status) and uptime reporting
- Automated restock predictions based on historical demand
- Improved audit trail for restocker actions
- Multi-machine support (multiple machines reporting to one dashboard)

---

## 34) Quick reference: capacities and thresholds (one glance)

Capacities (max stock):
- Alcohol 3
- Soap 7
- Deo 8
- Mouthwash 7
- Tissues 3
- Wet Wipes 3
- Panty Liners 6
- All Night Pads 5
- Regular with Wings 5
- Non-Wing Pads 5

Low-stock thresholds:
- Alcohol 1
- Soap 3
- Deodorant 3
- Mouthwash 3
- Wet Wipes 1
- Tissue 1
- Panty Liner 3
- All Night Pads 2
- Regular with Wings 3
- Non Wings Pad 3

---

## 35) Setup checklist (developer-oriented, still no secrets)

This checklist helps a new developer or evaluator set up the system quickly.

### 35.1 Machine checklist
1) Ensure Python is installed.
2) Run the machine app and confirm it creates/updates `vending.db`.
3) Confirm the `products` table has 10 slots with correct capacities.
4) Confirm you can complete a purchase and that a transaction is written to SQLite.

### 35.2 Supabase checklist
1) Create a Supabase project.
2) Create the tables required by the dashboard:
   - `public.products`
   - `public.transactions`
   - `public.live_feed`
   - `public.bug_reports`
3) Enable Realtime replication for the tables you want to stream to the dashboard.
4) Configure Row Level Security policies so the website can read rows (SELECT) as needed.

### 35.3 Bridge checklist
1) Place the machine’s Supabase env file on the machine (`supabase.env`).
2) Start the bridge (or let the machine start it automatically if configured).
3) Confirm that:
   - `products` rows appear in Supabase
   - a new sale creates a new `transactions` row in Supabase

### 35.4 Website checklist
1) Create `WebSite/.env.local` with:
   - `VITE_SUPABASE_URL`
   - `VITE_SUPABASE_PUBLISHABLE_KEY`
2) Install dependencies: `npm install`
3) Run locally: `npm run dev`
4) Confirm the dashboard loads and shows products/transactions.

---

## 36) Supabase table field cheat sheet (conceptual)

The exact schema can evolve, but typical fields are:

### 36.1 `products`
- `id`: row id
- `slot_number`: slot index (1–10)
- `name`: product name
- `details`: description
- `price`: price in PHP
- `capacity`: max stock
- `current_stock`: current count
- `updated_at`: last updated timestamp

### 36.2 `transactions`
- `id`: row id
- `created_at`: timestamp
- `product_id`: product reference (optional)
- `product_name`: product name (optional)
- `slot_number`: slot number (optional)
- `quantity`: quantity purchased
- `total_amount`: PHP amount
- `payment_method`: payment type (optional)
- `rfid_user_id`: user id (optional)

### 36.3 `live_feed`
- `id`: row id
- `created_at`: timestamp
- `event_type`: e.g., sale/info/test/machine
- `message`: human-readable text
- `quantity`: optional
- `total_amount`: optional
- `payload`: optional JSON data

### 36.4 `bug_reports`
- `id`: row id
- `created_at`: timestamp
- `machine_id`: optional machine identifier
- `category`: type of issue
- `details`: issue description
- `version`: optional software version
- `theme`: optional theme/UI context
- `status`: open/fixed
- `fixed_at`, `fixed_by`: optional resolution fields

---

## 37) Extra Q&A (common “panelist questions”)

### 37.1 “Why did you choose Supabase?”
Supabase provides a hosted Postgres database, realtime subscriptions, and an easy API layer. It reduces backend infrastructure work and makes the dashboard update smoothly.

### 37.2 “Why store data locally first?”
Storing data in SQLite keeps the machine operational offline. The bridge uploads data later so the dashboard remains accurate when connectivity is restored.

### 37.3 “How do you prevent inventory from going over capacity?”
Inventory is stored with both `capacity` and `current_stock`, and the system clamps impossible values so `current_stock` cannot exceed `capacity`.

### 37.4 “How do you ensure the dashboard is reliable?”
The dashboard uses realtime subscriptions when available and can fall back to periodic refresh. It also dedupes repeated records and sorts by timestamps so “Recent Transactions” stays correct.

### 37.5 “What is your main contribution as a team?”
We combined hardware integration and software engineering: a machine app that works offline with SQLite, plus a cloud-synced dashboard using Supabase for monitoring, reporting, and maintenance support.






