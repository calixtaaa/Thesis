import tkinter as tk
from tkinter import messagebox, simpledialog


UI_FONT = "Segoe UI"
UI_FONT_BODY = (UI_FONT, 12)
UI_FONT_SMALL = (UI_FONT, 10)

# Mint/teal login theme (matching reference)
LOGIN_PANEL_BG = "#99f6e4"
LOGIN_BTN_BG = "#0d9488"
LOGIN_BTN_HOVER = "#2dd4bf"
LOGIN_PAGE_BG = "#1e293b"


def _hover_btn(btn, normal, hover):
    def on_enter(_e):
        if btn.winfo_exists():
            btn.configure(bg=hover)
    def on_leave(_e):
        if btn.winfo_exists():
            btn.configure(bg=normal)
    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)


class StaffMixin:
    def enter_restock_mode(self):
        """Show in-app Staff Login (mint panel, no system dialog)."""
        if hasattr(self, "_apply_lcd_fit"):
            try:
                self._apply_lcd_fit(profile="admin_staff")
            except Exception:
                pass
        if self.sidebar_holder is not None and self.sidebar_holder.winfo_exists():
            self.sidebar_holder.destroy()
            self.sidebar_holder = None
        self.clear_screen()
        self.content_holder.configure(bg=LOGIN_PAGE_BG)

        center = tk.Frame(self.content_holder, bg=LOGIN_PAGE_BG)
        center.place(relx=0.5, rely=0.5, anchor="center")

        panel = tk.Frame(center, bg=LOGIN_PANEL_BG, padx=40, pady=28)
        panel.pack()

        tk.Label(
            panel,
            text="Staff Login",
            font=(UI_FONT, 18, "bold"),
            bg=LOGIN_PANEL_BG,
            fg="#0f766e",
        ).pack(pady=(0, 16))

        tk.Label(
            panel,
            text="Enter Staff RFID Card ID (simulate tap):",
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
        entry.pack(pady=(0, 20), ipady=8, ipadx=10)
        entry.focus_set()

        btn_frame = tk.Frame(panel, bg=LOGIN_PANEL_BG)
        btn_frame.pack(fill=tk.X)

        def submit():
            uid = uid_var.get().strip()
            if not uid:
                return
            user = self.get_user_by_uid_data(uid)
            if not user or not user["is_staff"]:
                messagebox.showerror("Access Denied", "Invalid staff card.")
                return
            self.show_restock_screen(user)

        ok_btn = tk.Button(
            btn_frame,
            text="OK",
            font=(UI_FONT, 11, "bold"),
            command=submit,
            bg=LOGIN_BTN_BG,
            fg="#ffffff",
            relief=tk.FLAT,
            padx=24,
            pady=8,
            cursor="hand2",
        )
        ok_btn.pack(side=tk.LEFT, padx=(0, 10))
        _hover_btn(ok_btn, LOGIN_BTN_BG, LOGIN_BTN_HOVER)

        cancel_btn = tk.Button(
            btn_frame,
            text="Cancel",
            font=(UI_FONT, 11, "bold"),
            command=self.build_main_menu,
            bg=LOGIN_BTN_BG,
            fg="#ffffff",
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor="hand2",
        )
        cancel_btn.pack(side=tk.LEFT)
        _hover_btn(cancel_btn, LOGIN_BTN_BG, LOGIN_BTN_HOVER)

        entry.bind("<Return>", lambda _: submit())
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

    def show_restock_screen(self, staff_user):
        self.clear_screen()

        frame = tk.Frame(self.content_holder, bg=self.current_theme["bg"])
        frame.place(relx=0, rely=0, relwidth=1, relheight=1, anchor="nw")
        inner = tk.Frame(frame, bg=self.current_theme["bg"])
        inner.pack(expand=True, fill=tk.BOTH, padx=20, pady=16)

        top_bar = tk.Frame(inner, bg=self.current_theme["bg"])
        top_bar.pack(fill=tk.X, pady=(0, 12))
        back_btn = tk.Button(
            top_bar,
            text="← Back to Dashboard",
            font=(UI_FONT, 11, "bold"),
            command=self.build_main_menu,
            bg=self.current_theme.get("accent", "#0d9488"),
            fg="#ffffff",
            relief=tk.FLAT,
            padx=14,
            pady=6,
            cursor="hand2",
        )
        back_btn.pack(side=tk.LEFT)
        _hover_btn(back_btn, self.current_theme.get("accent", "#0d9488"), LOGIN_BTN_HOVER)

        tk.Label(
            inner,
            text=f"Restock Mode – Staff: {staff_user['name'] or staff_user['rfid_uid']}",
            font=(UI_FONT, 18, "bold"),
            bg=self.current_theme["bg"],
            fg=self.current_theme["fg"],
        ).pack(pady=(0, 12))

        products = self.get_all_products_data()
        list_frame = tk.Frame(inner, bg=self.current_theme["bg"])
        list_frame.pack(expand=True, fill=tk.BOTH)

        accent = self.current_theme.get("accent", "#0d9488")
        card_bg = self.current_theme.get("card_bg", self.current_theme["button_bg"])
        card_border = self.current_theme.get("card_border", "#e2e8f0")

        for p in products:
            row = tk.Frame(
                list_frame,
                bg=card_bg,
                highlightthickness=1,
                highlightbackground=card_border,
            )
            row.pack(fill=tk.X, padx=0, pady=6)

            info = f"Slot {p['slot_number']} – {p['name']}  |  {p['current_stock']}/{p['capacity']}  |  ₱{p['price']:.2f}"
            tk.Label(
                row,
                text=info,
                anchor="w",
                font=UI_FONT_BODY,
                bg=card_bg,
                fg=self.current_theme["button_fg"],
            ).pack(side=tk.LEFT, expand=True, padx=12, pady=10)

            restock_btn = tk.Button(
                row,
                text="Restock",
                font=UI_FONT_BODY,
                command=lambda prod=p: self.restock_product_dialog(prod),
                bg=accent,
                fg="#ffffff",
                relief=tk.FLAT,
                padx=14,
                pady=6,
                cursor="hand2",
            )
            restock_btn.pack(side=tk.RIGHT, padx=10, pady=8)
            _hover_btn(restock_btn, accent, LOGIN_BTN_HOVER)

        exit_btn = tk.Button(
            inner,
            text="Exit Restock Mode",
            font=UI_FONT_BODY,
            command=self.build_main_menu,
            bg=self.current_theme["button_bg"],
            fg=self.current_theme["button_fg"],
            relief=tk.FLAT,
            padx=16,
            pady=8,
            cursor="hand2",
        )
        exit_btn.pack(pady=12)
        _hover_btn(exit_btn, self.current_theme["button_bg"], self.current_theme.get("accent", "#0d9488"))

        self._slide_in(frame)
        self.add_theme_toggle_footer()

    def restock_product_dialog(self, product_row):
        max_add = product_row["capacity"] - product_row["current_stock"]
        if max_add <= 0:
            messagebox.showinfo("Full", "This tray is already full.")
            return

        amount = simpledialog.askinteger(
            "Restock Amount",
            f"How many items to add? (max {max_add})",
            minvalue=1,
            maxvalue=max_add,
            parent=self,
        )
        if amount is None:
            return

        new_price = simpledialog.askfloat(
            "New Price",
            f"Enter new price per piece (current ₱{product_row['price']:.2f}), or cancel to keep:",
            parent=self,
        )

        try:
            self.restock_product_data(product_row["id"], amount, new_price)
            messagebox.showinfo("Restocked", f"Added {amount} items to {product_row['name']}.")
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

        dummy_staff = {"name": "", "rfid_uid": ""}
        self.show_restock_screen(dummy_staff)
