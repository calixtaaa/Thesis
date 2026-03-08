import hashlib
import tkinter as tk
from tkinter import messagebox, simpledialog

from admin.reports import list_sales_reports, open_sales_report


UI_FONT = "Segoe UI"
UI_FONT_SMALL = (UI_FONT, 10)
UI_FONT_BODY = (UI_FONT, 12)


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
        """Show in-app Admin Login (mint panel, username + password)."""
        if hasattr(self, "_apply_lcd_fit"):
            try:
                self._apply_lcd_fit(profile="admin_staff")
            except Exception:
                pass
        if self.sidebar_holder is not None and self.sidebar_holder.winfo_exists():
            self.sidebar_holder.destroy()
            self.sidebar_holder = None
        self.clear_screen()
        page_bg = "#1e293b"
        self.content_holder.configure(bg=page_bg)

        center = tk.Frame(self.content_holder, bg=page_bg)
        center.place(relx=0.5, rely=0.5, anchor="center")

        panel_bg = "#99f6e4"
        btn_bg = "#0d9488"
        btn_hover = "#2dd4bf"
        panel = tk.Frame(center, bg=panel_bg, padx=40, pady=28)
        panel.pack()

        stored_username, stored_hash = self.get_admin_credentials_data()
        if not stored_username or not stored_hash:
            tk.Label(
                panel,
                text="Admin credentials are not configured.\nPlease contact the system owner.",
                font=UI_FONT_BODY,
                bg=panel_bg,
                fg="#b91c1c",
                justify="center",
                wraplength=360,
            ).pack(pady=(8, 0))
            return

        def hover_btn(w, n, h):
            w.bind("<Enter>", lambda _: w.configure(bg=h) if w.winfo_exists() else None)
            w.bind("<Leave>", lambda _: w.configure(bg=n) if w.winfo_exists() else None)

        tk.Label(
            panel,
            text="Admin Login",
            font=(UI_FONT, 18, "bold"),
            bg=panel_bg,
            fg="#0f766e",
        ).pack(pady=(0, 20))

        tk.Label(panel, text="Username:", font=UI_FONT_SMALL, bg=panel_bg, fg="#134e4a").pack(anchor="w", pady=(0, 4))
        username_var = tk.StringVar()
        un_entry = tk.Entry(panel, textvariable=username_var, font=UI_FONT_BODY, width=26, relief=tk.FLAT, bg="#ffffff", fg="#1e293b")
        un_entry.pack(pady=(0, 14), ipady=8, ipadx=10)
        un_entry.focus_set()

        tk.Label(panel, text="Password:", font=UI_FONT_SMALL, bg=panel_bg, fg="#134e4a").pack(anchor="w", pady=(0, 4))
        password_var = tk.StringVar()
        pw_entry = tk.Entry(panel, textvariable=password_var, font=UI_FONT_BODY, width=26, relief=tk.FLAT, bg="#ffffff", fg="#1e293b", show="*")
        pw_entry.pack(pady=(0, 14), ipady=8, ipadx=10)

        status_var = tk.StringVar(value="")
        status_lbl = tk.Label(
            panel,
            textvariable=status_var,
            font=UI_FONT_SMALL,
            bg=panel_bg,
            fg="#b91c1c",
        )
        status_lbl.pack(fill=tk.X, pady=(0, 8))

        def submit():
            username = username_var.get().strip()
            password = password_var.get()
            if not username or not password:
                status_var.set("Please enter both username and password.")
                return
            pwd_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
            if username != stored_username or pwd_hash != stored_hash:
                status_var.set("Invalid admin credentials.")
                return
            status_var.set("")
            self.show_admin_dashboard({"name": username, "rfid_uid": ""})

        btn_frame = tk.Frame(panel, bg=panel_bg)
        btn_frame.pack(fill=tk.X)
        ok_btn = tk.Button(btn_frame, text="OK", font=(UI_FONT, 11, "bold"), command=submit, bg=btn_bg, fg="#ffffff", relief=tk.FLAT, padx=24, pady=8, cursor="hand2")
        ok_btn.pack(side=tk.LEFT, padx=(0, 10))
        hover_btn(ok_btn, btn_bg, btn_hover)
        cancel_btn = tk.Button(btn_frame, text="Cancel", font=(UI_FONT, 11, "bold"), command=self.build_main_menu, bg=btn_bg, fg="#ffffff", relief=tk.FLAT, padx=20, pady=8, cursor="hand2")
        cancel_btn.pack(side=tk.LEFT)
        hover_btn(cancel_btn, btn_bg, btn_hover)

        def on_return(_):
            submit()
        un_entry.bind("<Return>", lambda e: pw_entry.focus_set())
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
        self.clear_screen()
        self._current_admin_user = staff_user

        stats = self.get_admin_overview_stats_data()
        trend_points = self.get_sales_trend_data_points(15)
        monthly_points = self.get_monthly_sales_data_points(6)
        top_products = self.get_top_selling_products_data(5)
        low_stock_points = self.get_low_stock_chart_data_points(5)

        container = tk.Frame(self.content_holder, bg=self.current_theme["bg"])

        sidebar_bg = self.current_theme.get("search_bg", "#f1f5f9")
        sidebar = tk.Frame(container, bg=sidebar_bg, width=200)
        sidebar.pack_propagate(False)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=0, pady=0)

        main = tk.Frame(container, bg=self.current_theme["bg"])
        main.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=16, pady=12)

        tk.Label(
            sidebar,
            text="Admin",
            font=(UI_FONT, 16, "bold"),
            bg=sidebar_bg,
            fg=self.current_theme["fg"],
        ).pack(pady=(16, 12), padx=12)

        accent = self.current_theme.get("accent", "#0d9488")
        hover_bg = "#2dd4bf" if self.current_theme_name == "light" else "#5eead4"

        def nav_btn(text, cmd):
            b = tk.Button(
                sidebar,
                text=text,
                font=(UI_FONT, 11),
                anchor="w",
                command=cmd,
                bg=self.current_theme["button_bg"],
                fg=self.current_theme["button_fg"],
                activebackground=hover_bg,
                activeforeground="#0f766e",
                relief=tk.FLAT,
                padx=12,
                pady=10,
                cursor="hand2",
            )
            b.pack(fill=tk.X, padx=8, pady=4)
            b.bind("<Enter>", lambda e: b.configure(bg=hover_bg) if b.winfo_exists() else None)
            b.bind("<Leave>", lambda e: b.configure(bg=self.current_theme["button_bg"]) if b.winfo_exists() else None)
            return b

        nav_btn("Overview", lambda: self.show_admin_dashboard(staff_user))
        nav_btn("Sales Reports", self.show_sales_reports_screen)
        nav_btn("Generate Excel Report", self.export_sales_report_ui)
        nav_btn("Change Credentials", self.change_admin_credentials_screen)
        nav_btn("Back to Main", self.build_main_menu)

        header = tk.Frame(main, bg=self.current_theme["bg"])
        header.pack(fill=tk.X, pady=(0, 12))

        tk.Label(
            header,
            text="Overview",
            font=(UI_FONT, 20, "bold"),
            bg=self.current_theme["bg"],
            fg=self.current_theme["fg"],
        ).pack(side=tk.LEFT)
        tk.Label(
            header,
            text=f"Admin: {staff_user['name'] or staff_user['rfid_uid']}",
            font=UI_FONT_SMALL,
            bg=self.current_theme["bg"],
            fg=self.current_theme.get("muted", self.current_theme["fg"]),
        ).pack(side=tk.RIGHT)

        metrics_frame = tk.Frame(main, bg=self.current_theme["bg"])
        metrics_frame.pack(fill=tk.X, pady=(0, 12))

        def metric_card(parent, title, value_text):
            card = tk.Frame(
                parent,
                bg=self.current_theme.get("card_bg", self.current_theme["button_bg"]),
                highlightthickness=1,
                highlightbackground=self.current_theme.get("card_border", "#e2e8f0"),
            )
            card.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=6)
            tk.Label(
                card,
                text=title,
                font=UI_FONT_SMALL,
                bg=self.current_theme.get("card_bg", self.current_theme["button_bg"]),
                fg=self.current_theme.get("muted", self.current_theme["fg"]),
            ).pack(anchor="w", padx=12, pady=(10, 2))
            tk.Label(
                card,
                text=value_text,
                font=(UI_FONT, 18, "bold"),
                bg=self.current_theme.get("card_bg", self.current_theme["button_bg"]),
                fg=self.current_theme.get("accent", "#0d9488"),
            ).pack(anchor="w", padx=12, pady=(0, 12))

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
            font=(UI_FONT, 12, "bold"),
            command=self.export_sales_report_ui,
            bg=self.current_theme.get("accent", "#0d9488"),
            fg="#ffffff",
            relief=tk.FLAT,
            padx=20,
            pady=10,
        ).pack(anchor="nw", pady=(12, 0))

        self._slide_in(container)
        self.add_theme_toggle_footer()
        self.apply_theme_to_widget(self.content_holder)

    def show_sales_reports_screen(self):
        """Show a list of generated sales report Excel files for admin to open."""
        self.clear_screen()

        frame = tk.Frame(self.content_holder, bg=self.current_theme["bg"])
        frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=16)

        tk.Label(
            frame,
            text="Sales Reports",
            font=(UI_FONT, 20, "bold"),
            bg=self.current_theme["bg"],
            fg=self.current_theme["fg"],
        ).pack(pady=(0, 12))

        reports = list_sales_reports()
        list_frame = tk.Frame(frame, bg=self.current_theme["bg"])
        list_frame.pack(expand=True, fill=tk.BOTH)

        if not reports:
            tk.Label(
                list_frame,
                text="No sales reports found. Generate one first.",
                font=UI_FONT_BODY,
                bg=self.current_theme["bg"],
                fg=self.current_theme.get("muted", self.current_theme["fg"]),
            ).pack(pady=16)
        else:
            for report_path in reports:
                row = tk.Frame(list_frame, bg=self.current_theme["bg"])
                row.pack(fill=tk.X, pady=6)

                tk.Label(
                    row,
                    text=report_path.name,
                    anchor="w",
                    font=UI_FONT_BODY,
                    bg=self.current_theme["bg"],
                    fg=self.current_theme["fg"],
                ).pack(side=tk.LEFT, expand=True)

                def make_open_cmd(p=report_path):
                    def _cmd():
                        try:
                            open_sales_report(p)
                        except Exception as exc:
                            messagebox.showerror("Open Failed", str(exc))
                    return _cmd

                tk.Button(
                    row,
                    text="Open",
                    font=UI_FONT_BODY,
                    command=make_open_cmd(),
                    bg=self.current_theme.get("accent", "#0d9488"),
                    fg="#ffffff",
                    relief=tk.FLAT,
                    padx=14,
                    pady=4,
                ).pack(side=tk.RIGHT, padx=8)

        tk.Button(
            frame,
            text="Back to Admin Dashboard",
            font=UI_FONT_BODY,
            command=lambda: self.show_admin_dashboard(getattr(self, "_current_admin_user", {"name": "admin", "rfid_uid": ""})),
            bg=self.current_theme["button_bg"],
            fg=self.current_theme["button_fg"],
            relief=tk.FLAT,
            padx=16,
            pady=8,
        ).pack(pady=12)

        self.add_theme_toggle_footer()

    def change_admin_credentials_screen(self):
        """Allow the logged-in admin to change username and password (in-app, no pop-ups)."""
        self.clear_screen()

        user = getattr(self, "_current_admin_user", {"name": "admin", "rfid_uid": ""})
        panel_bg = "#99f6e4"
        accent = self.current_theme.get("accent", "#0d9488")
        accent_hover = "#2dd4bf" if self.current_theme_name == "light" else "#5eead4"

        container = tk.Frame(self.content_holder, bg=self.current_theme["bg"])
        container.pack(fill=tk.BOTH, expand=True)

        card = tk.Frame(
            container,
            bg=panel_bg,
            highlightthickness=1,
            highlightbackground="#5eead4",
            padx=22,
            pady=18,
        )
        card.place(relx=0.5, rely=0.45, anchor="center")

        tk.Label(
            card,
            text="Change Credentials",
            font=(UI_FONT, 18, "bold"),
            bg=panel_bg,
            fg="#134e4a",
        ).pack(pady=(0, 6))
        tk.Label(
            card,
            text=f"Admin: {user.get('name') or user.get('rfid_uid') or 'admin'}",
            font=UI_FONT_SMALL,
            bg=panel_bg,
            fg="#0f766e",
        ).pack(pady=(0, 14))

        tk.Label(card, text="New username", font=UI_FONT_SMALL, bg=panel_bg, fg="#134e4a").pack(anchor="w", pady=(0, 4))
        username_var = tk.StringVar()
        username_entry = tk.Entry(card, textvariable=username_var, font=UI_FONT_BODY, width=28, relief=tk.FLAT)
        username_entry.pack(fill=tk.X, ipady=8, ipadx=10, pady=(0, 10))

        tk.Label(card, text="New password", font=UI_FONT_SMALL, bg=panel_bg, fg="#134e4a").pack(anchor="w", pady=(0, 4))
        pw_var = tk.StringVar()
        pw_entry = tk.Entry(card, textvariable=pw_var, show="*", font=UI_FONT_BODY, width=28, relief=tk.FLAT)
        pw_entry.pack(fill=tk.X, ipady=8, ipadx=10, pady=(0, 10))

        tk.Label(card, text="Confirm password", font=UI_FONT_SMALL, bg=panel_bg, fg="#134e4a").pack(anchor="w", pady=(0, 4))
        confirm_var = tk.StringVar()
        confirm_entry = tk.Entry(card, textvariable=confirm_var, show="*", font=UI_FONT_BODY, width=28, relief=tk.FLAT)
        confirm_entry.pack(fill=tk.X, ipady=8, ipadx=10, pady=(0, 12))

        status_lbl = tk.Label(card, text="", font=UI_FONT_SMALL, bg=panel_bg, fg="#b91c1c")
        status_lbl.pack(pady=(0, 10))

        def save():
            new_username = (username_var.get() or "").strip()
            new_password = pw_var.get() or ""
            confirm_password = confirm_var.get() or ""

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

        btn_row = tk.Frame(card, bg=panel_bg)
        btn_row.pack(fill=tk.X, pady=(4, 0))

        save_btn = tk.Button(
            btn_row,
            text="Save",
            font=(UI_FONT, 12, "bold"),
            command=save,
            bg=accent,
            fg="#ffffff",
            relief=tk.FLAT,
            padx=18,
            pady=8,
            cursor="hand2",
        )
        save_btn.pack(side=tk.LEFT)
        save_btn.bind("<Enter>", lambda e: save_btn.configure(bg=accent_hover) if save_btn.winfo_exists() else None)
        save_btn.bind("<Leave>", lambda e: save_btn.configure(bg=accent) if save_btn.winfo_exists() else None)

        back_btn = tk.Button(
            btn_row,
            text="Back",
            font=(UI_FONT, 12, "bold"),
            command=lambda: self.show_admin_dashboard(getattr(self, "_current_admin_user", {"name": "admin", "rfid_uid": ""})),
            bg=self.current_theme["button_bg"],
            fg=self.current_theme["button_fg"],
            relief=tk.FLAT,
            padx=18,
            pady=8,
            cursor="hand2",
        )
        back_btn.pack(side=tk.LEFT, padx=(10, 0))
        back_btn.bind("<Enter>", lambda e: back_btn.configure(bg=accent_hover) if back_btn.winfo_exists() else None)
        back_btn.bind("<Leave>", lambda e: back_btn.configure(bg=self.current_theme["button_bg"]) if back_btn.winfo_exists() else None)

        username_entry.focus_set()
        container.after(10, lambda: self._slide_in(container) if hasattr(self, "_slide_in") else None)
        self.add_theme_toggle_footer()
