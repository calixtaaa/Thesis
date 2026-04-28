"""
Patch notes for the Hygiene Vending Machine.
Central place for: Version, Added, Improved, Bugs fixed, and Future updates.
Version history is retained so users can see all past patches when they click Patch Notes.
"""
from datetime import datetime


# App version (bump when releasing; shown in title, footers, and patch notes)
VERSION = "v1.0.1"


# ---------------------------------------------------------------------------
#  Version history (retained for in-app Patch Notes dialog)
# ---------------------------------------------------------------------------

PATCH_v0_01 = {
    "version": "v.0.01",
    "added": [
        "Product search bar with magnifying glass and backspace icons.",
        "Scrollable product grid for many products.",
        "Responsive sidebar menu from the hamburger icon (Admin & Staff).",
        "Admin dashboard with overview stats, sales reports, and Excel export.",
        "Admin login with username/password (hashed); change credentials in dashboard.",
        "Staff restock mode (RFID card authentication).",
        "RFID card purchase and reload flows.",
        "Light/dark theme support with slider-style toggle across main screens.",
        "Footer branding (SyntaxError™) and live Philippine date/time.",
        "Patch Notes and How to use dialogs.",
        "Sales trend graph, monthly sales bar chart, top-selling products chart, low-stock chart in admin overview.",
        "Dedicated folders: Downloads/Hygiene Vending Reports for Excel, debug_logs for debug output.",
        "Tap animation on product cards.",
        "Database module (database.py) and patch notes module (patchNotes.py).",
    ],
    "improved": [
        "UI/UX: consistent fonts (Segoe UI), card-style layout, step-by-step instructions (Step 1–3).",
        "Payment, quantity, cash, and RFID reload screens for consistent look and clarity.",
        "Pill-shaped search bar with placeholder 'Search for products'.",
        "Code organization: admin (admin.py), staff (staff.py), database (database.py) for cleaner main.py.",
        "Admin and staff icons moved into hamburger sidebar; small navbar toggle.",
        "7-inch touchscreen responsiveness and button clarity.",
    ],
    "bugs_fixed": [
        "SMS provider switched from Fast2SMS to PhilSMS for Philippine numbers (+63).",
        "Export Sales (Excel) limited to admin-only; button removed from user UI, available in admin dashboard.",
        "Product list: full seed of 10 hygiene products (delete vending.db once to re-seed if needed).",
        "Theme slider and debug log variable references corrected to avoid AttributeError.",
        "Payment screen buttons no longer clipped; font family and wraplength improved.",
    ],
    "future": [
        "Resolve TclError on main menu rebuild (search/scroll/theme interactions) if it recurs.",
        "Optional: SMS low-stock alerts via PhilSMS when stock falls below threshold.",
        "Optional: expanded hardware integration (MCP23017 stepper mapping and additional diagnostics) on Raspberry Pi.",
        "Optional: backup/restore for admin credentials and product list.",
    ],
}

PATCH_v0_02 = {
    "version": "v.0.02",
    "added": [],
    "improved": [
        "Unified color palette: teal #1A948E (Buy RFID) for accent, product add (+), and primary buttons.",
        "Admin dashboard KPI values (Total Sales, Orders, etc.) retain teal accent color when theme toggles.",
        "Theme toggle: deferred apply and throttling to keep UI responsive; recursion limit and widget checks.",
    ],
    "bugs_fixed": [
        "Theme toggle 3+ times: content no longer removed; slider applies theme in-place instead of rebuild.",
        "Theme toggle freeze and force close: deferred apply, throttling, recursion limit, and exception handling.",
        "Theme slider black line artifacts: removed sun/moon icon from knob for clean white knob design.",
    ],
    "future": [
        "Optional: SMS low-stock alerts via PhilSMS when stock falls below threshold.",
        "Optional: expanded hardware integration (MCP23017 stepper mapping and additional diagnostics) on Raspberry Pi.",
        "Optional: backup/restore for admin credentials and product list.",
    ],
}

# v0.03 – bug report UI + prediction analysis + UI fixes
PATCH_v0_03 = {
    "version": "v.0.03",
    "added": [
        "In-app Bug Report screen (category + explanation + submit) with local NDJSON storage.",
        "Prediction Analysis (runtime) shown in Admin Dashboard (predict demand tomorrow + restock recommendation).",
        "New project folder: predictionAnalysis/ (ML pipeline scripts, optional offline analysis).",
    ],
    "improved": [
        "Bug Report code extracted into bugreport.py for cleaner main.py.",
        "Main menu footer redesigned to two rows so PH time is always visible.",
        "PH date/time readability improved (badge style + larger bold text).",
    ],
    "bugs_fixed": [
        "Hamburger sidebar no longer persists across screens; sidebars now close on clear_screen().",
        "Main menu auto 'Menu' sidebar removed; sidebar only appears when hamburger is used.",
        "Prediction analysis ignores transactions without product_id (e.g., reload/buy flows) to prevent crashes.",
        "Theme toggle flicker: full-window overlay during clear+rebuild so theme switch is smooth (no visible destruction/redraw).",
        "'Back to products' on Order review and Choose quantity screens moved to a fixed bottom bar so it is always visible above the theme footer.",
    ],
    "future": [
        "Optional: upgrade prediction analysis to full ML models (Random Forest / Time Series) when Python 3.12 environment is available.",
        "Optional: export prediction results to Excel and add scheduled low-stock alerts.",
    ],
}

