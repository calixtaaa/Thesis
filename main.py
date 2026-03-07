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

# Simple theming (light / dark)
THEMES = {
    "light": {
        "bg": "#ffffff",
        "fg": "#000000",
        "button_bg": "#f0f0f0",
        "button_fg": "#000000",
    },
    "dark": {
        "bg": "#202124",
        "fg": "#e8eaed",
        "button_bg": "#3c4043",
        "button_fg": "#e8eaed",
    },
}

UI_FONT = "Segoe UI"
UI_FONT_BOLD = (UI_FONT, 20, "bold")
UI_FONT_TITLE = (UI_FONT, 18, "bold")
UI_FONT_BODY = (UI_FONT, 12)
UI_FONT_SMALL = (UI_FONT, 10)
UI_FONT_BUTTON = (UI_FONT, 12, "bold")

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
            self.geometry("800x480")
            self.minsize(800, 480)

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

        # Sidebar / navbar state
        self.role_menu = None
        self.sidebar_frame = None

        self.search_var = tk.StringVar()
        self.theme_animating = False

        self.build_main_menu()

    # ---------- Screen helpers ----------

    def clear_screen(self):
        # region agent log
        self._debug_log(
            "H5",
            "main.py:clear_screen",
            "clear_screen called",
            {"child_count": len(self.winfo_children())},
        )
        # endregion
        for w in self.winfo_children():
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

        pressed_bg = "#d9e7ff" if self.current_theme_name == "light" else "#5a6a85"

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
        """Add a bottom bar with a theme toggle button to the current screen."""
        bottom = tk.Frame(self, bg=self.current_theme["bg"])
        bottom.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        # Trademark / version footer label
        tk.Label(
            bottom,
            text=f"SyntaxError™  ·  {VERSION}",
            font=("Arial", 9),
            bg=self.current_theme["bg"],
            fg=self.current_theme["fg"],
        ).pack(side=tk.LEFT, padx=10)
        self.add_ph_datetime_label(bottom)
        tk.Button(
            bottom,
            text=f"Theme: {self.current_theme_name.capitalize()}",
            command=self.toggle_theme,
            bg=self.current_theme["button_bg"],
            fg=self.current_theme["button_fg"],
        ).pack(side=tk.RIGHT, padx=10)
        self.apply_theme_to_widget(self)

    def add_ph_datetime_label(self, parent):
        """Show a live Philippine date/time label inside the given parent."""
        label = tk.Label(
            parent,
            font=("Arial", 9),
            bg=self.current_theme["bg"],
            fg=self.current_theme["fg"],
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
        """Toggle a left sidebar for Staff/Admin actions (hamburger menu)."""
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

        # Create a vertical sidebar on the left, similar to the reference image
        sidebar_width = 200
        sidebar = tk.Frame(self, bg=self.current_theme["bg"], width=sidebar_width)
        sidebar.place(x=0, y=0, relheight=1.0)

        tk.Label(
            sidebar,
            text="Menu",
            font=("Arial", 14, "bold"),
            bg=self.current_theme["bg"],
            fg=self.current_theme["fg"],
        ).pack(anchor="w", padx=12, pady=(12, 8))

        def make_nav_button(text, command):
            btn = tk.Button(
                sidebar,
                text=text,
                anchor="w",
                font=("Arial", 11),
                command=command,
                bg=self.current_theme["button_bg"],
                fg=self.current_theme["button_fg"],
                relief="flat",
                padx=10,
                pady=4,
            )
            btn.pack(fill=tk.X, padx=8, pady=2)
            return btn

        # Dashboard just closes sidebar and keeps current screen
        make_nav_button("Dashboard (user view)", lambda: self.show_role_menu())

        # Staff restock screen
        make_nav_button(
            "Staff – Restock products",
            lambda: (self.show_role_menu(), self.enter_restock_mode()),
        )

        # Admin dashboard
        make_nav_button(
            "Admin – Reports & settings",
            lambda: (self.show_role_menu(), self.enter_admin_dashboard()),
        )

        # Sign out/back to main
        make_nav_button(
            "Back to main screen",
            lambda: (self.show_role_menu(), self.build_main_menu()),
        )

        self.apply_theme_to_widget(sidebar)
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

    # ---------- Main Menu ----------

    def build_main_menu(self):
        self.clear_screen()
        all_products = get_all_products()

        top = tk.Frame(self, bg=self.current_theme["bg"])
        top.pack(side=tk.TOP, fill=tk.X)

        header = tk.Frame(top, bg=self.current_theme["bg"])
        header.pack(side=tk.TOP, fill=tk.X, pady=2, padx=8)

        title_block = tk.Frame(header, bg=self.current_theme["bg"])
        title_block.pack(side=tk.LEFT)
        tk.Label(
            title_block,
            text="Select Product",
            font=("Arial", 20, "bold"),
            bg=self.current_theme["bg"],
            fg=self.current_theme["fg"],
        ).pack(anchor="w")
        tk.Label(
            title_block,
            text="Step 1 of 3 – Tap a product to begin",
            font=("Arial", 10),
            bg=self.current_theme["bg"],
            fg=self.current_theme["fg"],
        ).pack(anchor="w")

        # Header action buttons on the top-right
        icons_frame = tk.Frame(header, bg=self.current_theme["bg"])
        icons_frame.pack(side=tk.RIGHT)
        self.create_theme_slider(icons_frame).pack(side=tk.RIGHT, padx=6, pady=0)
        if self.menu_icon is not None:
            tk.Button(
                icons_frame,
                image=self.menu_icon,
                command=self.show_role_menu,
                bg=self.current_theme["bg"],
                activebackground=self.current_theme["bg"],
                bd=0,
                highlightthickness=0,
                width=self.menu_icon.width(),
                height=self.menu_icon.height(),
                padx=0,
                pady=0,
            ).pack(side=tk.RIGHT, padx=4, pady=0)
        else:
            tk.Button(
                icons_frame,
                text="☰",
                command=self.show_role_menu,
                bg=self.current_theme["button_bg"],
                fg=self.current_theme["button_fg"],
            ).pack(side=tk.RIGHT, padx=2, pady=0)

        # Search bar row (pill-shaped style)
        search_row = tk.Frame(self, bg=self.current_theme["bg"])
        search_row.pack(side=tk.TOP, fill=tk.X, padx=12, pady=(0, 8))

        # Outer container to simulate rounded, light background
        search_bg = "#f1f3f4"
        pill = tk.Frame(
            search_row,
            bg=search_bg,
            bd=0,
            highlightthickness=0,
        )
        pill.pack(side=tk.LEFT, fill=tk.X, expand=True)

        if self.search_icon is not None:
            tk.Label(
                pill,
                image=self.search_icon,
                bg=search_bg,
            ).pack(side=tk.LEFT, padx=(8, 4), pady=4)

        search_entry = tk.Entry(
            pill,
            textvariable=self.search_var,
            font=("Arial", 11),
            bd=0,
            highlightthickness=0,
            relief="flat",
            bg=search_bg,
        )
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4), pady=4)
        if not self.search_var.get():
            self.search_var.set("Search for products")

        def on_search_focus_in(_event):
            # region agent log
            self._debug_log(
                "H6",
                "main.py:on_search_focus_in",
                "search focus in",
                {"query_before": self.search_var.get()},
            )
            # endregion
            if self.search_var.get() == "Search for products":
                self.search_var.set("")

        def on_search_focus_out(_event):
            # region agent log
            self._debug_log(
                "H6",
                "main.py:on_search_focus_out",
                "search focus out",
                {"query_before": self.search_var.get()},
            )
            # endregion
            if not self.search_var.get().strip():
                self.search_var.set("Search for products")

        def refresh_products(_event=None):
            # region agent log
            self._debug_log(
                "H5",
                "main.py:refresh_products",
                "search refresh requested",
                {"query": self.search_var.get(), "event_type": getattr(_event, "type", None)},
            )
            # endregion
            self.build_main_menu()

        def clear_one_char():
            current = self.search_var.get()
            if current == "Search for products" or not current:
                return
            self.search_var.set(current[:-1])
            # region agent log
            self._debug_log(
                "H5",
                "main.py:clear_one_char",
                "backspace icon used",
                {"new_query": self.search_var.get()},
            )
            # endregion
            refresh_products()

        search_entry.bind("<FocusIn>", on_search_focus_in)
        search_entry.bind("<FocusOut>", on_search_focus_out)
        search_entry.bind("<KeyRelease>", refresh_products)

        # Backspace icon button to delete one character from search
        if self.backspace_icon is not None:
            tk.Button(
                pill,
                image=self.backspace_icon,
                command=clear_one_char,
                bg=search_bg,
                activebackground=search_bg,
                bd=0,
                highlightthickness=0,
            ).pack(side=tk.LEFT, padx=(0, 8), pady=4)

        # Filter products based on search text
        query = self.search_var.get().strip()
        if query and query != "Search for products":
            products = [p for p in all_products if query.lower() in p["name"].lower()]
        else:
            products = all_products

        # region agent log
        self._debug_log(
            "H4",
            "main.py:build_main_menu",
            "main menu rendered",
            {
                "all_products_count": len(all_products),
                "filtered_products_count": len(products),
                "query": query,
                "menu_icon_loaded": self.menu_icon is not None,
                "light_theme_icon_loaded": self.light_theme_icon is not None,
                "dark_theme_icon_loaded": self.dark_theme_icon is not None,
            },
        )
        # endregion

        # Scrollable product area
        content_frame = tk.Frame(self, bg=self.current_theme["bg"])
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

        # Make the product grid responsive (3 columns)
        for c in range(3):
            grid.grid_columnconfigure(c, weight=1)

        for idx, p in enumerate(products):
            name = p["name"]
            stock = p["current_stock"]
            capacity = p["capacity"]
            price = p["price"]

            btn_text = f"{name}\n{stock}/{capacity}\n₱{price:.2f}"
            state = tk.NORMAL if stock > 0 else tk.DISABLED

            btn = tk.Button(
                grid,
                text=btn_text,
                state=state,
                bg=self.current_theme["button_bg"],
                fg=self.current_theme["button_fg"],
                activebackground=self.current_theme["button_bg"],
                activeforeground=self.current_theme["button_fg"],
                wraplength=200,
                padx=10,
                pady=10,
                relief=tk.RAISED,
                bd=2,
            )
            btn.configure(command=lambda prod=p, button=btn: self.animate_button_press(
                button,
                lambda: self.select_product(prod),
            ))
            r = idx // 3
            c = idx % 3
            btn.grid(row=r, column=c, padx=10, pady=10, sticky="nsew")
            grid.grid_rowconfigure(r, weight=1)

        def _on_frame_configure(_event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        grid.bind("<Configure>", _on_frame_configure)

        # Mouse wheel scrolling for better UX
        def _on_mousewheel(event):
            # Windows / Mac delta handling
            delta = -1 * int(event.delta / 120)
            # region agent log
            self._debug_log(
                "H7",
                "main.py:_on_mousewheel",
                "mousewheel scroll",
                {"delta": delta},
            )
            # endregion
            canvas.yview_scroll(delta, "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        bottom = tk.Frame(self, bg=self.current_theme["bg"])
        bottom.pack(side=tk.BOTTOM, fill=tk.X, pady=10)

        # Visible buttons for regular users
        tk.Button(
            bottom,
            text="Reload (RFID)",
            command=self.reload_card_flow,
            bg="#4CAF50",
            fg=self.current_theme["button_fg"],
        ).pack(side=tk.LEFT, padx=10)
        tk.Button(
            bottom,
            text="Buy RFID Card",
            command=self.buy_card_flow,
            bg="#4CAF50",
            fg=self.current_theme["button_fg"],
        ).pack(side=tk.LEFT, padx=10)

        # Simple help button explaining the 3 steps
        tk.Button(
            bottom,
            text="How to use?",
            command=self.show_help_dialog,
            bg=self.current_theme["button_bg"],
            fg=self.current_theme["button_fg"],
        ).pack(side=tk.LEFT, padx=10)
        tk.Button(
            bottom,
            text="Patch Notes",
            command=self.show_patch_notes_dialog,
            bg=self.current_theme["button_bg"],
            fg=self.current_theme["button_fg"],
        ).pack(side=tk.LEFT, padx=10)

        # Trademark / version footer label
        tk.Label(
            bottom,
            text=f"SyntaxError™  ·  {VERSION}",
            font=("Arial", 9),
            bg=self.current_theme["bg"],
            fg=self.current_theme["fg"],
        ).pack(side=tk.LEFT, padx=10)

        self.add_ph_datetime_label(bottom)

        self.apply_theme_to_widget(self)

    def select_product(self, product_row):
        self.current_product = product_row
        self.current_quantity = 1
        self.show_quantity_screen()

    # ---------- Quantity Screen ----------

    def show_quantity_screen(self):
        self.clear_screen()
        p = self.current_product

        frame = tk.Frame(self, bg=self.current_theme["bg"])
        frame.pack(expand=True, fill=tk.BOTH)

        tk.Label(
            frame,
            text="Step 2 of 3 – Choose quantity",
            font=UI_FONT_SMALL,
            bg=self.current_theme["bg"],
            fg=self.current_theme["fg"],
        ).pack(pady=(10, 0))

        tk.Label(
            frame,
            text="Choose Quantity",
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

        tk.Label(
            card,
            text=f"Selected: {p['name']}",
            font=UI_FONT_BODY,
            bg=self.current_theme["button_bg"],
            fg=self.current_theme["button_fg"],
            wraplength=360,
            justify="center",
        ).pack(pady=(0, 8))
        tk.Label(
            card,
            text=f"Price: ₱{p['price']:.2f}",
            font=UI_FONT_BODY,
            bg=self.current_theme["button_bg"],
            fg=self.current_theme["button_fg"],
        ).pack(pady=3)
        tk.Label(
            card,
            text=f"Available: {p['current_stock']}",
            font=UI_FONT_BODY,
            bg=self.current_theme["button_bg"],
            fg=self.current_theme["button_fg"],
        ).pack(pady=(3, 12))

        qty_var = tk.IntVar(value=self.current_quantity)

        def update_qty(delta):
            new = qty_var.get() + delta
            if 1 <= new <= p["current_stock"]:
                qty_var.set(new)

        qty_frame = tk.Frame(card, bg=self.current_theme["button_bg"])
        qty_frame.pack(pady=12)

        tk.Button(
            qty_frame,
            text="-",
            width=4,
            font=UI_FONT_BUTTON,
            command=lambda: update_qty(-1),
        ).pack(side=tk.LEFT, padx=10)
        tk.Label(
            qty_frame,
            textvariable=qty_var,
            font=(UI_FONT, 24, "bold"),
            bg=self.current_theme["button_bg"],
            fg=self.current_theme["button_fg"],
            width=4,
        ).pack(side=tk.LEFT, padx=10)
        tk.Button(
            qty_frame,
            text="+",
            width=4,
            font=UI_FONT_BUTTON,
            command=lambda: update_qty(1),
        ).pack(side=tk.LEFT, padx=10)

        def proceed():
            self.current_quantity = qty_var.get()
            self.show_payment_method_screen()

        tk.Button(
            card,
            text="Continue to payment",
            font=UI_FONT_BUTTON,
            width=28,
            height=2,
            command=proceed,
        ).pack(pady=(14, 8), fill=tk.X)
        tk.Button(
            frame,
            text="Back to products",
            font=UI_FONT_BODY,
            padx=16,
            pady=6,
            command=self.build_main_menu,
        ).pack(pady=5)

        self.add_theme_toggle_footer()

    # ---------- Payment Method ----------

    def show_payment_method_screen(self):
        self.clear_screen()
        p = self.current_product
        q = self.current_quantity
        total = p["price"] * q

        frame = tk.Frame(self, bg=self.current_theme["bg"])
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

        tk.Label(
            card,
            text=f"Product: {p['name']} x{q}",
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
            text="Back to quantity",
            font=UI_FONT_BODY,
            padx=16,
            pady=6,
            command=self.show_quantity_screen,
        ).pack(pady=10)

        self.add_theme_toggle_footer()

    # ---------- Cash Payment Flow ----------

    def cash_payment_flow(self, total_amount: float):
        self.clear_screen()
        cash_session.reset()

        frame = tk.Frame(self, bg=self.current_theme["bg"])
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
        p = self.current_product
        q = self.current_quantity
        change = max(0.0, inserted - total_amount)

        self.show_wait_screen("Processing payment and dispensing...")

        try:
            decrement_stock(p["id"], q)
            dispense_from_slot(p["slot_number"], q)
            if change > 0:
                dispense_change(change)
            record_transaction(p["id"], q, total_amount, "cash")
            messagebox.showinfo(
                "Thank you",
                f"Please take your product.\nChange: ₱{change:.2f}"
            )
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            self.build_main_menu()

    # ---------- Utility Screens ----------

    def show_wait_screen(self, text: str):
        self.clear_screen()
        frame = tk.Frame(self, bg=self.current_theme["bg"])
        frame.pack(expand=True, fill=tk.BOTH)
        tk.Label(frame, text=text, font=("Arial", 18)).pack(pady=20)

        self.add_theme_toggle_footer()

    # ---------- RFID Card Purchase ----------

    def buy_card_flow(self):
        """Customer buys a new RFID card for a fixed price (e.g. ₱50)."""
        CARD_PRICE = 50.0
        self.clear_screen()
        cash_session.reset()

        frame = tk.Frame(self, bg=self.current_theme["bg"])
        frame.pack(expand=True, fill=tk.BOTH)

        tk.Label(frame, text="Buy a New RFID Card", font=("Arial", 20)).pack(pady=10)
        tk.Label(frame, text=f"Please pay ₱{CARD_PRICE:.2f}", font=("Arial", 14)).pack(pady=5)

        amount_var = tk.DoubleVar(value=0.0)
        remaining_var = tk.DoubleVar(value=CARD_PRICE)

        tk.Label(frame, text="Amount Inserted:", font=("Arial", 14)).pack(pady=5)
        tk.Label(frame, textvariable=amount_var, font=("Arial", 22)).pack()

        tk.Label(frame, text="Remaining:", font=("Arial", 14)).pack(pady=5)
        tk.Label(frame, textvariable=remaining_var, font=("Arial", 22)).pack()

        btn_frame = tk.Frame(frame, bg=self.current_theme["bg"])
        btn_frame.pack(pady=15)

        def add_money(val):
            cash_session.add(val)
            current = cash_session.get_amount()
            amount_var.set(current)
            remaining_var.set(max(0.0, CARD_PRICE - current))

        tk.Button(btn_frame, text="+₱1", width=8, command=lambda: add_money(1)).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="+₱5", width=8, command=lambda: add_money(5)).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="+₱10", width=8, command=lambda: add_money(10)).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="+₱20", width=8, command=lambda: add_money(20)).pack(side=tk.LEFT, padx=5)

        def confirm_purchase():
            inserted = cash_session.get_amount()
            if inserted < CARD_PRICE:
                messagebox.showwarning("Not enough", "Please insert full card price.")
                return

            self.show_wait_screen("Issuing RFID card...")

            # Generate a simple random UID for demonstration
            uid = uuid.uuid4().hex[:8].upper()
            user_id = create_user(uid, name=None, is_staff=0, initial_balance=0.0)

            # Record transaction (no specific product)
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
            font=("Arial", 14),
            command=confirm_purchase,
            bg="#4CAF50",
            fg=self.current_theme["button_fg"],
        ).pack(pady=15)

        tk.Button(
            frame,
            text="Cancel and go back",
            command=self.build_main_menu,
            bg="#E53935",
            fg=self.current_theme["button_fg"],
        ).pack(pady=5)

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

        self.clear_screen()
        cash_session.reset()

        frame = tk.Frame(self, bg=self.current_theme["bg"])
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

        p = self.current_product
        q = self.current_quantity

        self.show_wait_screen("Processing RFID payment and dispensing...")
        try:
            decrement_stock(p["id"], q)
            dispense_from_slot(p["slot_number"], q)
            record_transaction(
                product_id=p["id"],
                quantity=q,
                total_amount=total_amount,
                payment_method="rfid_purchase",
                rfid_user_id=user["id"],
            )
            messagebox.showinfo(
                "Thank you",
                f"Payment successful.\nRemaining balance: ₱{new_balance:.2f}\nPlease take your product."
            )
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
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