import os
import sys
import time
import uuid
import json
import datetime
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, simpledialog

from admin.admin import AdminMixin
from admin.reports import get_reports_dir
from staff.staff import StaffMixin
from database import (
    init_db,
    get_admin_credentials,
    update_admin_credentials,
    get_all_products,
    get_product_by_id,
    decrement_stock,
    record_transaction,
    get_user_by_uid,
    create_user,
    update_user_balance,
    adjust_user_balance,
    restock_product,
    export_sales_report,
    get_admin_overview_stats,
    get_sales_trend_data,
    get_monthly_sales_data,
    get_top_selling_products,
    get_low_stock_chart_data,
)
from patchNotes import get_patch_notes_text, VERSION

# ======================
#  ENV & GPIO HANDLING
# ======================

ON_RPI = False
try:
    import RPi.GPIO as GPIO  # type: ignore
    ON_RPI = True
except ImportError:
    # Simple mock for development on Windows
    class MockGPIO:
        BCM = "BCM"
        OUT = "OUT"
        IN = "IN"
        HIGH = 1
        LOW = 0
        PUD_UP = "PUD_UP"
        FALLING = "FALLING"

        def setmode(self, *_a, **_k): pass
        def setwarnings(self, *_a, **_k): pass
        def setup(self, *_a, **_k): pass
        def output(self, *_a, **_k): pass
        def cleanup(self): pass
        def add_event_detect(self, *_a, **_k): pass

    GPIO = MockGPIO()  # type: ignore

# ======================
#  CONFIG & CONSTANTS
# ======================

BASE_DIR = Path(__file__).resolve().parent
DEBUG_LOGS_DIR = BASE_DIR / "debug_logs"

# Base layout size (matches current design)
BASE_APP_W = 800
BASE_APP_H = 480

# Simple theming (light / dark) – expanded for a more polished UI
THEMES = {
    "light": {
        "bg": "#f8fafc",
        "fg": "#1e293b",
        "button_bg": "#f1f5f9",
        "button_fg": "#1e293b",
        "accent": "#0d9488",
        "accent_hover": "#0f766e",
        "card_bg": "#ffffff",
        "card_border": "#e2e8f0",
        "search_bg": "#f1f5f9",
        "search_border": "#e2e8f0",
        "muted": "#64748b",
    },
    "dark": {
        "bg": "#0f172a",
        "fg": "#e2e8f0",
        "button_bg": "#1e293b",
        "button_fg": "#e2e8f0",
        "accent": "#14b8a6",
        "accent_hover": "#2dd4bf",
        "card_bg": "#1e293b",
        "card_border": "#334155",
        "search_bg": "#1e293b",
        "search_border": "#334155",
        "muted": "#94a3b8",
    },
}

UI_FONT = "Segoe UI"
UI_FONT_BOLD = (UI_FONT, 20, "bold")
UI_FONT_TITLE = (UI_FONT, 18, "bold")
UI_FONT_BODY = (UI_FONT, 12)
UI_FONT_SMALL = (UI_FONT, 10)
UI_FONT_BUTTON = (UI_FONT, 12, "bold")


def _hover_scale_btn(btn, normal_padx=10, normal_pady=6, hover_padx=14, hover_pady=10):
    """Make button appear to scale up on hover by increasing padding."""
    def on_enter(_e):
        if btn.winfo_exists():
            btn.configure(padx=hover_padx, pady=hover_pady)
    def on_leave(_e):
        if btn.winfo_exists():
            btn.configure(padx=normal_padx, pady=normal_pady)
    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)

# Simple pin assignments (adjust on real Pi)
PRODUCT_STEPPER_PINS = {
    1: {"step": 17, "dir": 27},   # Slot 1
    2: {"step": 22, "dir": 23},   # Slot 2
}
COIN_HOPPER_PIN = 24
STEPS_PER_PRODUCT = 200  # adjust per mechanism
COINS_PER_SECOND = 5     # for hopper simulation
COIN_VALUE = 1.0         # 1 peso per coin (example)


# ======================
#  HARDWARE ABSTRACTION
# ======================

def gpio_init():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)

    # Stepper pins
    for cfg in PRODUCT_STEPPER_PINS.values():
        GPIO.setup(cfg["step"], GPIO.OUT)
        GPIO.setup(cfg["dir"], GPIO.OUT)

    # Hopper
    GPIO.setup(COIN_HOPPER_PIN, GPIO.OUT)

