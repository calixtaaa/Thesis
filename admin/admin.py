import hashlib
import hmac as _hmac
import tkinter as tk
from tkinter import messagebox, simpledialog
import customtkinter as ctk

from admin.reports import list_sales_reports, open_sales_report
from pathlib import Path as _Path
import secrets as _secrets

_SALT_FILE = _Path(__file__).resolve().parent.parent / ".secret_salt"
if _SALT_FILE.exists():
    _PASSWORD_SALT = _SALT_FILE.read_text(encoding="utf-8").strip()
else:
    _PASSWORD_SALT = _secrets.token_hex(16)
    try:
        _SALT_FILE.write_text(_PASSWORD_SALT, encoding="utf-8")
    except Exception:
        pass


def _verify_password(password: str, stored_hash: str) -> bool:
    """Verify password against stored hash (salted HMAC-SHA256 or legacy SHA-256)."""
    salted = _hmac.new(_PASSWORD_SALT.encode("utf-8"), password.encode("utf-8"), hashlib.sha256).hexdigest()
    if _hmac.compare_digest(salted, stored_hash):
        return True
    legacy = hashlib.sha256(password.encode("utf-8")).hexdigest()
    return _hmac.compare_digest(legacy, stored_hash)


UI_FONT = "Segoe UI"
UI_FONT_SMALL = (UI_FONT, 10)
UI_FONT_BODY = (UI_FONT, 12)


