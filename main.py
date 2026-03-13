import os
import sys
import time
import uuid
import json
import datetime
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, simpledialog
import customtkinter as ctk

import prediction_runtime
from customer import checkout_ui, main_menu_ui, status_ui

from admin.admin import AdminMixin
from admin.reports import get_reports_dir
from staff.staff import (
    StaffMixin,
)
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

class MainApp(AdminMixin, StaffMixin, ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"Hygiene Vending Machine  {VERSION}")

        # Set CTk appearance based on default theme
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("green")

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
        self._ui_font_name = UI_FONT
        self._ui_font_bold = UI_FONT_BOLD
        self._ui_font_title = UI_FONT_TITLE
        self._ui_font_body = UI_FONT_BODY
        self._ui_font_small = UI_FONT_SMALL
        self._ui_font_button = UI_FONT_BUTTON
        self.cash_session = cash_session

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

        self.search_var = tk.StringVar()
        self.theme_animating = False
        self._pending_theme_apply_id = None
        self._current_screen_builder = None  # callable to rebuild the active screen

        # Prediction Analysis cache (run once per session unless forced)
        self._prediction_results = None
        self._prediction_summary = None
        self._prediction_ran = False

        # Main content lives here; sidebar (when shown) is a sibling on the right
        self.content_holder = ctk.CTkFrame(self, fg_color=self.current_theme["bg"], corner_radius=0)
        self.content_holder.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.build_welcome_screen()

    def run_prediction_analysis_once(self, force: bool = False):
        """
        Run lightweight prediction analysis using SQLite data.
        Runs once per session unless force=True.
        """
        if self._prediction_ran and not force and self._prediction_results is not None:
            return self._prediction_results, self._prediction_summary
        try:
            results, summary = prediction_runtime.run_prediction_analysis(db_path=BASE_DIR / "vending.db")
            self._prediction_results = results
            self._prediction_summary = summary
            self._prediction_ran = True
            return results, summary
        except Exception as e:
            messagebox.showerror("Prediction Analysis", f"Failed to run prediction.\n\n{e}")
            return None, None

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
        # Close any right-side sidebars (not children of content_holder)
        try:
            if self.sidebar_frame is not None and self.sidebar_frame.winfo_exists():
                self.sidebar_frame.destroy()
        except Exception:
            pass
        self.sidebar_frame = None
        try:
            if self.sidebar_holder is not None and self.sidebar_holder.winfo_exists():
                self.sidebar_holder.destroy()
        except Exception:
            pass
        self.sidebar_holder = None

        try:
            self.unbind_all("<MouseWheel>")
        except Exception:
            pass
        # Cancel any pending focus callbacks before destroying widgets
        for after_id in getattr(self, "_pending_focus_ids", []):
            try:
                self.after_cancel(after_id)
            except Exception:
                pass
        self._pending_focus_ids = []
        for w in self.content_holder.winfo_children():
            w.destroy()
        # Reset any per-screen background colour changes (e.g. LOGIN_PAGE_BG)
        try:
            self.content_holder.configure(fg_color=self.current_theme["bg"])
        except Exception:
            pass

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
                        # Datetime uses a "badge" background for visibility
                        badge_bg = self.current_theme.get("button_bg", self.current_theme["bg"])
                        fg = self.current_theme["fg"]
                        child.configure(bg=badge_bg, fg=fg)
                    elif getattr(child, "_admin_metric_value", False):
                        acc = self.current_theme.get("accent", "#1A948E")
                        child.configure(bg=self.current_theme.get("card_bg", "#ffffff"), fg=acc)
                    else:
                        child.configure(bg=self.current_theme["bg"], fg=self.current_theme["fg"])
                elif isinstance(child, tk.Radiobutton) and getattr(child, "_bug_report", False):
                    try:
                        parent_bg = child.master.cget("bg")
                    except Exception:
                        parent_bg = self.current_theme.get("card_bg", self.current_theme["bg"])
                    child.configure(
                        bg=parent_bg,
                        fg=self.current_theme["fg"],
                        activebackground=parent_bg,
                        activeforeground=self.current_theme["fg"],
                        selectcolor=self.current_theme.get("card_bg", "#ffffff"),
                    )
                elif isinstance(child, tk.Text) and getattr(child, "_bug_report", False):
                    try:
                        parent_bg = child.master.cget("bg")
                    except Exception:
                        parent_bg = self.current_theme.get("card_bg", self.current_theme["bg"])
                    child.configure(
                        bg=self.current_theme.get("search_bg", self.current_theme.get("card_bg", "#ffffff")),
                        fg=self.current_theme["fg"],
                        insertbackground=self.current_theme["fg"],
                        highlightbackground=self.current_theme.get("card_border", "#e2e8f0"),
                    )
                elif isinstance(child, tk.Frame):
                    if getattr(child, "_datetime_badge", False):
                        badge_bg = self.current_theme.get("button_bg", self.current_theme["bg"])
                        child.configure(
                            bg=badge_bg,
                            highlightbackground=self.current_theme.get("card_border", "#e2e8f0"),
                        )
                    else:
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

    def _translate_theme_color(self, value, old_theme, new_theme):
        """Map known old-theme color values to their new-theme equivalents."""
        if isinstance(value, str):
            for key, old_val in old_theme.items():
                if value == old_val and key in new_theme:
                    return new_theme[key]
            return value
        if isinstance(value, tuple):
            mapped = tuple(self._translate_theme_color(v, old_theme, new_theme) for v in value)
            return mapped
        if isinstance(value, list):
            mapped = [self._translate_theme_color(v, old_theme, new_theme) for v in value]
            return mapped
        return value

    def _apply_theme_to_ctk_widget_tree(self, widget, old_theme, new_theme, _depth=0):
        """Update CTk widget explicit color options in-place without rebuilding the screen."""
        if _depth > 80:
            return
        option_names = (
            "fg_color",
            "hover_color",
            "text_color",
            "border_color",
            "button_color",
            "button_hover_color",
            "progress_color",
        )
        for child in list(widget.winfo_children()):
            try:
                for opt in option_names:
                    try:
                        current = child.cget(opt)
                    except Exception:
                        continue
                    updated = self._translate_theme_color(current, old_theme, new_theme)
                    if updated != current:
                        try:
                            child.configure(**{opt: updated})
                        except Exception:
                            pass
            except Exception:
                pass
            self._apply_theme_to_ctk_widget_tree(child, old_theme, new_theme, _depth + 1)

    def _safe_focus(self, widget):
        """Focus widget only if it still exists (prevents async focus TclError)."""
        try:
            exists = widget is not None and widget.winfo_exists()
        except Exception:
            return
        if not exists:
            return
        try:
            # CTkEntry wraps a native tk.Entry in ._entry; focus that directly
            # so we never touch a destroyed inner widget path.
            inner = getattr(widget, "_entry", None)
            if inner is not None:
                inner.focus_set()
            else:
                widget.focus_set()
        except Exception:
            pass

    def toggle_theme(self):
        """Switch between light and dark modes without rebuilding the active screen."""
        if getattr(self, "theme_animating", False):
            return
        self.theme_animating = True

        old_theme = dict(self.current_theme)
        next_theme_name = "dark" if self.current_theme_name == "light" else "light"
        next_theme = THEMES[next_theme_name]

        self.current_theme_name = next_theme_name
        self.current_theme = next_theme
        ctk.set_appearance_mode(self.current_theme_name)
        try:
            self.configure(fg_color=self.current_theme["bg"])
            try:
                self.content_holder.configure(fg_color=self.current_theme["bg"])
            except Exception:
                pass

            # Update explicit CustomTkinter colors that were set at build time.
            self._apply_theme_to_ctk_widget_tree(self, old_theme, self.current_theme)
            # Update raw tkinter widgets and special tags (datetime, bug report, etc.).
            self.apply_theme_to_widget(self)
        except Exception:
            self.theme_animating = False
            raise
        self.theme_animating = False

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
                    ctk.set_appearance_mode(self.current_theme_name)
                    self.configure(fg_color=self.current_theme["bg"])
                    self.theme_animating = False
                    # Overlay in new theme color so clear+rebuild is not visible (reduces flicker)
                    overlay = ctk.CTkFrame(self, fg_color=self.current_theme["bg"], corner_radius=0)
                    overlay.place(x=0, y=0, relwidth=1, relheight=1)
                    try:
                        if callable(self._current_screen_builder):
                            self._current_screen_builder()
                        else:
                            self.build_main_menu()
                    finally:
                        try:
                            if overlay.winfo_exists():
                                overlay.destroy()
                        except Exception:
                            pass
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
        bottom = ctk.CTkFrame(self.content_holder, fg_color=self.current_theme["bg"], corner_radius=0)
        bottom.pack(side=tk.BOTTOM, fill=tk.X, pady=4)
        ctk.CTkLabel(
            bottom,
            text=f"SyntaxError™  ·  {VERSION}",
            font=UI_FONT_SMALL,
            text_color=self.current_theme.get("muted", self.current_theme["fg"]),
        ).pack(side=tk.LEFT, padx=10)
        self.add_ph_datetime_label(bottom)
        theme_btn = ctk.CTkButton(
            bottom,
            text=f"Theme: {self.current_theme_name.capitalize()}",
            command=self.toggle_theme,
            font=UI_FONT_BODY,
            fg_color=self.current_theme["button_bg"],
            hover_color=self.current_theme.get("accent", "#1A948E"),
            text_color=self.current_theme["button_fg"],
            corner_radius=8,
            height=32,
        )
        theme_btn._is_theme_toggle = True
        theme_btn.pack(side=tk.RIGHT, padx=10)

    def add_ph_datetime_label(self, parent):
        """Show a live Philippine date/time label inside the given parent."""
        badge_bg = self.current_theme.get("button_bg", self.current_theme["bg"])
        badge = ctk.CTkFrame(
            parent,
            fg_color=badge_bg,
            border_width=1,
            border_color=self.current_theme.get("card_border", "#e2e8f0"),
            corner_radius=8,
        )
        badge._datetime_badge = True
        badge.pack(side=tk.RIGHT, padx=8, pady=2)

        label = ctk.CTkLabel(
            badge,
            font=(UI_FONT, 10),
            text_color=self.current_theme.get("muted", self.current_theme["fg"]),
            text="",
        )
        label._datetime_label = True
        label.pack(padx=10, pady=4)

        ph_tz = datetime.timezone(datetime.timedelta(hours=8))

        def _refresh():
            if not label.winfo_exists():
                return
            now = datetime.datetime.now(ph_tz)
            # Compact format so the datetime badge doesn't crowd footer buttons.
            label.configure(text=now.strftime("%I:%M %p"))
            label.after(1000, _refresh)

        _refresh()
        return label

    def show_patch_notes_dialog(self):
        """In-app Patch Notes screen (no external pop-up)."""
        self._current_screen_builder = self.show_patch_notes_dialog
        if self.sidebar_holder is not None and self.sidebar_holder.winfo_exists():
            self.sidebar_holder.destroy()
            self.sidebar_holder = None
        self.clear_screen()
        self.content_holder.configure(fg_color=self.current_theme["bg"])

        frame = ctk.CTkFrame(self.content_holder, fg_color=self.current_theme["bg"], corner_radius=0)
        frame.pack(expand=True, fill=tk.BOTH)

        # Top bar with back button for easier navigation
        top_bar = ctk.CTkFrame(frame, fg_color=self.current_theme["bg"], corner_radius=0)
        top_bar.pack(side=tk.TOP, fill=tk.X, pady=(8, 0), padx=10)
        ctk.CTkButton(
            top_bar,
            text="← Back to Dashboard",
            font=UI_FONT_BODY,
            command=self.build_main_menu,
            fg_color=self.current_theme.get("button_bg", "#e5e7eb"),
            hover_color=self.current_theme.get("accent", "#1A948E"),
            text_color=self.current_theme["button_fg"],
            corner_radius=8,
            height=36,
        ).pack(side=tk.LEFT)

        card = ctk.CTkFrame(
            frame,
            fg_color=self.current_theme.get("card_bg", "#ffffff"),
            border_width=1,
            border_color=self.current_theme.get("card_border", "#e2e8f0"),
            corner_radius=12,
        )
        card.place(relx=0.5, rely=0.55, anchor="center", relwidth=0.9, relheight=0.72)

        ctk.CTkLabel(
            card,
            text=f"Patch Notes  ·  {VERSION}",
            font=(UI_FONT, 18, "bold"),
            text_color=self.current_theme["fg"],
        ).pack(anchor="w", padx=24, pady=(20, 8))

        txt = ctk.CTkTextbox(
            card,
            font=UI_FONT_SMALL,
            fg_color=self.current_theme.get("card_bg", "#ffffff"),
            text_color=self.current_theme["fg"],
            corner_radius=8,
        )
        txt.pack(expand=True, fill=tk.BOTH, padx=24, pady=(4, 20))
        txt.insert("1.0", get_patch_notes_text())
        txt.configure(state="disabled")

        self.add_theme_toggle_footer()

    def show_help_dialog(self):
        """In-app 'How to use' page (no external pop-up)."""
        self._current_screen_builder = self.show_help_dialog
        if self.sidebar_holder is not None and self.sidebar_holder.winfo_exists():
            self.sidebar_holder.destroy()
            self.sidebar_holder = None
        self.clear_screen()
        self.content_holder.configure(fg_color=self.current_theme["bg"])

        frame = ctk.CTkFrame(self.content_holder, fg_color=self.current_theme["bg"], corner_radius=0)
        frame.pack(expand=True, fill=tk.BOTH)

        card = ctk.CTkFrame(
            frame,
            fg_color=self.current_theme.get("card_bg", "#ffffff"),
            border_width=1,
            border_color=self.current_theme.get("card_border", "#e2e8f0"),
            corner_radius=12,
        )
        card.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            card,
            text="How to Use the Vending Machine",
            font=(UI_FONT, 18, "bold"),
            text_color=self.current_theme["fg"],
        ).pack(pady=(20, 10), padx=32)

        steps = (
            "1. Select Product – Tap the item you want on the main menu.\n"
            "2. Set Quantity – Use the + and − buttons to choose how many pieces you need.\n"
            "3. Choose Payment – Pay with Cash or RFID Card.\n"
            "4. Take Products – Wait for the machine to dispense your items.\n\n"
            "You can also use the buttons at the bottom of the main menu to reload an existing RFID card "
            "or buy a new RFID card."
        )
        ctk.CTkLabel(
            card,
            text=steps,
            font=UI_FONT_BODY,
            text_color=self.current_theme["fg"],
            justify="left",
            wraplength=480,
        ).pack(pady=(4, 18), padx=32)

        ctk.CTkButton(
            card,
            text="Back to Dashboard",
            font=UI_FONT_BUTTON,
            command=self.build_main_menu,
            fg_color=self.current_theme.get("accent", "#1A948E"),
            hover_color=self.current_theme.get("accent_hover", "#15857B"),
            text_color="#ffffff",
            corner_radius=10,
            width=200,
            height=40,
        ).pack(pady=(0, 20), padx=32)

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
        sidebar = ctk.CTkFrame(self, fg_color=sidebar_bg, width=sidebar_width, corner_radius=0)
        sidebar.place(relx=1.0, x=0, y=0, anchor="ne", relheight=1.0)

        # Top row: "Menu" label + close button so sidebar doesn't block the hamburger
        top_row = ctk.CTkFrame(sidebar, fg_color=sidebar_bg)
        top_row.pack(fill=tk.X, padx=10, pady=(10, 6))
        ctk.CTkLabel(
            top_row,
            text="Menu",
            font=(UI_FONT, 12, "bold"),
            text_color="#ffffff",
        ).pack(side=tk.LEFT, padx=4)
        ctk.CTkButton(
            top_row,
            text="✕",
            width=32,
            height=32,
            font=(UI_FONT, 14, "bold"),
            fg_color="transparent",
            hover_color=strip_bg,
            text_color="#ffffff",
            corner_radius=6,
            command=self.show_role_menu,
        ).pack(side=tk.RIGHT)

        def make_nav_button(text, command):
            btn = ctk.CTkButton(
                sidebar,
                text=text,
                anchor="w",
                font=(UI_FONT, 11, "bold"),
                command=command,
                fg_color=strip_bg,
                hover_color=sidebar_bg,
                text_color="#ffffff",
                corner_radius=8,
                height=40,
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
        self._current_screen_builder = self.build_welcome_screen
        if hasattr(self, "_apply_lcd_fit"):
            try:
                self._apply_lcd_fit(profile="customer")
            except Exception:
                pass
        if self.sidebar_holder is not None and self.sidebar_holder.winfo_exists():
            self.sidebar_holder.destroy()
            self.sidebar_holder = None
        self.clear_screen()
        self.configure(fg_color=self.current_theme["bg"])
        self.content_holder.configure(fg_color=self.current_theme["bg"])

        # Centered container (inside content_holder)
        center = ctk.CTkFrame(self.content_holder, fg_color=self.current_theme["bg"], corner_radius=0)
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
        ctk.CTkLabel(
            center,
            text="Welcome",
            font=(UI_FONT, 28, "bold"),
            text_color=self.current_theme["fg"],
        ).pack(pady=(0, 2))

        # "Syntaxer" line
        ctk.CTkLabel(
            center,
            text="Syntaxer",
            font=(UI_FONT, 24, "bold"),
            text_color=self.current_theme["fg"],
        ).pack(pady=(0, 28))

        # Start Order button – accent, rounded look
        accent = self.current_theme.get("accent", "#1A948E")
        start_btn = ctk.CTkButton(
            center,
            text="Start Order",
            font=(UI_FONT, 14, "bold"),
            fg_color=accent,
            hover_color=self.current_theme.get("accent_hover", accent),
            text_color="#ffffff",
            corner_radius=12,
            width=200,
            height=48,
            command=self.build_main_menu,
        )
        start_btn.pack(pady=0)

    def show_thank_you_screen(self):
        """Show 'Thank you, come again!' in-app, then return to welcome screen."""
        self._current_screen_builder = self.show_thank_you_screen
        if self.sidebar_holder is not None and self.sidebar_holder.winfo_exists():
            self.sidebar_holder.destroy()
            self.sidebar_holder = None
        self.clear_screen()
        self.content_holder.configure(fg_color=self.current_theme["bg"])

        center = ctk.CTkFrame(self.content_holder, fg_color=self.current_theme["bg"], corner_radius=0)
        center.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            center,
            text="Thank you, come again!",
            font=(UI_FONT, 22, "bold"),
            text_color=self.current_theme["fg"],
        ).pack(pady=(0, 24))

        def go_welcome():
            self.build_welcome_screen()

        ctk.CTkButton(
            center,
            text="OK",
            font=(UI_FONT, 12, "bold"),
            command=go_welcome,
            fg_color=self.current_theme.get("accent", "#1A948E"),
            hover_color=self.current_theme.get("accent_hover", "#15857B"),
            text_color="#ffffff",
            corner_radius=10,
            width=120,
            height=40,
        ).pack(pady=0)
        self.after(3500, go_welcome)  # Auto-return to welcome after 3.5 s

    # ---------- Main Menu ----------

    def build_main_menu(self):
        self._current_screen_builder = self.build_main_menu
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

        # Note: The right-side menu is shown only via the hamburger (☰),
        # not automatically on the main menu.

        # Left + order panel area (inside content_holder)
        main_row = ctk.CTkFrame(self.content_holder, fg_color=self.current_theme["bg"], corner_radius=0)
        main_row.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self._main_row = main_row

        left_part = ctk.CTkFrame(main_row, fg_color=self.current_theme["bg"], corner_radius=0)
        left_part.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._build_main_menu_header(left_part)
        self._build_main_menu_products(left_part, all_products)

        # Order panel (dark green) – right of left_part, only when cart has items
        self._build_order_panel(main_row)

        self._build_main_menu_footer()

    def _build_main_menu_header(self, parent):
        """Main menu top bar: title, menu button, and theme slider."""
        main_menu_ui.build_main_menu_header(
            self,
            parent,
            ui_font=UI_FONT,
            ui_font_title=UI_FONT_TITLE,
            ui_font_small=UI_FONT_SMALL,
        )

    def _build_main_menu_products(self, parent, products):
        """Scrollable product grid for the customer main menu."""
        main_menu_ui.build_main_menu_products(self, parent, products)

    def _build_product_card(self, grid, product, idx):
        """Single product card in the main menu grid."""
        main_menu_ui.build_product_card(self, grid, product, idx)

    def _build_product_card_button(self, card, product, in_cart):
        """Add/remove button for a product card."""
        return main_menu_ui.build_product_card_button(self, card, product, in_cart)

    def _build_main_menu_footer(self):
        """Footer actions and info row for the main menu."""
        main_menu_ui.build_main_menu_footer(self, version=VERSION, hover_scale_btn=_hover_scale_btn)

    def _cart_has_product(self, product):
        return any(entry["product"]["id"] == product["id"] for entry in self.cart)

    def _add_product_to_cart(self, product):
        if product["current_stock"] <= 0:
            return
        self.cart.append({"product": product, "quantity": 1})
        ref = self._product_card_refs.get(product["id"])
        if ref:
            try:
                ref["card"].configure(fg_color=self._cart_selected_bg, border_color=self._cart_selected_border)
                ref["btn"].configure(
                    text="✕",
                    hover_color=self.current_theme.get("accent_hover", "#0f766e"),
                    command=lambda prod=product: self._remove_product_from_cart(prod),
                )
            except Exception:
                pass
        self._refresh_order_panel()

    def _remove_product_from_cart(self, product):
        self.cart = [entry for entry in self.cart if entry["product"]["id"] != product["id"]]
        ref = self._product_card_refs.get(product["id"])
        if ref:
            try:
                ref["card"].configure(fg_color=self._cart_card_bg, border_color=self._cart_card_border)
                ref["btn"].configure(
                    text="+",
                    hover_color=self.current_theme.get("accent_hover", "#15857B"),
                    state=tk.NORMAL if product["current_stock"] > 0 else tk.DISABLED,
                    command=ref["add_cmd"],
                )
            except Exception:
                pass
        self._refresh_order_panel()

    def _cancel_cart(self):
        """Clear the cart and reset every product card button in-place — no full screen rebuild."""
        self.cart.clear()
        card_bg = getattr(self, "_cart_card_bg", None)
        card_border = getattr(self, "_cart_card_border", None)
        for ref in getattr(self, "_product_card_refs", {}).values():
            p = ref["product"]
            try:
                if ref["card"].winfo_exists() and card_bg:
                    ref["card"].configure(fg_color=card_bg, border_color=card_border)
                if ref["btn"].winfo_exists():
                    ref["btn"].configure(
                        text="+",
                        hover_color=self.current_theme.get("accent_hover", "#15857B"),
                        state=tk.NORMAL if p["current_stock"] > 0 else tk.DISABLED,
                        command=ref["add_cmd"],
                    )
            except Exception:
                pass
        self._refresh_order_panel()

    def _build_order_panel(self, main_row):
        """Build (or rebuild) only the order panel inside main_row."""
        order_panel_width = 260
        panel_bg = "#0f766e" if self.current_theme_name == "light" else "#134e4a"
        if not self.cart:
            self._order_panel = None
            self._order_qty_vars = {}
            return
        self._order_panel = ctk.CTkFrame(main_row, fg_color=panel_bg, width=order_panel_width, corner_radius=0)
        self._order_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=0, pady=0)
        self._order_panel.pack_propagate(False)
        order_panel = self._order_panel
        self._order_qty_vars = {}

        ctk.CTkButton(
            order_panel,
            text="Cancel",
            font=(UI_FONT, 11, "bold"),
            text_color="#ffffff",
            fg_color=panel_bg,
            hover_color=self.current_theme.get("accent_hover", "#0f766e"),
            corner_radius=8,
            height=36,
            command=self._cancel_cart,
        ).pack(side=tk.TOP, fill=tk.X, padx=10, pady=(10, 8))

        for entry in self.cart:
            prod = entry["product"]
            qty_var = tk.IntVar(value=entry["quantity"])
            self._order_qty_vars[prod["id"]] = qty_var

            row = ctk.CTkFrame(order_panel, fg_color=panel_bg, corner_radius=0)
            row.pack(side=tk.TOP, fill=tk.X, padx=10, pady=4)

            ctk.CTkLabel(
                row,
                text=prod["name"][:18] + ("…" if len(prod["name"]) > 18 else ""),
                font=UI_FONT_SMALL,
                text_color="#ffffff",
            ).pack(anchor="center")

            ctrl = ctk.CTkFrame(row, fg_color=panel_bg, corner_radius=0)
            ctrl.pack(anchor="center", pady=2)

            ctk.CTkButton(
                ctrl,
                text="-",
                font=(UI_FONT, 12, "bold"),
                text_color="#ffffff",
                fg_color=panel_bg,
                hover_color="#134e4a",
                width=32,
                height=28,
                corner_radius=6,
                command=lambda pid=prod["id"]: self._change_cart_quantity(pid, -1),
            ).pack(side=tk.LEFT, padx=(0, 6))
            tk.Label(ctrl, textvariable=qty_var, font=(UI_FONT, 12, "bold"), bg=panel_bg, fg="#ffffff", width=3).pack(side=tk.LEFT, padx=(0, 6))
            ctk.CTkButton(
                ctrl,
                text="+",
                font=(UI_FONT, 12, "bold"),
                text_color="#ffffff",
                fg_color=panel_bg,
                hover_color="#134e4a",
                width=32,
                height=28,
                corner_radius=6,
                command=lambda pid=prod["id"]: self._change_cart_quantity(pid, 1),
            ).pack(side=tk.LEFT)

        ctk.CTkButton(
            order_panel,
            text="Confirm Order",
            font=(UI_FONT, 12, "bold"),
            text_color="#ffffff",
            fg_color=self.current_theme.get("accent", "#1A948E"),
            hover_color=self.current_theme.get("accent_hover", "#0f766e"),
            corner_radius=10,
            height=44,
            command=lambda: self._confirm_cart_order(),
        ).pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(8, 12))

    def _refresh_order_panel(self):
        """Destroy and rebuild only the order panel, leaving the product grid untouched."""
        if hasattr(self, "_order_panel") and self._order_panel is not None and self._order_panel.winfo_exists():
            self._order_panel.destroy()
            self._order_panel = None
        if hasattr(self, "_main_row") and self._main_row is not None and self._main_row.winfo_exists():
            self._build_order_panel(self._main_row)

    def _change_cart_quantity(self, product_id: int, delta: int):
        """Update a single cart item's quantity and its on-screen label in place."""
        for entry in self.cart:
            if entry["product"]["id"] != product_id:
                continue
            old_qty = int(entry["quantity"] if entry["quantity"] is not None else 1)
            max_stock = int(entry["product"]["current_stock"] or old_qty)
            new_qty = max(1, min(max_stock, old_qty + int(delta)))
            if new_qty == old_qty:
                return
            entry["quantity"] = new_qty
            var = getattr(self, "_order_qty_vars", {}).get(product_id)
            if var is not None:
                try:
                    var.set(new_qty)
                except Exception:
                    pass
            return

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
            # Quantity is already adjustable in the order panel for cart-based checkout.
            # Go directly to payment for a single selected product.
            self.show_payment_method_screen()
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
        self._current_screen_builder = self.show_order_review_screen
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

        frame = ctk.CTkFrame(self.content_holder, fg_color=self.current_theme["bg"], corner_radius=0)
        frame.pack(expand=True, fill=tk.BOTH)

        self._build_checkout_back_bar(
            frame,
            text="Back to products",
            command=lambda: (self.checkout_items.clear(), self.build_main_menu()),
        )
        self._build_order_review_content(frame, items, total, accent, accent_hover)
        self.add_theme_toggle_footer()

    def _build_checkout_back_bar(self, parent, text, command):
        """Bottom back/cancel bar shared by checkout-related screens."""
        checkout_ui.build_checkout_back_bar(self, parent, text, command)

    def _build_order_review_content(self, parent, items, total, accent, accent_hover):
        """Order review title, item list, and continue button."""
        checkout_ui.build_order_review_content(self, parent, items, total, accent, accent_hover)

    # ---------- Quantity Screen ----------

    def show_quantity_screen(self):
        self._current_screen_builder = self.show_quantity_screen
        if self.sidebar_holder is not None and self.sidebar_holder.winfo_exists():
            self.sidebar_holder.destroy()
            self.sidebar_holder = None
        self.clear_screen()
        p = self.current_product
        accent = self.current_theme.get("accent", "#1A948E")
        accent_hover = self.current_theme.get("accent_hover", "#0f766e")

        frame = ctk.CTkFrame(self.content_holder, fg_color=self.current_theme["bg"], corner_radius=0)
        frame.pack(expand=True, fill=tk.BOTH)

        self._build_checkout_back_bar(
            frame,
            text="Back to products",
            command=lambda: (self.checkout_items.clear(), self.build_main_menu()),
        )
        self._build_quantity_content(frame, p, accent, accent_hover)
        self.add_theme_toggle_footer()

    def _build_quantity_content(self, parent, product, accent, accent_hover):
        """Single-product quantity selector card."""
        checkout_ui.build_quantity_content(self, parent, product, accent, accent_hover)

    # ---------- Payment Method ----------

    def show_payment_method_screen(self):
        self._current_screen_builder = self.show_payment_method_screen
        if self.sidebar_holder is not None and self.sidebar_holder.winfo_exists():
            self.sidebar_holder.destroy()
            self.sidebar_holder = None
        self.clear_screen()
        items = self._get_checkout_items()
        if not items:
            self.build_main_menu()
            return
        total = self._get_checkout_total(items)

        frame = ctk.CTkFrame(self.content_holder, fg_color=self.current_theme["bg"], corner_radius=0)
        frame.pack(expand=True, fill=tk.BOTH)

        self._build_payment_method_content(frame, items, total)
        self.add_theme_toggle_footer()

    def _build_payment_method_content(self, parent, items, total):
        """Payment method chooser with order summary."""
        checkout_ui.build_payment_method_content(self, parent, items, total)

    # ---------- Cash Payment Flow ----------

    def cash_payment_flow(self, total_amount: float):
        self._current_screen_builder = lambda: self.cash_payment_flow(total_amount)
        if self.sidebar_holder is not None and self.sidebar_holder.winfo_exists():
            self.sidebar_holder.destroy()
            self.sidebar_holder = None
        self.clear_screen()
        cash_session.reset()

        frame = ctk.CTkFrame(self.content_holder, fg_color=self.current_theme["bg"], corner_radius=0)
        frame.pack(expand=True, fill=tk.BOTH)

        self._build_cash_payment_content(frame, total_amount)
        self.add_theme_toggle_footer()

    def _build_cash_payment_content(self, parent, total_amount: float):
        """Cash payment screen with simulated coin/bill buttons."""
        checkout_ui.build_cash_payment_content(self, parent, total_amount)

    def complete_purchase_cash(self, total_amount: float, inserted: float):
        items = self._get_checkout_items()
        if not items:
            self.build_main_menu()
            return
        change = max(0.0, inserted - total_amount)
        self._show_dispensing_screen()
        self.after(50, lambda: self._do_dispense_cash(items, change))

    def _do_dispense_cash(self, items, change):
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
        # Don't update _current_screen_builder for transient screens
        if self.sidebar_holder is not None and self.sidebar_holder.winfo_exists():
            self.sidebar_holder.destroy()
            self.sidebar_holder = None
        self.clear_screen()
        self._build_wait_screen_content(text)
        self.add_theme_toggle_footer()

    def _build_wait_screen_content(self, text: str):
        """Centered wait/status card used for transient wait states."""
        status_ui.build_wait_screen_content(self, text)


    def _show_dispensing_screen(self):
        """Full-screen dispensing overlay - shown before the blocking hardware call."""
        if self.sidebar_holder is not None and self.sidebar_holder.winfo_exists():
            self.sidebar_holder.destroy()
            self.sidebar_holder = None
        self.clear_screen()
        self._build_dispensing_screen_content()
        self.update_idletasks()

    def _build_dispensing_screen_content(self):
        """Centered dispensing status card."""
        status_ui.build_dispensing_screen_content(self)

    def _do_dispense_rfid(self, items, rfid_user_id, new_balance):
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
                    rfid_user_id=rfid_user_id,
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

    def show_success_screen(self, title: str, message: str, on_ok=None):
        """In-app success screen (no messagebox pop-up)."""
        # Don't update _current_screen_builder for transient screens
        if self.sidebar_holder is not None and self.sidebar_holder.winfo_exists():
            self.sidebar_holder.destroy()
            self.sidebar_holder = None
        self.clear_screen()
        self._build_success_screen_content(title, message, on_ok)
        self.add_theme_toggle_footer()

    def _build_success_screen_content(self, title: str, message: str, on_ok=None):
        """Centered success/result card with OK action."""
        status_ui.build_success_screen_content(self, title, message, on_ok)

    # ---------- RFID Card Purchase ----------

    def buy_card_flow(self):
        """Customer buys a new RFID card for a fixed price (e.g. ₱50)."""
        self._current_screen_builder = self.buy_card_flow
        CARD_PRICE = 50.0
        theme = self.current_theme
        if self.sidebar_holder is not None and self.sidebar_holder.winfo_exists():
            self.sidebar_holder.destroy()
            self.sidebar_holder = None
        self.clear_screen()
        cash_session.reset()

        self.content_holder.configure(fg_color=theme["bg"])
        frame = ctk.CTkFrame(self.content_holder, fg_color=theme["bg"])
        frame.pack(expand=True, fill=tk.BOTH)

        self._build_buy_card_content(frame, CARD_PRICE, theme)
        self.add_theme_toggle_footer()

    def _build_buy_card_content(self, parent, card_price: float, theme):
        """RFID card purchase UI and actions."""
        panel = ctk.CTkFrame(
            parent,
            fg_color=theme["card_bg"],
            corner_radius=16,
            border_width=1,
            border_color=theme["card_border"],
        )
        panel.place(relx=0.5, rely=0.5, anchor="center")
        inner = ctk.CTkFrame(panel, fg_color=theme["card_bg"])
        inner.pack(padx=40, pady=28)

        ctk.CTkLabel(inner, text="Buy a New RFID Card", font=(UI_FONT, 18, "bold"), text_color=theme["fg"]).pack(pady=(0, 10))
        ctk.CTkLabel(
            inner,
            text=f"Please pay ₱{card_price:.2f} using the cash buttons below.",
            font=UI_FONT_BODY,
            text_color=theme["muted"],
            wraplength=360,
            justify="left",
        ).pack(pady=(0, 10))

        amount_var = tk.DoubleVar(value=0.0)
        remaining_var = tk.DoubleVar(value=card_price)
        ctk.CTkLabel(inner, text="Amount Inserted:", font=UI_FONT_BODY, text_color=theme["muted"]).pack(pady=4)
        tk.Label(inner, textvariable=amount_var, font=(UI_FONT, 20, "bold"), bg=theme["card_bg"], fg=theme["fg"]).pack()
        ctk.CTkLabel(inner, text="Remaining:", font=UI_FONT_BODY, text_color=theme["muted"]).pack(pady=4)
        tk.Label(inner, textvariable=remaining_var, font=(UI_FONT, 20, "bold"), bg=theme["card_bg"], fg=theme["fg"]).pack()

        def add_money(value):
            cash_session.add(value)
            current = cash_session.get_amount()
            amount_var.set(current)
            remaining_var.set(max(0.0, card_price - current))

        btn_frame = ctk.CTkFrame(inner, fg_color=theme["card_bg"])
        btn_frame.pack(pady=12)
        for text, value in [("+₱1", 1), ("+₱5", 5), ("+₱10", 10), ("+₱20", 20)]:
            ctk.CTkButton(
                btn_frame,
                text=text,
                width=80,
                font=UI_FONT_BODY,
                command=lambda v=value: add_money(v),
                fg_color=theme["accent"],
                hover_color=theme["accent_hover"],
                text_color="#ffffff",
                corner_radius=8,
            ).pack(side=tk.LEFT, padx=10)

        def confirm_purchase():
            inserted = cash_session.get_amount()
            if inserted < card_price:
                messagebox.showwarning("Not enough", "Please insert full card price.")
                return
            uid = uuid.uuid4().hex[:8].upper()
            user_id = create_user(uid, name=None, is_staff=0, initial_balance=0.0)
            record_transaction(product_id=None, quantity=None, total_amount=card_price, payment_method="card_purchase", rfid_user_id=user_id)
            self.show_success_screen("Card Issued", f"New RFID card created.\nCard ID (simulate UID): {uid}", on_ok=self.build_main_menu)

        action_frame = ctk.CTkFrame(inner, fg_color=theme["card_bg"])
        action_frame.pack(pady=(8, 0), fill=tk.X)
        ctk.CTkButton(action_frame, text="Confirm and issue card", font=UI_FONT_BUTTON, command=confirm_purchase, fg_color=theme["accent"], hover_color=theme["accent_hover"], text_color="#ffffff", corner_radius=8, height=40).pack(side=tk.LEFT, padx=(0, 10))
        ctk.CTkButton(action_frame, text="Cancel and go back", font=UI_FONT_BODY, command=self.build_main_menu, fg_color=theme["button_bg"], hover_color=theme["card_border"], text_color=theme["button_fg"], corner_radius=8, height=36).pack(side=tk.LEFT)

    # ---------- RFID Reload ----------

    def reload_card_flow(self):
        """Customer reloads an existing RFID card balance."""
        self._current_screen_builder = self.reload_card_flow
        theme = self.current_theme
        if self.sidebar_holder is not None and self.sidebar_holder.winfo_exists():
            self.sidebar_holder.destroy()
            self.sidebar_holder = None
        self.clear_screen()
        self.content_holder.configure(fg_color=theme["bg"])

        frame = ctk.CTkFrame(self.content_holder, fg_color=theme["bg"])
        frame.pack(expand=True, fill=tk.BOTH)

        self._build_reload_card_content(frame, theme)
        self.add_theme_toggle_footer()

    def _build_reload_card_content(self, parent, theme):
        """RFID reload card lookup screen."""
        panel = ctk.CTkFrame(
            parent,
            fg_color=theme["card_bg"],
            corner_radius=16,
            border_width=1,
            border_color=theme["card_border"],
        )
        panel.place(relx=0.5, rely=0.5, anchor="center")
        inner = ctk.CTkFrame(panel, fg_color=theme["card_bg"])
        inner.pack(padx=40, pady=28)
        ctk.CTkLabel(inner, text="Reload RFID Card", font=(UI_FONT, 18, "bold"), text_color=theme["fg"]).pack(pady=(0, 10))
        ctk.CTkLabel(inner, text="Enter RFID Card ID (simulate tap):", font=UI_FONT_SMALL, text_color=theme["muted"]).pack(anchor="w", pady=(0, 6))

        uid_entry = ctk.CTkEntry(inner, font=UI_FONT_BODY, width=280, fg_color=theme["search_bg"], text_color=theme["fg"], border_color=theme["search_border"], corner_radius=8, height=40)
        uid_entry.pack(pady=(0, 8))

        error_lbl = ctk.CTkLabel(inner, text="", font=UI_FONT_SMALL, text_color="#b91c1c")
        error_lbl.pack(pady=(0, 4))

        def proceed_to_amount():
            uid = uid_entry.get().strip()
            if not uid:
                error_lbl.configure(text="Please enter a card ID.")
                return
            user = get_user_by_uid(uid)
            if not user:
                error_lbl.configure(text="Card not found. Please buy a new card first.")
                return
            self._reload_amount_screen(uid, user)

        btn_row = ctk.CTkFrame(inner, fg_color=theme["card_bg"])
        btn_row.pack(fill=tk.X, pady=(8, 0))
        ctk.CTkButton(btn_row, text="OK", font=(UI_FONT, 11, "bold"), command=proceed_to_amount, fg_color=theme["accent"], hover_color=theme["accent_hover"], text_color="#ffffff", corner_radius=8, height=38).pack(side=tk.LEFT, padx=(0, 10))
        ctk.CTkButton(btn_row, text="Cancel", font=(UI_FONT, 11, "bold"), command=self.build_main_menu, fg_color=theme["button_bg"], hover_color=theme["card_border"], text_color=theme["button_fg"], corner_radius=8, height=38).pack(side=tk.LEFT)
        uid_entry.bind("<Return>", lambda _e: proceed_to_amount())

    def _reload_amount_screen(self, uid, user):
        """Second step for reload – choose amount, still in-app."""
        self._current_screen_builder = lambda: self._reload_amount_screen(uid, user)
        if self.sidebar_holder is not None and self.sidebar_holder.winfo_exists():
            self.sidebar_holder.destroy()
            self.sidebar_holder = None
        self.clear_screen()
        cash_session.reset()

        theme = self.current_theme
        self.content_holder.configure(fg_color=theme["bg"])
        frame = ctk.CTkFrame(self.content_holder, fg_color=theme["bg"])
        frame.pack(expand=True, fill=tk.BOTH)

        self._build_reload_amount_content(frame, uid, user, theme)
        self.add_theme_toggle_footer()

    def _build_reload_amount_content(self, parent, uid, user, theme):
        """RFID reload amount entry screen."""
        ctk.CTkLabel(parent, text="Reload RFID Card", font=UI_FONT_BOLD, text_color=theme["fg"]).pack(pady=10)
        card = ctk.CTkFrame(parent, fg_color=theme["button_bg"], corner_radius=12, border_width=1, border_color="#94a3b8")
        card.pack(padx=24, pady=10)
        card_inner = ctk.CTkFrame(card, fg_color=theme["button_bg"])
        card_inner.pack(padx=20, pady=18)
        ctk.CTkLabel(card_inner, text=f"Card ID: {uid}", font=UI_FONT_BODY, text_color=theme["button_fg"]).pack(pady=(0, 4))
        ctk.CTkLabel(card_inner, text=f"Current Balance: ₱{user['balance']:.2f}", font=UI_FONT_BODY, text_color=theme["button_fg"]).pack(pady=(0, 10))

        amount_var = tk.DoubleVar(value=0.0)
        ctk.CTkLabel(card_inner, text="Amount to Load:", font=UI_FONT_BODY, text_color=theme["button_fg"]).pack(pady=5)
        tk.Label(card_inner, textvariable=amount_var, font=(UI_FONT, 22, "bold"), bg=theme["button_bg"], fg=theme["button_fg"]).pack()

        btn_frame = ctk.CTkFrame(card_inner, fg_color=theme["button_bg"])
        btn_frame.pack(pady=15)

        def add_money(value):
            cash_session.add(value)
            amount_var.set(cash_session.get_amount())

        for text, value in [("+₱1", 1), ("+₱5", 5), ("+₱10", 10), ("+₱20", 20)]:
            ctk.CTkButton(btn_frame, text=text, width=70, font=UI_FONT_BODY, command=lambda v=value: add_money(v), fg_color=theme["accent"], hover_color=theme["accent_hover"], text_color="#ffffff", corner_radius=8).pack(side=tk.LEFT, padx=5)

        def confirm_reload():
            amount = cash_session.get_amount()
            if amount <= 0:
                messagebox.showwarning("No amount", "Please add some amount to reload.")
                return
            new_balance = user["balance"] + amount
            update_user_balance(user["id"], new_balance)
            record_transaction(product_id=None, quantity=None, total_amount=amount, payment_method="rfid_reload", rfid_user_id=user["id"])
            self.show_success_screen("Reload Successful", f"New balance: ₱{new_balance:.2f}", on_ok=self.build_main_menu)

        ctk.CTkButton(card_inner, text="Add balance", font=UI_FONT_BUTTON, command=confirm_reload, fg_color=theme["accent"], hover_color=theme["accent_hover"], text_color="#ffffff", corner_radius=8, height=44).pack(pady=(10, 8), fill=tk.X)
        ctk.CTkButton(parent, text="Cancel and go back", font=UI_FONT_BODY, command=self.build_main_menu, fg_color=theme["button_bg"], hover_color=theme["card_border"], text_color=theme["button_fg"], corner_radius=8, height=36).pack(pady=5)

    # ---------- RFID Purchase Payment ----------

    def rfid_payment_flow(self, total_amount: float):
        """Purchase products using RFID card balance – in-app card ID entry."""
        self._current_screen_builder = lambda: self.rfid_payment_flow(total_amount)
        theme = self.current_theme
        if self.sidebar_holder is not None and self.sidebar_holder.winfo_exists():
            self.sidebar_holder.destroy()
            self.sidebar_holder = None
        self.clear_screen()
        self.content_holder.configure(fg_color=theme["bg"])

        frame = ctk.CTkFrame(self.content_holder, fg_color=theme["bg"])
        frame.pack(expand=True, fill=tk.BOTH)

        self._build_rfid_payment_content(frame, total_amount, theme)
        self.add_theme_toggle_footer()

    def _build_rfid_payment_content(self, parent, total_amount: float, theme):
        """RFID payment entry and validation screen."""
        panel = ctk.CTkFrame(
            parent,
            fg_color=theme["card_bg"],
            corner_radius=16,
            border_width=1,
            border_color=theme["card_border"],
        )
        panel.place(relx=0.5, rely=0.5, anchor="center")
        inner = ctk.CTkFrame(panel, fg_color=theme["card_bg"])
        inner.pack(padx=40, pady=28)
        ctk.CTkLabel(inner, text="RFID Payment", font=(UI_FONT, 18, "bold"), text_color=theme["fg"]).pack(pady=(0, 6))
        ctk.CTkLabel(inner, text=f"Total: ₱{total_amount:.2f}", font=(UI_FONT, 16), text_color=theme["muted"]).pack(pady=(0, 10))
        ctk.CTkLabel(inner, text="Enter RFID Card ID (simulate tap):", font=UI_FONT_SMALL, text_color=theme["muted"]).pack(anchor="w", pady=(0, 6))

        uid_entry = ctk.CTkEntry(inner, font=UI_FONT_BODY, width=280, fg_color=theme["search_bg"], text_color=theme["fg"], border_color=theme["search_border"], corner_radius=8, height=40)
        uid_entry.pack(pady=(0, 8))
        error_lbl = ctk.CTkLabel(inner, text="", font=UI_FONT_SMALL, text_color="#b91c1c")
        error_lbl.pack(pady=(0, 4))

        def process_rfid():
            uid = uid_entry.get().strip()
            if not uid:
                error_lbl.configure(text="Please enter a card ID.")
                return
            user = get_user_by_uid(uid)
            if not user:
                error_lbl.configure(text="Card not found.")
                return
            if user["balance"] < total_amount:
                error_lbl.configure(text="Insufficient card balance.")
                return
            new_balance = user["balance"] - total_amount
            update_user_balance(user["id"], new_balance)
            items = self._get_checkout_items()
            if not items:
                self.build_main_menu()
                return
            self._show_dispensing_screen()
            self.after(50, lambda i=items, uid=user["id"], nb=new_balance: self._do_dispense_rfid(i, uid, nb))

        btn_row = ctk.CTkFrame(inner, fg_color=theme["card_bg"])
        btn_row.pack(fill=tk.X, pady=(8, 0))
        ctk.CTkButton(btn_row, text="Pay Now", font=(UI_FONT, 11, "bold"), command=process_rfid, fg_color=theme["accent"], hover_color=theme["accent_hover"], text_color="#ffffff", corner_radius=8, height=38).pack(side=tk.LEFT, padx=(0, 10))
        ctk.CTkButton(btn_row, text="Cancel", font=(UI_FONT, 11, "bold"), command=lambda: (self._reset_checkout_state(), self.build_main_menu()), fg_color=theme["button_bg"], hover_color=theme["card_border"], text_color=theme["button_fg"], corner_radius=8, height=38).pack(side=tk.LEFT)
        uid_entry.bind("<Return>", lambda _e: process_rfid())

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