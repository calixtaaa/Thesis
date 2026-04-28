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
            text="Tap restocker/admin RFID card. Reader is always listening:",
            font=UI_FONT_SMALL,
            text_color=theme.get("muted", theme["fg"]),
        ).pack(anchor="w", pady=(0, 6))

        nav_bg = theme.get("nav_bg", "#1c1c1e")
        nav_fg = theme.get("nav_fg", "#ffffff")
        nav_hover = theme.get("nav_hover", "#333333")

        scan_hint = ctk.CTkLabel(
            inner,
            text="Waiting for RFID tap...",
            font=(UI_FONT, 12, "bold"),
            text_color=theme.get("accent", "#22c55e"),
        )
        scan_hint.pack(anchor="w", pady=(0, 12))

        auth_status_var = tk.StringVar(value="Last accepted: none")
        auth_status_lbl = ctk.CTkLabel(
            inner,
            textvariable=auth_status_var,
            font=UI_FONT_SMALL,
            text_color=theme.get("muted", theme["fg"]),
        )
        auth_status_lbl.pack(anchor="w", pady=(0, 8))

        error_lbl = ctk.CTkLabel(
            inner,
            text="",
            font=UI_FONT_SMALL,
            text_color=theme.get("status_error", "#ef4444"),
        )
        error_lbl.pack(fill=tk.X, pady=(0, 6))

        btn_frame = ctk.CTkFrame(inner, fg_color=theme["card_bg"])
        btn_frame.pack(fill=tk.X, pady=(4, 0))

        last_uid = {"value": None}

        def user_value(user, key, default=None):
            try:
                value = user[key]
            except Exception:
                value = default
            return default if value is None else value

        def resolve_door_from_user(user):
            role = str(user_value(user, "role", "")).strip().lower()

            if role == "restocker":
                return "restock"
            if role == "admin":
                return "admin"
            return None

        def handle_uid(uid: str):
            user = self.get_user_by_uid_data(uid)
            if not user:
                error_lbl.configure(text=f"RFID {uid}: card not found")
                return

            selected_door = resolve_door_from_user(user)
            if not selected_door:
                error_lbl.configure(text=f"RFID {uid}: role has no door access")
                return
            if not self.is_user_authorized_for_door(user, selected_door):
                error_lbl.configure(text=f"RFID {uid}: not authorized for {selected_door} door")
                return

            role = str(user_value(user, "role", "")).strip().lower() or "unknown"
            if selected_door == "admin":
                auth_status_var.set(f"Last accepted: UID {uid} | role {role} | doors restock + troubleshoot")
                scan_hint.configure(text=f"RFID {uid} accepted. Unlocking restock and troubleshoot doors...")
                error_lbl.configure(text="")
                try:
                    self.unlock_access_door("restock")
                    self.unlock_access_door("troubleshoot")
                except Exception as exc:
                    error_lbl.configure(text=f"Failed to unlock admin doors: {exc}")
                    scan_hint.configure(text="Waiting for RFID tap...")
                    return
                self.show_troubleshooting_screen(user)
                return

            auth_status_var.set(f"Last accepted: UID {uid} | role {role} | door {selected_door}")
            scan_hint.configure(text=f"RFID {uid} accepted. Unlocking {selected_door} door...")
            error_lbl.configure(text="")
            try:
                self.unlock_access_door(selected_door)
            except Exception as exc:
                error_lbl.configure(text=f"Failed to unlock {selected_door} door: {exc}")
                scan_hint.configure(text="Waiting for RFID tap...")
                return

            if selected_door == "restock":
                self.show_restock_screen(user)
            else:
                self.show_troubleshooting_screen(user)

        def poll_rfid():
            if not inner.winfo_exists():
                return

            try:
                uid = self.read_rfid_uid("door")
            except Exception:
                uid = None

            if uid:
                uid = uid.strip().upper()
                if uid != last_uid["value"]:
                    last_uid["value"] = uid
                    handle_uid(uid)

            if inner.winfo_exists() and self._current_screen_builder == self.enter_restock_mode:
                self.after(250, poll_rfid)

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

        self.after(250, poll_rfid)
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

    def _make_door_reopen_command(self, door: str, label: str):
        def _cmd():
            try:
                self.unlock_access_door(door)
            except Exception as exc:
                messagebox.showerror("Unlock Failed", str(exc))
                return
            messagebox.showinfo("Door Unlocked", f"{label} door reopened successfully.")

        return _cmd

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
        button_row = ctk.CTkFrame(action_bar, fg_color=theme["bg"], corner_radius=0)
        button_row.pack(fill=tk.X, padx=8)

        ctk.CTkButton(
            button_row,
            text="Exit Restock Mode",
            font=(UI_FONT, 13, "bold"),
            command=self.enter_restock_mode,
            fg_color=theme.get("button_bg", "#ffffff"),
            hover_color=theme.get("card_border", "#d1d1d6"),
            text_color=theme.get("button_fg", "#1c1c1e"),
            corner_radius=980,
            height=40,
            border_width=1,
            border_color=theme.get("card_border", "#d1d1d6"),
        ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 6))

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
                text_color=theme.get("on_accent", "#ffffff"),
                corner_radius=980,
                width=100,
            ).pack(side=tk.RIGHT, padx=12, pady=8)

        ctk.CTkButton(
            button_row,
            text="Reopen Restock Door",
            font=(UI_FONT, 13, "bold"),
            command=self._make_door_reopen_command("restock", "Restock"),
            fg_color=accent,
            hover_color=theme.get("accent_hover", "#16a34a"),
            text_color=theme.get("on_accent", "#ffffff"),
            corner_radius=980,
            height=40,
        ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(6, 0))

        self._slide_in(frame)
        self.add_theme_toggle_footer()

    def show_troubleshooting_screen(self, staff_user):
        self._current_screen_builder = lambda: self.show_troubleshooting_screen(staff_user)
        self.clear_screen()
        self._current_staff_user = staff_user
        theme = self.current_theme

        frame = ctk.CTkFrame(self.content_holder, fg_color=theme["bg"])
        frame.place(relx=0, rely=0, relwidth=1, relheight=1, anchor="nw")

        inner = ctk.CTkFrame(frame, fg_color=theme["bg"])
        inner.pack(expand=True, fill=tk.BOTH, padx=20, pady=16)

        ctk.CTkLabel(
            inner,
            text=f"Troubleshooting Mode - {staff_user['name'] or staff_user['rfid_uid']}",
            font=(UI_FONT, 20, "bold"),
            text_color=theme["fg"],
        ).pack(pady=(0, 10))

        status_card = ctk.CTkFrame(
            inner,
            fg_color=theme.get("card_bg", theme["button_bg"]),
            corner_radius=14,
            border_width=1,
            border_color=theme.get("card_border", "#d1d1d6"),
        )
        status_card.pack(fill=tk.X, pady=(0, 10))

        ctk.CTkLabel(
            status_card,
            text="Troubleshooting door is unlocked.",
            font=(UI_FONT, 14, "bold"),
            text_color=theme.get("accent", "#22c55e"),
            anchor="w",
        ).pack(fill=tk.X, padx=14, pady=(12, 2))

        ctk.CTkLabel(
            status_card,
            text="Use this screen as your maintenance checklist while diagnostics are in progress.",
            font=UI_FONT_SMALL,
            text_color=theme.get("muted", theme["fg"]),
            anchor="w",
            justify="left",
        ).pack(fill=tk.X, padx=14, pady=(0, 12))

        checklist_card = ctk.CTkFrame(
            inner,
            fg_color=theme.get("card_bg", theme["button_bg"]),
            corner_radius=14,
            border_width=1,
            border_color=theme.get("card_border", "#d1d1d6"),
        )
        checklist_card.pack(fill=tk.BOTH, expand=True)

        checklist_lines = [
            "1. Verify power rails (3.3V and GND) at the RFID reader.",
            "2. Verify CE0/SCK/MOSI/MISO continuity and connector fit.",
            "3. Check that the reader reset line (GPIO5) is stable.",
            "4. Run RFID probe test from terminal if needed:",
            "   venv/bin/python rfid_single_reader_test.py --ui",
            "5. Re-seat connectors, then retry card tap/read flow.",
            "6. Exit troubleshooting mode when maintenance is complete.",
        ]
        ctk.CTkLabel(
            checklist_card,
            text="\n".join(checklist_lines),
            font=UI_FONT_BODY,
            text_color=theme.get("button_fg", theme["fg"]),
            anchor="nw",
            justify="left",
        ).pack(fill=tk.BOTH, expand=True, padx=14, pady=14)

        action_bar = ctk.CTkFrame(inner, fg_color=theme["bg"], corner_radius=0)
        action_bar.pack(side=tk.BOTTOM, fill=tk.X, pady=(8, 52))

        button_row = ctk.CTkFrame(action_bar, fg_color=theme["bg"], corner_radius=0)
        button_row.pack(fill=tk.X, padx=8)

        ctk.CTkButton(
            button_row,
            text="Back To Staff Login",
            font=(UI_FONT, 12, "bold"),
            command=self.enter_restock_mode,
            fg_color=theme.get("button_bg", "#ffffff"),
            hover_color=theme.get("card_border", "#d1d1d6"),
            text_color=theme.get("button_fg", "#1c1c1e"),
            corner_radius=980,
            height=40,
            border_width=1,
            border_color=theme.get("card_border", "#d1d1d6"),
        ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 6))

        ctk.CTkButton(
            button_row,
            text="Reopen Restock Door",
            font=(UI_FONT, 12, "bold"),
            command=self._make_door_reopen_command("restock", "Restock"),
            fg_color=theme.get("accent", "#22c55e"),
            hover_color=theme.get("accent_hover", "#16a34a"),
            text_color=theme.get("on_accent", "#ffffff"),
            corner_radius=980,
            height=40,
        ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(6, 6))

        ctk.CTkButton(
            button_row,
            text="Reopen Troubleshoot Door",
            font=(UI_FONT, 12, "bold"),
            command=self._make_door_reopen_command("troubleshoot", "Troubleshoot"),
            fg_color=theme.get("button_bg", "#ffffff"),
            hover_color=theme.get("card_border", "#d1d1d6"),
            text_color=theme.get("button_fg", "#1c1c1e"),
            corner_radius=980,
            height=40,
            border_width=1,
            border_color=theme.get("card_border", "#d1d1d6"),
        ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(6, 0))

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