class AdminMixin:
    def create_sales_chart(self, parent, title: str, subtitle: str, points):
        """Create a responsive sales line chart similar to a dashboard card."""
        chart_card = ctk.CTkFrame(
            parent,
            fg_color=self.current_theme["button_bg"],
            corner_radius=10,
            border_width=1,
            border_color=self.current_theme.get("card_border", "#d1d1d6"),
        )
        chart_card.pack(fill=tk.BOTH, expand=True, pady=(6, 0))
        chart_inner = ctk.CTkFrame(chart_card, fg_color=self.current_theme.get("card_bg", self.current_theme["button_bg"]))
        chart_inner.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        ctk.CTkLabel(
            chart_inner,
            text=title,
            font=(UI_FONT, 14, "bold"),
            text_color=self.current_theme["fg"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            chart_inner,
            text=subtitle,
            font=UI_FONT_SMALL,
            text_color=self.current_theme.get("muted", self.current_theme["fg"]),
        ).pack(anchor="w", pady=(0, 8))

        canvas = tk.Canvas(
            chart_inner,
            height=180,
            bg=self.current_theme.get("card_bg", "#ffffff"),
            highlightthickness=0,
            bd=0,
        )
        canvas.pack(fill=tk.BOTH, expand=True)

        def draw_chart(_event=None):
            canvas.delete("all")
            width = max(canvas.winfo_width(), 520)
            height = max(canvas.winfo_height(), 220)
            left_pad = 46
            right_pad = 20
            top_pad = 20
            bottom_pad = 52

            plot_w = width - left_pad - right_pad
            plot_h = height - top_pad - bottom_pad
            if plot_w <= 0 or plot_h <= 0 or not points:
                return

            max_value = max((point["value"] for point in points), default=0.0)
            max_value = max(max_value, 1.0)
            y_steps = 5

            grid_color = self.current_theme.get("chart_grid", "#e5e5ea")
            axis_color = self.current_theme.get("muted", "#8e8e93")
            line_color = self.current_theme.get("chart_line", "#22c55e")
            point_fill = self.current_theme.get("accent", "#22c55e")

            for step in range(y_steps + 1):
                y = top_pad + (plot_h * step / y_steps)
                canvas.create_line(left_pad, y, width - right_pad, y, fill=grid_color)
                value = max_value * (1 - step / y_steps)
                canvas.create_text(
                    left_pad - 10,
                    y,
                    text=f"{value:.0f}",
                    fill=axis_color,
                    font=(UI_FONT, 8),
                )

            canvas.create_line(left_pad, top_pad, left_pad, top_pad + plot_h, fill=axis_color)
            canvas.create_line(left_pad, top_pad + plot_h, width - right_pad, top_pad + plot_h, fill=axis_color)

            coords = []
            count = len(points)
            x_step = plot_w / max(count - 1, 1)
            for idx, point in enumerate(points):
                x = left_pad + (idx * x_step if count > 1 else plot_w / 2)
                y = top_pad + plot_h - ((point["value"] / max_value) * plot_h)
                coords.append((x, y, point))

            for idx in range(len(coords) - 1):
                x1, y1, _ = coords[idx]
                x2, y2, _ = coords[idx + 1]
                canvas.create_line(x1, y1, x2, y2, fill=line_color, width=2, smooth=True)

            for x, y, point in coords:
                canvas.create_oval(x - 4, y - 4, x + 4, y + 4, fill=point_fill, outline=point_fill)
                canvas.create_text(
                    x,
                    y - 12,
                    text=f"{point['value']:.0f}",
                    fill=axis_color,
                    font=(UI_FONT, 8, "bold"),
                )
                canvas.create_text(
                    x,
                    top_pad + plot_h + 18,
                    text=point["label"],
                    fill=axis_color,
                    font=(UI_FONT, 8),
                    angle=35,
                )

        canvas.bind("<Configure>", draw_chart)
        draw_chart()
        return chart_card

    def create_bar_chart(
        self,
        parent,
        title: str,
        subtitle: str,
        points,
        color="#5C6BC0",
        left_pad: int = 46,
        right_pad: int = 20,
    ):
        """Create a responsive vertical bar chart card."""
        chart_card = ctk.CTkFrame(
            parent,
            fg_color=self.current_theme["button_bg"],
            corner_radius=10,
            border_width=1,
            border_color=self.current_theme.get("card_border", "#d1d1d6"),
        )
        chart_card.pack(fill=tk.BOTH, expand=True, pady=(6, 0))
        chart_inner = ctk.CTkFrame(chart_card, fg_color=self.current_theme["button_bg"])
        chart_inner.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        ctk.CTkLabel(
            chart_inner,
            text=title,
            font=(UI_FONT, 14, "bold"),
            text_color=self.current_theme["button_fg"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            chart_inner,
            text=subtitle,
            font=UI_FONT_SMALL,
            text_color=self.current_theme["button_fg"],
        ).pack(anchor="w", pady=(0, 8))

        canvas = tk.Canvas(
            chart_inner,
            height=240,
            bg=self.current_theme.get("card_bg", "#ffffff"),
            highlightthickness=0,
            bd=0,
        )
        canvas.pack(fill=tk.BOTH, expand=True)

        def draw_chart(_event=None):
            canvas.delete("all")
            width = max(canvas.winfo_width(), 520)
            height = max(canvas.winfo_height(), 220)
            top_pad = 20
            bottom_pad = 62

            plot_w = width - left_pad - right_pad
            plot_h = height - top_pad - bottom_pad
            if plot_w <= 0 or plot_h <= 0 or not points:
                return

            max_value = max((point["value"] for point in points), default=0.0)
            max_value = max(max_value, 1.0)
            y_steps = 5

            grid_color = self.current_theme.get("chart_grid", "#e5e5ea")
            axis_color = self.current_theme.get("muted", "#8e8e93")

            for step in range(y_steps + 1):
                y = top_pad + (plot_h * step / y_steps)
                canvas.create_line(left_pad, y, width - right_pad, y, fill=grid_color)
                value = max_value * (1 - step / y_steps)
                canvas.create_text(
                    left_pad - 10,
                    y,
                    text=f"{value:.0f}",
                    fill=axis_color,
                    font=(UI_FONT, 8),
                )

            canvas.create_line(left_pad, top_pad, left_pad, top_pad + plot_h, fill=axis_color)
            canvas.create_line(left_pad, top_pad + plot_h, width - right_pad, top_pad + plot_h, fill=axis_color)

            count = len(points)
            slot_w = plot_w / max(count, 1)
            bar_w = min(42, max(20, slot_w * 0.55))

            for idx, point in enumerate(points):
                center_x = left_pad + (slot_w * idx) + (slot_w / 2)
                bar_h = (point["value"] / max_value) * plot_h
                x1 = center_x - (bar_w / 2)
                y1 = top_pad + plot_h - bar_h
                x2 = center_x + (bar_w / 2)
                y2 = top_pad + plot_h
                canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline=color)
                canvas.create_text(
                    center_x,
                    y1 - 10,
                    text=f"{point['value']:.0f}",
                    fill=axis_color,
                    font=(UI_FONT, 8, "bold"),
                )
                canvas.create_text(
                    center_x,
                    top_pad + plot_h + 22,
                    text=point["label"],
                    fill=axis_color,
                    font=(UI_FONT, 8),
                    angle=35,
                )

        canvas.bind("<Configure>", draw_chart)
        draw_chart()
        return chart_card

    def create_low_stock_chart(self, parent, title: str, subtitle: str, points):
        """Create a low-stock comparison chart using current stock vs capacity."""
        chart_card = ctk.CTkFrame(
            parent,
            fg_color=self.current_theme["button_bg"],
            corner_radius=10,
            border_width=1,
            border_color=self.current_theme.get("card_border", "#d1d1d6"),
        )
        chart_card.pack(fill=tk.BOTH, expand=True, pady=(6, 0))
        chart_inner = ctk.CTkFrame(chart_card, fg_color=self.current_theme["button_bg"])
        chart_inner.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        ctk.CTkLabel(
            chart_inner,
            text=title,
            font=(UI_FONT, 14, "bold"),
            text_color=self.current_theme["button_fg"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            chart_inner,
            text=subtitle,
            font=UI_FONT_SMALL,
            text_color=self.current_theme["button_fg"],
        ).pack(anchor="w", pady=(0, 8))

        canvas = tk.Canvas(
            chart_inner,
            height=240,
            bg=self.current_theme.get("card_bg", "#ffffff"),
            highlightthickness=0,
            bd=0,
        )
        canvas.pack(fill=tk.BOTH, expand=True)

        def draw_chart(_event=None):
            canvas.delete("all")
            width = canvas.winfo_width()
            height = canvas.winfo_height()
            if width <= 1 or height <= 1:
                return
            max_label_chars = max((len(str(p.get("label", ""))) for p in points), default=12)
            left_pad = min(240, max(130, int(max_label_chars * 6.2) + 28))
            right_pad = 120
            top_pad = 30
            bottom_pad = 16

            # Keep this chart compact while preserving readable row labels/values.
            visible_rows = max(1, min(len(points), 6))
            target_height = max(150, top_pad + bottom_pad + (visible_rows * 30))
            if abs(canvas.winfo_height() - target_height) > 2:
                canvas.after_idle(lambda h=target_height: canvas.configure(height=h))

            plot_w = width - left_pad - right_pad
            plot_h = height - top_pad - bottom_pad
            if plot_w <= 0 or plot_h <= 0 or not points:
                return

            # Keep a minimum drawable width for bars even when labels are long.
            if plot_w < 170:
                left_pad = max(110, width - right_pad - 170)
                plot_w = width - left_pad - right_pad
                if plot_w <= 0:
                    return

            # Keep bars visually shorter so labels/values are easier to scan.
            bar_scale = 0.50
            usable_plot_w = plot_w * bar_scale

            max_capacity = max((point.get("capacity", point["value"]) for point in points), default=1.0)
            max_capacity = max(max_capacity, 1.0)

            axis_color = "#666666" if self.current_theme_name == "light" else "#d7dde8"
            row_h = max(28, plot_h / max(len(points), 1))
            value_col_x = max(left_pad + usable_plot_w + 10, left_pad + 10)

            canvas.create_text(
                left_pad,
                top_pad - 12,
                text="Stock Level",
                fill=axis_color,
                font=(UI_FONT, 9, "bold"),
                anchor="w",
            )
            canvas.create_text(
                value_col_x,
                top_pad - 12,
                text="Qty",
                fill=axis_color,
                font=(UI_FONT, 9, "bold"),
                anchor="w",
            )

            for idx, point in enumerate(points):
                y = top_pad + (idx * row_h) + (row_h / 2)
                stock_value = float(point.get("value", 0) or 0)
                capacity_value = float(point.get("capacity", stock_value) or stock_value)
                stock_int = int(round(stock_value))
                capacity_int = int(round(capacity_value))
                label_text = str(point.get("label", ""))

                canvas.create_text(
                    left_pad - 8,
                    y,
                    text=label_text,
                    fill=axis_color,
                    font=(UI_FONT, 9),
                    anchor="e",
                )
                capacity_w = (capacity_value / max_capacity) * usable_plot_w
                stock_w = (stock_value / max_capacity) * usable_plot_w
                canvas.create_rectangle(
                    left_pad,
                    y - 8,
                    left_pad + capacity_w,
                    y + 8,
                    fill="#CFD8DC",
                    outline="",
                )
                canvas.create_rectangle(
                    left_pad,
                    y - 8,
                    left_pad + stock_w,
                    y + 8,
                    fill="#EF5350",
                    outline="",
                )
                canvas.create_text(
                    value_col_x,
                    y,
                    text=f"{stock_int} / {capacity_int}",
                    fill=axis_color,
                    font=(UI_FONT, 10, "bold"),
                    anchor="w",
                )

        canvas.bind("<Configure>", draw_chart)
        draw_chart()
        return chart_card

    def enter_admin_dashboard(self):
        """Show in-app Admin Login (mint panel, username + password)."""
        self._current_screen_builder = self.enter_admin_dashboard
        if hasattr(self, "_apply_lcd_fit"):
            try:
                self._apply_lcd_fit(profile="admin_staff")
            except Exception:
                pass
        if self.sidebar_holder is not None and self.sidebar_holder.winfo_exists():
            self.sidebar_holder.destroy()
            self.sidebar_holder = None
        self.clear_screen()
        theme = self.current_theme
        self.content_holder.configure(fg_color=theme["bg"])

        center = ctk.CTkFrame(self.content_holder, fg_color=theme["bg"])
        center.place(relx=0.5, rely=0.5, anchor="center")

        nav_bg = theme.get("nav_bg", "#1c1c1e")
        nav_fg = theme.get("nav_fg", "#ffffff")
        nav_hover = theme.get("nav_hover", "#333333")

        panel = ctk.CTkFrame(center, fg_color=theme["card_bg"], corner_radius=20, border_width=1, border_color=theme["card_border"])
        panel.pack()
        inner = ctk.CTkFrame(panel, fg_color=theme["card_bg"])
        inner.pack(padx=40, pady=28)

        stored_username, stored_hash = self.get_admin_credentials_data()
        if not stored_username or not stored_hash:
            ctk.CTkLabel(
                inner,
                text="Admin credentials are not configured.\nPlease contact the system owner.",
                font=UI_FONT_BODY,
                text_color="#ef4444",
                justify="center",
                wraplength=360,
            ).pack(pady=(8, 0))
            return

        ctk.CTkLabel(
            inner,
            text="Admin Login",
            font=(UI_FONT, 20, "bold"),
            text_color=theme["fg"],
        ).pack(pady=(0, 20))

        ctk.CTkLabel(inner, text="Username:", font=UI_FONT_SMALL, text_color=theme.get("muted", "#8e8e93")).pack(anchor="w", pady=(0, 4))
        un_entry = ctk.CTkEntry(inner, font=UI_FONT_BODY, width=280, fg_color=theme.get("search_bg", "#f2f2f7"), text_color=theme["fg"], border_color=theme.get("search_border", "#d1d1d6"), corner_radius=12, height=42)
        un_entry.pack(pady=(0, 14))
        un_entry.focus_set()

        ctk.CTkLabel(inner, text="Password:", font=UI_FONT_SMALL, text_color=theme.get("muted", "#8e8e93")).pack(anchor="w", pady=(0, 4))
        pw_entry = ctk.CTkEntry(inner, font=UI_FONT_BODY, width=280, fg_color=theme.get("search_bg", "#f2f2f7"), text_color=theme["fg"], border_color=theme.get("search_border", "#d1d1d6"), corner_radius=12, height=42, show="*")
        pw_entry.pack(pady=(0, 14))

        status_lbl = ctk.CTkLabel(
            inner,
            text="",
            font=UI_FONT_SMALL,
            text_color="#ef4444",
        )
        status_lbl.pack(fill=tk.X, pady=(0, 8))

        def submit():
            username = un_entry.get().strip()
            password = pw_entry.get()
            if not username or not password:
                status_lbl.configure(text="Please enter both username and password.")
                return
            if username != stored_username or not _verify_password(password, stored_hash):
                status_lbl.configure(text="Invalid admin credentials.")
                return
            status_lbl.configure(text="")
            self.show_admin_dashboard({"name": username, "rfid_uid": ""})

        btn_frame = ctk.CTkFrame(inner, fg_color=theme["card_bg"])
        btn_frame.pack(fill=tk.X)
        ctk.CTkButton(btn_frame, text="OK", font=(UI_FONT, 12, "bold"), command=submit, fg_color=nav_bg, hover_color=nav_hover, text_color=nav_fg, corner_radius=980, height=40).pack(side=tk.LEFT, padx=(0, 10))
        ctk.CTkButton(btn_frame, text="Cancel", font=(UI_FONT, 12, "bold"), command=self.build_main_menu, fg_color=theme["button_bg"], hover_color=theme.get("card_border", "#d1d1d6"), text_color=theme["button_fg"], corner_radius=980, height=40, border_width=1, border_color=theme.get("card_border", "#d1d1d6")).pack(side=tk.LEFT)

        def on_return(_):
            submit()
        un_entry.bind("<Return>", lambda e: pw_entry.focus())
        pw_entry.bind("<Return>", on_return)
        self.add_theme_toggle_footer()

    def _slide_in(self, frame, steps=12, step_ms=20):
        """Animate frame sliding in from the right (relx 1 -> 0)."""
        start, end = 1.0, 0.0
        step_val = (end - start) / steps
        def step(n=0):
            if n >= steps or not frame.winfo_exists():
                frame.place(relx=end, rely=0, relwidth=1, relheight=1, anchor="nw")
                return
            relx = start + step_val * (n + 1)
            frame.place(relx=relx, rely=0, relwidth=1, relheight=1, anchor="nw")
            frame.after(step_ms, lambda: step(n + 1))
        frame.place(relx=start, rely=0, relwidth=1, relheight=1, anchor="nw")
        frame.after(step_ms, lambda: step(0))

    def show_admin_dashboard(self, staff_user):
        self._current_screen_builder = lambda: self.show_admin_dashboard(staff_user)
        self.clear_screen()
        self._current_admin_user = staff_user

        stats = self.get_admin_overview_stats_data()
        trend_points = self.get_sales_trend_data_points(15)
        monthly_points = self.get_monthly_sales_data_points(6)
        top_products = self.get_top_selling_products_data()
        low_stock_points = self.get_low_stock_chart_data_points(10)

        container = ctk.CTkFrame(self.content_holder, fg_color=self.current_theme["bg"])

        sidebar_bg = self.current_theme.get("search_bg", "#f1f5f9")
        sidebar = ctk.CTkFrame(container, fg_color=sidebar_bg, width=200, corner_radius=0)
        sidebar.pack_propagate(False)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=0, pady=0)

        main = ctk.CTkFrame(container, fg_color=self.current_theme["bg"])
        main.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=16, pady=12)

        ctk.CTkLabel(
            sidebar,
            text="Admin",
            font=(UI_FONT, 16, "bold"),
            text_color=self.current_theme["fg"],
        ).pack(pady=(16, 12), padx=12)

        nav_bg = self.current_theme.get("nav_bg", "#1c1c1e")
        nav_fg = self.current_theme.get("nav_fg", "#ffffff")
        nav_hover = self.current_theme.get("nav_hover", "#333333")

        def nav_btn(text, cmd):
            b = ctk.CTkButton(
                sidebar,
                text=text,
                font=(UI_FONT, 12),
                anchor="w",
                command=cmd,
                fg_color=nav_bg,
                hover_color=nav_hover,
                text_color=nav_fg,
                corner_radius=980,
                height=38,
            )
            b.pack(fill=tk.X, padx=8, pady=3)
            return b

        nav_btn("Overview", lambda: self.show_admin_dashboard(staff_user))
        nav_btn("RFID Roles", self.show_rfid_roles_screen)
        nav_btn("Cash Pulse Settings", self.show_cash_pulse_settings_screen)
        nav_btn("Hardware Diagnostics", self.show_hardware_diagnostics_screen)
        nav_btn("Sales Reports", self.show_sales_reports_screen)
        nav_btn("Generate Excel Report", self.export_sales_report_ui)
        nav_btn("Change Credentials", self.change_admin_credentials_screen)
        nav_btn("Back to Main", self.build_main_menu)

        header = ctk.CTkFrame(main, fg_color=self.current_theme["bg"])
        header.pack(fill=tk.X, pady=(0, 12))

        ctk.CTkLabel(
            header,
            text="Overview",
            font=(UI_FONT, 20, "bold"),
            text_color=self.current_theme["fg"],
        ).pack(side=tk.LEFT)
        ctk.CTkLabel(
            header,
            text=f"Admin: {staff_user['name'] or staff_user['rfid_uid']}",
            font=UI_FONT_SMALL,
            text_color=self.current_theme.get("muted", self.current_theme["fg"]),
        ).pack(side=tk.RIGHT)

        metrics_frame = ctk.CTkFrame(main, fg_color=self.current_theme["bg"])
        metrics_frame.pack(fill=tk.X, pady=(0, 12))

        def metric_card(parent, title, value_text):
            card = ctk.CTkFrame(
                parent,
                fg_color=self.current_theme.get("card_bg", self.current_theme["button_bg"]),
                corner_radius=10,
                border_width=1,
                border_color=self.current_theme.get("card_border", "#e2e8f0"),
            )
            card.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=6)
            ctk.CTkLabel(
                card,
                text=title,
                font=UI_FONT_SMALL,
                text_color=self.current_theme.get("muted", self.current_theme["fg"]),
            ).pack(anchor="w", padx=12, pady=(10, 2))
            ctk.CTkLabel(
                card,
                text=value_text,
                font=(UI_FONT, 18, "bold"),
                text_color=self.current_theme.get("accent", "#10b981"),
            ).pack(anchor="w", padx=12, pady=(0, 12))

        metric_card(metrics_frame, "Total Sales", f"₱{stats['total_sales']:.2f}")
        metric_card(metrics_frame, "Orders", str(stats["orders"]))
        metric_card(metrics_frame, "Active Customers", str(stats["active_customers"]))
        metric_card(metrics_frame, "Low-stock Products", str(stats["low_stock"]))

        body = ctk.CTkScrollableFrame(main, fg_color=self.current_theme["bg"])
        body.pack(fill=tk.BOTH, expand=True, padx=20, pady=(5, 20))

        ctk.CTkLabel(
            body,
            text="Sales trend by created date",
            font=(UI_FONT, 12, "bold"),
            text_color=self.current_theme["fg"],
            justify="left",
        ).pack(anchor="nw", pady=(0, 4))

        self.create_sales_chart(body, "Sales by Created Date", "Last 15 days", trend_points)
        self.create_bar_chart(body, "Monthly Sales", "Last 6 months", monthly_points, color="#42A5F5")
        self.create_bar_chart(
            body,
            "Top-selling Products",
            "All products by quantity sold",
            top_products if top_products else [{"label": "No sales yet", "value": 0}],
            color="#7E57C2",
            left_pad=28,
            right_pad=34,
        )
        self.create_low_stock_chart(body, "Low-stock Products", "Items with fewer than 4 stocks left (current/capacity)", low_stock_points)

        # -----------------------------
        # Prediction Analysis (runtime)
        # -----------------------------
        pred_card = ctk.CTkFrame(
            body,
            fg_color=self.current_theme.get("card_bg", self.current_theme["button_bg"]),
            corner_radius=10,
            border_width=1,
            border_color=self.current_theme.get("card_border", "#e2e8f0"),
        )
        pred_card.pack(anchor="nw", fill=tk.X, pady=(14, 0))
        pred_inner = ctk.CTkFrame(pred_card, fg_color=self.current_theme.get("card_bg", self.current_theme["button_bg"]))
        pred_inner.pack(fill=tk.X, padx=14, pady=12)

        ctk.CTkLabel(
            pred_inner,
            text="Prediction Analysis (Demand + Restock)",
            font=(UI_FONT, 12, "bold"),
            text_color=self.current_theme["fg"],
        ).pack(anchor="w")

        ctk.CTkLabel(
            pred_inner,
            text="Predicts sales tomorrow and recommends restock using historical transactions (runs once per session).",
            font=UI_FONT_SMALL,
            text_color=self.current_theme.get("muted", self.current_theme["fg"]),
            wraplength=520,
            justify="left",
        ).pack(anchor="w", pady=(2, 10))

        btn_row = ctk.CTkFrame(pred_inner, fg_color=self.current_theme.get("card_bg", self.current_theme["button_bg"]))
        btn_row.pack(anchor="w", fill=tk.X)

        def _run_pred():
            self.run_prediction_analysis_once(force=False)
            self.show_admin_dashboard(staff_user)

        ran = bool(getattr(self, "_prediction_ran", False))
        ctk.CTkButton(
            btn_row,
            text="Run Prediction Analysis" if not ran else "Prediction Ready",
            font=(UI_FONT, 11, "bold"),
            command=_run_pred if not ran else None,
            state="normal" if not ran else "disabled",
            fg_color=self.current_theme.get("accent", "#10b981"),
            hover_color=self.current_theme.get("accent_hover", "#059669"),
            text_color="#ffffff",
            corner_radius=8,
            height=38,
        ).pack(side=tk.LEFT)

        # Show results table if available
        results = getattr(self, "_prediction_results", None)
        summary = getattr(self, "_prediction_summary", None)
        card_bg = self.current_theme.get("card_bg", self.current_theme["button_bg"])
        if results:
            info = []
            if summary and getattr(summary, "based_on_last_date", None):
                info.append(f"Based on data up to: {summary.based_on_last_date}")
            if summary and getattr(summary, "generated_at_iso", None):
                info.append(f"Generated: {summary.generated_at_iso}")
            if info:
                ctk.CTkLabel(
                    pred_inner,
                    text="  ·  ".join(info),
                    font=UI_FONT_SMALL,
                    text_color=self.current_theme.get("muted", self.current_theme["fg"]),
                ).pack(anchor="w", pady=(10, 6))

            table = ctk.CTkFrame(pred_inner, fg_color=card_bg)
            table.pack(fill=tk.X, pady=(2, 0))

            headers = ["Product", "Predicted Sales Tomorrow", "Restock Needed"]
            head_row = ctk.CTkFrame(table, fg_color=card_bg)
            head_row.pack(fill=tk.X)
            for h in headers:
                ctk.CTkLabel(
                    head_row,
                    text=h,
                    font=(UI_FONT, 10, "bold"),
                    text_color=self.current_theme["fg"],
                    anchor="w",
                ).pack(side=tk.LEFT, fill=tk.X, expand=True)

            for r in results[:6]:
                row = ctk.CTkFrame(table, fg_color=card_bg)
                row.pack(fill=tk.X, pady=1)
                ctk.CTkLabel(
                    row,
                    text=str(getattr(r, "product_name", "")),
                    font=UI_FONT_SMALL,
                    text_color=self.current_theme["fg"],
                    anchor="w",
                ).pack(side=tk.LEFT, fill=tk.X, expand=True)
                ctk.CTkLabel(
                    row,
                    text=str(getattr(r, "predicted_sales_tomorrow", 0)),
                    font=UI_FONT_SMALL,
                    text_color=self.current_theme["fg"],
                    anchor="w",
                ).pack(side=tk.LEFT, fill=tk.X, expand=True)
                need = "Yes" if getattr(r, "recommended_restock_qty", 0) > 0 else "No"
                ctk.CTkLabel(
                    row,
                    text=need,
                    font=UI_FONT_SMALL,
                    text_color=self.current_theme.get("accent", "#10b981") if need == "Yes" else self.current_theme.get("muted", self.current_theme["fg"]),
                    anchor="w",
                ).pack(side=tk.LEFT, fill=tk.X, expand=True)

        ctk.CTkButton(
            body,
            text="Generate Excel Report",
            font=(UI_FONT, 12, "bold"),
            command=self.export_sales_report_ui,
            fg_color=self.current_theme.get("accent", "#10b981"),
            hover_color=self.current_theme.get("accent_hover", "#059669"),
            text_color="#ffffff",
            corner_radius=8,
            height=42,
        ).pack(anchor="nw", pady=(12, 0))

        self._slide_in(container)
        self.add_theme_toggle_footer()

    def show_sales_reports_screen(self):
        """Show a list of generated sales report Excel files for admin to open."""
        self._current_screen_builder = self.show_sales_reports_screen
        self.clear_screen()

        frame = ctk.CTkFrame(self.content_holder, fg_color=self.current_theme["bg"])
        frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=16)

        ctk.CTkLabel(
            frame,
            text="Sales Reports",
            font=(UI_FONT, 20, "bold"),
            text_color=self.current_theme["fg"],
        ).pack(pady=(0, 12))

        reports = list_sales_reports()
        list_frame = ctk.CTkFrame(frame, fg_color=self.current_theme["bg"])
        list_frame.pack(expand=True, fill=tk.BOTH)

        if not reports:
            ctk.CTkLabel(
                list_frame,
                text="No sales reports found. Generate one first.",
                font=UI_FONT_BODY,
                text_color=self.current_theme.get("muted", self.current_theme["fg"]),
            ).pack(pady=16)
        else:
            for report_path in reports:
                row = ctk.CTkFrame(list_frame, fg_color=self.current_theme["bg"])
                row.pack(fill=tk.X, pady=6)

                ctk.CTkLabel(
                    row,
                    text=report_path.name,
                    anchor="w",
                    font=UI_FONT_BODY,
                    text_color=self.current_theme["fg"],
                ).pack(side=tk.LEFT, expand=True)

                def make_open_cmd(p=report_path):
                    def _cmd():
                        try:
                            open_sales_report(p)
                        except Exception as exc:
                            messagebox.showerror("Open Failed", str(exc))
                    return _cmd

                ctk.CTkButton(
                    row,
                    text="Open",
                    font=UI_FONT_BODY,
                    command=make_open_cmd(),
                    fg_color=self.current_theme.get("accent", "#10b981"),
                    hover_color=self.current_theme.get("accent_hover", "#059669"),
                    text_color="#ffffff",
                    corner_radius=8,
                    width=80,
                ).pack(side=tk.RIGHT, padx=8)

        ctk.CTkButton(
            frame,
            text="Back to Admin Dashboard",
            font=UI_FONT_BODY,
            command=lambda: self.show_admin_dashboard(getattr(self, "_current_admin_user", {"name": "admin", "rfid_uid": ""})),
            fg_color=self.current_theme["button_bg"],
            hover_color=self.current_theme.get("accent", "#10b981"),
            text_color=self.current_theme["button_fg"],
            corner_radius=8,
            height=38,
        ).pack(pady=12)

        self.add_theme_toggle_footer()

    def show_rfid_roles_screen(self):
        """Manage RFID user roles for door access control."""
        self._current_screen_builder = self.show_rfid_roles_screen
        self.clear_screen()

        frame = ctk.CTkFrame(self.content_holder, fg_color=self.current_theme["bg"])
        frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=16)

        ctk.CTkLabel(
            frame,
            text="RFID Role Management",
            font=(UI_FONT, 20, "bold"),
            text_color=self.current_theme["fg"],
        ).pack(pady=(0, 6))

        ctk.CTkLabel(
            frame,
            text="Roles: customer, restocker, researcher, troubleshooter, admin",
            font=UI_FONT_SMALL,
            text_color=self.current_theme.get("muted", self.current_theme["fg"]),
        ).pack(pady=(0, 10))

        table = ctk.CTkScrollableFrame(frame, fg_color=self.current_theme["bg"])
        table.pack(expand=True, fill=tk.BOTH)

        users = self.get_all_rfid_users_data()
        role_values = ["customer", "restocker", "researcher", "troubleshooter", "admin"]

        for user in users:
            row = ctk.CTkFrame(
                table,
                fg_color=self.current_theme.get("card_bg", self.current_theme["button_bg"]),
                border_width=1,
                border_color=self.current_theme.get("card_border", "#e2e8f0"),
                corner_radius=8,
            )
            row.pack(fill=tk.X, pady=6)

            name_text = user["name"] or "(no name)"
            ctk.CTkLabel(
                row,
                text=f"UID: {user['rfid_uid']}  |  {name_text}  |  Bal: ₱{float(user['balance']):.2f}",
                font=UI_FONT_BODY,
                text_color=self.current_theme["button_fg"],
                anchor="w",
            ).pack(side=tk.LEFT, padx=10, pady=10, expand=True, fill=tk.X)

            role_var = tk.StringVar(value=(user["role"] or "customer"))
            picker = ctk.CTkOptionMenu(
                row,
                variable=role_var,
                values=role_values,
                width=150,
                fg_color=self.current_theme.get("accent", "#10b981"),
                button_color=self.current_theme.get("accent_hover", "#059669"),
                button_hover_color=self.current_theme.get("accent_hover", "#059669"),
                text_color="#ffffff",
            )
            picker.pack(side=tk.LEFT, padx=(0, 8), pady=8)

            def make_save(uid=user["id"], rvar=role_var):
                def _save():
                    try:
                        self.update_rfid_user_role_data(uid, rvar.get())
                        messagebox.showinfo("Saved", "RFID role updated successfully.")
                    except Exception as exc:
                        messagebox.showerror("Error", str(exc))
                return _save

            ctk.CTkButton(
                row,
                text="Save",
                font=(UI_FONT, 11, "bold"),
                command=make_save(),
                fg_color=self.current_theme.get("accent", "#10b981"),
                hover_color=self.current_theme.get("accent_hover", "#059669"),
                text_color="#ffffff",
                corner_radius=8,
                width=72,
            ).pack(side=tk.LEFT, padx=(0, 10), pady=8)

        ctk.CTkButton(
            frame,
            text="Back to Admin Dashboard",
            font=UI_FONT_BODY,
            command=lambda: self.show_admin_dashboard(getattr(self, "_current_admin_user", {"name": "admin", "rfid_uid": ""})),
            fg_color=self.current_theme["button_bg"],
            hover_color=self.current_theme.get("accent", "#10b981"),
            text_color=self.current_theme["button_fg"],
            corner_radius=8,
            height=38,
        ).pack(pady=12)

        self.add_theme_toggle_footer()

    def show_cash_pulse_settings_screen(self):
        """Configure bill/coin acceptor pulse-to-value mappings."""
        self._current_screen_builder = self.show_cash_pulse_settings_screen
        self.clear_screen()

        frame = ctk.CTkFrame(self.content_holder, fg_color=self.current_theme["bg"])
        frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=16)

        ctk.CTkLabel(
            frame,
            text="Cash Pulse Settings",
            font=(UI_FONT, 20, "bold"),
            text_color=self.current_theme["fg"],
        ).pack(pady=(0, 8))

        ctk.CTkLabel(
            frame,
            text="Set how much peso value each input pulse represents.",
            font=UI_FONT_SMALL,
            text_color=self.current_theme.get("muted", self.current_theme["fg"]),
        ).pack(pady=(0, 12))

        card = ctk.CTkFrame(
            frame,
            fg_color=self.current_theme.get("card_bg", self.current_theme["button_bg"]),
            border_width=1,
            border_color=self.current_theme.get("card_border", "#e2e8f0"),
            corner_radius=10,
        )
        card.pack(fill=tk.X, padx=8, pady=6)

        inner = ctk.CTkFrame(card, fg_color=self.current_theme.get("card_bg", self.current_theme["button_bg"]))
        inner.pack(fill=tk.X, padx=14, pady=14)

        coin_var = tk.StringVar(value=str(getattr(self, "coin_pulse_value", 1.0)))
        bill_var = tk.StringVar(value=str(getattr(self, "bill_pulse_value", 20.0)))

        ctk.CTkLabel(inner, text="Coin acceptor pulse value (PHP):", font=UI_FONT_BODY, text_color=self.current_theme["fg"]).pack(anchor="w")
        coin_entry = ctk.CTkEntry(inner, textvariable=coin_var, width=220)
        coin_entry.pack(anchor="w", pady=(4, 10))

        ctk.CTkLabel(inner, text="Bill acceptor pulse value (PHP):", font=UI_FONT_BODY, text_color=self.current_theme["fg"]).pack(anchor="w")
        bill_entry = ctk.CTkEntry(inner, textvariable=bill_var, width=220)
        bill_entry.pack(anchor="w", pady=(4, 10))

        status_lbl = ctk.CTkLabel(inner, text="", font=UI_FONT_SMALL, text_color="#b91c1c")
        status_lbl.pack(anchor="w", pady=(0, 8))

        def save_values():
            try:
                coin_val = float((coin_var.get() or "").strip())
                bill_val = float((bill_var.get() or "").strip())
                if coin_val <= 0 or bill_val <= 0:
                    raise ValueError("Values must be positive numbers.")

                self.coin_pulse_value = coin_val
                self.bill_pulse_value = bill_val
                self.set_hardware_setting_data("coin_pulse_value", str(coin_val))
                self.set_hardware_setting_data("bill_pulse_value", str(bill_val))
                status_lbl.configure(text="Saved.", text_color="#065f46")
            except Exception as exc:
                status_lbl.configure(text=f"Invalid values: {exc}", text_color="#b91c1c")

        ctk.CTkButton(
            inner,
            text="Save Settings",
            font=(UI_FONT, 11, "bold"),
            command=save_values,
            fg_color=self.current_theme.get("accent", "#10b981"),
            hover_color=self.current_theme.get("accent_hover", "#059669"),
            text_color="#ffffff",
            corner_radius=8,
            width=150,
        ).pack(anchor="w")

        ctk.CTkButton(
            frame,
            text="Back to Admin Dashboard",
            font=UI_FONT_BODY,
            command=lambda: self.show_admin_dashboard(getattr(self, "_current_admin_user", {"name": "admin", "rfid_uid": ""})),
            fg_color=self.current_theme["button_bg"],
            hover_color=self.current_theme.get("accent", "#10b981"),
            text_color=self.current_theme["button_fg"],
            corner_radius=8,
            height=38,
        ).pack(pady=12)

        self.add_theme_toggle_footer()

    def show_hardware_diagnostics_screen(self):
        """Show real-time pulse counters and quick RFID read diagnostics."""
        self._current_screen_builder = self.show_hardware_diagnostics_screen
        self.clear_screen()

        frame = ctk.CTkFrame(self.content_holder, fg_color=self.current_theme["bg"])
        frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=16)

        ctk.CTkLabel(
            frame,
            text="Hardware Diagnostics",
            font=(UI_FONT, 20, "bold"),
            text_color=self.current_theme["fg"],
        ).pack(pady=(0, 8))

        card = ctk.CTkFrame(
            frame,
            fg_color=self.current_theme.get("card_bg", self.current_theme["button_bg"]),
            border_width=1,
            border_color=self.current_theme.get("card_border", "#e2e8f0"),
            corner_radius=10,
        )
        card.pack(fill=tk.X, padx=8, pady=6)

        coin_lbl = ctk.CTkLabel(card, text="Coin pulses: 0", font=UI_FONT_BODY, text_color=self.current_theme["fg"])
        coin_lbl.pack(anchor="w", padx=14, pady=(12, 4))

        bill_lbl = ctk.CTkLabel(card, text="Bill pulses: 0", font=UI_FONT_BODY, text_color=self.current_theme["fg"])
        bill_lbl.pack(anchor="w", padx=14, pady=4)

        uid_lbl = ctk.CTkLabel(card, text="Last RFID UID: (none)", font=UI_FONT_BODY, text_color=self.current_theme["fg"])
        uid_lbl.pack(anchor="w", padx=14, pady=4)

        result_lbl = ctk.CTkLabel(card, text="", font=UI_FONT_SMALL, text_color=self.current_theme.get("muted", self.current_theme["fg"]))
        result_lbl.pack(anchor="w", padx=14, pady=(0, 8))

        btn_row = ctk.CTkFrame(card, fg_color=self.current_theme.get("card_bg", self.current_theme["button_bg"]))
        btn_row.pack(fill=tk.X, padx=14, pady=(0, 12))

        def tap_payment():
            uid = self.read_rfid_uid("payment")
            if uid:
                uid_lbl.configure(text=f"Last RFID UID: {uid}")
                result_lbl.configure(text="Payment reader tap detected.")
            else:
                result_lbl.configure(text="No payment RFID tap detected.")

        def tap_door():
            uid = self.read_rfid_uid("door")
            if uid:
                uid_lbl.configure(text=f"Last RFID UID: {uid}")
                result_lbl.configure(text="Door reader tap detected.")
            else:
                result_lbl.configure(text="No door RFID tap detected.")

        ctk.CTkButton(
            btn_row,
            text="Read Payment RFID",
            command=tap_payment,
            fg_color=self.current_theme.get("accent", "#10b981"),
            hover_color=self.current_theme.get("accent_hover", "#059669"),
            text_color="#ffffff",
            corner_radius=8,
            width=150,
        ).pack(side=tk.LEFT, padx=(0, 8))

        ctk.CTkButton(
            btn_row,
            text="Read Door RFID",
            command=tap_door,
            fg_color=self.current_theme.get("accent", "#10b981"),
            hover_color=self.current_theme.get("accent_hover", "#059669"),
            text_color="#ffffff",
            corner_radius=8,
            width=150,
        ).pack(side=tk.LEFT)

        def refresh_counts():
            if not frame.winfo_exists():
                return
            counts = self.get_payment_pulse_counts_data()
            coin_lbl.configure(text=f"Coin pulses: {counts['coin_acceptor']}")
            bill_lbl.configure(text=f"Bill pulses: {counts['bill_acceptor']}")
            frame.after(500, refresh_counts)

        refresh_counts()

        ctk.CTkButton(
            frame,
            text="Back to Admin Dashboard",
            font=UI_FONT_BODY,
            command=lambda: self.show_admin_dashboard(getattr(self, "_current_admin_user", {"name": "admin", "rfid_uid": ""})),
            fg_color=self.current_theme["button_bg"],
            hover_color=self.current_theme.get("accent", "#10b981"),
            text_color=self.current_theme["button_fg"],
            corner_radius=8,
            height=38,
        ).pack(pady=12)

        self.add_theme_toggle_footer()

    def change_admin_credentials_screen(self):
        """Allow the logged-in admin to change username and password (in-app, no pop-ups)."""
        self._current_screen_builder = self.change_admin_credentials_screen
        self.clear_screen()

        user = getattr(self, "_current_admin_user", {"name": "admin", "rfid_uid": ""})
        theme = self.current_theme
        nav_bg = theme.get("nav_bg", "#1c1c1e")
        nav_fg = theme.get("nav_fg", "#ffffff")
        nav_hover = theme.get("nav_hover", "#333333")

        container = ctk.CTkFrame(self.content_holder, fg_color=theme["bg"])
        container.pack(fill=tk.BOTH, expand=True)

        card = ctk.CTkFrame(
            container,
            fg_color=theme["card_bg"],
            corner_radius=20,
            border_width=1,
            border_color=theme["card_border"],
        )
        card.place(relx=0.5, rely=0.45, anchor="center")
        card_inner = ctk.CTkFrame(card, fg_color=theme["card_bg"])
        card_inner.pack(padx=22, pady=18)

        ctk.CTkLabel(
            card_inner,
            text="Change Credentials",
            font=(UI_FONT, 20, "bold"),
            text_color=theme["fg"],
        ).pack(pady=(0, 6))
        ctk.CTkLabel(
            card_inner,
            text=f"Admin: {user.get('name') or user.get('rfid_uid') or 'admin'}",
            font=UI_FONT_SMALL,
            text_color=theme.get("muted", "#8e8e93"),
        ).pack(pady=(0, 14))

        ctk.CTkLabel(card_inner, text="New username", font=UI_FONT_SMALL, text_color=theme.get("muted", "#8e8e93")).pack(anchor="w", pady=(0, 4))
        username_entry = ctk.CTkEntry(card_inner, font=UI_FONT_BODY, width=280, fg_color=theme.get("search_bg", "#f2f2f7"), text_color=theme["fg"], border_color=theme.get("search_border", "#d1d1d6"), corner_radius=12, height=42)
        username_entry.pack(fill=tk.X, pady=(0, 10))

        ctk.CTkLabel(card_inner, text="New password", font=UI_FONT_SMALL, text_color=theme.get("muted", "#8e8e93")).pack(anchor="w", pady=(0, 4))
        pw_entry = ctk.CTkEntry(card_inner, show="*", font=UI_FONT_BODY, width=280, fg_color=theme.get("search_bg", "#f2f2f7"), text_color=theme["fg"], border_color=theme.get("search_border", "#d1d1d6"), corner_radius=12, height=42)
        pw_entry.pack(fill=tk.X, pady=(0, 10))

        ctk.CTkLabel(card_inner, text="Confirm password", font=UI_FONT_SMALL, text_color=theme.get("muted", "#8e8e93")).pack(anchor="w", pady=(0, 4))
        confirm_entry = ctk.CTkEntry(card_inner, show="*", font=UI_FONT_BODY, width=280, fg_color=theme.get("search_bg", "#f2f2f7"), text_color=theme["fg"], border_color=theme.get("search_border", "#d1d1d6"), corner_radius=12, height=42)
        confirm_entry.pack(fill=tk.X, pady=(0, 12))

        status_lbl = ctk.CTkLabel(card_inner, text="", font=UI_FONT_SMALL, text_color="#ef4444")
        status_lbl.pack(pady=(0, 10))

        def save():
            new_username = (username_entry.get() or "").strip()
            new_password = pw_entry.get() or ""
            confirm_password = confirm_entry.get() or ""

            if not new_username:
                status_lbl.configure(text="Please enter a username.")
                return
            if len(new_password) < 4:
                status_lbl.configure(text="Password must be at least 4 characters.")
                return
            if new_password != confirm_password:
                status_lbl.configure(text="Passwords do not match.")
                return

            try:
                self.update_admin_credentials_data(new_username, new_password)
                self.show_success_screen(
                    "Success",
                    "Admin username and password have been updated.",
                    on_ok=lambda: self.show_admin_dashboard(getattr(self, "_current_admin_user", {"name": new_username, "rfid_uid": ""})),
                )
            except Exception as exc:
                status_lbl.configure(text=f"Failed to update credentials: {exc}")

        btn_row = ctk.CTkFrame(card_inner, fg_color=theme["card_bg"])
        btn_row.pack(fill=tk.X, pady=(4, 0))

        ctk.CTkButton(
            btn_row,
            text="Save",
            font=(UI_FONT, 12, "bold"),
            command=save,
            fg_color=nav_bg,
            hover_color=nav_hover,
            text_color=nav_fg,
            corner_radius=980,
            height=40,
        ).pack(side=tk.LEFT)

        ctk.CTkButton(
            btn_row,
            text="Back",
            font=(UI_FONT, 12, "bold"),
            command=lambda: self.show_admin_dashboard(getattr(self, "_current_admin_user", {"name": "admin", "rfid_uid": ""})),
            fg_color=theme["button_bg"],
            hover_color=theme.get("card_border", "#d1d1d6"),
            text_color=theme["button_fg"],
            corner_radius=980,
            height=40,
            border_width=1,
            border_color=theme.get("card_border", "#d1d1d6"),
        ).pack(side=tk.LEFT, padx=(10, 0))

        username_entry.focus_set()
        container.after(10, lambda: self._slide_in(container) if hasattr(self, "_slide_in") else None)
        self.add_theme_toggle_footer()