# v1.0.0 – Major UI Redesign + Chatbot Upgrade + Responsiveness
PATCH_v1_0_0 = {
    "version": "v1.0.0",
    "added": [
        "🤖 Hygiene Hero AI Chatbot — bilingual support (English + Tagalog/Filipino).",
        "🤖 Chatbot profanity filter — detects bad language and responds with a witty comeback.",
        "🤖 Chatbot now understands 'How to use this machine' / 'Paano gamitin ito' and gives step-by-step instructions.",
        "🤖 Chatbot dynamic follow-up suggestions — after each reply, related suggestions appear for the user to tap.",
        "🛒 New Product Detail Modal — tap any product card to see a full-screen page with image, description, benefits, and Add to Cart button.",
        "📢 Auto-cycling Promotional Carousel — rotating banner at the top of the product grid highlighting products and deals.",
        "📝 Product descriptions embedded in every detail modal explaining how each item helps the user's hygiene.",
        "🧭 Navigation breadcrumb system — Step 1/2/3 indicator in the header so users always know where they are.",
        "🤖 'Ask Hygiene Hero' button moved to top-right header — prominently visible for easy access.",
    ],
    "improved": [
        "🎨 Complete brand palette redesign: Emerald Green (#50C878), Plum (#8E4585), Creamy White (#F9F9FB).",
        "🎨 Dark mode updated to Deep Navy (#1A1A2E) with Mint-Emerald accents (#6AEAA0).",
        "✏️ Typography upgraded from Segoe UI → Poppins for a modern, premium feel.",
        "🖼️ All product images now load from images/Products/ with explicit mapping for all 10 items.",
        "🖼️ Uniform image sizing — all product images rendered at identical dimensions via PIL centering on transparent canvas.",
        "🎲 2.5D elevated product cards — thicker borders, larger corner radius, dimensional styling.",
        "👆 All product cards are now fully touchable — optimized for touchscreen LCD interaction.",
        "📱 App responsiveness optimized — layouts adapt to any screen size, fullscreen on Raspberry Pi.",
        "🤖 Chatbot welcome message improved with richer formatting and clearer feature list.",
        "🤖 Chatbot now shows contextual quick-reply chips after each bot response.",
    ],
    "bugs_fixed": [
        "Chatbot could not answer 'how to use this machine' — fixed with new keyword matching and Tagalog support.",
        "Product images had inconsistent sizes — fixed with uniform PIL canvas sizing.",
        "Chatbot button was hard to find in the footer — moved to top-right header for visibility.",
    ],
    "future": [
        "Voice-activated chatbot for hands-free interaction.",
        "Product recommendation engine based on purchase history.",
        "Multi-language support beyond English and Tagalog.",
        "Real-time inventory sync with cloud dashboard.",
    ],
}

# v1.0.1 – Product layout + pricing + Supabase realtime sync
PATCH_v1_0_1 = {
    "version": "v1.0.1",
    "added": [
        "Supabase realtime sync foundation: website now reads inventory/transactions from Supabase and subscribes to Realtime updates.",
        "Machine-to-cloud bridge script (sync/machine_supabase_bridge.py) that upserts products + posts new transactions to Supabase without changing hardware logic.",
        "Supabase SQL schema helper (supabase/schema_machine_sync.sql) for products + transactions tables (realtime-ready).",
        "Website performance helpers: debounce/throttle utilities (WebSite/src/utils/timing.js).",
        "Machine UI performance helpers: Tk debounce/throttle utilities (ui_timing.py).",
        "Product metadata support: new products.details column for brand/size/net weight display.",
    ],
    "improved": [
        "Updated physical tray placement (slot_number → product) to match the latest machine layout.",
        "Updated product prices to match the latest 'Selling Price' list.",
        "Customer product grid ordering now matches physical tray stacking (heaviest at bottom shown last).",
        "Product detail modal now shows brand/size/net weight when available.",
        "Reduced cloud API traffic: product sync is throttled; transactions are still sent immediately after purchases.",
        "Smoother admin charts: resize redraw is debounced to avoid lag during fast scrolling/resizing.",
        "Smoother website interactions: heavy chart refresh is debounced and rapid key navigation is raf-throttled.",
    ],
    "bugs_fixed": [
        "Corrected pad naming alignment (Regular w/ wings, Regular w/o wings) so UI/DB naming matches the final product list.",
        "Resolved inconsistent pricing between earlier drafts and the final selling-price sheet.",
    ],
    "future": [
        "Optional: bi-directional sync (cloud → machine) for remote restock/price changes if needed.",
        "Optional: secure machine identity + RLS policies for multi-machine deployments.",
    ],
}

# All versions in order (oldest first)
PATCH_HISTORY = [PATCH_v0_01, PATCH_v0_02, PATCH_v0_03, PATCH_v1_0_0, PATCH_v1_0_1]


def get_patch_notes_text() -> str:
    """Return a single string with full version history for the Patch Notes dialog.
    Latest version is shown first (at the top), oldest at the bottom.
    """
    lines = [f"Patch Notes / Updates  —  Current: {VERSION}", ""]
    for patch in reversed(PATCH_HISTORY):
        v = patch["version"]
        lines.extend([f"═══════════════════════════════════  {v}  ═══════════════════════════════════", ""])
        if patch["added"]:
            lines.extend(["——— ADDED ———", *("• " + item for item in patch["added"]), ""])
        if patch["improved"]:
            lines.extend(["——— IMPROVED ———", *("• " + item for item in patch["improved"]), ""])
        if patch["bugs_fixed"]:
            lines.extend(["——— BUGS FIXED ———", *("• " + item for item in patch["bugs_fixed"]), ""])
        if patch["future"]:
            lines.extend(["——— FUTURE UPDATES ———", *("• " + item for item in patch["future"]), ""])
        lines.append("")
    return "\n".join(lines)


def get_last_updated() -> str:
    """Return a string for 'last updated' display (e.g. in dialog title)."""
    return datetime.now().strftime("%Y-%m-%d")
