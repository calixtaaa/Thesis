import tkinter as tk
from tkinter import messagebox, simpledialog


class StaffMixin:
    def enter_restock_mode(self):
        """Authenticate staff using RFID card ID."""
        uid = simpledialog.askstring(
            "Staff Login",
            "Enter Staff RFID Card ID (simulate tap):",
            parent=self,
        )
        if not uid:
            return

        user = self.get_user_by_uid_data(uid)
        if not user or not user["is_staff"]:
            messagebox.showerror("Access Denied", "Invalid staff card.")
            return

        self.show_restock_screen(user)

    def show_restock_screen(self, staff_user):
        self.clear_screen()

        tk.Label(
            self,
            text=f"Restock Mode - Staff: {staff_user['name'] or staff_user['rfid_uid']}",
            font=("Arial", 16),
        ).pack(pady=10)

        products = self.get_all_products_data()
        list_frame = tk.Frame(self, bg=self.current_theme["bg"])
        list_frame.pack(expand=True, fill=tk.BOTH)

        for p in products:
            row = tk.Frame(list_frame, bg=self.current_theme["bg"])
            row.pack(fill=tk.X, padx=10, pady=5)

            info = f"Slot {p['slot_number']} - {p['name']} | {p['current_stock']}/{p['capacity']} | ₱{p['price']:.2f}"
            tk.Label(row, text=info, anchor="w").pack(side=tk.LEFT, expand=True)

            tk.Button(
                row,
                text="Restock",
                command=lambda prod=p: self.restock_product_dialog(prod),
            ).pack(side=tk.RIGHT, padx=5)

        tk.Button(self, text="Exit Restock Mode", command=self.build_main_menu).pack(pady=10)

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
