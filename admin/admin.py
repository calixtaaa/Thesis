import hashlib
import tkinter as tk
from tkinter import messagebox, simpledialog

from admin.reports import list_sales_reports, open_sales_report


UI_FONT = "Segoe UI"
UI_FONT_SMALL = (UI_FONT, 10)


class AdminMixin:
    def create_sales_chart(self, parent, title: str, subtitle: str, points):
        """Create a responsive sales line chart similar to a dashboard card."""
        chart_card = tk.Frame(
            parent,
            bg=self.current_theme["button_bg"],
            bd=1,
            relief="solid",
            padx=12,
            pady=12,
        )
        chart_card.pack(fill=tk.BOTH, expand=True, pady=(6, 0))

        tk.Label(
            chart_card,
            text=title,
            font=(UI_FONT, 14, "bold"),
            bg=self.current_theme["button_bg"],
            fg=self.current_theme["button_fg"],
        ).pack(anchor="w")
        tk.Label(
            chart_card,
            text=subtitle,
            font=UI_FONT_SMALL,
            bg=self.current_theme["button_bg"],
            fg=self.current_theme["button_fg"],
        ).pack(anchor="w", pady=(0, 8))

        canvas = tk.Canvas(
            chart_card,
            height=240,
            bg="#ffffff" if self.current_theme_name == "light" else "#253041",
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

            grid_color = "#d9d9d9" if self.current_theme_name == "light" else "#4b5a73"
            axis_color = "#666666" if self.current_theme_name == "light" else "#d7dde8"
            line_color = "#c2185b"
            point_fill = "#d81b60"

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

    def create_bar_chart(self, parent, title: str, subtitle: str, points, color="#5C6BC0"):
        """Create a responsive vertical bar chart card."""
        chart_card = tk.Frame(
            parent,
            bg=self.current_theme["button_bg"],
            bd=1,
            relief="solid",
            padx=12,
            pady=12,
        )
        chart_card.pack(fill=tk.BOTH, expand=True, pady=(6, 0))

        tk.Label(
            chart_card,
            text=title,
            font=(UI_FONT, 14, "bold"),
            bg=self.current_theme["button_bg"],
            fg=self.current_theme["button_fg"],
        ).pack(anchor="w")
        tk.Label(
            chart_card,
            text=subtitle,
            font=UI_FONT_SMALL,
            bg=self.current_theme["button_bg"],
            fg=self.current_theme["button_fg"],
        ).pack(anchor="w", pady=(0, 8))

        canvas = tk.Canvas(
            chart_card,
            height=240,
            bg="#ffffff" if self.current_theme_name == "light" else "#253041",
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
            bottom_pad = 62

            plot_w = width - left_pad - right_pad
            plot_h = height - top_pad - bottom_pad
            if plot_w <= 0 or plot_h <= 0 or not points:
                return

            max_value = max((point["value"] for point in points), default=0.0)
            max_value = max(max_value, 1.0)
            y_steps = 5

            grid_color = "#d9d9d9" if self.current_theme_name == "light" else "#4b5a73"
            axis_color = "#666666" if self.current_theme_name == "light" else "#d7dde8"

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
        chart_card = tk.Frame(
            parent,
            bg=self.current_theme["button_bg"],
            bd=1,
            relief="solid",
            padx=12,
            pady=12,
        )
        chart_card.pack(fill=tk.BOTH, expand=True, pady=(6, 0))

        tk.Label(
            chart_card,
            text=title,
            font=(UI_FONT, 14, "bold"),
            bg=self.current_theme["button_bg"],
            fg=self.current_theme["button_fg"],
        ).pack(anchor="w")
        tk.Label(
            chart_card,
            text=subtitle,
            font=UI_FONT_SMALL,
            bg=self.current_theme["button_bg"],
            fg=self.current_theme["button_fg"],
        ).pack(anchor="w", pady=(0, 8))

        canvas = tk.Canvas(
            chart_card,
            height=240,
            bg="#ffffff" if self.current_theme_name == "light" else "#253041",
            highlightthickness=0,
            bd=0,
        )
        canvas.pack(fill=tk.BOTH, expand=True)

        def draw_chart(_event=None):
            canvas.delete("all")
            width = max(canvas.winfo_width(), 520)
            height = max(canvas.winfo_height(), 220)
            left_pad = 110
            right_pad = 20
            top_pad = 20
            bottom_pad = 20

            plot_w = width - left_pad - right_pad
            plot_h = height - top_pad - bottom_pad
            if plot_w <= 0 or plot_h <= 0 or not points:
                return

            max_capacity = max((point.get("capacity", point["value"]) for point in points), default=1.0)
            max_capacity = max(max_capacity, 1.0)

            axis_color = "#666666" if self.current_theme_name == "light" else "#d7dde8"
            grid_color = "#d9d9d9" if self.current_theme_name == "light" else "#4b5a73"
            row_h = plot_h / max(len(points), 1)

            for idx, point in enumerate(points):
                y = top_pad + (idx * row_h) + (row_h / 2)
                canvas.create_text(
                    left_pad - 8,
                    y,
                    text=point["label"],
                    fill=axis_color,
                    font=(UI_FONT, 8),
                    anchor="e",
                )
                canvas.create_line(left_pad, y + 12, width - right_pad, y + 12, fill=grid_color)
                capacity_w = (point.get("capacity", point["value"]) / max_capacity) * plot_w
                stock_w = (point["value"] / max_capacity) * plot_w
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
                    left_pad + capacity_w + 8,
                    y,
                    text=f"{int(point['value'])}/{int(point.get('capacity', point['value']))}",
                    fill=axis_color,
                    font=(UI_FONT, 8, "bold"),
                    anchor="w",
                )

        canvas.bind("<Configure>", draw_chart)
        draw_chart()
        return chart_card

    def enter_admin_dashboard(self):
        """Authenticate admin using username/password, then show dashboard."""
        stored_username, stored_hash = self.get_admin_credentials_data()
        if not stored_username or not stored_hash:
            messagebox.showerror("Error", "Admin credentials not configured.")
            return

        username = simpledialog.askstring(
            "Admin Login",
            "Enter admin username:",
            parent=self,
        )
        if username is None:
            return

        password = simpledialog.askstring(
            "Admin Login",
            "Enter admin password:",
            parent=self,
            show="*",
        )
        if password is None:
            return

        pwd_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
        if username != stored_username or pwd_hash != stored_hash:
            messagebox.showerror("Access Denied", "Invalid admin credentials.")
            return

        admin_user = {"name": username, "rfid_uid": ""}
        self.show_admin_dashboard(admin_user)

    def show_admin_dashboard(self, staff_user):
        self.clear_screen()

        stats = self.get_admin_overview_stats_data()
        trend_points = self.get_sales_trend_data_points(15)
        monthly_points = self.get_monthly_sales_data_points(6)
        top_products = self.get_top_selling_products_data(5)
        low_stock_points = self.get_low_stock_chart_data_points(5)

        container = tk.Frame(self, bg=self.current_theme["bg"])
        container.pack(fill=tk.BOTH, expand=True)

        sidebar = tk.Frame(container, bg=self.current_theme["bg"], width=180)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)

        main = tk.Frame(container, bg=self.current_theme["bg"])
        main.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        tk.Label(
            sidebar,
            text="Admin",
            font=("Arial", 16, "bold"),
            bg=self.current_theme["bg"],
            fg=self.current_theme["fg"],
        ).pack(pady=(15, 10))

        tk.Button(sidebar, text="Overview", font=("Arial", 12), anchor="w", width=18,
                  command=lambda: self.show_admin_dashboard(staff_user)).pack(pady=2, padx=10)
        tk.Button(sidebar, text="Sales Reports", font=("Arial", 12), anchor="w", width=18,
                  command=self.show_sales_reports_screen).pack(pady=2, padx=10)
        tk.Button(sidebar, text="Generate Excel Report", font=("Arial", 12), anchor="w", width=18,
                  command=self.export_sales_report_ui).pack(pady=2, padx=10)
        tk.Button(sidebar, text="Change Credentials", font=("Arial", 12), anchor="w", width=18,
                  command=self.change_admin_credentials_screen).pack(pady=2, padx=10)
        tk.Button(sidebar, text="Back to Main", font=("Arial", 12), anchor="w", width=18,
                  command=self.build_main_menu).pack(pady=(20, 0), padx=10)

        header = tk.Frame(main, bg=self.current_theme["bg"])
        header.pack(fill=tk.X, pady=10, padx=20)

        tk.Label(
            header,
            text="Overview",
            font=("Arial", 18, "bold"),
            bg=self.current_theme["bg"],
            fg=self.current_theme["fg"],
        ).pack(side=tk.LEFT)
        tk.Label(
            header,
            text=f"Admin: {staff_user['name'] or staff_user['rfid_uid']}",
            font=("Arial", 10),
            bg=self.current_theme["bg"],
            fg=self.current_theme["fg"],
        ).pack(side=tk.RIGHT)

        metrics_frame = tk.Frame(main, bg=self.current_theme["bg"])
        metrics_frame.pack(fill=tk.X, padx=20, pady=10)

        def metric_card(parent, title, value_text):
            card = tk.Frame(parent, bg=self.current_theme["button_bg"], bd=1, relief="solid")
            card.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
            tk.Label(card, text=title, font=("Arial", 10),
                     bg=self.current_theme["button_bg"], fg=self.current_theme["button_fg"]).pack(anchor="w", padx=8, pady=(6, 0))
            tk.Label(card, text=value_text, font=("Arial", 16, "bold"),
                     bg=self.current_theme["button_bg"], fg=self.current_theme["button_fg"]).pack(anchor="w", padx=8, pady=(0, 8))

        metric_card(metrics_frame, "Total Sales", f"₱{stats['total_sales']:.2f}")
        metric_card(metrics_frame, "Orders", str(stats["orders"]))
        metric_card(metrics_frame, "Active Customers", str(stats["active_customers"]))
        metric_card(metrics_frame, "Low-stock Products", str(stats["low_stock"]))

        body_container = tk.Frame(main, bg=self.current_theme["bg"])
        body_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=(5, 20))

        body_canvas = tk.Canvas(body_container, bg=self.current_theme["bg"], highlightthickness=0)
        body_scrollbar = tk.Scrollbar(body_container, orient="vertical", command=body_canvas.yview)
        body_canvas.configure(yscrollcommand=body_scrollbar.set)
        body_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        body_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        body = tk.Frame(body_canvas, bg=self.current_theme["bg"])
        body_canvas.create_window((0, 0), window=body, anchor="nw")

        def _resize_admin_body(_event):
            body_canvas.configure(scrollregion=body_canvas.bbox("all"))

        body.bind("<Configure>", _resize_admin_body)

        tk.Label(
            body,
            text="Sales trend by created date",
            font=(UI_FONT, 12, "bold"),
            bg=self.current_theme["bg"],
            fg=self.current_theme["fg"],
            justify="left",
        ).pack(anchor="nw", pady=(0, 4))

        self.create_sales_chart(body, "Sales by Created Date", "Last 15 days", trend_points)
        self.create_bar_chart(body, "Monthly Sales", "Last 6 months", monthly_points, color="#42A5F5")
        self.create_bar_chart(
            body,
            "Top-selling Products",
            "By quantity sold",
            top_products if top_products else [{"label": "No sales yet", "value": 0}],
            color="#7E57C2",
        )
        self.create_low_stock_chart(body, "Low-stock Products", "Current stock vs capacity", low_stock_points)

        tk.Button(
            body,
            text="Generate Excel Report",
            font=("Arial", 12, "bold"),
            command=self.export_sales_report_ui,
            bg="#4CAF50",
            fg=self.current_theme["button_fg"],
            padx=18,
            pady=10,
        ).pack(anchor="nw", pady=(12, 0))

        self.apply_theme_to_widget(self)

    def show_sales_reports_screen(self):
        """Show a list of generated sales report Excel files for admin to open."""
        self.clear_screen()

        tk.Label(self, text="Sales Reports", font=("Arial", 18)).pack(pady=10)

        reports = list_sales_reports()
        list_frame = tk.Frame(self, bg=self.current_theme["bg"])
        list_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=10)

        if not reports:
            tk.Label(
                list_frame,
                text="No sales reports found. Generate one first.",
                font=("Arial", 12),
            ).pack(pady=10)
        else:
            for report_path in reports:
                row = tk.Frame(list_frame, bg=self.current_theme["bg"])
                row.pack(fill=tk.X, pady=5)

                tk.Label(row, text=report_path.name, anchor="w").pack(side=tk.LEFT, expand=True)

                def make_open_cmd(p=report_path):
                    def _cmd():
                        try:
                            open_sales_report(p)
                        except Exception as exc:
                            messagebox.showerror("Open Failed", str(exc))
                    return _cmd

                tk.Button(row, text="Open", command=make_open_cmd()).pack(side=tk.RIGHT, padx=5)

        tk.Button(
            self,
            text="Back to Admin Dashboard",
            font=("Arial", 12),
            command=self.enter_admin_dashboard,
        ).pack(pady=10)

        self.add_theme_toggle_footer()

    def change_admin_credentials_screen(self):
        """Allow the logged-in admin to change username and password."""
        new_username = simpledialog.askstring(
            "Change Admin Username",
            "Enter new admin username:",
            parent=self,
        )
        if not new_username:
            return

        new_password = simpledialog.askstring(
            "Change Admin Password",
            "Enter new admin password:",
            parent=self,
            show="*",
        )
        if not new_password:
            return

        confirm_password = simpledialog.askstring(
            "Confirm Admin Password",
            "Re-enter new admin password:",
            parent=self,
            show="*",
        )
        if new_password != confirm_password:
            messagebox.showerror("Error", "Passwords do not match.")
            return

        try:
            self.update_admin_credentials_data(new_username, new_password)
            messagebox.showinfo("Success", "Admin username and password have been updated.")
        except Exception as exc:
            messagebox.showerror("Error", f"Failed to update admin credentials: {exc}")
