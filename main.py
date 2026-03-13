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

import bugreport
import prediction_runtime

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

    def toggle_theme(self):
        """Switch between light and dark modes and rebuild the current screen."""
        self.current_theme_name = "dark" if self.current_theme_name == "light" else "light"
        self.current_theme = THEMES[self.current_theme_name]
        ctk.set_appearance_mode(self.current_theme_name)
        self.configure(fg_color=self.current_theme["bg"])
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
            font=(UI_FONT, 11, "bold"),
            text_color=self.current_theme["fg"],
            text="",
        )
        label._datetime_label = True
        label.pack(padx=10, pady=4)

        ph_tz = datetime.timezone(datetime.timedelta(hours=8))

        def _refresh():
            if not label.winfo_exists():
                return
            now = datetime.datetime.now(ph_tz)
            # Shorter, high-signal format so it fits beside footer buttons.
            label.configure(text=now.strftime("PH %b %d, %I:%M %p"))
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

        left_part = ctk.CTkFrame(main_row, fg_color=self.current_theme["bg"], corner_radius=0)
        left_part.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        top = ctk.CTkFrame(left_part, fg_color=self.current_theme["bg"], corner_radius=0)
        top.pack(side=tk.TOP, fill=tk.X)

        header = ctk.CTkFrame(top, fg_color=self.current_theme["bg"], corner_radius=0)
        header.pack(side=tk.TOP, fill=tk.X, pady=(2, 4), padx=10)

        title_block = ctk.CTkFrame(header, fg_color=self.current_theme["bg"], corner_radius=0)
        title_block.pack(side=tk.LEFT)
        ctk.CTkLabel(
            title_block,
            text="Syntax Error",
            font=UI_FONT_TITLE,
            text_color=self.current_theme["fg"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_block,
            text="Main menu",
            font=UI_FONT_SMALL,
            text_color=self.current_theme.get("muted", self.current_theme["fg"]),
        ).pack(anchor="w")

        # Menu + theme toggle (right side)
        icons_frame = ctk.CTkFrame(header, fg_color=self.current_theme["bg"], corner_radius=0)
        icons_frame.pack(side=tk.RIGHT)

        # Hamburger / role menu button
        menu_btn = ctk.CTkButton(
            icons_frame,
            text="☰",
            command=self.show_role_menu,
            font=(UI_FONT, 16, "bold"),
            fg_color="transparent",
            hover_color=self.current_theme["button_bg"],
            text_color=self.current_theme["fg"],
            width=40,
            height=36,
            corner_radius=8,
        )
        menu_btn._hamburger_btn = True
        menu_btn.pack(side=tk.RIGHT, padx=(0, 6), pady=0)

        self.create_theme_slider(icons_frame).pack(side=tk.RIGHT, padx=6, pady=0)

        products = all_products

        # Scrollable product area (using CTkScrollableFrame)
        content_frame = ctk.CTkFrame(left_part, fg_color=self.current_theme["bg"], corner_radius=0)
        content_frame.pack(expand=True, fill=tk.BOTH)

        scroll_frame = ctk.CTkScrollableFrame(
            content_frame,
            fg_color=self.current_theme["bg"],
            corner_radius=0,
        )
        scroll_frame.pack(fill=tk.BOTH, expand=True)

        grid = scroll_frame

        # 2 products per row (2 columns, scroll for more rows)
        for col in range(2):
            grid.grid_columnconfigure(col, weight=1)

        card_bg = self.current_theme.get("card_bg", self.current_theme["button_bg"])
        card_border = self.current_theme.get("card_border", "#e2e8f0")
        selected_bg = "#bbf7d0" if self.current_theme_name == "light" else "#14532d"
        selected_border = self.current_theme.get("accent", "#1A948E")
        placeholder_bg = "#cbd5e1" if self.current_theme_name == "light" else "#475569"
        # Larger placeholder so products are easier to tap on touch screen
        placeholder_size = 160

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

            card = ctk.CTkFrame(
                grid,
                fg_color=selected_bg if in_cart else card_bg,
                border_width=2,
                border_color=selected_border if in_cart else card_border,
                corner_radius=12,
            )
            card.grid(row=r, column=c, padx=10, pady=8, sticky="nsew")
            grid.grid_rowconfigure(r, weight=1)

            # Placeholder (gray square for product image)
            placeholder = ctk.CTkFrame(
                card,
                fg_color=placeholder_bg,
                width=placeholder_size,
                height=placeholder_size,
                corner_radius=8,
            )
            placeholder.pack(pady=(10, 8), padx=10, fill=tk.NONE)
            placeholder.pack_propagate(False)

            # Product name and price inside the card
            name_text = p["name"]
            if len(name_text) > 18:
                name_text = name_text[:18] + "…"
            ctk.CTkLabel(
                card,
                text=name_text,
                font=UI_FONT_BODY,
                text_color=self.current_theme["fg"],
                wraplength=placeholder_size + 40,
                justify="center",
            ).pack(padx=8, pady=(0, 2))
            ctk.CTkLabel(
                card,
                text=f"₱{p['price']:.2f}",
                font=UI_FONT_SMALL,
                text_color=self.current_theme.get("muted", self.current_theme["fg"]),
            ).pack(pady=(0, 6))

            # Add (+) or Remove (X) button
            if in_cart:
                action_btn = ctk.CTkButton(
                    card,
                    text="✕",
                    font=(UI_FONT, 18, "bold"),
                    text_color="#ffffff",
                    fg_color=self.current_theme.get("accent", "#1A948E"),
                    hover_color=self.current_theme.get("accent_hover", "#0f766e"),
                    width=60,
                    height=36,
                    corner_radius=8,
                    command=lambda prod=p: remove_from_cart(prod),
                )
            else:
                action_btn = ctk.CTkButton(
                    card,
                    text="+",
                    font=(UI_FONT, 20, "bold"),
                    text_color="#ffffff",
                    fg_color=self.current_theme.get("accent", "#1A948E"),
                    hover_color=self.current_theme.get("accent_hover", "#15857B"),
                    width=60,
                    height=36,
                    corner_radius=8,
                    state=tk.NORMAL if p["current_stock"] > 0 else tk.DISABLED,
                    command=lambda prod=p: add_to_cart(prod),
                )
                action_btn._product_add_btn = True
            action_btn.pack(pady=(2, 12))

        # Order panel (dark green) – right of left_part, only when cart has items
        order_panel_width = 260
        panel_bg = "#0f766e" if self.current_theme_name == "light" else "#134e4a"
        if self.cart:
            order_panel = ctk.CTkFrame(main_row, fg_color=panel_bg, width=order_panel_width, corner_radius=0)
            order_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=0, pady=0)
            order_panel.pack_propagate(False)

            ctk.CTkButton(
                order_panel,
                text="Cancel",
                font=(UI_FONT, 11, "bold"),
                text_color="#ffffff",
                fg_color=panel_bg,
                hover_color=self.current_theme.get("accent_hover", "#0f766e"),
                corner_radius=8,
                height=36,
                command=lambda: (self.cart.clear(), self.build_main_menu()),
            ).pack(side=tk.TOP, fill=tk.X, padx=10, pady=(10, 8))

            for entry in self.cart:
                prod = entry["product"]
                qty_var = tk.IntVar(value=entry["quantity"])

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
                    command=lambda e=entry: (e.update({"quantity": max(1, e["quantity"] - 1)}), self.build_main_menu()),
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
                    command=lambda e=entry: (e.update({"quantity": min(e["product"]["current_stock"], e["quantity"] + 1)}), self.build_main_menu()),
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

        # Footer: two rows so the datetime is always visible
        bottom = ctk.CTkFrame(self.content_holder, fg_color=self.current_theme["bg"], corner_radius=0)
        bottom.pack(side=tk.BOTTOM, fill=tk.X, pady=(6, 8))
        actions_row = ctk.CTkFrame(bottom, fg_color=self.current_theme["bg"], corner_radius=0)
        actions_row.pack(side=tk.TOP, fill=tk.X)
        info_row = ctk.CTkFrame(bottom, fg_color=self.current_theme["bg"], corner_radius=0)
        info_row.pack(side=tk.TOP, fill=tk.X, pady=(6, 0))

        accent = self.current_theme.get("accent", "#1A948E")
        accent_hover = self.current_theme.get("accent_hover", "#0f766e")
        reload_btn = ctk.CTkButton(
            actions_row,
            text="Reload (RFID)",
            command=self.reload_card_flow,
            font=UI_FONT_BUTTON,
            fg_color=accent,
            hover_color=accent_hover,
            text_color="#ffffff",
            corner_radius=10,
            height=36,
        )
        reload_btn.pack(side=tk.LEFT, padx=(12, 6))
        buy_btn = ctk.CTkButton(
            actions_row,
            text="Buy RFID Card",
            command=self.buy_card_flow,
            font=UI_FONT_BUTTON,
            fg_color=accent,
            hover_color=accent_hover,
            text_color="#ffffff",
            corner_radius=10,
            height=36,
        )
        buy_btn.pack(side=tk.LEFT, padx=6)

        ctk.CTkButton(
            actions_row,
            text="Report",
            command=lambda: bugreport.show_bug_report_screen(self, version=VERSION, hover_scale_btn=_hover_scale_btn),
            font=UI_FONT_BODY,
            fg_color="transparent",
            hover_color=self.current_theme["button_bg"],
            text_color=self.current_theme["fg"],
            border_width=1,
            border_color=self.current_theme.get("card_border", "#e2e8f0"),
            corner_radius=8,
            height=36,
        ).pack(side=tk.LEFT, padx=6)

        ctk.CTkButton(
            actions_row,
            text="How to use?",
            command=self.show_help_dialog,
            font=UI_FONT_BODY,
            fg_color="transparent",
            hover_color=self.current_theme["button_bg"],
            text_color=self.current_theme["fg"],
            border_width=1,
            border_color=self.current_theme.get("card_border", "#e2e8f0"),
            corner_radius=8,
            height=36,
        ).pack(side=tk.LEFT, padx=6)
        ctk.CTkButton(
            actions_row,
            text="Patch Notes",
            command=self.show_patch_notes_dialog,
            font=UI_FONT_BODY,
            fg_color="transparent",
            hover_color=self.current_theme["button_bg"],
            text_color=self.current_theme["fg"],
            border_width=1,
            border_color=self.current_theme.get("card_border", "#e2e8f0"),
            corner_radius=8,
            height=36,
        ).pack(side=tk.LEFT, padx=6)

        # Info row: datetime on the right, version on the left
        self.add_ph_datetime_label(info_row)
        ctk.CTkLabel(
            info_row,
            text=f"SyntaxError™  ·  {VERSION}",
            font=UI_FONT_SMALL,
            text_color=self.current_theme.get("muted", self.current_theme["fg"]),
        ).pack(side=tk.LEFT, padx=(12, 8))

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

        # Bottom bar first so "Back to products" is always visible above the theme footer
        back_bar = ctk.CTkFrame(frame, fg_color=self.current_theme["bg"], corner_radius=0)
        back_bar.pack(side=tk.BOTTOM, fill=tk.X, pady=(8, 0))
        ctk.CTkButton(
            back_bar,
            text="Back to products",
            font=UI_FONT_BODY,
            command=lambda: (self.checkout_items.clear(), self.build_main_menu()),
            fg_color=self.current_theme["button_bg"],
            hover_color=accent,
            text_color=self.current_theme["button_fg"],
            corner_radius=8,
            height=38,
        ).pack(pady=10)

        ctk.CTkLabel(
            frame,
            text="Step 2 of 3 – Review order",
            font=UI_FONT_SMALL,
            text_color=self.current_theme.get("muted", self.current_theme["fg"]),
        ).pack(pady=(16, 0))
        ctk.CTkLabel(
            frame,
            text="Order Summary",
            font=(UI_FONT, 22, "bold"),
            text_color=self.current_theme["fg"],
        ).pack(pady=10)

        card = ctk.CTkFrame(
            frame,
            fg_color=self.current_theme.get("card_bg", self.current_theme["button_bg"]),
            border_width=1,
            border_color=self.current_theme.get("card_border", "#e2e8f0"),
            corner_radius=12,
        )
        card.pack(padx=40, pady=18)

        card_bg_color = self.current_theme.get("card_bg", self.current_theme["button_bg"])
        list_frame = ctk.CTkFrame(card, fg_color=card_bg_color, corner_radius=0)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=(22, 0))
        for col in range(3):
            list_frame.grid_columnconfigure(col, weight=1 if col == 0 else 0)

        for r, it in enumerate(items):
            p = it["product"]
            q = int(it["quantity"])
            line_total = float(p["price"]) * q
            ctk.CTkLabel(
                list_frame,
                text=p["name"],
                font=UI_FONT_BODY,
                text_color=self.current_theme["button_fg"],
                anchor="w",
                wraplength=420,
                justify="left",
            ).grid(row=r, column=0, sticky="w", pady=4)
            ctk.CTkLabel(
                list_frame,
                text=f"x{q}",
                font=(UI_FONT, 12, "bold"),
                text_color=self.current_theme.get("muted", self.current_theme["button_fg"]),
                anchor="e",
            ).grid(row=r, column=1, sticky="e", padx=(10, 0))
            ctk.CTkLabel(
                list_frame,
                text=f"₱{line_total:.2f}",
                font=(UI_FONT, 12, "bold"),
                text_color=self.current_theme["button_fg"],
                anchor="e",
            ).grid(row=r, column=2, sticky="e", padx=(18, 0))

        ctk.CTkLabel(
            card,
            text=f"Total: ₱{total:.2f}",
            font=(UI_FONT, 16, "bold"),
            text_color=self.current_theme["button_fg"],
        ).pack(pady=(14, 10), padx=30)

        ctk.CTkButton(
            card,
            text="Continue to payment",
            font=UI_FONT_BUTTON,
            command=self.show_payment_method_screen,
            fg_color=accent,
            hover_color=accent_hover,
            text_color="#ffffff",
            corner_radius=10,
            height=44,
        ).pack(fill=tk.X, padx=30, pady=(6, 22))

        self.add_theme_toggle_footer()

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

        # Bottom bar first so "Back to products" is always visible above the theme footer
        back_bar = ctk.CTkFrame(frame, fg_color=self.current_theme["bg"], corner_radius=0)
        back_bar.pack(side=tk.BOTTOM, fill=tk.X, pady=(8, 0))
        ctk.CTkButton(
            back_bar,
            text="Back to products",
            font=UI_FONT_BODY,
            command=lambda: (self.checkout_items.clear(), self.build_main_menu()),
            fg_color=self.current_theme["button_bg"],
            hover_color=accent,
            text_color=self.current_theme["button_fg"],
            corner_radius=8,
            height=38,
        ).pack(pady=10)

        ctk.CTkLabel(
            frame,
            text="Step 2 of 3 – Choose quantity",
            font=UI_FONT_SMALL,
            text_color=self.current_theme.get("muted", self.current_theme["fg"]),
        ).pack(pady=(16, 0))

        ctk.CTkLabel(
            frame,
            text="Choose Quantity",
            font=(UI_FONT, 22, "bold"),
            text_color=self.current_theme["fg"],
        ).pack(pady=10)

        card_bg_color = self.current_theme.get("card_bg", self.current_theme["button_bg"])
        card = ctk.CTkFrame(
            frame,
            fg_color=card_bg_color,
            border_width=1,
            border_color=self.current_theme.get("card_border", "#e2e8f0"),
            corner_radius=12,
        )
        card.pack(padx=40, pady=20)

        ctk.CTkLabel(
            card,
            text=f"Selected: {p['name']}",
            font=(UI_FONT, 14, "bold"),
            text_color=self.current_theme["button_fg"],
            wraplength=420,
            justify="center",
        ).pack(pady=(28, 10), padx=36)
        ctk.CTkLabel(
            card,
            text=f"Price: ₱{p['price']:.2f}",
            font=UI_FONT_BODY,
            text_color=self.current_theme["button_fg"],
        ).pack(pady=4, padx=36)
        ctk.CTkLabel(
            card,
            text=f"Available: {p['current_stock']}",
            font=UI_FONT_BODY,
            text_color=self.current_theme.get("muted", self.current_theme["button_fg"]),
        ).pack(pady=(4, 16), padx=36)

        qty_var = tk.IntVar(value=self.current_quantity)

        def update_qty(delta):
            new = qty_var.get() + delta
            if 1 <= new <= p["current_stock"]:
                qty_var.set(new)

        qty_frame = ctk.CTkFrame(card, fg_color=card_bg_color, corner_radius=0)
        qty_frame.pack(pady=14)

        ctk.CTkButton(
            qty_frame,
            text="−",
            font=(UI_FONT, 16, "bold"),
            command=lambda: update_qty(-1),
            fg_color=accent,
            hover_color=accent_hover,
            text_color="#ffffff",
            width=60,
            height=40,
            corner_radius=10,
        ).pack(side=tk.LEFT, padx=12)

        tk.Label(
            qty_frame,
            textvariable=qty_var,
            font=(UI_FONT, 28, "bold"),
            bg=card_bg_color,
            fg=self.current_theme["button_fg"],
            width=5,
        ).pack(side=tk.LEFT, padx=12)

        ctk.CTkButton(
            qty_frame,
            text="+",
            font=(UI_FONT, 16, "bold"),
            command=lambda: update_qty(1),
            fg_color=accent,
            hover_color=accent_hover,
            text_color="#ffffff",
            width=60,
            height=40,
            corner_radius=10,
        ).pack(side=tk.LEFT, padx=12)

        def proceed():
            self.current_quantity = qty_var.get()
            self.checkout_items = [{"product": p, "quantity": int(self.current_quantity or 1)}]
            self.show_payment_method_screen()

        ctk.CTkButton(
            card,
            text="Continue to payment",
            font=UI_FONT_BUTTON,
            command=proceed,
            fg_color=accent,
            hover_color=accent_hover,
            text_color="#ffffff",
            corner_radius=10,
            height=44,
        ).pack(pady=(18, 28), padx=36, fill=tk.X)

        self.add_theme_toggle_footer()

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

        ctk.CTkLabel(
            frame,
            text="Step 3 of 3 – Choose payment method",
            font=UI_FONT_SMALL,
            text_color=self.current_theme["fg"],
        ).pack(pady=(10, 0))
        ctk.CTkLabel(
            frame,
            text="Choose Payment Method",
            font=UI_FONT_BOLD,
            text_color=self.current_theme["fg"],
        ).pack(pady=6)

        card = ctk.CTkFrame(
            frame,
            fg_color=self.current_theme["button_bg"],
            border_width=1,
            border_color=self.current_theme.get("card_border", "#e2e8f0"),
            corner_radius=12,
        )
        card.pack(padx=24, pady=10)

        summary_lines = []
        for it in items:
            p = it["product"]
            q = int(it["quantity"])
            summary_lines.append(f"{p['name']} x{q}")
        summary_text = "\n".join(summary_lines)

        ctk.CTkLabel(
            card,
            text=summary_text,
            font=UI_FONT_BODY,
            text_color=self.current_theme["button_fg"],
            wraplength=360,
            justify="center",
        ).pack(pady=(20, 8), padx=20)
        ctk.CTkLabel(
            card,
            text=f"Total: ₱{total:.2f}",
            font=UI_FONT_TITLE,
            text_color=self.current_theme["button_fg"],
        ).pack(pady=(0, 16), padx=20)

        ctk.CTkButton(
            card,
            text="Pay with Cash\nInsert coins or bills",
            font=UI_FONT_BUTTON,
            fg_color=self.current_theme.get("accent", "#1A948E"),
            hover_color=self.current_theme.get("accent_hover", "#15857B"),
            text_color="#ffffff",
            corner_radius=10,
            height=60,
            command=lambda: self.cash_payment_flow(total),
        ).pack(pady=8, padx=20, fill=tk.X)

        ctk.CTkButton(
            card,
            text="Pay with RFID Card\nCashless payment",
            font=UI_FONT_BUTTON,
            fg_color=self.current_theme.get("accent", "#1A948E"),
            hover_color=self.current_theme.get("accent_hover", "#15857B"),
            text_color="#ffffff",
            corner_radius=10,
            height=60,
            command=lambda: self.rfid_payment_flow(total),
        ).pack(pady=(8, 20), padx=20, fill=tk.X)

        ctk.CTkButton(
            frame,
            text="Back",
            font=UI_FONT_BODY,
            fg_color=self.current_theme["button_bg"],
            hover_color=self.current_theme.get("accent", "#1A948E"),
            text_color=self.current_theme["button_fg"],
            corner_radius=8,
            height=36,
            command=(self.show_order_review_screen if self.checkout_items and len(self.checkout_items) > 1 else self.show_quantity_screen),
        ).pack(pady=10)

        self.add_theme_toggle_footer()

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

        ctk.CTkLabel(
            frame,
            text="Pay with Cash",
            font=UI_FONT_BOLD,
            text_color=self.current_theme["fg"],
        ).pack(pady=(10, 6))
        ctk.CTkLabel(
            frame,
            text="Press the buttons below to simulate inserting coins/bills.",
            font=UI_FONT_SMALL,
            text_color=self.current_theme["fg"],
        ).pack(pady=2)

        card = ctk.CTkFrame(
            frame,
            fg_color=self.current_theme["button_bg"],
            border_width=1,
            border_color=self.current_theme.get("card_border", "#e2e8f0"),
            corner_radius=12,
        )
        card.pack(padx=24, pady=10)

        ctk.CTkLabel(
            card,
            text=f"Total to Pay: ₱{total_amount:.2f}",
            font=UI_FONT_TITLE,
            text_color=self.current_theme["button_fg"],
        ).pack(pady=(20, 12), padx=20)

        amount_var = tk.DoubleVar(value=0.0)
        remaining_var = tk.DoubleVar(value=total_amount)

        ctk.CTkLabel(
            card,
            text="Amount Inserted:",
            font=UI_FONT_BODY,
            text_color=self.current_theme["button_fg"],
        ).pack(pady=4, padx=20)
        tk.Label(
            card,
            textvariable=amount_var,
            font=(UI_FONT, 22, "bold"),
            bg=self.current_theme["button_bg"],
            fg=self.current_theme["button_fg"],
        ).pack()

        ctk.CTkLabel(
            card,
            text="Remaining:",
            font=UI_FONT_BODY,
            text_color=self.current_theme["button_fg"],
        ).pack(pady=(10, 4), padx=20)
        tk.Label(
            card,
            textvariable=remaining_var,
            font=(UI_FONT, 22, "bold"),
            bg=self.current_theme["button_bg"],
            fg=self.current_theme["button_fg"],
        ).pack()

        # Simulated cash buttons for development
        btn_frame = ctk.CTkFrame(card, fg_color=self.current_theme["button_bg"], corner_radius=0)
        btn_frame.pack(pady=15, padx=20)

        def add_money(val):
            cash_session.add(val)
            current = cash_session.get_amount()
            amount_var.set(current)
            remaining_var.set(max(0.0, total_amount - current))

        for text, val in [("+₱1", 1), ("+₱5", 5), ("+₱10", 10), ("+₱20", 20)]:
            ctk.CTkButton(
                btn_frame,
                text=text,
                font=UI_FONT_BODY,
                fg_color=self.current_theme.get("accent", "#1A948E"),
                hover_color=self.current_theme.get("accent_hover", "#15857B"),
                text_color="#ffffff",
                corner_radius=8,
                width=70,
                height=34,
                command=lambda v=val: add_money(v),
            ).pack(side=tk.LEFT, padx=5)

        def finish_if_enough():
            current = cash_session.get_amount()
            if current < total_amount:
                messagebox.showwarning("Not enough", "Please insert more cash.")
                return
            self.complete_purchase_cash(total_amount, current)

        ctk.CTkButton(
            card,
            text="Dispense product",
            font=UI_FONT_BUTTON,
            command=finish_if_enough,
            fg_color="#4CAF50",
            hover_color="#388E3C",
            text_color="#ffffff",
            corner_radius=10,
            height=44,
        ).pack(pady=(10, 20), padx=20, fill=tk.X)

        ctk.CTkButton(
            frame,
            text="Cancel and go back",
            font=UI_FONT_BODY,
            command=self.build_main_menu,
            fg_color="#E53935",
            hover_color="#C62828",
            text_color="#ffffff",
            corner_radius=8,
            height=36,
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
        # Don't update _current_screen_builder for transient screens
        if self.sidebar_holder is not None and self.sidebar_holder.winfo_exists():
            self.sidebar_holder.destroy()
            self.sidebar_holder = None
        self.clear_screen()
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
            text=text,
            font=(UI_FONT, 14),
            text_color=self.current_theme["fg"],
        ).pack(padx=40, pady=24)

        self.add_theme_toggle_footer()

    def show_success_screen(self, title: str, message: str, on_ok=None):
        """In-app success screen (no messagebox pop-up)."""
        # Don't update _current_screen_builder for transient screens
        if self.sidebar_holder is not None and self.sidebar_holder.winfo_exists():
            self.sidebar_holder.destroy()
            self.sidebar_holder = None
        self.clear_screen()
        frame = ctk.CTkFrame(self.content_holder, fg_color=self.current_theme["bg"], corner_radius=0)
        frame.pack(expand=True, fill=tk.BOTH)
        card = ctk.CTkFrame(
            frame,
            fg_color=self.current_theme.get("card_bg", "#ffffff"),
            border_width=2,
            border_color=self.current_theme.get("accent", "#1A948E"),
            corner_radius=12,
        )
        card.place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(
            card,
            text=title,
            font=(UI_FONT, 18, "bold"),
            text_color=self.current_theme.get("accent", "#1A948E"),
        ).pack(pady=(20, 8), padx=32)
        ctk.CTkLabel(
            card,
            text=message,
            font=UI_FONT_BODY,
            text_color=self.current_theme["fg"],
            justify="center",
        ).pack(padx=32, pady=(0, 20))
        ctk.CTkButton(
            card,
            text="OK",
            font=(UI_FONT, 12, "bold"),
            command=on_ok or self.build_main_menu,
            fg_color=self.current_theme.get("accent", "#1A948E"),
            hover_color=self.current_theme.get("accent_hover", "#15857B"),
            text_color="#ffffff",
            corner_radius=10,
            width=120,
            height=40,
        ).pack(pady=(0, 20))
        self.add_theme_toggle_footer()

    # ---------- RFID Card Purchase ----------

    def buy_card_flow(self):
        """Customer buys a new RFID card for a fixed price (e.g. ₱50)."""
        self._current_screen_builder = self.buy_card_flow
        CARD_PRICE = 50.0
        if self.sidebar_holder is not None and self.sidebar_holder.winfo_exists():
            self.sidebar_holder.destroy()
            self.sidebar_holder = None
        self.clear_screen()
        cash_session.reset()

        self.content_holder.configure(fg_color=LOGIN_PAGE_BG)
        frame = ctk.CTkFrame(self.content_holder, fg_color=LOGIN_PAGE_BG)
        frame.pack(expand=True, fill=tk.BOTH)

        panel = ctk.CTkFrame(frame, fg_color=LOGIN_PANEL_BG, corner_radius=16)
        panel.place(relx=0.5, rely=0.5, anchor="center")
        inner = ctk.CTkFrame(panel, fg_color=LOGIN_PANEL_BG)
        inner.pack(padx=40, pady=28)

        ctk.CTkLabel(
            inner,
            text="Buy a New RFID Card",
            font=(UI_FONT, 18, "bold"),
            text_color="#0f766e",
        ).pack(pady=(0, 10))
        ctk.CTkLabel(
            inner,
            text=f"Please pay ₱{CARD_PRICE:.2f} using the cash buttons below.",
            font=UI_FONT_BODY,
            text_color="#134e4a",
            wraplength=360,
            justify="left",
        ).pack(pady=(0, 10))

        amount_var = tk.DoubleVar(value=0.0)
        remaining_var = tk.DoubleVar(value=CARD_PRICE)

        ctk.CTkLabel(
            inner,
            text="Amount Inserted:",
            font=UI_FONT_BODY,
            text_color="#134e4a",
        ).pack(pady=4)
        tk.Label(
            inner,
            textvariable=amount_var,
            font=(UI_FONT, 20, "bold"),
            bg=LOGIN_PANEL_BG,
            fg="#0f172a",
        ).pack()
        ctk.CTkLabel(
            inner,
            text="Remaining:",
            font=UI_FONT_BODY,
            text_color="#134e4a",
        ).pack(pady=4)
        tk.Label(
            inner,
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

        btn_frame = ctk.CTkFrame(inner, fg_color=LOGIN_PANEL_BG)
        btn_frame.pack(pady=12)
        for txt, val in [("+₱1", 1), ("+₱5", 5), ("+₱10", 10), ("+₱20", 20)]:
            ctk.CTkButton(
                btn_frame,
                text=txt,
                width=80,
                font=UI_FONT_BODY,
                command=lambda v=val: add_money(v),
                fg_color=LOGIN_BTN_BG,
                hover_color=LOGIN_BTN_HOVER,
                text_color="#ffffff",
                corner_radius=8,
            ).pack(side=tk.LEFT, padx=10)

        def confirm_purchase():
            inserted = cash_session.get_amount()
            if inserted < CARD_PRICE:
                messagebox.showwarning("Not enough", "Please insert full card price.")
                return

            uid = uuid.uuid4().hex[:8].upper()
            user_id = create_user(uid, name=None, is_staff=0, initial_balance=0.0)

            record_transaction(
                product_id=None,
                quantity=None,
                total_amount=CARD_PRICE,
                payment_method="card_purchase",
                rfid_user_id=user_id,
            )

            self.show_success_screen(
                "Card Issued",
                f"New RFID card created.\nCard ID (simulate UID): {uid}",
                on_ok=self.build_main_menu,
            )

        action_frame = ctk.CTkFrame(inner, fg_color=LOGIN_PANEL_BG)
        action_frame.pack(pady=(8, 0), fill=tk.X)

        ctk.CTkButton(
            action_frame,
            text="Confirm and issue card",
            font=UI_FONT_BUTTON,
            command=confirm_purchase,
            fg_color=LOGIN_BTN_BG,
            hover_color=LOGIN_BTN_HOVER,
            text_color="#ffffff",
            corner_radius=8,
            height=40,
        ).pack(side=tk.LEFT, padx=(0, 10))

        ctk.CTkButton(
            action_frame,
            text="Cancel and go back",
            font=UI_FONT_BODY,
            command=self.build_main_menu,
            fg_color=LOGIN_BTN_BG,
            hover_color=LOGIN_BTN_HOVER,
            text_color="#ffffff",
            corner_radius=8,
            height=36,
        ).pack(side=tk.LEFT)

        self.add_theme_toggle_footer()

    # ---------- RFID Reload ----------

    def reload_card_flow(self):
        """Customer reloads an existing RFID card balance."""
        self._current_screen_builder = self.reload_card_flow
        if self.sidebar_holder is not None and self.sidebar_holder.winfo_exists():
            self.sidebar_holder.destroy()
            self.sidebar_holder = None
        self.clear_screen()
        self.content_holder.configure(fg_color=LOGIN_PAGE_BG)

        frame = ctk.CTkFrame(self.content_holder, fg_color=LOGIN_PAGE_BG)
        frame.pack(expand=True, fill=tk.BOTH)

        panel = ctk.CTkFrame(frame, fg_color=LOGIN_PANEL_BG, corner_radius=16)
        panel.place(relx=0.5, rely=0.5, anchor="center")
        inner = ctk.CTkFrame(panel, fg_color=LOGIN_PANEL_BG)
        inner.pack(padx=40, pady=28)

        ctk.CTkLabel(
            inner,
            text="Reload RFID Card",
            font=(UI_FONT, 18, "bold"),
            text_color="#0f766e",
        ).pack(pady=(0, 10))

        ctk.CTkLabel(
            inner,
            text="Enter RFID Card ID (simulate tap):",
            font=UI_FONT_SMALL,
            text_color="#134e4a",
        ).pack(anchor="w", pady=(0, 6))

        uid_entry = ctk.CTkEntry(
            inner,
            font=UI_FONT_BODY,
            width=280,
            fg_color="#ffffff",
            text_color="#1e293b",
            border_color="#94a3b8",
            corner_radius=8,
            height=40,
        )
        uid_entry.pack(pady=(0, 8))
        uid_entry.focus_set()

        error_lbl = ctk.CTkLabel(
            inner,
            text="",
            font=UI_FONT_SMALL,
            text_color="#b91c1c",
        )
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

        btn_row = ctk.CTkFrame(inner, fg_color=LOGIN_PANEL_BG)
        btn_row.pack(fill=tk.X, pady=(8, 0))

        ctk.CTkButton(
            btn_row,
            text="OK",
            font=(UI_FONT, 11, "bold"),
            command=proceed_to_amount,
            fg_color=LOGIN_BTN_BG,
            hover_color=LOGIN_BTN_HOVER,
            text_color="#ffffff",
            corner_radius=8,
            height=38,
        ).pack(side=tk.LEFT, padx=(0, 10))

        ctk.CTkButton(
            btn_row,
            text="Cancel",
            font=(UI_FONT, 11, "bold"),
            command=self.build_main_menu,
            fg_color=LOGIN_BTN_BG,
            hover_color=LOGIN_BTN_HOVER,
            text_color="#ffffff",
            corner_radius=8,
            height=38,
        ).pack(side=tk.LEFT)

        uid_entry.bind("<Return>", lambda _e: proceed_to_amount())
        self.add_theme_toggle_footer()

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

        ctk.CTkLabel(
            frame,
            text="Reload RFID Card",
            font=UI_FONT_BOLD,
            text_color=theme["fg"],
        ).pack(pady=10)

        card = ctk.CTkFrame(
            frame,
            fg_color=theme["button_bg"],
            corner_radius=12,
            border_width=1,
            border_color="#94a3b8",
        )
        card.pack(padx=24, pady=10)
        card_inner = ctk.CTkFrame(card, fg_color=theme["button_bg"])
        card_inner.pack(padx=20, pady=18)

        ctk.CTkLabel(
            card_inner,
            text=f"Card ID: {uid}",
            font=UI_FONT_BODY,
            text_color=theme["button_fg"],
        ).pack(pady=(0, 4))
        ctk.CTkLabel(
            card_inner,
            text=f"Current Balance: ₱{user['balance']:.2f}",
            font=UI_FONT_BODY,
            text_color=theme["button_fg"],
        ).pack(pady=(0, 10))

        amount_var = tk.DoubleVar(value=0.0)

        ctk.CTkLabel(
            card_inner,
            text="Amount to Load:",
            font=UI_FONT_BODY,
            text_color=theme["button_fg"],
        ).pack(pady=5)
        tk.Label(
            card_inner,
            textvariable=amount_var,
            font=(UI_FONT, 22, "bold"),
            bg=theme["button_bg"],
            fg=theme["button_fg"],
        ).pack()

        btn_frame = ctk.CTkFrame(card_inner, fg_color=theme["button_bg"])
        btn_frame.pack(pady=15)

        def add_money(val):
            cash_session.add(val)
            amount_var.set(cash_session.get_amount())

        for txt, val in [("+₱1", 1), ("+₱5", 5), ("+₱10", 10), ("+₱20", 20)]:
            ctk.CTkButton(
                btn_frame,
                text=txt,
                width=70,
                font=UI_FONT_BODY,
                command=lambda v=val: add_money(v),
                fg_color=LOGIN_BTN_BG,
                hover_color=LOGIN_BTN_HOVER,
                text_color="#ffffff",
                corner_radius=8,
            ).pack(side=tk.LEFT, padx=5)

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

        ctk.CTkButton(
            card_inner,
            text="Add balance",
            font=UI_FONT_BUTTON,
            command=confirm_reload,
            fg_color="#4CAF50",
            hover_color="#388E3C",
            text_color="#ffffff",
            corner_radius=8,
            height=44,
        ).pack(pady=(10, 8), fill=tk.X)

        ctk.CTkButton(
            frame,
            text="Cancel and go back",
            font=UI_FONT_BODY,
            command=self.build_main_menu,
            fg_color="#E53935",
            hover_color="#C62828",
            text_color="#ffffff",
            corner_radius=8,
            height=36,
        ).pack(pady=5)

        self.add_theme_toggle_footer()

    # ---------- RFID Purchase Payment ----------

    def rfid_payment_flow(self, total_amount: float):
        """Purchase products using RFID card balance – in-app card ID entry."""
        self._current_screen_builder = lambda: self.rfid_payment_flow(total_amount)
        if self.sidebar_holder is not None and self.sidebar_holder.winfo_exists():
            self.sidebar_holder.destroy()
            self.sidebar_holder = None
        self.clear_screen()
        self.content_holder.configure(fg_color=LOGIN_PAGE_BG)

        frame = ctk.CTkFrame(self.content_holder, fg_color=LOGIN_PAGE_BG)
        frame.pack(expand=True, fill=tk.BOTH)

        panel = ctk.CTkFrame(frame, fg_color=LOGIN_PANEL_BG, corner_radius=16)
        panel.place(relx=0.5, rely=0.5, anchor="center")
        inner = ctk.CTkFrame(panel, fg_color=LOGIN_PANEL_BG)
        inner.pack(padx=40, pady=28)

        ctk.CTkLabel(
            inner,
            text="RFID Payment",
            font=(UI_FONT, 18, "bold"),
            text_color="#0f766e",
        ).pack(pady=(0, 6))
        ctk.CTkLabel(
            inner,
            text=f"Total: ₱{total_amount:.2f}",
            font=(UI_FONT, 16),
            text_color="#134e4a",
        ).pack(pady=(0, 10))
        ctk.CTkLabel(
            inner,
            text="Enter RFID Card ID (simulate tap):",
            font=UI_FONT_SMALL,
            text_color="#134e4a",
        ).pack(anchor="w", pady=(0, 6))

        uid_entry = ctk.CTkEntry(
            inner,
            font=UI_FONT_BODY,
            width=280,
            fg_color="#ffffff",
            text_color="#1e293b",
            border_color="#94a3b8",
            corner_radius=8,
            height=40,
        )
        uid_entry.pack(pady=(0, 8))
        uid_entry.focus_set()

        error_lbl = ctk.CTkLabel(
            inner,
            text="",
            font=UI_FONT_SMALL,
            text_color="#b91c1c",
        )
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

        btn_row = ctk.CTkFrame(inner, fg_color=LOGIN_PANEL_BG)
        btn_row.pack(fill=tk.X, pady=(8, 0))

        ctk.CTkButton(
            btn_row,
            text="Pay Now",
            font=(UI_FONT, 11, "bold"),
            command=process_rfid,
            fg_color=LOGIN_BTN_BG,
            hover_color=LOGIN_BTN_HOVER,
            text_color="#ffffff",
            corner_radius=8,
            height=38,
        ).pack(side=tk.LEFT, padx=(0, 10))

        ctk.CTkButton(
            btn_row,
            text="Cancel",
            font=(UI_FONT, 11, "bold"),
            command=lambda: (self._reset_checkout_state(), self.build_main_menu()),
            fg_color="#E53935",
            hover_color="#C62828",
            text_color="#ffffff",
            corner_radius=8,
            height=38,
        ).pack(side=tk.LEFT)

        uid_entry.bind("<Return>", lambda _e: process_rfid())
        self.add_theme_toggle_footer()

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