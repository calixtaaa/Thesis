"""
Patch notes for the Hygiene Vending Machine.
Central place for: Version, Added, Improved, Bugs fixed, and Future updates.
"""
from datetime import datetime


# App version (bump when releasing; shown in title, footers, and patch notes)
VERSION = "v.0.01"


# ---------------------------------------------------------------------------
#  Content sections (edit here to update the in-app Patch Notes dialog)
# ---------------------------------------------------------------------------

ADDED = [
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
]

IMPROVED = [
    "UI/UX: consistent fonts (Segoe UI), card-style layout, step-by-step instructions (Step 1–3).",
    "Payment, quantity, cash, and RFID reload screens for consistent look and clarity.",
    "Pill-shaped search bar with placeholder 'Search for products'.",
    "Code organization: admin (admin.py), staff (staff.py), database (database.py) for cleaner main.py.",
    "Admin and staff icons moved into hamburger sidebar; small navbar toggle.",
    "7-inch touchscreen responsiveness and button clarity.",
]

BUGS_FIXED = [
    "SMS provider switched from Fast2SMS to PhilSMS for Philippine numbers (+63).",
    "Export Sales (Excel) limited to admin-only; button removed from user UI, available in admin dashboard.",
    "Product list: full seed of 10 hygiene products (delete vending.db once to re-seed if needed).",
    "Theme slider and debug log variable references corrected to avoid AttributeError.",
    "Payment screen buttons no longer clipped; font family and wraplength improved.",
]

FUTURE_UPDATES = [
    "Resolve TclError on main menu rebuild (search/scroll/theme interactions) if it recurs.",
    "Optional: SMS low-stock alerts via PhilSMS when stock falls below threshold.",
    "Optional: real hardware integration (RPi.GPIO stepper/coin hopper) on Raspberry Pi.",
    "Optional: backup/restore for admin credentials and product list.",
]


def get_patch_notes_text() -> str:
    """Return a single string suitable for the Patch Notes messagebox."""
    lines = [
        f"Patch Notes / Updates  —  {VERSION}",
        "",
        "——— ADDED ———",
        *("• " + item for item in ADDED),
        "",
        "——— IMPROVED ———",
        *("• " + item for item in IMPROVED),
        "",
        "——— BUGS FIXED ———",
        *("• " + item for item in BUGS_FIXED),
        "",
        "——— FUTURE UPDATES ———",
        *("• " + item for item in FUTURE_UPDATES),
    ]
    return "\n".join(lines)


def get_last_updated() -> str:
    """Return a string for 'last updated' display (e.g. in dialog title)."""
    return datetime.now().strftime("%Y-%m-%d")