def dispense_from_slot(slot_number: int, quantity: int = 1):
    pins = PRODUCT_STEPPER_PINS.get(slot_number)
    if not pins:
        print(f"[HW] No stepper pins configured for slot {slot_number}")
        return

    print(f"[HW] Dispensing from slot {slot_number} x{quantity}")
    steps = STEPS_PER_PRODUCT * quantity
    delay = 0.001  # 1ms

    GPIO.output(pins["dir"], GPIO.HIGH)
    for _ in range(steps):
        GPIO.output(pins["step"], GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(pins["step"], GPIO.LOW)
        time.sleep(delay)

def dispense_change(amount: float):
    coins_to_dispense = int(amount // COIN_VALUE)
    if coins_to_dispense <= 0:
        return
    print(f"[HW] Dispensing change: {coins_to_dispense} coins (₱{amount:.2f})")
    duration = coins_to_dispense / COINS_PER_SECOND
    GPIO.output(COIN_HOPPER_PIN, GPIO.HIGH)
    time.sleep(duration)
    GPIO.output(COIN_HOPPER_PIN, GPIO.LOW)


# ======================
#  SIMPLE CASH SESSION
#  (Simulated for now)
# ======================

class CashSession:
    """
    For now: simulated cash input using "+" buttons on GUI.
    On real machine, replace with pulse‑based reader.
    """
    def __init__(self):
        self.total_amount = 0.0

    def reset(self):
        self.total_amount = 0.0

    def add(self, value: float):
        self.total_amount += value

    def get_amount(self) -> float:
        return self.total_amount

cash_session = CashSession()


# ======================
#  TKINTER GUI
# ======================

class MainApp(AdminMixin, StaffMixin, tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"Hygiene Vending Machine  {VERSION}")

        # On the Raspberry Pi 7\" touchscreen, use fullscreen.
        # On desktop (development), use a resizable 800x480 window.
        if ON_RPI:
            self.attributes("-fullscreen", True)
        else:
            # Fixed-size window that matches the LCD target aspect.
            self.geometry(f"{BASE_APP_W}x{BASE_APP_H}")
            self.minsize(BASE_APP_W, BASE_APP_H)
            self.maxsize(BASE_APP_W, BASE_APP_H)
            self.resizable(False, False)

        # Auto-fit scale for different LCD resolutions (keeps layout consistent)
        try:
            self.after(50, lambda: self._apply_lcd_fit(profile="customer"))
        except Exception:
            pass

        self.current_product = None
        self.current_quantity = 1

        # Theme state
        self.current_theme_name = "light"
        self.current_theme = THEMES[self.current_theme_name]
        self.configure(bg=self.current_theme["bg"])

        # Icon images (loaded lazily if files exist)
        self.staff_icon = None
        self.admin_icon = None
        self.menu_icon = None
        self.search_icon = None
        self.light_theme_icon = None
        self.dark_theme_icon = None

        # Staff icon
        try:
            for name in ("staff.png", "staff_icon.png"):
                staff_path = BASE_DIR / "images" / name
                if staff_path.exists():
                    self.staff_icon = tk.PhotoImage(file=str(staff_path))
                    break
        except Exception:
            self.staff_icon = None

        # Admin icon
        try:
            for name in ("admin.png", "admin_icon.png"):
                admin_path = BASE_DIR / "images" / name
                if admin_path.exists():
                    self.admin_icon = tk.PhotoImage(file=str(admin_path))
                    break
        except Exception:
            self.admin_icon = None

        # Hamburger / menu icon
        try:
            menu_path = BASE_DIR / "images" / "hamburger.png"
            if menu_path.exists():
                # Load and aggressively downscale so it appears as a small navbar icon
                img = tk.PhotoImage(file=str(menu_path))
                # Adjust subsample factors if you later change the SVG export size
                self.menu_icon = img.subsample(4, 4)
        except Exception:
            self.menu_icon = None

        # Search / magnifying glass icon
        try:
            search_path = BASE_DIR / "images" / "magnifying glass.png"
            if search_path.exists():
                img = tk.PhotoImage(file=str(search_path))
                self.search_icon = img.subsample(4, 4)
        except Exception:
            self.search_icon = None

        # Theme icons for light/dark toggle
        try:
            theme_path = BASE_DIR / "images" / "light-mode.png"
            if theme_path.exists():
                img = tk.PhotoImage(file=str(theme_path))
                self.light_theme_icon = img.subsample(5, 5)
        except Exception:
            self.light_theme_icon = None
        try:
            theme_path = BASE_DIR / "images" / "darkMode.png"
            if theme_path.exists():
                img = tk.PhotoImage(file=str(theme_path))
                self.dark_theme_icon = img.subsample(5, 5)
        except Exception:
            self.dark_theme_icon = None

        # Backspace icon for clearing search text
        self.backspace_icon = None
        try:
            backspace_path = BASE_DIR / "images" / "backspace.png"
            if backspace_path.exists():
                img = tk.PhotoImage(file=str(backspace_path))
                self.backspace_icon = img.subsample(4, 4)
        except Exception:
            self.backspace_icon = None

        # Welcome screen logo (medal/icon); optional
        self.welcome_icon = None
        try:
            for name in ("welcome.png", "logo.png", "welcome_icon.png"):
                welcome_path = BASE_DIR / "images" / name
                if welcome_path.exists():
                    self.welcome_icon = tk.PhotoImage(file=str(welcome_path))
                    break
        except Exception:
            self.welcome_icon = None

        # Sidebar / navbar state
        self.role_menu = None
        self.sidebar_frame = None
        self.sidebar_holder = None  # Persistent right teal sidebar (created in main menu)

        # Cart: list of {"product": p, "quantity": int} for order panel
        self.cart = []
        # Checkout snapshot (so totals stay consistent after leaving main menu)
        self.checkout_items = []  # list of {"product": p, "quantity": int}

        self.search_var = tk.StringVar()
        self.theme_animating = False

        # Main content lives here; sidebar (when shown) is a sibling on the right
        self.content_holder = tk.Frame(self, bg=self.current_theme["bg"])
        self.content_holder.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.build_welcome_screen()

    def _apply_lcd_fit(self, profile: str = "customer"):
        """
        Fit the app window to the current display size and lock resizing.
        On Windows dev this helps match whatever LCD resolution you're using.
        """
        if ON_RPI:
            return  # fullscreen already
        try:
            sw = int(self.winfo_screenwidth())
            sh = int(self.winfo_screenheight())
        except Exception:
            sw, sh = BASE_APP_W, BASE_APP_H

        # two profiles: customer = base; admin_staff = slightly larger if screen allows
        target_w, target_h = BASE_APP_W, BASE_APP_H
        if profile == "admin_staff":
            # prefer 1024x600 if available (common 7" LCD); else fallback to base
            if sw >= 1024 and sh >= 600:
                target_w, target_h = 1024, 600

        # If the screen is smaller, clamp to screen size (minus a small margin for window borders)
        margin_w, margin_h = 16, 72
        target_w = min(target_w, max(400, sw - margin_w))
        target_h = min(target_h, max(300, sh - margin_h))

        self.geometry(f"{target_w}x{target_h}")
        self.minsize(target_w, target_h)
        self.maxsize(target_w, target_h)
        self.resizable(False, False)

    # ---------- Screen helpers ----------

    def clear_screen(self):
        # region agent log
        self._debug_log(
            "H5",
            "main.py:clear_screen",
            "clear_screen called",
            {"child_count": len(self.content_holder.winfo_children())},
        )
        # endregion
        try:
            self.unbind_all("<MouseWheel>")
        except Exception:
            pass
        for w in self.content_holder.winfo_children():
            w.destroy()

    def _debug_log(self, hypothesis_id: str, location: str, message: str, data: dict):
        DEBUG_LOGS_DIR.mkdir(parents=True, exist_ok=True)
        payload = {
            "sessionId": "14d174",
            "runId": "initial",
            "hypothesisId": hypothesis_id,
            "location": location,
            "message": message,
            "data": data,
            "timestamp": int(time.time() * 1000),
        }
        with open(DEBUG_LOGS_DIR / "debug-14d174.log", "a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, ensure_ascii=True) + "\n")
        # Keep a compatibility copy in the project root for existing tooling.
        with open(BASE_DIR / "debug-14d174.log", "a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, ensure_ascii=True) + "\n")

    # Data wrappers for extracted admin/staff modules
    def get_user_by_uid_data(self, rfid_uid: str):
        return get_user_by_uid(rfid_uid)

    def get_all_products_data(self):
        return get_all_products()

    def restock_product_data(self, product_id: int, amount: int, new_price: float | None = None):
        return restock_product(product_id, amount, new_price)

    def get_admin_credentials_data(self):
        return get_admin_credentials()

    def update_admin_credentials_data(self, new_username: str, new_password: str):
        return update_admin_credentials(new_username, new_password)

    def get_admin_overview_stats_data(self):
        return get_admin_overview_stats()

    def get_sales_trend_data_points(self, days: int = 15):
        return get_sales_trend_data(days)

    def get_monthly_sales_data_points(self, months: int = 6):
        return get_monthly_sales_data(months)

    def get_top_selling_products_data(self, limit: int = 5):
        return get_top_selling_products(limit)

    def get_low_stock_chart_data_points(self, limit: int = 5):
        return get_low_stock_chart_data(limit)

    def apply_theme_to_widget(self, widget):
        """Apply current theme colors to a widget and its children."""
        try:
            widget.configure(bg=self.current_theme["bg"])
        except tk.TclError:
            pass
        for child in widget.winfo_children():
            if isinstance(child, (tk.Button, tk.Label, tk.Frame)):
                try:
                    if isinstance(child, tk.Button):
                        child.configure(
                            bg=self.current_theme["button_bg"],
                            fg=self.current_theme["button_fg"],
                            activebackground=self.current_theme["button_bg"],
                            activeforeground=self.current_theme["button_fg"],
                        )
                    elif isinstance(child, tk.Label) or isinstance(child, tk.Frame):
                        child.configure(
                            bg=self.current_theme["bg"],
                            fg=self.current_theme["fg"] if isinstance(child, tk.Label) else None,
                        )
                except tk.TclError:
                    pass

    def toggle_theme(self):
        """Switch between light and dark modes and refresh current screen."""
        self.current_theme_name = "dark" if self.current_theme_name == "light" else "light"
        self.current_theme = THEMES[self.current_theme_name]
        self.configure(bg=self.current_theme["bg"])
        self.apply_theme_to_widget(self)

    def animate_button_press(self, button, callback):
        """Play a quick press animation before running a button action."""
        normal_bg = button.cget("bg")
        normal_relief = button.cget("relief")
        normal_bd = button.cget("bd")

        pressed_bg = self.current_theme.get("accent_hover", self.current_theme.get("accent", "#0d9488"))

        try:
            button.configure(bg=pressed_bg, relief=tk.SUNKEN, bd=3)
        except tk.TclError:
            callback()
            return

        def finish():
            if button.winfo_exists():
                try:
                    button.configure(bg=normal_bg, relief=normal_relief, bd=normal_bd)
                except tk.TclError:
                    pass
            callback()

        button.after(100, finish)

    def create_theme_slider(self, parent):
        """Create a small animated theme slider near the hamburger icon."""
        width = 64
        height = 30
        padding = 3
        knob_size = height - (padding * 2)

        track_light = "#DDE6F2"
        track_dark = "#1F2A44"
        knob_fill = "#FFFFFF"
        border_light = "#C8D4E3"
        border_dark = "#2F3B57"

        is_dark = self.current_theme_name == "dark"
        start_x = width - padding - knob_size if is_dark else padding
        icon_image = self.dark_theme_icon if is_dark else self.light_theme_icon

        canvas = tk.Canvas(
            parent,
            width=width,
            height=height,
            bg=self.current_theme["bg"],
            highlightthickness=0,
            bd=0,
        )

        track = canvas.create_oval(
            padding,
            padding,
            width - padding,
            height - padding,
            fill=track_dark if is_dark else track_light,
            outline=border_dark if is_dark else border_light,
        )
        knob = canvas.create_oval(
            start_x,
            padding,
            start_x + knob_size,
            padding + knob_size,
            fill=knob_fill,
            outline="",
        )

        knob_icon = None
        if icon_image is not None:
            knob_icon = canvas.create_image(
                start_x + (knob_size / 2),
                padding + (knob_size / 2),
                image=icon_image,
            )

        def animate_toggle(_event=None):
            if self.theme_animating:
                return

            self.theme_animating = True
            target_dark = self.current_theme_name != "dark"
            end_x = width - padding - knob_size if target_dark else padding
            current_coords = canvas.coords(knob)
            current_x = current_coords[0]
            step_count = 10
            delta = (end_x - current_x) / step_count if step_count else 0

            def step(index=0):
                if index >= step_count:
                    self.current_theme_name = "dark" if target_dark else "light"
                    self.current_theme = THEMES[self.current_theme_name]
                    self.configure(bg=self.current_theme["bg"])
                    self.theme_animating = False
                    self.build_main_menu()
                    return

                canvas.move(knob, delta, 0)
                if knob_icon is not None:
                    canvas.move(knob_icon, delta, 0)
                progress = (index + 1) / step_count
                if progress > 0.5:
                    canvas.itemconfigure(
                        track,
                        fill=track_dark if target_dark else track_light,
                        outline=border_dark if target_dark else border_light,
                    )
                canvas.after(18, lambda: step(index + 1))

            step()

        canvas.bind("<Button-1>", animate_toggle)
        return canvas

    def add_theme_toggle_footer(self):
        """Add a bottom bar with a theme toggle button to the current screen (inside content_holder so it clears on screen change)."""
        bottom = tk.Frame(self.content_holder, bg=self.current_theme["bg"])
        bottom.pack(side=tk.BOTTOM, fill=tk.X, pady=4)
        tk.Label(
            bottom,
            text=f"SyntaxError™  ·  {VERSION}",
            font=UI_FONT_SMALL,
            bg=self.current_theme["bg"],
            fg=self.current_theme.get("muted", self.current_theme["fg"]),
        ).pack(side=tk.LEFT, padx=10)
        self.add_ph_datetime_label(bottom)
        tk.Button(
            bottom,
            text=f"Theme: {self.current_theme_name.capitalize()}",
            command=self.toggle_theme,
            font=UI_FONT_BODY,
            bg=self.current_theme["button_bg"],
            fg=self.current_theme["button_fg"],
        ).pack(side=tk.RIGHT, padx=10)
        self.apply_theme_to_widget(self.content_holder)

    def add_ph_datetime_label(self, parent):
        """Show a live Philippine date/time label inside the given parent."""
        label = tk.Label(
            parent,
            font=UI_FONT_SMALL,
            bg=self.current_theme["bg"],
            fg=self.current_theme.get("muted", self.current_theme["fg"]),
        )
        label.pack(side=tk.RIGHT, padx=10)

        ph_tz = datetime.timezone(datetime.timedelta(hours=8))

        def _refresh():
            if not label.winfo_exists():
                return
            now = datetime.datetime.now(ph_tz)
            label.config(text=now.strftime("PH Time: %b %d, %Y %I:%M:%S %p"))
            label.after(1000, _refresh)

        _refresh()
        return label

    def show_patch_notes_dialog(self):
        """Show recent UI and feature updates from patchNotes.py."""
        messagebox.showinfo(f"Patch Notes  ·  {VERSION}", get_patch_notes_text())

    def show_help_dialog(self):
        """Explain the basic usage steps to the user."""
        message = (
            "How to use the vending machine:\n\n"
            "1. Select Product – Tap the item you want.\n"
            "2. Quantity – Choose how many pieces you need.\n"
            "3. Payment – Pay with Cash or RFID Card, then wait for the product to be dispensed.\n\n"
            "You can also buy a new RFID card or reload an existing card using the buttons below."
        )
        messagebox.showinfo("How to use", message)

    def show_role_menu(self):
        """Toggle a right-side teal sidebar for Dashboard / Staff / Admin (hamburger menu)."""
        # region agent log
        self._debug_log(
            "H3",
            "main.py:show_role_menu",
            "hamburger action invoked",
            {
                "sidebar_exists_before": bool(self.sidebar_frame and self.sidebar_frame.winfo_exists()),
                "current_theme": self.current_theme_name,
            },
        )
        # endregion
        # If sidebar already open, close it
        if self.sidebar_frame is not None and self.sidebar_frame.winfo_exists():
            self.sidebar_frame.destroy()
            self.sidebar_frame = None
            return

        # Teal-green sidebar on the right (fixed width, anchored right)
        sidebar_width = 220
        sidebar_bg = self.current_theme.get("accent", "#0d9488")
        strip_bg = "#14b8a6" if self.current_theme_name == "light" else "#2dd4bf"  # Slightly lighter strip per button
        sidebar = tk.Frame(self, bg=sidebar_bg, width=sidebar_width)
        sidebar.place(relx=1.0, x=0, y=0, anchor="ne", relheight=1.0)

        tk.Label(
            sidebar,
            text="Menu",
            font=(UI_FONT, 12, "bold"),
            bg=sidebar_bg,
            fg="#ffffff",
        ).pack(anchor="w", padx=14, pady=(14, 10))

        def make_nav_button(text, command):
            btn = tk.Button(
                sidebar,
                text=text,
                anchor="w",
                font=(UI_FONT, 11, "bold"),
                command=command,
                bg=strip_bg,
                fg="#ffffff",
                activebackground=sidebar_bg,
                activeforeground="#ffffff",
                relief=tk.FLAT,
                padx=12,
                pady=10,
            )
            btn.pack(fill=tk.X, padx=10, pady=4)
            return btn

        # Dashboard – close sidebar and stay on current screen
        make_nav_button("Dashboard", lambda: self.show_role_menu())

        # Staff restock screen
        make_nav_button(
            "Staff",
            lambda: (self.show_role_menu(), self.enter_restock_mode()),
        )

        # Admin dashboard
        make_nav_button(
            "Admin",
            lambda: (self.show_role_menu(), self.enter_admin_dashboard()),
        )

        # Back to main screen: show thank-you in-app then return to welcome screen
        def go_back_to_welcome():
            self.show_role_menu()
            self.show_thank_you_screen()

        make_nav_button("Back to main screen", go_back_to_welcome)

        self.sidebar_frame = sidebar
        # region agent log
        self._debug_log(
            "H3",
            "main.py:show_role_menu",
            "sidebar created",
            {
                "sidebar_width": sidebar_width,
                "sidebar_exists_after": bool(self.sidebar_frame and self.sidebar_frame.winfo_exists()),
            },
        )
        # endregion

    # ---------- Welcome Screen ----------

    def build_welcome_screen(self):
        """Show welcome page (icon, Welcome / Syntaxer, Start Order) before dashboard."""
        if hasattr(self, "_apply_lcd_fit"):
            try:
                self._apply_lcd_fit(profile="customer")
            except Exception:
                pass
        if self.sidebar_holder is not None and self.sidebar_holder.winfo_exists():
            self.sidebar_holder.destroy()
            self.sidebar_holder = None
        self.clear_screen()
        self.configure(bg=self.current_theme["bg"])
        self.content_holder.configure(bg=self.current_theme["bg"])

        # Centered container (inside content_holder)
        center = tk.Frame(self.content_holder, bg=self.current_theme["bg"])
        center.place(relx=0.5, rely=0.5, anchor="center")

        # Optional logo / icon at top
        if self.welcome_icon is not None:
            icon_label = tk.Label(
                center,
                image=self.welcome_icon,
                bg=self.current_theme["bg"],
            )
            icon_label.pack(pady=(0, 16))
            icon_label.image = self.welcome_icon

        # "Welcome" line
        tk.Label(
            center,
            text="Welcome",
            font=(UI_FONT, 28, "bold"),
            bg=self.current_theme["bg"],
            fg=self.current_theme["fg"],
        ).pack(pady=(0, 2))

        # "Syntaxer" line
        tk.Label(
            center,
            text="Syntaxer",
            font=(UI_FONT, 24, "bold"),
            bg=self.current_theme["bg"],
            fg=self.current_theme["fg"],
        ).pack(pady=(0, 28))

        # Start Order button – accent, rounded look via padding
        accent = self.current_theme.get("accent", "#0d9488")
        start_btn = tk.Button(
            center,
            text="Start Order",
            font=(UI_FONT, 14, "bold"),
            bg=accent,
            fg="#ffffff",
            activebackground=self.current_theme.get("accent_hover", accent),
            activeforeground="#ffffff",
            relief=tk.FLAT,
            padx=40,
            pady=12,
            cursor="hand2",
            command=self.build_main_menu,
        )
        start_btn.pack(pady=0)

        self.apply_theme_to_widget(self.content_holder)
        # Re-apply accent for the button (apply_theme_to_widget overwrites it)
        if start_btn.winfo_exists():
            try:
                start_btn.configure(
                    bg=self.current_theme.get("accent", accent),
                    fg="#ffffff",
                    activebackground=self.current_theme.get("accent_hover", accent),
                    activeforeground="#ffffff",
                )
            except tk.TclError:
                pass

    def show_thank_you_screen(self):
        """Show 'Thank you, come again!' in-app, then return to welcome screen."""
        if self.sidebar_holder is not None and self.sidebar_holder.winfo_exists():
            self.sidebar_holder.destroy()
            self.sidebar_holder = None
        self.clear_screen()
        self.content_holder.configure(bg=self.current_theme["bg"])

        center = tk.Frame(self.content_holder, bg=self.current_theme["bg"])
        center.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(
            center,
            text="Thank you, come again!",
            font=(UI_FONT, 22, "bold"),
            bg=self.current_theme["bg"],
            fg=self.current_theme["fg"],
        ).pack(pady=(0, 24))

        def go_welcome():
            self.build_welcome_screen()

        ok_btn = tk.Button(
            center,
            text="OK",
            font=(UI_FONT, 12, "bold"),
            command=go_welcome,
            bg=self.current_theme.get("accent", "#0d9488"),
            fg="#ffffff",
            relief=tk.FLAT,
            padx=24,
            pady=8,
        )
        ok_btn.pack(pady=0)
        self.after(3500, go_welcome)  # Auto-return to welcome after 3.5 s

    # ---------- Main Menu ----------

    def build_main_menu(self):
        if hasattr(self, "_apply_lcd_fit"):
            try:
                self._apply_lcd_fit(profile="customer")
            except Exception:
                pass
        self.clear_screen()
        all_products = get_all_products()

        # Destroy any existing sidebar
        if self.sidebar_holder is not None and self.sidebar_holder.winfo_exists():
            self.sidebar_holder.destroy()
            self.sidebar_holder = None

        # Right teal sidebar – IPINAPAKITA LAMANG kapag WALANG cart (hindi sa quantity/order section)
        if not self.cart:
            sidebar_width = 220
            sidebar_bg = "#0d9488"
            strip_bg = "#14b8a6"
            self.sidebar_holder = tk.Frame(self, bg=sidebar_bg, width=sidebar_width)
            self.sidebar_holder.pack_propagate(False)
            self.sidebar_holder.pack(side=tk.RIGHT, fill=tk.Y)

            tk.Label(
                self.sidebar_holder,
                text="Menu",
                font=(UI_FONT, 12, "bold"),
                bg=sidebar_bg,
                fg="#ffffff",
            ).pack(anchor="w", padx=14, pady=(14, 10))

            hover_strip = "#2dd4bf"
            def make_nav_btn(text, cmd):
                b = tk.Button(
                    self.sidebar_holder,
                    text=text,
                    anchor="w",
                    font=(UI_FONT, 11, "bold"),
                    command=cmd,
                    bg=strip_bg,
                    fg="#ffffff",
                    activebackground=hover_strip,
                    activeforeground="#ffffff",
                    relief=tk.FLAT,
                    padx=12,
                    pady=10,
                    cursor="hand2",
                )
                b.pack(fill=tk.X, padx=10, pady=4)
                def on_enter(_e):
                    if b.winfo_exists():
                        b.configure(bg=hover_strip)
                def on_leave(_e):
                    if b.winfo_exists():
                        b.configure(bg=strip_bg)
                b.bind("<Enter>", on_enter)
                b.bind("<Leave>", on_leave)
                return b

            make_nav_btn("Dashboard", lambda: None)
            make_nav_btn("Staff", lambda: self.enter_restock_mode())
            make_nav_btn("Admin", lambda: self.enter_admin_dashboard())
            make_nav_btn("Back to main screen", lambda: self.show_thank_you_screen())

        # Left + order panel area (inside content_holder)
        main_row = tk.Frame(self.content_holder, bg=self.current_theme["bg"])
        main_row.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        left_part = tk.Frame(main_row, bg=self.current_theme["bg"])
        left_part.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        top = tk.Frame(left_part, bg=self.current_theme["bg"])
        top.pack(side=tk.TOP, fill=tk.X)

        header = tk.Frame(top, bg=self.current_theme["bg"])
        header.pack(side=tk.TOP, fill=tk.X, pady=(2, 4), padx=10)

        title_block = tk.Frame(header, bg=self.current_theme["bg"])
        title_block.pack(side=tk.LEFT)
        tk.Label(
            title_block,
            text="Syntax Error",
            font=UI_FONT_TITLE,
            bg=self.current_theme["bg"],
            fg=self.current_theme["fg"],
        ).pack(anchor="w")
        tk.Label(
            title_block,
            text="Main menu",
            font=UI_FONT_SMALL,
            bg=self.current_theme["bg"],
            fg=self.current_theme.get("muted", self.current_theme["fg"]),
        ).pack(anchor="w")

        # Theme toggle only
        icons_frame = tk.Frame(header, bg=self.current_theme["bg"])
        icons_frame.pack(side=tk.RIGHT)
        self.create_theme_slider(icons_frame).pack(side=tk.RIGHT, padx=6, pady=0)

        products = all_products

        # Scrollable product area (inside left_part)
        content_frame = tk.Frame(left_part, bg=self.current_theme["bg"])
        content_frame.pack(expand=True, fill=tk.BOTH)

        canvas = tk.Canvas(
            content_frame,
            bg=self.current_theme["bg"],
            highlightthickness=0,
        )
        scrollbar = tk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        grid = tk.Frame(canvas, bg=self.current_theme["bg"])
        canvas.create_window((0, 0), window=grid, anchor="nw")

        # 2 products per row (2 columns, scroll for more rows)
        for col in range(2):
            grid.grid_columnconfigure(col, weight=1)

        card_bg = self.current_theme.get("card_bg", self.current_theme["button_bg"])
        card_border = self.current_theme.get("card_border", "#e2e8f0")
        selected_bg = "#bbf7d0" if self.current_theme_name == "light" else "#14532d"
        selected_border = self.current_theme.get("accent", "#0d9488")
        placeholder_bg = "#cbd5e1" if self.current_theme_name == "light" else "#475569"
        # Mas compact – bawasan empty space, mas maraming products visible
        placeholder_size = 110

        def cart_has(p):
            return any(e["product"]["id"] == p["id"] for e in self.cart)

        def add_to_cart(p):
            if p["current_stock"] <= 0:
                return
            self.cart.append({"product": p, "quantity": 1})
            self.build_main_menu()

        def remove_from_cart(p):
            self.cart = [e for e in self.cart if e["product"]["id"] != p["id"]]
            self.build_main_menu()

        for idx, p in enumerate(products):
            in_cart = cart_has(p)
            r, c = idx // 2, idx % 2  # 2 by N: 2 products per line

            card = tk.Frame(
                grid,
                bg=selected_bg if in_cart else card_bg,
                highlightthickness=2,
                highlightbackground=selected_border if in_cart else card_border,
            )
            card.grid(row=r, column=c, padx=6, pady=6, sticky="nsew")
            grid.grid_rowconfigure(r, weight=1)

            # Placeholder (gray square for product image) – compact
            placeholder = tk.Frame(card, bg=placeholder_bg, width=placeholder_size, height=placeholder_size)
            placeholder.pack(pady=(8, 6), padx=8, fill=tk.NONE)
            placeholder.pack_propagate(False)

            # Add (+) or Remove (X) button
            if in_cart:
                action_btn = tk.Button(
                    card,
                    text="✕",
                    font=(UI_FONT, 14, "bold"),
                    fg="#ffffff",
                    bg=self.current_theme.get("accent", "#0d9488"),
                    activeforeground="#ffffff",
                    activebackground=self.current_theme.get("accent_hover", "#0f766e"),
                    relief=tk.FLAT,
                    width=3,
                    command=lambda prod=p: remove_from_cart(prod),
                )
            else:
                action_btn = tk.Button(
                    card,
                    text="+",
                    font=(UI_FONT, 18, "bold"),
                    fg="#ffffff",
                    bg=self.current_theme.get("accent", "#0d9488"),
                    activeforeground="#ffffff",
                    activebackground=self.current_theme.get("accent_hover", "#0f766e"),
                    relief=tk.FLAT,
                    width=3,
                    state=tk.NORMAL if p["current_stock"] > 0 else tk.DISABLED,
                    command=lambda prod=p: add_to_cart(prod),
                )
            action_btn.pack(pady=(0, 8))

        def _set_scroll_region():
            try:
                if not canvas.winfo_exists() or not grid.winfo_exists():
                    return
                b = canvas.bbox("all")
                if b:
                    canvas.configure(scrollregion=b)
            except tk.TclError:
                pass

        def _on_frame_configure(_event):
            try:
                if not canvas.winfo_exists() or not grid.winfo_exists():
                    return
                self.after(50, _set_scroll_region)
            except tk.TclError:
                pass

        grid.bind("<Configure>", _on_frame_configure)
        self.after(100, _set_scroll_region)

        def _on_mousewheel(event):
            try:
                if not canvas.winfo_exists():
                    return
                delta = -1 * int(event.delta / 120)
                canvas.yview_scroll(delta, "units")
                y0, y1 = canvas.yview()
                if y1 > 1.0:
                    canvas.yview_moveto(max(0.0, 1.0 - (y1 - y0)))
            except (tk.TclError, AttributeError):
                pass

        canvas.bind("<MouseWheel>", _on_mousewheel)

        # Order panel (dark green) – right of left_part, only when cart has items
        order_panel_width = 260
        panel_bg = "#0f766e" if self.current_theme_name == "light" else "#134e4a"
        if self.cart:
            order_panel = tk.Frame(main_row, bg=panel_bg, width=order_panel_width)
            order_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=0, pady=0)
            order_panel.pack_propagate(False)

            tk.Button(
                order_panel,
                text="Cancel",
                font=(UI_FONT, 11, "bold"),
                fg="#ffffff",
                bg=panel_bg,
                activeforeground="#ffffff",
                activebackground=self.current_theme.get("accent_hover", "#0f766e"),
                relief=tk.FLAT,
                padx=16,
                pady=8,
                command=lambda: (self.cart.clear(), self.build_main_menu()),
            ).pack(side=tk.TOP, fill=tk.X, padx=10, pady=(10, 8))

            for entry in self.cart:
                prod = entry["product"]
                qty_var = tk.IntVar(value=entry["quantity"])

                row = tk.Frame(order_panel, bg=panel_bg)
                row.pack(side=tk.TOP, fill=tk.X, padx=10, pady=4)

                tk.Label(
                    row,
                    text=prod["name"][:18] + ("…" if len(prod["name"]) > 18 else ""),
                    font=UI_FONT_SMALL,
                    bg=panel_bg,
                    fg="#ffffff",
                ).pack(anchor="center")

                ctrl = tk.Frame(row, bg=panel_bg)
                ctrl.pack(anchor="center", pady=2)

                tk.Button(
                    ctrl,
                    text="-",
                    font=(UI_FONT, 12, "bold"),
                    fg="#ffffff",
                    bg=panel_bg,
                    relief=tk.FLAT,
                    width=2,
                    command=lambda e=entry: (e.update({"quantity": max(1, e["quantity"] - 1)}), self.build_main_menu()),
                ).pack(side=tk.LEFT, padx=(0, 6))
                lbl = tk.Label(ctrl, textvariable=qty_var, font=(UI_FONT, 12, "bold"), bg=panel_bg, fg="#ffffff", width=3)
                lbl.pack(side=tk.LEFT, padx=(0, 6))
                tk.Button(
                    ctrl,
                    text="+",
                    font=(UI_FONT, 12, "bold"),
                    fg="#ffffff",
                    bg=panel_bg,
                    relief=tk.FLAT,
                    width=2,
                    command=lambda e=entry: (e.update({"quantity": min(e["product"]["current_stock"], e["quantity"] + 1)}), self.build_main_menu()),
                ).pack(side=tk.LEFT)

            tk.Button(
                order_panel,
                text="Confirm Order",
                font=(UI_FONT, 12, "bold"),
                fg="#ffffff",
                bg=self.current_theme.get("accent", "#0d9488"),
                activeforeground="#ffffff",
                activebackground=self.current_theme.get("accent_hover", "#0f766e"),
                relief=tk.FLAT,
                padx=16,
                pady=10,
                command=lambda: self._confirm_cart_order(),
            ).pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(8, 12))

        # Footer: isang linya lang, walang duplicate text sa gilid
        bottom = tk.Frame(self.content_holder, bg=self.current_theme["bg"])
        bottom.pack(side=tk.BOTTOM, fill=tk.X, pady=(6, 8))

        accent = self.current_theme.get("accent", "#4CAF50")
        accent_hover = self.current_theme.get("accent_hover", "#2dd4bf")
        reload_btn = tk.Button(
            bottom,
            text="Reload (RFID)",
            command=self.reload_card_flow,
            font=UI_FONT_BUTTON,
            bg=accent,
            fg="#ffffff",
            activebackground=accent_hover,
            activeforeground="#ffffff",
            relief=tk.FLAT,
            padx=14,
            pady=6,
            cursor="hand2",
        )
        reload_btn.pack(side=tk.LEFT, padx=(12, 6))
        reload_btn.bind("<Enter>", lambda e: reload_btn.configure(bg=accent_hover) if reload_btn.winfo_exists() else None)
        reload_btn.bind("<Leave>", lambda e: reload_btn.configure(bg=accent) if reload_btn.winfo_exists() else None)
        buy_btn = tk.Button(
            bottom,
            text="Buy RFID Card",
            command=self.buy_card_flow,
            font=UI_FONT_BUTTON,
            bg=accent,
            fg="#ffffff",
            activebackground=accent_hover,
            activeforeground="#ffffff",
            relief=tk.FLAT,
            padx=14,
            pady=6,
            cursor="hand2",
        )
        buy_btn.pack(side=tk.LEFT, padx=6)
        buy_btn.bind("<Enter>", lambda e: buy_btn.configure(bg=accent_hover) if buy_btn.winfo_exists() else None)
        buy_btn.bind("<Leave>", lambda e: buy_btn.configure(bg=accent) if buy_btn.winfo_exists() else None)

        tk.Button(
            bottom,
            text="How to use?",
            command=self.show_help_dialog,
            font=UI_FONT_BODY,
            bg=self.current_theme["bg"],
            fg=self.current_theme["fg"],
            activebackground=self.current_theme["button_bg"],
            activeforeground=self.current_theme["fg"],
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=self.current_theme.get("card_border", "#e2e8f0"),
            padx=12,
            pady=6,
            cursor="hand2",
        ).pack(side=tk.LEFT, padx=6)
        tk.Button(
            bottom,
            text="Patch Notes",
            command=self.show_patch_notes_dialog,
            font=UI_FONT_BODY,
            bg=self.current_theme["bg"],
            fg=self.current_theme["fg"],
            activebackground=self.current_theme["button_bg"],
            activeforeground=self.current_theme["fg"],
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=self.current_theme.get("card_border", "#e2e8f0"),
            padx=12,
            pady=6,
            cursor="hand2",
        ).pack(side=tk.LEFT, padx=6)

        # Isang version label lang (LEFT), datetime sa RIGHT – iwas duplicate sa gilid
        tk.Label(
            bottom,
            text=f"SyntaxError™  ·  {VERSION}",
            font=UI_FONT_SMALL,
            bg=self.current_theme["bg"],
            fg=self.current_theme.get("muted", self.current_theme["fg"]),
        ).pack(side=tk.LEFT, padx=(12, 8))

        self.add_ph_datetime_label(bottom)

        self.apply_theme_to_widget(self.content_holder)
        for b in (reload_btn, buy_btn):
            if b.winfo_exists():
                try:
                    b.configure(
                        bg=self.current_theme.get("accent", "#4CAF50"),
                        fg="#ffffff",
                        activebackground=self.current_theme.get("accent_hover"),
                        activeforeground="#ffffff",
                    )
                except tk.TclError:
                    pass

    def _confirm_cart_order(self):
        """Proceed to review/quantity/payment based on current cart."""
        if not self.cart:
            return
        # snapshot the cart so later screens reflect what was confirmed
        items = [{"product": e["product"], "quantity": int(e.get("quantity", 1) or 1)} for e in self.cart]
        # clamp to current stock (defensive)
        for it in items:
            try:
                it["quantity"] = max(1, min(int(it["product"]["current_stock"]), int(it["quantity"])))
            except Exception:
                it["quantity"] = max(1, int(it["quantity"]))

        self.checkout_items = items
        if len(items) == 1:
            self.current_product = items[0]["product"]
            self.current_quantity = items[0]["quantity"]
            self.show_quantity_screen()
        else:
            self.show_order_review_screen()

    def select_product(self, product_row):
        self.current_product = product_row
        self.current_quantity = 1
        self.checkout_items = []
        self.show_quantity_screen()

    def _get_checkout_items(self):
        """Return a stable list of items for checkout screens and payment flows."""
        if getattr(self, "checkout_items", None):
            return self.checkout_items
        if self.current_product is not None:
            return [{"product": self.current_product, "quantity": int(self.current_quantity or 1)}]
        return []

    def _get_checkout_total(self, items):
        return sum((float(it["product"]["price"]) * int(it["quantity"])) for it in items)

    def _reset_checkout_state(self):
        self.cart.clear()
        self.checkout_items = []
        self.current_product = None
        self.current_quantity = 1

    def show_order_review_screen(self):
        """Step 2 of 3 for multi-item carts: review order & totals."""
        if self.sidebar_holder is not None and self.sidebar_holder.winfo_exists():
            self.sidebar_holder.destroy()
            self.sidebar_holder = None
        self.clear_screen()

        items = self._get_checkout_items()
        if not items:
            self.build_main_menu()
            return

        accent = self.current_theme.get("accent", "#0d9488")
        accent_hover = self.current_theme.get("accent_hover", "#0f766e")
        total = self._get_checkout_total(items)

        frame = tk.Frame(self.content_holder, bg=self.current_theme["bg"])
        frame.pack(expand=True, fill=tk.BOTH)

        tk.Label(
            frame,
            text="Step 2 of 3 – Review order",
            font=UI_FONT_SMALL,
            bg=self.current_theme["bg"],
            fg=self.current_theme.get("muted", self.current_theme["fg"]),
        ).pack(pady=(16, 0))
        tk.Label(
            frame,
            text="Order Summary",
            font=(UI_FONT, 22, "bold"),
            bg=self.current_theme["bg"],
            fg=self.current_theme["fg"],
        ).pack(pady=10)

        card = tk.Frame(
            frame,
            bg=self.current_theme.get("card_bg", self.current_theme["button_bg"]),
            highlightthickness=1,
            highlightbackground=self.current_theme.get("card_border", "#e2e8f0"),
            padx=30,
            pady=22,
        )
        card.pack(padx=40, pady=18)

        list_frame = tk.Frame(card, bg=self.current_theme.get("card_bg", self.current_theme["button_bg"]))
        list_frame.pack(fill=tk.BOTH, expand=True)
        for col in range(3):
            list_frame.grid_columnconfigure(col, weight=1 if col == 0 else 0)

        for r, it in enumerate(items):
            p = it["product"]
            q = int(it["quantity"])
            line_total = float(p["price"]) * q
            tk.Label(
                list_frame,
                text=p["name"],
                font=UI_FONT_BODY,
                bg=self.current_theme.get("card_bg", self.current_theme["button_bg"]),
                fg=self.current_theme["button_fg"],
                anchor="w",
                wraplength=420,
                justify="left",
            ).grid(row=r, column=0, sticky="w", pady=4)
            tk.Label(
                list_frame,
                text=f"x{q}",
                font=(UI_FONT, 12, "bold"),
                bg=self.current_theme.get("card_bg", self.current_theme["button_bg"]),
                fg=self.current_theme.get("muted", self.current_theme["button_fg"]),
                anchor="e",
            ).grid(row=r, column=1, sticky="e", padx=(10, 0))
            tk.Label(
                list_frame,
                text=f"₱{line_total:.2f}",
                font=(UI_FONT, 12, "bold"),
                bg=self.current_theme.get("card_bg", self.current_theme["button_bg"]),
                fg=self.current_theme["button_fg"],
                anchor="e",
            ).grid(row=r, column=2, sticky="e", padx=(18, 0))

        sep = tk.Frame(card, bg=self.current_theme.get("card_border", "#e2e8f0"), height=1)
        sep.pack(fill=tk.X, pady=(14, 10))

        tk.Label(
            card,
            text=f"Total: ₱{total:.2f}",
            font=(UI_FONT, 16, "bold"),
            bg=self.current_theme.get("card_bg", self.current_theme["button_bg"]),
            fg=self.current_theme["button_fg"],
        ).pack(pady=(0, 10))

        continue_btn = tk.Button(
            card,
            text="Continue to payment",
            font=UI_FONT_BUTTON,
            command=self.show_payment_method_screen,
            bg=accent,
            fg="#ffffff",
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor="hand2",
        )
        continue_btn.pack(fill=tk.X, pady=(6, 8))
        _hover_scale_btn(continue_btn, normal_padx=20, normal_pady=10, hover_padx=26, hover_pady=14)
        continue_btn.bind("<Enter>", lambda e: continue_btn.configure(bg=accent_hover) if continue_btn.winfo_exists() else None)
        continue_btn.bind("<Leave>", lambda e: continue_btn.configure(bg=accent) if continue_btn.winfo_exists() else None)

        back_btn = tk.Button(
            frame,
            text="Back to products",
            font=UI_FONT_BODY,
            command=lambda: (self.checkout_items.clear(), self.build_main_menu()),
            bg=self.current_theme["button_bg"],
            fg=self.current_theme["button_fg"],
            relief=tk.FLAT,
            padx=18,
            pady=8,
            cursor="hand2",
        )
        back_btn.pack(pady=10)
        _hover_scale_btn(back_btn, normal_padx=18, normal_pady=8, hover_padx=22, hover_pady=12)
        back_btn.bind("<Enter>", lambda e: back_btn.configure(bg=accent, fg="#ffffff") if back_btn.winfo_exists() else None)
        back_btn.bind("<Leave>", lambda e: back_btn.configure(bg=self.current_theme["button_bg"], fg=self.current_theme["button_fg"]) if back_btn.winfo_exists() else None)

        self.add_theme_toggle_footer()

    # ---------- Quantity Screen ----------

    def show_quantity_screen(self):
        if self.sidebar_holder is not None and self.sidebar_holder.winfo_exists():
            self.sidebar_holder.destroy()
            self.sidebar_holder = None
        self.clear_screen()
        p = self.current_product
        accent = self.current_theme.get("accent", "#0d9488")
        accent_hover = self.current_theme.get("accent_hover", "#0f766e")

        frame = tk.Frame(self.content_holder, bg=self.current_theme["bg"])
        frame.pack(expand=True, fill=tk.BOTH)

        tk.Label(
            frame,
            text="Step 2 of 3 – Choose quantity",
            font=UI_FONT_SMALL,
            bg=self.current_theme["bg"],
            fg=self.current_theme.get("muted", self.current_theme["fg"]),
        ).pack(pady=(16, 0))

        tk.Label(
            frame,
            text="Choose Quantity",
            font=(UI_FONT, 22, "bold"),
            bg=self.current_theme["bg"],
            fg=self.current_theme["fg"],
        ).pack(pady=10)

        card = tk.Frame(
            frame,
            bg=self.current_theme.get("card_bg", self.current_theme["button_bg"]),
            highlightthickness=1,
            highlightbackground=self.current_theme.get("card_border", "#e2e8f0"),
            padx=36,
            pady=28,
        )
        card.pack(padx=40, pady=20)

        tk.Label(
            card,
            text=f"Selected: {p['name']}",
            font=(UI_FONT, 14, "bold"),
            bg=self.current_theme.get("card_bg", self.current_theme["button_bg"]),
            fg=self.current_theme["button_fg"],
            wraplength=420,
            justify="center",
        ).pack(pady=(0, 10))
        tk.Label(
            card,
            text=f"Price: ₱{p['price']:.2f}",
            font=UI_FONT_BODY,
            bg=self.current_theme.get("card_bg", self.current_theme["button_bg"]),
            fg=self.current_theme["button_fg"],
        ).pack(pady=4)
        tk.Label(
            card,
            text=f"Available: {p['current_stock']}",
            font=UI_FONT_BODY,
            bg=self.current_theme.get("card_bg", self.current_theme["button_bg"]),
            fg=self.current_theme.get("muted", self.current_theme["button_fg"]),
        ).pack(pady=(4, 16))

        qty_var = tk.IntVar(value=self.current_quantity)

        def update_qty(delta):
            new = qty_var.get() + delta
            if 1 <= new <= p["current_stock"]:
                qty_var.set(new)

        qty_frame = tk.Frame(card, bg=self.current_theme.get("card_bg", self.current_theme["button_bg"]))
        qty_frame.pack(pady=14)

        minus_btn = tk.Button(
            qty_frame,
            text="−",
            width=4,
            font=(UI_FONT, 16, "bold"),
            command=lambda: update_qty(-1),
            bg=accent,
            fg="#ffffff",
            relief=tk.FLAT,
            padx=12,
            pady=8,
            cursor="hand2",
        )
        minus_btn.pack(side=tk.LEFT, padx=12)
        _hover_scale_btn(minus_btn, normal_padx=12, normal_pady=8, hover_padx=16, hover_pady=12)
        minus_btn.bind("<Enter>", lambda e: minus_btn.configure(bg=accent_hover) if minus_btn.winfo_exists() else None)
        minus_btn.bind("<Leave>", lambda e: minus_btn.configure(bg=accent) if minus_btn.winfo_exists() else None)

        tk.Label(
            qty_frame,
            textvariable=qty_var,
            font=(UI_FONT, 28, "bold"),
            bg=self.current_theme.get("card_bg", self.current_theme["button_bg"]),
            fg=self.current_theme["button_fg"],
            width=5,
        ).pack(side=tk.LEFT, padx=12)
        plus_btn = tk.Button(
            qty_frame,
            text="+",
            width=4,
            font=(UI_FONT, 16, "bold"),
            command=lambda: update_qty(1),
            bg=accent,
            fg="#ffffff",
            relief=tk.FLAT,
            padx=12,
            pady=8,
            cursor="hand2",
        )
        plus_btn.pack(side=tk.LEFT, padx=12)
        _hover_scale_btn(plus_btn, normal_padx=12, normal_pady=8, hover_padx=16, hover_pady=12)
        plus_btn.bind("<Enter>", lambda e: plus_btn.configure(bg=accent_hover) if plus_btn.winfo_exists() else None)
        plus_btn.bind("<Leave>", lambda e: plus_btn.configure(bg=accent) if plus_btn.winfo_exists() else None)

        def proceed():
            self.current_quantity = qty_var.get()
            self.checkout_items = [{"product": p, "quantity": int(self.current_quantity or 1)}]
            self.show_payment_method_screen()

        continue_btn = tk.Button(
            card,
            text="Continue to payment",
            font=UI_FONT_BUTTON,
            width=26,
            height=2,
            command=proceed,
            bg=accent,
            fg="#ffffff",
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor="hand2",
        )
        continue_btn.pack(pady=(18, 10), fill=tk.X)
        _hover_scale_btn(continue_btn, normal_padx=20, normal_pady=10, hover_padx=26, hover_pady=14)
        continue_btn.bind("<Enter>", lambda e: continue_btn.configure(bg=accent_hover) if continue_btn.winfo_exists() else None)
        continue_btn.bind("<Leave>", lambda e: continue_btn.configure(bg=accent) if continue_btn.winfo_exists() else None)

        back_btn = tk.Button(
            frame,
            text="Back to products",
            font=UI_FONT_BODY,
            padx=18,
            pady=8,
            command=lambda: (self.checkout_items.clear(), self.build_main_menu()),
            bg=self.current_theme["button_bg"],
            fg=self.current_theme["button_fg"],
            relief=tk.FLAT,
            cursor="hand2",
        )
        back_btn.pack(pady=10)
        _hover_scale_btn(back_btn, normal_padx=18, normal_pady=8, hover_padx=22, hover_pady=12)
        back_btn.bind("<Enter>", lambda e: back_btn.configure(bg=self.current_theme.get("accent", "#0d9488"), fg="#ffffff") if back_btn.winfo_exists() else None)
        back_btn.bind("<Leave>", lambda e: back_btn.configure(bg=self.current_theme["button_bg"], fg=self.current_theme["button_fg"]) if back_btn.winfo_exists() else None)

        self.add_theme_toggle_footer()

    # ---------- Payment Method ----------

    def show_payment_method_screen(self):
        if self.sidebar_holder is not None and self.sidebar_holder.winfo_exists():
            self.sidebar_holder.destroy()
            self.sidebar_holder = None
        self.clear_screen()
        items = self._get_checkout_items()
        if not items:
            self.build_main_menu()
            return
        total = self._get_checkout_total(items)

        frame = tk.Frame(self.content_holder, bg=self.current_theme["bg"])
        frame.pack(expand=True, fill=tk.BOTH)

        tk.Label(
            frame,
            text="Step 3 of 3 – Choose payment method",
            font=UI_FONT_SMALL,
            bg=self.current_theme["bg"],
            fg=self.current_theme["fg"],
        ).pack(pady=(10, 0))
        tk.Label(
            frame,
            text="Choose Payment Method",
            font=UI_FONT_BOLD,
            bg=self.current_theme["bg"],
            fg=self.current_theme["fg"],
        ).pack(pady=6)

        card = tk.Frame(
            frame,
            bg=self.current_theme["button_bg"],
            bd=1,
            relief="solid",
            padx=20,
            pady=18,
        )
        card.pack(padx=24, pady=10)

        summary_lines = []
        for it in items:
            p = it["product"]
            q = int(it["quantity"])
            summary_lines.append(f"{p['name']} x{q}")
        summary_text = "\n".join(summary_lines)

        tk.Label(
            card,
            text=summary_text,
            font=UI_FONT_BODY,
            bg=self.current_theme["button_bg"],
            fg=self.current_theme["button_fg"],
            wraplength=360,
            justify="center",
        ).pack(pady=(0, 8))
        tk.Label(
            card,
            text=f"Total: ₱{total:.2f}",
            font=UI_FONT_TITLE,
            bg=self.current_theme["button_bg"],
            fg=self.current_theme["button_fg"],
        ).pack(pady=(0, 16))

        tk.Button(
            card,
            text="Pay with Cash\nInsert coins or bills",
            font=UI_FONT_BUTTON,
            width=28,
            height=3,
            wraplength=300,
            justify="center",
            command=lambda: self.cash_payment_flow(total),
        ).pack(pady=8, fill=tk.X)

        tk.Button(
            card,
            text="Pay with RFID Card\nCashless payment",
            font=UI_FONT_BUTTON,
            width=28,
            height=3,
            wraplength=300,
            justify="center",
            command=lambda: self.rfid_payment_flow(total),
        ).pack(pady=8, fill=tk.X)

        tk.Button(
            frame,
            text="Back",
            font=UI_FONT_BODY,
            padx=16,
            pady=6,
            command=(self.show_order_review_screen if self.checkout_items and len(self.checkout_items) > 1 else self.show_quantity_screen),
        ).pack(pady=10)

        self.add_theme_toggle_footer()

    # ---------- Cash Payment Flow ----------

    def cash_payment_flow(self, total_amount: float):
        if self.sidebar_holder is not None and self.sidebar_holder.winfo_exists():
            self.sidebar_holder.destroy()
            self.sidebar_holder = None
        self.clear_screen()
        cash_session.reset()

        frame = tk.Frame(self.content_holder, bg=self.current_theme["bg"])
        frame.pack(expand=True, fill=tk.BOTH)

        tk.Label(
            frame,
            text="Pay with Cash",
            font=UI_FONT_BOLD,
            bg=self.current_theme["bg"],
            fg=self.current_theme["fg"],
        ).pack(pady=(10, 6))
        tk.Label(
            frame,
            text="Press the buttons below to simulate inserting coins/bills.",
            font=UI_FONT_SMALL,
            bg=self.current_theme["bg"],
            fg=self.current_theme["fg"],
        ).pack(pady=2)

        card = tk.Frame(
            frame,
            bg=self.current_theme["button_bg"],
            bd=1,
            relief="solid",
            padx=20,
            pady=18,
        )
        card.pack(padx=24, pady=10)

        tk.Label(
            card,
            text=f"Total to Pay: ₱{total_amount:.2f}",
            font=UI_FONT_TITLE,
            bg=self.current_theme["button_bg"],
            fg=self.current_theme["button_fg"],
        ).pack(pady=(0, 12))

        amount_var = tk.DoubleVar(value=0.0)
        remaining_var = tk.DoubleVar(value=total_amount)

        tk.Label(
            card,
            text="Amount Inserted:",
            font=UI_FONT_BODY,
            bg=self.current_theme["button_bg"],
            fg=self.current_theme["button_fg"],
        ).pack(pady=4)
        tk.Label(
            card,
            textvariable=amount_var,
            font=(UI_FONT, 22, "bold"),
            bg=self.current_theme["button_bg"],
            fg=self.current_theme["button_fg"],
        ).pack()

        tk.Label(
            card,
            text="Remaining:",
            font=UI_FONT_BODY,
            bg=self.current_theme["button_bg"],
            fg=self.current_theme["button_fg"],
        ).pack(pady=(10, 4))
        tk.Label(
            card,
            textvariable=remaining_var,
            font=(UI_FONT, 22, "bold"),
            bg=self.current_theme["button_bg"],
            fg=self.current_theme["button_fg"],
        ).pack()

        # Simulated cash buttons for development
        btn_frame = tk.Frame(card, bg=self.current_theme["button_bg"])
        btn_frame.pack(pady=15)

        def add_money(val):
            cash_session.add(val)
            current = cash_session.get_amount()
            amount_var.set(current)
            remaining_var.set(max(0.0, total_amount - current))

        tk.Button(btn_frame, text="+₱1", width=7, font=UI_FONT_BODY, command=lambda: add_money(1)).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="+₱5", width=7, font=UI_FONT_BODY, command=lambda: add_money(5)).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="+₱10", width=7, font=UI_FONT_BODY, command=lambda: add_money(10)).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="+₱20", width=7, font=UI_FONT_BODY, command=lambda: add_money(20)).pack(side=tk.LEFT, padx=5)

        def finish_if_enough():
            current = cash_session.get_amount()
            if current < total_amount:
                messagebox.showwarning("Not enough", "Please insert more cash.")
                return
            self.complete_purchase_cash(total_amount, current)

        tk.Button(
            card,
            text="Dispense product",
            font=UI_FONT_BUTTON,
            command=finish_if_enough,
            bg="#4CAF50",
            fg=self.current_theme["button_fg"],
            width=28,
            height=2,
        ).pack(pady=(10, 8), fill=tk.X)

        tk.Button(
            frame,
            text="Cancel and go back",
            font=UI_FONT_BODY,
            command=self.build_main_menu,
            bg="#E53935",
            fg=self.current_theme["button_fg"],
            padx=16,
            pady=6,
        ).pack(pady=5)

        self.add_theme_toggle_footer()

    def complete_purchase_cash(self, total_amount: float, inserted: float):
        items = self._get_checkout_items()
        if not items:
            self.build_main_menu()
            return
        change = max(0.0, inserted - total_amount)

        self.show_wait_screen("Processing payment and dispensing...")

        try:
            for it in items:
                p = it["product"]
                q = int(it["quantity"])
                line_total = float(p["price"]) * q
                decrement_stock(p["id"], q)
                dispense_from_slot(p["slot_number"], q)
                record_transaction(p["id"], q, line_total, "cash")
            if change > 0:
                dispense_change(change)
            self.show_success_screen(
                "Thank you!",
                f"Please take your products.\n\nChange: ₱{change:.2f}",
                on_ok=lambda: (self._reset_checkout_state(), self.build_main_menu()),
            )
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self._reset_checkout_state()
            self.build_main_menu()

    # ---------- Utility Screens ----------

    def show_wait_screen(self, text: str):
        """In-app styled wait screen (no pop-up)."""
        if self.sidebar_holder is not None and self.sidebar_holder.winfo_exists():
            self.sidebar_holder.destroy()
            self.sidebar_holder = None
        self.clear_screen()
        frame = tk.Frame(self.content_holder, bg=self.current_theme["bg"])
        frame.pack(expand=True, fill=tk.BOTH)
        card = tk.Frame(
            frame,
            bg=self.current_theme.get("card_bg", "#ffffff"),
            highlightthickness=1,
            highlightbackground=self.current_theme.get("card_border", "#e2e8f0"),
        )
        card.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(
            card,
            text=text,
            font=(UI_FONT, 14),
            bg=self.current_theme.get("card_bg", "#ffffff"),
            fg=self.current_theme["fg"],
        ).pack(padx=40, pady=24)

        self.add_theme_toggle_footer()

    def show_success_screen(self, title: str, message: str, on_ok=None):
        """In-app success screen (no messagebox pop-up)."""
        if self.sidebar_holder is not None and self.sidebar_holder.winfo_exists():
            self.sidebar_holder.destroy()
            self.sidebar_holder = None
        self.clear_screen()
        frame = tk.Frame(self.content_holder, bg=self.current_theme["bg"])
        frame.pack(expand=True, fill=tk.BOTH)
        card = tk.Frame(
            frame,
            bg=self.current_theme.get("card_bg", "#ffffff"),
            highlightthickness=1,
            highlightbackground=self.current_theme.get("accent", "#0d9488"),
        )
        card.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(
            card,
            text=title,
            font=(UI_FONT, 18, "bold"),
            bg=self.current_theme.get("card_bg", "#ffffff"),
            fg=self.current_theme.get("accent", "#0d9488"),
        ).pack(pady=(20, 8))
        tk.Label(
            card,
            text=message,
            font=UI_FONT_BODY,
            bg=self.current_theme.get("card_bg", "#ffffff"),
            fg=self.current_theme["fg"],
            justify="center",
        ).pack(padx=32, pady=(0, 20))
        tk.Button(
            card,
            text="OK",
            font=(UI_FONT, 12, "bold"),
            command=on_ok or self.build_main_menu,
            bg=self.current_theme.get("accent", "#0d9488"),
            fg="#ffffff",
            relief=tk.FLAT,
            padx=28,
            pady=10,
        ).pack(pady=(0, 20))
        self.add_theme_toggle_footer()

    # ---------- RFID Card Purchase ----------

    def buy_card_flow(self):
        """Customer buys a new RFID card for a fixed price (e.g. ₱50)."""
        CARD_PRICE = 50.0
        if self.sidebar_holder is not None and self.sidebar_holder.winfo_exists():
            self.sidebar_holder.destroy()
            self.sidebar_holder = None
        self.clear_screen()
        cash_session.reset()

        frame = tk.Frame(self.content_holder, bg=self.current_theme["bg"])
        frame.pack(expand=True, fill=tk.BOTH)

        tk.Label(
            frame,
            text="Buy a New RFID Card",
            font=UI_FONT_TITLE,
            bg=self.current_theme["bg"],
            fg=self.current_theme["fg"],
        ).pack(pady=12)
        tk.Label(
            frame,
            text=f"Please pay ₱{CARD_PRICE:.2f}",
            font=UI_FONT_BODY,
            bg=self.current_theme["bg"],
            fg=self.current_theme["fg"],
        ).pack(pady=4)

        amount_var = tk.DoubleVar(value=0.0)
        remaining_var = tk.DoubleVar(value=CARD_PRICE)

        tk.Label(
            frame,
            text="Amount Inserted:",
            font=UI_FONT_BODY,
            bg=self.current_theme["bg"],
            fg=self.current_theme["fg"],
        ).pack(pady=4)
        tk.Label(
            frame,
            textvariable=amount_var,
            font=(UI_FONT, 20, "bold"),
            bg=self.current_theme["bg"],
            fg=self.current_theme["fg"],
        ).pack()
        tk.Label(
            frame,
            text="Remaining:",
            font=UI_FONT_BODY,
            bg=self.current_theme["bg"],
            fg=self.current_theme["fg"],
        ).pack(pady=4)
        tk.Label(
            frame,
            textvariable=remaining_var,
            font=(UI_FONT, 20, "bold"),
            bg=self.current_theme["bg"],
            fg=self.current_theme["fg"],
        ).pack()

        def add_money(val):
            cash_session.add(val)
            current = cash_session.get_amount()
            amount_var.set(current)
            remaining_var.set(max(0.0, CARD_PRICE - current))

        btn_frame = tk.Frame(frame, bg=self.current_theme["bg"])
        btn_frame.pack(pady=12)
        tk.Button(
            btn_frame,
            text="+₱1",
            width=8,
            font=UI_FONT_BODY,
            command=lambda: add_money(1),
            bg=self.current_theme["button_bg"],
            fg=self.current_theme["button_fg"],
        ).pack(side=tk.LEFT, padx=10)
        tk.Button(
            btn_frame,
            text="+₱5",
            width=8,
            font=UI_FONT_BODY,
            command=lambda: add_money(5),
            bg=self.current_theme["button_bg"],
            fg=self.current_theme["button_fg"],
        ).pack(side=tk.LEFT, padx=10)
        tk.Button(
            btn_frame,
            text="+₱10",
            width=8,
            font=UI_FONT_BODY,
            command=lambda: add_money(10),
            bg=self.current_theme["button_bg"],
            fg=self.current_theme["button_fg"],
        ).pack(side=tk.LEFT, padx=10)
        tk.Button(
            btn_frame,
            text="+₱20",
            width=8,
            font=UI_FONT_BODY,
            command=lambda: add_money(20),
            bg=self.current_theme["button_bg"],
            fg=self.current_theme["button_fg"],
        ).pack(side=tk.LEFT, padx=10)

        def confirm_purchase():
            inserted = cash_session.get_amount()
            if inserted < CARD_PRICE:
                messagebox.showwarning("Not enough", "Please insert full card price.")
                return

            self.show_wait_screen("Issuing RFID card...")

            uid = uuid.uuid4().hex[:8].upper()
            user_id = create_user(uid, name=None, is_staff=0, initial_balance=0.0)

            record_transaction(
                product_id=None,
                quantity=None,
                total_amount=CARD_PRICE,
                payment_method="card_purchase",
                rfid_user_id=user_id,
            )

            messagebox.showinfo(
                "Card Issued",
                f"New RFID card created.\nCard ID (simulate UID): {uid}"
            )
            self.build_main_menu()

        tk.Button(
            frame,
            text="Confirm and issue card",
            font=UI_FONT_BUTTON,
            command=confirm_purchase,
            bg=self.current_theme.get("accent", "#4CAF50"),
            fg="#ffffff",
            relief=tk.FLAT,
            padx=20,
            pady=10,
        ).pack(pady=12)

        tk.Button(
            frame,
            text="Cancel and go back",
            font=UI_FONT_BODY,
            command=self.build_main_menu,
            bg="#E53935",
            fg="#ffffff",
            relief=tk.FLAT,
            padx=16,
            pady=6,
        ).pack(pady=6)

        self.add_theme_toggle_footer()

    # ---------- RFID Reload ----------

    def reload_card_flow(self):
        """Customer reloads an existing RFID card balance."""
        # Simulate RFID scan by asking for card ID
        uid = simpledialog.askstring(
            "RFID Reload",
            "Enter RFID Card ID (simulate tap):",
            parent=self,
        )
        if not uid:
            self.build_main_menu()
            return

        user = get_user_by_uid(uid)
        if not user:
            messagebox.showerror("Error", "Card not found. Please buy a new card first.")
            self.build_main_menu()
            return

        if self.sidebar_holder is not None and self.sidebar_holder.winfo_exists():
            self.sidebar_holder.destroy()
            self.sidebar_holder = None
        self.clear_screen()
        cash_session.reset()

        frame = tk.Frame(self.content_holder, bg=self.current_theme["bg"])
        frame.pack(expand=True, fill=tk.BOTH)

        tk.Label(
            frame,
            text="Reload RFID Card",
            font=UI_FONT_BOLD,
            bg=self.current_theme["bg"],
            fg=self.current_theme["fg"],
        ).pack(pady=10)

        card = tk.Frame(
            frame,
            bg=self.current_theme["button_bg"],
            bd=1,
            relief="solid",
            padx=20,
            pady=18,
        )
        card.pack(padx=24, pady=10)

        tk.Label(
            card,
            text=f"Card ID: {uid}",
            font=UI_FONT_BODY,
            bg=self.current_theme["button_bg"],
            fg=self.current_theme["button_fg"],
        ).pack(pady=(0, 4))
        tk.Label(
            card,
            text=f"Current Balance: ₱{user['balance']:.2f}",
            font=UI_FONT_BODY,
            bg=self.current_theme["button_bg"],
            fg=self.current_theme["button_fg"],
        ).pack(pady=(0, 10))

        amount_var = tk.DoubleVar(value=0.0)

        tk.Label(
            card,
            text="Amount to Load:",
            font=UI_FONT_BODY,
            bg=self.current_theme["button_bg"],
            fg=self.current_theme["button_fg"],
        ).pack(pady=5)
        tk.Label(
            card,
            textvariable=amount_var,
            font=(UI_FONT, 22, "bold"),
            bg=self.current_theme["button_bg"],
            fg=self.current_theme["button_fg"],
        ).pack()

        btn_frame = tk.Frame(card, bg=self.current_theme["button_bg"])
        btn_frame.pack(pady=15)

        def add_money(val):
            cash_session.add(val)
            amount_var.set(cash_session.get_amount())

        tk.Button(btn_frame, text="+₱1", width=7, font=UI_FONT_BODY, command=lambda: add_money(1)).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="+₱5", width=7, font=UI_FONT_BODY, command=lambda: add_money(5)).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="+₱10", width=7, font=UI_FONT_BODY, command=lambda: add_money(10)).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="+₱20", width=7, font=UI_FONT_BODY, command=lambda: add_money(20)).pack(side=tk.LEFT, padx=5)

        def confirm_reload():
            amount = cash_session.get_amount()
            if amount <= 0:
                messagebox.showwarning("No amount", "Please add some amount to reload.")
                return

            new_balance = user["balance"] + amount
            update_user_balance(user["id"], new_balance)

            record_transaction(
                product_id=None,
                quantity=None,
                total_amount=amount,
                payment_method="rfid_reload",
                rfid_user_id=user["id"],
            )

            messagebox.showinfo(
                "Reload Successful",
                f"New balance: ₱{new_balance:.2f}"
            )
            self.build_main_menu()

        tk.Button(
            card,
            text="Add balance",
            font=UI_FONT_BUTTON,
            command=confirm_reload,
            bg="#4CAF50",
            fg=self.current_theme["button_fg"],
            width=28,
            height=2,
        ).pack(pady=(10, 8), fill=tk.X)

        tk.Button(
            frame,
            text="Cancel and go back",
            font=UI_FONT_BODY,
            command=self.build_main_menu,
            bg="#E53935",
            fg=self.current_theme["button_fg"],
            padx=16,
            pady=6,
        ).pack(pady=5)

        self.add_theme_toggle_footer()

        self.apply_theme_to_widget(self)

    # ---------- RFID Purchase Payment ----------

    def rfid_payment_flow(self, total_amount: float):
        """Purchase products using RFID card balance."""
        uid = simpledialog.askstring(
            "RFID Payment",
            "Enter RFID Card ID (simulate tap):",
            parent=self,
        )
        if not uid:
            self.build_main_menu()
            return

        user = get_user_by_uid(uid)
        if not user:
            messagebox.showerror("Error", "Card not found.")
            self.build_main_menu()
            return

        if user["balance"] < total_amount:
            messagebox.showerror("Error", "Insufficient card balance.")
            self.build_main_menu()
            return

        new_balance = user["balance"] - total_amount
        update_user_balance(user["id"], new_balance)

        items = self._get_checkout_items()
        if not items:
            self.build_main_menu()
            return

        self.show_wait_screen("Processing RFID payment and dispensing...")
        try:
            for it in items:
                p = it["product"]
                q = int(it["quantity"])
                line_total = float(p["price"]) * q
                decrement_stock(p["id"], q)
                dispense_from_slot(p["slot_number"], q)
                record_transaction(
                    product_id=p["id"],
                    quantity=q,
                    total_amount=line_total,
                    payment_method="rfid_purchase",
                    rfid_user_id=user["id"],
                )
            self.show_success_screen(
                "Thank you!",
                f"Payment successful.\n\nRemaining balance: ₱{new_balance:.2f}\nPlease take your products.",
                on_ok=lambda: (self._reset_checkout_state(), self.build_main_menu()),
            )
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self._reset_checkout_state()
            self.build_main_menu()

    # ---------- Sales Report Export ----------

    def export_sales_report_ui(self):
        """Generate an Excel file with transaction, daily, and monthly sales."""
        try:
            path = export_sales_report()
            messagebox.showinfo(
                "Export Complete",
                f"Sales report saved as:\n{path}"
            )
        except Exception as e:
            messagebox.showerror("Export Failed", str(e))


# ======================
#  MAIN ENTRYPOINT
# ======================

def main():
    init_db()
    gpio_init()

    app = MainApp()
    try:
        app.mainloop()
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    main()