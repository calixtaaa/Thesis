import tkinter as tk
from tkinter import messagebox, simpledialog
import customtkinter as ctk


UI_FONT = "Segoe UI"
UI_FONT_BODY = (UI_FONT, 13)
UI_FONT_SMALL = (UI_FONT, 11)


def _hover_btn(btn, normal, hover):
    """Hover effect; stores colors on btn so Leave always restores correctly."""
    btn._hover_normal = normal
    btn._hover_hover = hover

    def on_enter(_e):
        if btn.winfo_exists():
            btn.configure(bg=btn._hover_hover)

    def on_leave(_e):
        if btn.winfo_exists():
            btn.configure(bg=btn._hover_normal)

    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)


class StaffMixin:
    def enter_restock_mode(self):
        """Show in-app Staff Login with iOS-style card panel."""
        self._current_screen_builder = self.enter_restock_mode
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

        panel = ctk.CTkFrame(
            center,
            fg_color=theme["card_bg"],
            corner_radius=20,
            border_width=1,
            border_color=theme["card_border"],
        )
        panel.pack()
        inner = ctk.CTkFrame(panel, fg_color=theme["card_bg"])
        inner.pack(padx=40, pady=28)

        ctk.CTkLabel(
            inner,
            text="Staff Login",
            font=(UI_FONT, 20, "bold"),
            text_color=theme["fg"],
        ).pack(pady=(0, 16))

        ctk.CTkLabel(
            inner,
            text="Select door and tap staff/research RFID card:",
            font=UI_FONT_SMALL,
            text_color=theme.get("muted", theme["fg"]),
        ).pack(anchor="w", pady=(0, 6))

        nav_bg = theme.get("nav_bg", "#1c1c1e")
        nav_fg = theme.get("nav_fg", "#ffffff")
        nav_hover = theme.get("nav_hover", "#333333")

        door_var = tk.StringVar(value="restock")
        ctk.CTkOptionMenu(
            inner,
            variable=door_var,
            values=["restock", "troubleshoot"],
            width=280,
            fg_color=nav_bg,
            button_color=nav_hover,
            button_hover_color=theme.get("accent", "#22c55e"),
            text_color=nav_fg,
            dropdown_fg_color=theme["card_bg"],
            dropdown_text_color=theme["fg"],
            dropdown_hover_color=theme.get("search_bg", "#f2f2f7"),
        ).pack(pady=(0, 12))

        entry = ctk.CTkEntry(
            inner,
            font=UI_FONT_BODY,
            width=280,
            fg_color=theme.get("search_bg", "#ffffff"),
            text_color=theme["fg"],
            border_color=theme.get("search_border", "#d1d1d6"),
            corner_radius=12,
            height=42,
        )
        entry.pack(pady=(0, 20))
        entry.focus_set()

        def read_from_door_reader():
            uid = self.read_rfid_uid("door")
            if not uid:
                error_lbl.configure(text="No RFID tap detected. You can type card ID manually.")
                return
            entry.delete(0, tk.END)
            entry.insert(0, uid)
            error_lbl.configure(text="")

        ctk.CTkButton(
            inner,
            text="Read from Door RFID Reader",
            font=(UI_FONT, 11, "bold"),
            command=read_from_door_reader,
            fg_color=theme.get("button_bg", "#ffffff"),
            hover_color=theme.get("card_border", "#d1d1d6"),
            text_color=theme.get("button_fg", "#1c1c1e"),
            corner_radius=980,
            height=34,
            border_width=1,
            border_color=theme.get("card_border", "#d1d1d6"),
        ).pack(anchor="w", pady=(0, 12))

        error_lbl = ctk.CTkLabel(
            inner,
            text="",
            font=UI_FONT_SMALL,
            text_color="#ef4444",
        )
        error_lbl.pack(fill=tk.X, pady=(0, 6))

        btn_frame = ctk.CTkFrame(inner, fg_color=theme["card_bg"])
        btn_frame.pack(fill=tk.X, pady=(4, 0))

        def submit():
            uid = entry.get().strip()
            if not uid:
                error_lbl.configure(text="Please enter a staff RFID card ID.")
                return

            selected_door = door_var.get().strip().lower()
            user = self.get_user_by_uid_data(uid)
            if not user:
                error_lbl.configure(text="RFID card not found.")
                return
            if not self.is_user_authorized_for_door(user, selected_door):
                error_lbl.configure(text=f"Card role is not allowed to open {selected_door} door.")
                return

            try:
                self.unlock_access_door(selected_door)
            except Exception as exc:
                error_lbl.configure(text=f"Failed to unlock door: {exc}")
                return

            error_lbl.configure(text="")
            if selected_door == "restock":
                self.show_restock_screen(user)
            else:
                messagebox.showinfo(
                    "Door Unlocked",
                    "Troubleshooting door unlocked successfully.\nProceed with maintenance.",
                )

        ctk.CTkButton(
            btn_frame,
            text="Unlock",
            font=(UI_FONT, 12, "bold"),
            command=submit,
            fg_color=nav_bg,
            hover_color=nav_hover,
            text_color=nav_fg,
            corner_radius=980,
            height=40,
        ).pack(side=tk.LEFT, padx=(0, 10))

        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            font=(UI_FONT, 12, "bold"),
            command=self.build_main_menu,
            fg_color=theme.get("button_bg", "#ffffff"),
            hover_color=theme.get("card_border", "#d1d1d6"),
            text_color=theme.get("button_fg", "#1c1c1e"),
            corner_radius=980,
            height=40,
            border_width=1,
            border_color=theme.get("card_border", "#d1d1d6"),
        ).pack(side=tk.LEFT)

        entry.bind("<Return>", lambda _: submit())
        self.add_theme_toggle_footer()

    def _slide_in(self, frame, steps=12, step_ms=20):
        """Animate frame sliding in from the right."""
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
        self._current_screen_builder = lambda: self.show_restock_screen(staff_user)
        self.clear_screen()
        self._current_staff_user = staff_user
        theme = self.current_theme

        frame = ctk.CTkFrame(self.content_holder, fg_color=theme["bg"])
        frame.place(relx=0, rely=0, relwidth=1, relheight=1, anchor="nw")
        inner = ctk.CTkFrame(frame, fg_color=theme["bg"])
        inner.pack(expand=True, fill=tk.BOTH, padx=20, pady=16)

        ctk.CTkLabel(
            inner,
            text=f"Restock Mode — {staff_user['name'] or staff_user['rfid_uid']}",
            font=(UI_FONT, 20, "bold"),
            text_color=theme["fg"],
        ).pack(pady=(0, 12))

        products = self.get_all_products_data()
        card_bg = theme.get("card_bg", theme["button_bg"])
        accent = theme.get("accent", "#22c55e")

        action_bar = ctk.CTkFrame(inner, fg_color=theme["bg"], corner_radius=0)
        # Keep this above the global footer/theme bar on compact displays.
        action_bar.pack(side=tk.BOTTOM, fill=tk.X, pady=(8, 52))
        ctk.CTkButton(
            action_bar,
            text="Exit Restock Mode",
            font=(UI_FONT, 13, "bold"),
            command=self.build_main_menu,
            fg_color=theme.get("button_bg", "#ffffff"),
            hover_color=theme.get("card_border", "#d1d1d6"),
            text_color=theme.get("button_fg", "#1c1c1e"),
            corner_radius=980,
            height=40,
            border_width=1,
            border_color=theme.get("card_border", "#d1d1d6"),
        ).pack(fill=tk.X, padx=8)

        list_frame = ctk.CTkScrollableFrame(inner, fg_color=theme["bg"])
        list_frame.pack(expand=True, fill=tk.BOTH)

        for p in products:
            row = ctk.CTkFrame(
                list_frame,
                fg_color=card_bg,
                corner_radius=14,
                border_width=1,
                border_color=theme.get("card_border", "#d1d1d6"),
            )
            row.pack(fill=tk.X, padx=0, pady=5)

            info = f"Slot {p['slot_number']}  —  {p['name']}  |  {p['current_stock']}/{p['capacity']}  |  ₱{p['price']:.2f}"
            ctk.CTkLabel(
                row,
                text=info,
                anchor="w",
                font=UI_FONT_BODY,
                text_color=theme.get("button_fg", theme["fg"]),
            ).pack(side=tk.LEFT, expand=True, padx=14, pady=12)

            ctk.CTkButton(
                row,
                text="Restock",
                font=(UI_FONT, 12, "bold"),
                command=lambda prod=p: self.restock_product_dialog(prod),
                fg_color=accent,
                hover_color=theme.get("accent_hover", "#16a34a"),
                text_color="#ffffff",
                corner_radius=980,
                width=100,
            ).pack(side=tk.RIGHT, padx=12, pady=8)

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

        staff_user = getattr(self, "_current_staff_user", {"name": "", "rfid_uid": ""})
        self.show_restock_screen(staff_user)
