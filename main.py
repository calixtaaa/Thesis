import os
import sys
import time
import threading
import uuid
import json
import datetime
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

from admin.admin import AdminMixin
from admin.reports import get_reports_dir
from staff.staff import (
    StaffMixin,
    LOGIN_PANEL_BG,
    LOGIN_BTN_BG,
    LOGIN_BTN_HOVER,
    LOGIN_PAGE_BG,
)
from database import (
    init_db,
    get_admin_credentials,
    update_admin_credentials,
    get_all_products,
    get_product_by_id,
    record_transaction,
    get_user_by_uid,
    create_user,
    update_user_balance,
    restock_product,
    export_sales_report,
    finalize_purchase_records,
    get_admin_overview_stats,
    get_sales_trend_data,
    get_monthly_sales_data,
    get_top_selling_products,
    get_low_stock_chart_data,
)
from patchNotes import get_patch_notes_text, VERSION
from customer_ui import build_welcome_screen, show_thank_you_screen, build_main_menu

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

# Simple theming (light / dark) – palette: teal #1A948E (Buy RFID), white plus on teal for product add
THEMES = {
    "light": {
        "bg": "#f8fafc",
        "fg": "#1e293b",
        "button_bg": "#f1f5f9",
        "button_fg": "#1e293b",
        "accent": "#1A948E",
        "accent_hover": "#15857B",
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
    """Make button appear to scale up on hover/press by increasing padding (works for mouse + touch)."""

    def apply_hover():
        if btn.winfo_exists():
            btn.configure(padx=hover_padx, pady=hover_pady)

    def apply_normal():
        if btn.winfo_exists():
            btn.configure(padx=normal_padx, pady=normal_pady)

    def on_enter(_e):
        apply_hover()

    def on_leave(_e):
        apply_normal()

    def on_press(_e):
        apply_hover()

    def on_release(_e):
        apply_normal()

    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)
    btn.bind("<ButtonPress-1>", on_press)
    btn.bind("<ButtonRelease-1>", on_release)

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
    print(f"[HW] Dispensing from slot {slot_number} x{quantity}")
    if not pins:
        if not ON_RPI:
            print(f"[HW] (Simulated – no pins for slot {slot_number})")
        else:
            print(f"[HW] WARNING: No stepper pins for slot {slot_number}, skipping")
        return

    steps = STEPS_PER_PRODUCT * quantity
    delay = 0.001  # 1ms

    GPIO.output(pins["dir"], GPIO.HIGH)
    for _ in range(steps):
        GPIO.output(pins["step"], GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(pins["step"], GPIO.LOW)
        time.sleep(delay)

def dispense_change(amount: float):
    coins_to_dispense = int(round(amount / COIN_VALUE))
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

        # Hamburger / menu icon (subsample 4x for compact size, matches dark mode text size)
        try:
            menu_path = BASE_DIR / "images" / "hamburger.png"
            if menu_path.exists():
                img = tk.PhotoImage(file=str(menu_path))
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
        self._thank_you_after_id = None
        self.debug_session_id = uuid.uuid4().hex[:6]
        self.debug_run_id = f"run-{int(time.time())}"

        self.search_var = tk.StringVar()
        self.theme_animating = False
        self._pending_theme_apply_id = None

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

        # Keep a single fixed base layout size for all profiles
        # so that Staff/Admin screens do NOT change window scale.
        target_w, target_h = BASE_APP_W, BASE_APP_H

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
        try:
            self.unbind_all("<MouseWheel>")
        except Exception:
            pass
        for w in self.content_holder.winfo_children():
            w.destroy()

    def _debug_log(self, hypothesis_id: str, location: str, message: str, data: dict):
        DEBUG_LOGS_DIR.mkdir(parents=True, exist_ok=True)
        payload = {
            "sessionId": self.debug_session_id,
            "runId": self.debug_run_id,
            "hypothesisId": hypothesis_id,
            "location": location,
            "message": message,
            "data": data,
            "timestamp": int(time.time() * 1000),
        }
        log_name = f"debug-{self.debug_session_id}.log"
        with open(DEBUG_LOGS_DIR / log_name, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, ensure_ascii=True) + "\n")
        # Keep a compatibility copy in the project root for existing tooling.
        with open(BASE_DIR / log_name, "a", encoding="utf-8") as fh:
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

    def apply_theme_to_widget(self, widget, _depth=0):
        """Apply current theme colors to a widget and its children (recursive)."""
        if _depth > 80:
            return
        try:
            if not widget.winfo_exists():
                return
            widget.configure(bg=self.current_theme["bg"])
        except tk.TclError:
            pass
        for child in list(widget.winfo_children()):
            try:
                if isinstance(child, tk.Button):
                    if getattr(child, "_sidebar_nav", False):
                        nav_bg = "#e2e8f0" if self.current_theme_name == "light" else "#334155"
                        nav_fg = "#0f172a" if self.current_theme_name == "light" else "#ffffff"
                        child.configure(bg=nav_bg, fg=nav_fg, activebackground="#2dd4bf" if self.current_theme_name == "light" else "#5eead4", activeforeground="#0f172a")
                        child._sidebar_nav_bg = nav_bg
                        child._sidebar_nav_fg = nav_fg
                    elif getattr(child, "_staff_exit_btn", False):
                        exit_bg = "#e2e8f0" if self.current_theme_name == "light" else "#334155"
                        exit_fg = "#0f172a" if self.current_theme_name == "light" else "#ffffff"
                        child.configure(bg=exit_bg, fg=exit_fg)
                        child._staff_exit_bg = exit_bg
                        child._staff_exit_fg = exit_fg
                    elif getattr(child, "_hamburger_btn", False):
                        child.configure(text="☰", image="", font=(UI_FONT, 16, "bold"), bg=self.current_theme["bg"], fg=self.current_theme["fg"])
                        if hasattr(child, "image"):
                            child.image = None
                    elif getattr(child, "_restock_btn", False):
                        acc = self.current_theme.get("accent", "#1A948E")
                        child.configure(bg=acc, fg="#ffffff")
                        child._hover_normal = acc
                        child._hover_hover = "#2dd4bf" if self.current_theme_name == "light" else "#5eead4"
                    elif getattr(child, "_product_add_btn", False):
                        acc = self.current_theme.get("accent", "#1A948E")
                        child.configure(
                            fg="#ffffff",
                            bg=acc,
                            activeforeground="#ffffff",
                            activebackground=self.current_theme.get("accent_hover", "#15857B"),
                        )
                    else:
                        child.configure(
                            bg=self.current_theme["button_bg"],
                            fg=self.current_theme["button_fg"],
                            activebackground=self.current_theme["button_bg"],
                            activeforeground=self.current_theme["button_fg"],
                        )
                    if getattr(child, "_is_theme_toggle", False):
                        child.configure(text=f"Theme: {self.current_theme_name.capitalize()}")
                elif isinstance(child, tk.Label):
                    if getattr(child, "_datetime_label", False):
                        fg = self.current_theme["fg"] if self.current_theme_name == "dark" else self.current_theme.get("muted", self.current_theme["fg"])
                        child.configure(bg=self.current_theme["bg"], fg=fg)
                    elif getattr(child, "_admin_metric_value", False):
                        acc = self.current_theme.get("accent", "#1A948E")
                        child.configure(bg=self.current_theme.get("card_bg", "#ffffff"), fg=acc)
                    else:
                        child.configure(bg=self.current_theme["bg"], fg=self.current_theme["fg"])
                elif isinstance(child, tk.Frame):
                    child.configure(bg=self.current_theme["bg"])
                    self.apply_theme_to_widget(child, _depth + 1)
                elif isinstance(child, tk.Canvas):
                    try:
                        child.configure(bg="#ffffff" if self.current_theme_name == "light" else "#253041")
                    except tk.TclError:
                        pass
                    self.apply_theme_to_widget(child, _depth + 1)
            except tk.TclError:
                pass

    def _do_deferred_theme_apply(self):
        self._pending_theme_apply_id = None
        try:
            self.apply_theme_to_widget(self)
        except Exception:
            pass

    def toggle_theme(self):
        """Switch between light and dark modes and refresh current screen."""
        self.current_theme_name = "dark" if self.current_theme_name == "light" else "light"
        self.current_theme = THEMES[self.current_theme_name]
        self.configure(bg=self.current_theme["bg"])
        if self._pending_theme_apply_id:
            self.after_cancel(self._pending_theme_apply_id)
        self._pending_theme_apply_id = self.after(50, self._do_deferred_theme_apply)

    def animate_button_press(self, button, callback):
        """Play a quick press animation before running a button action."""
        normal_bg = button.cget("bg")
        normal_relief = button.cget("relief")
        normal_bd = button.cget("bd")

        pressed_bg = self.current_theme.get("accent_hover", self.current_theme.get("accent", "#1A948E"))

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

        # No icon inside knob – avoids black line artifacts (reference: clean white knob)

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
                    # Update slider visuals (track/knob) to match new theme
                    canvas.itemconfigure(
                        track,
                        fill=track_dark if target_dark else track_light,
                        outline=border_dark if target_dark else border_light,
                    )
                    if self._pending_theme_apply_id:
                        self.after_cancel(self._pending_theme_apply_id)
                    self._pending_theme_apply_id = self.after(50, self._do_deferred_theme_apply)
                    return

                canvas.move(knob, delta, 0)
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
        theme_btn = tk.Button(
            bottom,
            text=f"Theme: {self.current_theme_name.capitalize()}",
            command=self.toggle_theme,
            font=UI_FONT_BODY,
            bg=self.current_theme["button_bg"],
            fg=self.current_theme["button_fg"],
        )
        theme_btn._is_theme_toggle = True
        theme_btn.pack(side=tk.RIGHT, padx=10)
        self.apply_theme_to_widget(self.content_holder)

    def add_ph_datetime_label(self, parent):
        """Show a live Philippine date/time label inside the given parent."""
        # Use fg (not muted) in dark mode for better visibility
        dt_fg = self.current_theme["fg"] if self.current_theme_name == "dark" else self.current_theme.get("muted", self.current_theme["fg"])
        label = tk.Label(
            parent,
            font=UI_FONT_SMALL,
            bg=self.current_theme["bg"],
            fg=dt_fg,
        )
        label._datetime_label = True
        label.pack(side=tk.RIGHT, padx=10)

        ph_tz = datetime.timezone(datetime.timedelta(hours=8))

        def _refresh():
            if not label.winfo_exists():
                return
            now = datetime.datetime.now(ph_tz)
            label.config(text=now.strftime("PH Time: %b %d, %Y %I:%M %p"))
            label.after(1000, _refresh)

        _refresh()
        return label

    def show_patch_notes_dialog(self):
        """In-app Patch Notes screen (no external pop-up)."""
        if self.sidebar_holder is not None and self.sidebar_holder.winfo_exists():
            self.sidebar_holder.destroy()
            self.sidebar_holder = None
        self.clear_screen()
        self.content_holder.configure(bg=self.current_theme["bg"])

        frame = tk.Frame(self.content_holder, bg=self.current_theme["bg"])
        frame.pack(expand=True, fill=tk.BOTH)

        # Top bar with back button for easier navigation
        top_bar = tk.Frame(frame, bg=self.current_theme["bg"])
        top_bar.pack(side=tk.TOP, fill=tk.X, pady=(8, 0), padx=10)
        back_btn = tk.Button(
            top_bar,
            text="← Back to Dashboard",
            font=UI_FONT_BODY,
            command=self.build_main_menu,
            bg=self.current_theme.get("button_bg", "#e5e7eb"),
            fg=self.current_theme["button_fg"],
            relief=tk.FLAT,
            padx=14,
            pady=6,
            cursor="hand2",
        )
        back_btn.pack(side=tk.LEFT)
        _hover_scale_btn(back_btn, normal_padx=14, normal_pady=6, hover_padx=18, hover_pady=10)

        card = tk.Frame(
            frame,
            bg=self.current_theme.get("card_bg", "#ffffff"),
            highlightthickness=1,
            highlightbackground=self.current_theme.get("card_border", "#e2e8f0"),
            padx=24,
            pady=20,
        )
        card.place(relx=0.5, rely=0.55, anchor="center", relwidth=0.9, relheight=0.72)

        tk.Label(
            card,
            text=f"Patch Notes  ·  {VERSION}",
            font=(UI_FONT, 18, "bold"),
            bg=card["bg"],
            fg=self.current_theme["fg"],
        ).pack(anchor="w", pady=(0, 8))

        text_container = tk.Frame(card, bg=card["bg"])
        text_container.pack(expand=True, fill=tk.BOTH, pady=(4, 12))

        scrollbar = tk.Scrollbar(text_container, orient="vertical")
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        txt = tk.Text(
            text_container,
            wrap="word",
            font=UI_FONT_SMALL,
            bg=card["bg"],
            fg=self.current_theme["fg"],
            bd=0,
            highlightthickness=0,
        )
        txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        txt.insert("1.0", get_patch_notes_text())
        txt.configure(state="disabled", yscrollcommand=scrollbar.set)
        scrollbar.configure(command=txt.yview)

        self.add_theme_toggle_footer()

    def show_help_dialog(self):
        """In-app 'How to use' page (no external pop-up)."""
        if self.sidebar_holder is not None and self.sidebar_holder.winfo_exists():
            self.sidebar_holder.destroy()
            self.sidebar_holder = None
        self.clear_screen()
        self.content_holder.configure(bg=self.current_theme["bg"])

        frame = tk.Frame(self.content_holder, bg=self.current_theme["bg"])
        frame.pack(expand=True, fill=tk.BOTH)

        card = tk.Frame(
            frame,
            bg=self.current_theme.get("card_bg", "#ffffff"),
            highlightthickness=1,
            highlightbackground=self.current_theme.get("card_border", "#e2e8f0"),
            padx=32,
            pady=28,
        )
        card.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(
            card,
            text="How to Use the Vending Machine",
            font=(UI_FONT, 18, "bold"),
            bg=card["bg"],
            fg=self.current_theme["fg"],
        ).pack(pady=(0, 10))

        steps = (
            "1. Select Product – Tap the item you want on the main menu.\n"
            "2. Set Quantity – Use the + and − buttons to choose how many pieces you need.\n"
            "3. Choose Payment – Pay with Cash or RFID Card.\n"
            "4. Take Products – Wait for the machine to dispense your items.\n\n"
            "You can also use the buttons at the bottom of the main menu to reload an existing RFID card "
            "or buy a new RFID card."
        )
        tk.Label(
            card,
            text=steps,
            font=UI_FONT_BODY,
            bg=card["bg"],
            fg=self.current_theme["fg"],
            justify="left",
            wraplength=480,
        ).pack(pady=(4, 18))

        tk.Button(
            card,
            text="Back to Dashboard",
            font=UI_FONT_BUTTON,
            command=self.build_main_menu,
            bg=self.current_theme.get("accent", "#1A948E"),
            fg="#ffffff",
            relief=tk.FLAT,
            padx=24,
            pady=8,
            cursor="hand2",
        ).pack(pady=(0, 4))

        self.add_theme_toggle_footer()

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
        sidebar_bg = self.current_theme.get("accent", "#1A948E")
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
        build_welcome_screen(self)

    def show_thank_you_screen(self):
        show_thank_you_screen(self)

    def build_main_menu(self):
        build_main_menu(self)

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

    def _prepare_checkout_items(self, expected_total: float | None = None):
        """Refresh checkout items from the DB and validate stock and totals."""
        raw_items = self._get_checkout_items()
        if not raw_items:
            return [], 0.0

        prepared_items = []
        for entry in raw_items:
            product = entry.get("product") if isinstance(entry, dict) else None
            product_id = product["id"] if product and "id" in product.keys() else None
            if product_id is None:
                raise ValueError("One of the selected products is invalid.")

            fresh_product = get_product_by_id(int(product_id))
            if fresh_product is None:
                raise ValueError("One of the selected products is no longer available.")

            quantity = max(1, int(entry.get("quantity", 1) or 1))
            if int(fresh_product["current_stock"]) < quantity:
                raise ValueError(f"Insufficient stock for {fresh_product['name']}.")

            prepared_items.append(
                {
                    "product": fresh_product,
                    "quantity": quantity,
                    "line_total": float(fresh_product["price"]) * quantity,
                }
            )

        total = sum(item["line_total"] for item in prepared_items)
        if expected_total is not None and abs(total - expected_total) > 0.009:
            raise ValueError("Product prices changed. Please review your order again.")

        self.checkout_items = [
            {"product": item["product"], "quantity": item["quantity"]}
            for item in prepared_items
        ]
        if len(prepared_items) == 1:
            self.current_product = prepared_items[0]["product"]
            self.current_quantity = prepared_items[0]["quantity"]

        return prepared_items, total

    def _run_background_task(self, wait_text: str, worker, on_success, on_error=None):
        """Run a blocking task off the Tk thread and marshal results back to the UI."""
        self.show_wait_screen(wait_text)
        try:
            self.update_idletasks()
        except Exception:
            pass

        def runner():
            try:
                result = worker()
            except Exception as exc:
                handler = on_error or self._handle_background_error
                self.after(0, lambda exc=exc: handler(exc))
            else:
                self.after(0, lambda result=result: on_success(result))

        threading.Thread(target=runner, daemon=True).start()

    def _handle_background_error(self, exc: Exception):
        messagebox.showerror(
            "Operation failed",
            f"{exc}\n\nPlease check the machine for any partially dispensed items before retrying.",
        )
        self._reset_checkout_state()
        self.build_main_menu()

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

        accent = self.current_theme.get("accent", "#1A948E")
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

        tk.Button(
            card,
            text="Back to products",
            font=UI_FONT_BODY,
            command=lambda: (self._reset_checkout_state(), self.build_main_menu()),
            bg=self.current_theme["button_bg"],
            fg=self.current_theme["button_fg"],
            relief=tk.FLAT,
            padx=18,
            pady=8,
            cursor="hand2",
        ).pack(fill=tk.X, pady=(0, 4))

        back_btn = tk.Button(
            frame,
            text="Back to products",
            font=UI_FONT_BODY,
            command=lambda: (self._reset_checkout_state(), self.build_main_menu()),
            bg=self.current_theme["button_bg"],
            fg=self.current_theme["button_fg"],
            relief=tk.FLAT,
            padx=18,
            pady=8,
            cursor="hand2",
        )
        back_btn.pack_forget()
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
        if p is None:
            self.build_main_menu()
            return
        accent = self.current_theme.get("accent", "#1A948E")
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

        tk.Button(
            card,
            text="Back to products",
            font=UI_FONT_BODY,
            padx=18,
            pady=8,
            command=lambda: (self._reset_checkout_state(), self.build_main_menu()),
            bg=self.current_theme["button_bg"],
            fg=self.current_theme["button_fg"],
            relief=tk.FLAT,
            cursor="hand2",
        ).pack(fill=tk.X)

        back_btn = tk.Button(
            frame,
            text="Back to products",
            font=UI_FONT_BODY,
            padx=18,
            pady=8,
            command=lambda: (self._reset_checkout_state(), self.build_main_menu()),
            bg=self.current_theme["button_bg"],
            fg=self.current_theme["button_fg"],
            relief=tk.FLAT,
            cursor="hand2",
        )
        back_btn.pack_forget()
        _hover_scale_btn(back_btn, normal_padx=18, normal_pady=8, hover_padx=22, hover_pady=12)
        back_btn.bind("<Enter>", lambda e: back_btn.configure(bg=self.current_theme.get("accent", "#1A948E"), fg="#ffffff") if back_btn.winfo_exists() else None)
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
            command=lambda: (self._reset_checkout_state(), self.build_main_menu()),
            bg="#E53935",
            fg=self.current_theme["button_fg"],
            padx=16,
            pady=6,
        ).pack(pady=5)

        self.add_theme_toggle_footer()

    def complete_purchase_cash(self, total_amount: float, inserted: float):
        try:
            items, refreshed_total = self._prepare_checkout_items(expected_total=total_amount)
        except Exception as exc:
            messagebox.showerror("Checkout Error", str(exc))
            self._reset_checkout_state()
            self.build_main_menu()
            return

        change = max(0.0, inserted - refreshed_total)
        purchase_rows = [
            {
                "product_id": int(item["product"]["id"]),
                "product_name": str(item["product"]["name"]),
                "quantity": int(item["quantity"]),
                "line_total": float(item["line_total"]),
            }
            for item in items
        ]

        def worker():
            for item in items:
                dispense_from_slot(int(item["product"]["slot_number"]), int(item["quantity"]))
            if change > 0:
                dispense_change(change)
            finalize_purchase_records(purchase_rows, payment_method="cash")
            return change

        def on_success(change_due: float):
            self.show_success_screen(
                "Thank you!",
                f"Please take your products.\n\nChange: ₱{change_due:.2f}",
                on_ok=lambda: (self._reset_checkout_state(), self.build_main_menu()),
            )

        self._run_background_task(
            "Processing payment and dispensing...",
            worker,
            on_success,
        )

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
            highlightbackground=self.current_theme.get("accent", "#1A948E"),
        )
        card.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(
            card,
            text=title,
            font=(UI_FONT, 18, "bold"),
            bg=self.current_theme.get("card_bg", "#ffffff"),
            fg=self.current_theme.get("accent", "#1A948E"),
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
            bg=self.current_theme.get("accent", "#1A948E"),
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

        # Use the same mint login style as Staff Login
        self.content_holder.configure(bg=LOGIN_PAGE_BG)
        frame = tk.Frame(self.content_holder, bg=LOGIN_PAGE_BG)
        frame.pack(expand=True, fill=tk.BOTH)

        panel = tk.Frame(frame, bg=LOGIN_PANEL_BG, padx=40, pady=28)
        panel.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(
            panel,
            text="Buy a New RFID Card",
            font=(UI_FONT, 18, "bold"),
            bg=LOGIN_PANEL_BG,
            fg="#0f766e",
        ).pack(pady=(0, 10))
        tk.Label(
            panel,
            text=f"Please pay ₱{CARD_PRICE:.2f} using the cash buttons below.",
            font=UI_FONT_BODY,
            bg=LOGIN_PANEL_BG,
            fg="#134e4a",
            wraplength=360,
            justify="left",
        ).pack(pady=(0, 10))

        amount_var = tk.DoubleVar(value=0.0)
        remaining_var = tk.DoubleVar(value=CARD_PRICE)

        tk.Label(
            panel,
            text="Amount Inserted:",
            font=UI_FONT_BODY,
            bg=LOGIN_PANEL_BG,
            fg="#134e4a",
        ).pack(pady=4)
        tk.Label(
            panel,
            textvariable=amount_var,
            font=(UI_FONT, 20, "bold"),
            bg=LOGIN_PANEL_BG,
            fg="#0f172a",
        ).pack()
        tk.Label(
            panel,
            text="Remaining:",
            font=UI_FONT_BODY,
            bg=LOGIN_PANEL_BG,
            fg="#134e4a",
        ).pack(pady=4)
        tk.Label(
            panel,
            textvariable=remaining_var,
            font=(UI_FONT, 20, "bold"),
            bg=LOGIN_PANEL_BG,
            fg="#0f172a",
        ).pack()

        def add_money(val):
            cash_session.add(val)
            current = cash_session.get_amount()
            amount_var.set(current)
            remaining_var.set(max(0.0, CARD_PRICE - current))

        btn_frame = tk.Frame(panel, bg=LOGIN_PANEL_BG)
        btn_frame.pack(pady=12)
        tk.Button(
            btn_frame,
            text="+₱1",
            width=8,
            font=UI_FONT_BODY,
            command=lambda: add_money(1),
            bg=LOGIN_BTN_BG,
            fg="#ffffff",
        ).pack(side=tk.LEFT, padx=10)
        tk.Button(
            btn_frame,
            text="+₱5",
            width=8,
            font=UI_FONT_BODY,
            command=lambda: add_money(5),
            bg=LOGIN_BTN_BG,
            fg="#ffffff",
        ).pack(side=tk.LEFT, padx=10)
        tk.Button(
            btn_frame,
            text="+₱10",
            width=8,
            font=UI_FONT_BODY,
            command=lambda: add_money(10),
            bg=LOGIN_BTN_BG,
            fg="#ffffff",
        ).pack(side=tk.LEFT, padx=10)
        tk.Button(
            btn_frame,
            text="+₱20",
            width=8,
            font=UI_FONT_BODY,
            command=lambda: add_money(20),
            bg=LOGIN_BTN_BG,
            fg="#ffffff",
        ).pack(side=tk.LEFT, padx=10)

        def confirm_purchase():
            inserted = cash_session.get_amount()
            if inserted < CARD_PRICE:
                messagebox.showwarning("Not enough", "Please insert full card price.")
                return

            change = max(0.0, inserted - CARD_PRICE)

            def worker():
                uid = uuid.uuid4().hex[:8].upper()
                user_id = create_user(uid, name=None, is_staff=0, initial_balance=0.0)
                record_transaction(
                    product_id=None,
                    quantity=None,
                    total_amount=CARD_PRICE,
                    payment_method="card_purchase",
                    rfid_user_id=user_id,
                )
                if change > 0:
                    dispense_change(change)
                return uid, change

            def on_success(result):
                uid, change_due = result
                change_text = f"\nChange returned: ₱{change_due:.2f}" if change_due > 0 else ""
                self.show_success_screen(
                    "Card Issued",
                    f"New RFID card created.\nCard ID (simulate UID): {uid}{change_text}",
                    on_ok=lambda: (self._reset_checkout_state(), self.build_main_menu()),
                )

            self._run_background_task("Issuing RFID card...", worker, on_success)

        action_frame = tk.Frame(panel, bg=LOGIN_PANEL_BG)
        action_frame.pack(pady=(8, 0), fill=tk.X)

        confirm_btn = tk.Button(
            action_frame,
            text="Confirm and issue card",
            font=UI_FONT_BUTTON,
            command=confirm_purchase,
            bg=LOGIN_BTN_BG,
            fg="#ffffff",
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor="hand2",
        )
        confirm_btn.pack(side=tk.LEFT, padx=(0, 10))
        _hover_scale_btn(confirm_btn, normal_padx=20, normal_pady=10, hover_padx=24, hover_pady=14)

        cancel_btn = tk.Button(
            action_frame,
            text="Cancel and go back",
            font=UI_FONT_BODY,
            command=lambda: (self._reset_checkout_state(), self.build_main_menu()),
            bg=LOGIN_BTN_BG,
            fg="#ffffff",
            relief=tk.FLAT,
            padx=16,
            pady=6,
            cursor="hand2",
        )
        cancel_btn.pack(side=tk.LEFT)
        _hover_scale_btn(cancel_btn, normal_padx=16, normal_pady=6, hover_padx=20, hover_pady=10)

        self.add_theme_toggle_footer()

    # ---------- RFID Reload ----------

    def reload_card_flow(self):
        """Customer reloads an existing RFID card balance."""
        # Step 1: in-app mint-style card ID entry (no system dialog)
        if self.sidebar_holder is not None and self.sidebar_holder.winfo_exists():
            self.sidebar_holder.destroy()
            self.sidebar_holder = None
        self.clear_screen()
        self.content_holder.configure(bg=LOGIN_PAGE_BG)

        frame = tk.Frame(self.content_holder, bg=LOGIN_PAGE_BG)
        frame.pack(expand=True, fill=tk.BOTH)

        panel = tk.Frame(frame, bg=LOGIN_PANEL_BG, padx=40, pady=28)
        panel.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(
            panel,
            text="Reload RFID Card",
            font=(UI_FONT, 18, "bold"),
            bg=LOGIN_PANEL_BG,
            fg="#0f766e",
        ).pack(pady=(0, 10))

        tk.Label(
            panel,
            text="Enter RFID Card ID (simulate tap):",
            font=UI_FONT_SMALL,
            bg=LOGIN_PANEL_BG,
            fg="#134e4a",
        ).pack(anchor="w", pady=(0, 6))

        uid_var = tk.StringVar()
        entry = tk.Entry(
            panel,
            textvariable=uid_var,
            font=UI_FONT_BODY,
            width=28,
            relief=tk.FLAT,
            bg="#ffffff",
            fg="#1e293b",
        )
        entry.pack(pady=(0, 8), ipady=8, ipadx=10)
        entry.focus_set()

        error_var = tk.StringVar(value="")
        error_lbl = tk.Label(
            panel,
            textvariable=error_var,
            font=UI_FONT_SMALL,
            bg=LOGIN_PANEL_BG,
            fg="#b91c1c",
        )
        error_lbl.pack(pady=(0, 4))

        def proceed_to_amount():
            uid = uid_var.get().strip()
            if not uid:
                error_var.set("Please enter a card ID.")
                return

            user = get_user_by_uid(uid)
            if not user:
                error_var.set("Card not found. Please buy a new card first.")
                return

            self._reload_amount_screen(uid, user)

        btn_row = tk.Frame(panel, bg=LOGIN_PANEL_BG)
        btn_row.pack(fill=tk.X, pady=(8, 0))

        ok_btn = tk.Button(
            btn_row,
            text="OK",
            font=(UI_FONT, 11, "bold"),
            command=proceed_to_amount,
            bg=LOGIN_BTN_BG,
            fg="#ffffff",
            relief=tk.FLAT,
            padx=24,
            pady=8,
            cursor="hand2",
        )
        ok_btn.pack(side=tk.LEFT, padx=(0, 10))
        _hover_scale_btn(ok_btn, normal_padx=24, normal_pady=8, hover_padx=28, hover_pady=12)

        cancel_btn = tk.Button(
            btn_row,
            text="Cancel",
            font=(UI_FONT, 11, "bold"),
            command=lambda: (self._reset_checkout_state(), self.build_main_menu()),
            bg=LOGIN_BTN_BG,
            fg="#ffffff",
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor="hand2",
        )
        cancel_btn.pack(side=tk.LEFT)
        _hover_scale_btn(cancel_btn, normal_padx=20, normal_pady=8, hover_padx=24, hover_pady=12)

        entry.bind("<Return>", lambda _e: proceed_to_amount())
        self.add_theme_toggle_footer()

    def _reload_amount_screen(self, uid, user):
        """Second step for reload – choose amount, still in-app."""
        if self.sidebar_holder is not None and self.sidebar_holder.winfo_exists():
            self.sidebar_holder.destroy()
            self.sidebar_holder = None
        self.clear_screen()
        cash_session.reset()

        self.content_holder.configure(bg=self.current_theme["bg"])
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

            self.show_success_screen(
                "Reload Successful",
                f"New balance: ₱{new_balance:.2f}",
                on_ok=self.build_main_menu,
            )

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
            command=lambda: (self._reset_checkout_state(), self.build_main_menu()),
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
        items = self._get_checkout_items()
        if not items:
            self.build_main_menu()
            return
        if self.sidebar_holder is not None and self.sidebar_holder.winfo_exists():
            self.sidebar_holder.destroy()
            self.sidebar_holder = None
        self.clear_screen()
        self.content_holder.configure(bg=LOGIN_PAGE_BG)

        frame = tk.Frame(self.content_holder, bg=LOGIN_PAGE_BG)
        frame.pack(expand=True, fill=tk.BOTH)

        panel = tk.Frame(frame, bg=LOGIN_PANEL_BG, padx=40, pady=28)
        panel.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(
            panel,
            text="RFID Payment",
            font=(UI_FONT, 18, "bold"),
            bg=LOGIN_PANEL_BG,
            fg="#0f766e",
        ).pack(pady=(0, 10))

        tk.Label(
            panel,
            text=f"Total amount: ₱{total_amount:.2f}",
            font=UI_FONT_BODY,
            bg=LOGIN_PANEL_BG,
            fg="#134e4a",
        ).pack(pady=(0, 10))

        tk.Label(
            panel,
            text="Enter RFID Card ID (simulate tap):",
            font=UI_FONT_SMALL,
            bg=LOGIN_PANEL_BG,
            fg="#134e4a",
        ).pack(anchor="w", pady=(0, 6))

        uid_var = tk.StringVar()
        entry = tk.Entry(
            panel,
            textvariable=uid_var,
            font=UI_FONT_BODY,
            width=28,
            relief=tk.FLAT,
            bg="#ffffff",
            fg="#1e293b",
        )
        entry.pack(pady=(0, 8), ipady=8, ipadx=10)
        entry.focus_set()

        error_var = tk.StringVar(value="")
        tk.Label(
            panel,
            textvariable=error_var,
            font=UI_FONT_SMALL,
            bg=LOGIN_PANEL_BG,
            fg="#b91c1c",
        ).pack(pady=(0, 4))

        def confirm_payment():
            uid = uid_var.get().strip()
            if not uid:
                error_var.set("Please enter a card ID.")
                return

            user = get_user_by_uid(uid)
            if not user:
                error_var.set("Card not found.")
                return

            try:
                prepared_items, refreshed_total = self._prepare_checkout_items(expected_total=total_amount)
            except Exception as exc:
                error_var.set(str(exc))
                return

            if float(user["balance"]) < refreshed_total:
                error_var.set("Insufficient card balance.")
                return

            new_balance = float(user["balance"]) - refreshed_total
            purchase_rows = [
                {
                    "product_id": int(item["product"]["id"]),
                    "product_name": str(item["product"]["name"]),
                    "quantity": int(item["quantity"]),
                    "line_total": float(item["line_total"]),
                }
                for item in prepared_items
            ]

            def worker():
                for item in prepared_items:
                    dispense_from_slot(int(item["product"]["slot_number"]), int(item["quantity"]))
                finalize_purchase_records(
                    purchase_rows,
                    payment_method="rfid_purchase",
                    rfid_user_id=int(user["id"]),
                    new_balance=new_balance,
                )
                return new_balance

            def on_success(balance_after: float):
                self.show_success_screen(
                    "Thank you!",
                    f"Payment successful.\n\nRemaining balance: ₱{balance_after:.2f}\nPlease take your products.",
                    on_ok=lambda: (self._reset_checkout_state(), self.build_main_menu()),
                )

            self._run_background_task(
                "Processing RFID payment and dispensing...",
                worker,
                on_success,
            )

        btn_row = tk.Frame(panel, bg=LOGIN_PANEL_BG)
        btn_row.pack(fill=tk.X, pady=(8, 0))

        confirm_btn = tk.Button(
            btn_row,
            text="Confirm payment",
            font=(UI_FONT, 11, "bold"),
            command=confirm_payment,
            bg=LOGIN_BTN_BG,
            fg="#ffffff",
            relief=tk.FLAT,
            padx=24,
            pady=8,
            cursor="hand2",
        )
        confirm_btn.pack(side=tk.LEFT, padx=(0, 10))
        _hover_scale_btn(confirm_btn, normal_padx=24, normal_pady=8, hover_padx=28, hover_pady=12)

        cancel_btn = tk.Button(
            btn_row,
            text="Cancel",
            font=(UI_FONT, 11, "bold"),
            command=lambda: (self._reset_checkout_state(), self.build_main_menu()),
            bg=LOGIN_BTN_BG,
            fg="#ffffff",
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor="hand2",
        )
        cancel_btn.pack(side=tk.LEFT)
        _hover_scale_btn(cancel_btn, normal_padx=20, normal_pady=8, hover_padx=24, hover_pady=12)

        entry.bind("<Return>", lambda _e: confirm_payment())
        self.add_theme_toggle_footer()

    # ---------- Sales Report Export ----------

    def export_sales_report_ui(self):
        """Generate an Excel file with transaction, daily, and monthly sales."""
        try:
            path = export_sales_report()
            reports_dir = get_reports_dir()
            messagebox.showinfo(
                "Export Complete",
                f"Sales report saved as:\n{path}\n\nReports folder:\n{reports_dir}"
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