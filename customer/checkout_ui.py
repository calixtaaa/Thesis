import tkinter as tk

import customtkinter as ctk


def build_checkout_back_bar(app, parent, text, command):
    back_bar = ctk.CTkFrame(parent, fg_color=app.current_theme["bg"], corner_radius=0)
    back_bar.pack(side=tk.BOTTOM, fill=tk.X, pady=(8, 0))
    ctk.CTkButton(
        back_bar,
        text=text,
        font=app._ui_font_body,
        command=command,
        fg_color=app.current_theme["button_bg"],
        hover_color=app.current_theme.get("accent", "#1A948E"),
        text_color=app.current_theme["button_fg"],
        corner_radius=8,
        height=38,
    ).pack(pady=10)


def build_order_review_content(app, parent, items, total, accent, accent_hover):
    nav_bar = ctk.CTkFrame(parent, fg_color=app.current_theme["bg"], corner_radius=0)
    nav_bar.pack(side=tk.BOTTOM, fill=tk.X, pady=(0, 6))

    ctk.CTkButton(
        nav_bar,
        text="Back to products",
        font=app._ui_font_body,
        command=lambda: (app.checkout_items.clear(), app.build_main_menu()),
        fg_color=app.current_theme["button_bg"],
        hover_color=app.current_theme.get("accent", "#1A948E"),
        text_color=app.current_theme["button_fg"],
        corner_radius=8,
        height=38,
    ).pack(side=tk.LEFT, padx=(24, 8), pady=8, expand=True, fill=tk.X)

    ctk.CTkButton(
        nav_bar,
        text="Continue to payment",
        font=app._ui_font_button,
        command=app.show_payment_method_screen,
        fg_color=accent,
        hover_color=accent_hover,
        text_color="#ffffff",
        corner_radius=10,
        height=38,
    ).pack(side=tk.LEFT, padx=(8, 24), pady=8, expand=True, fill=tk.X)

    ctk.CTkLabel(
        parent,
        text="Step 2 of 3 – Review order",
        font=app._ui_font_small,
        text_color=app.current_theme.get("muted", app.current_theme["fg"]),
    ).pack(pady=(10, 0))
    ctk.CTkLabel(
        parent,
        text="Order Summary",
        font=(app._ui_font_name, 22, "bold"),
        text_color=app.current_theme["fg"],
    ).pack(pady=10)

    card = ctk.CTkFrame(
        parent,
        fg_color=app.current_theme.get("card_bg", app.current_theme["button_bg"]),
        border_width=1,
        border_color=app.current_theme.get("card_border", "#e2e8f0"),
        corner_radius=12,
    )
    card.pack(padx=24, pady=10)

    card_bg_color = app.current_theme.get("card_bg", app.current_theme["button_bg"])
    list_frame = ctk.CTkScrollableFrame(
        card,
        fg_color=card_bg_color,
        corner_radius=0,
        height=150,
        scrollbar_button_color=app.current_theme.get("search_border", "#cbd5e1"),
        scrollbar_button_hover_color=app.current_theme.get("accent", "#10b981"),
    )
    list_frame.pack(fill=tk.BOTH, expand=False, padx=30, pady=(22, 0))
    for col in range(3):
        list_frame.grid_columnconfigure(col, weight=1 if col == 0 else 0)

    for row_index, item in enumerate(items):
        product = item["product"]
        quantity = int(item["quantity"])
        line_total = float(product["price"]) * quantity
        ctk.CTkLabel(
            list_frame,
            text=product["name"],
            font=app._ui_font_body,
            text_color=app.current_theme["button_fg"],
            anchor="w",
            wraplength=420,
            justify="left",
        ).grid(row=row_index, column=0, sticky="w", pady=4)
        ctk.CTkLabel(
            list_frame,
            text=f"x{quantity}",
            font=(app._ui_font_name, 12, "bold"),
            text_color=app.current_theme.get("muted", app.current_theme["button_fg"]),
            anchor="e",
        ).grid(row=row_index, column=1, sticky="e", padx=(10, 0))
        ctk.CTkLabel(
            list_frame,
            text=f"₱{line_total:.2f}",
            font=(app._ui_font_name, 12, "bold"),
            text_color=app.current_theme["button_fg"],
            anchor="e",
        ).grid(row=row_index, column=2, sticky="e", padx=(18, 0))

    ctk.CTkLabel(
        card,
        text=f"Total: ₱{total:.2f}",
        font=(app._ui_font_name, 16, "bold"),
        text_color=app.current_theme["button_fg"],
    ).pack(pady=(14, 10), padx=30)


def build_quantity_content(app, parent, product, accent, accent_hover):
    ctk.CTkLabel(
        parent,
        text="Step 2 of 3 – Choose quantity",
        font=app._ui_font_small,
        text_color=app.current_theme.get("muted", app.current_theme["fg"]),
    ).pack(pady=(16, 0))
    ctk.CTkLabel(
        parent,
        text="Choose Quantity",
        font=(app._ui_font_name, 22, "bold"),
        text_color=app.current_theme["fg"],
    ).pack(pady=10)

    card_bg_color = app.current_theme.get("card_bg", app.current_theme["button_bg"])
    card = ctk.CTkFrame(
        parent,
        fg_color=card_bg_color,
        border_width=1,
        border_color=app.current_theme.get("card_border", "#e2e8f0"),
        corner_radius=12,
    )
    card.pack(padx=40, pady=20)

    ctk.CTkLabel(
        card,
        text=f"Selected: {product['name']}",
        font=(app._ui_font_name, 14, "bold"),
        text_color=app.current_theme["button_fg"],
        wraplength=420,
        justify="center",
    ).pack(pady=(28, 10), padx=36)
    ctk.CTkLabel(card, text=f"Price: ₱{product['price']:.2f}", font=app._ui_font_body, text_color=app.current_theme["button_fg"]).pack(pady=4, padx=36)
    ctk.CTkLabel(card, text=f"Available: {product['current_stock']}", font=app._ui_font_body, text_color=app.current_theme.get("muted", app.current_theme["button_fg"])).pack(pady=(4, 16), padx=36)

    qty_var = tk.IntVar(value=app.current_quantity)

    def update_qty(delta):
        new = qty_var.get() + delta
        if 1 <= new <= product["current_stock"]:
            qty_var.set(new)

    qty_frame = ctk.CTkFrame(card, fg_color=card_bg_color, corner_radius=0)
    qty_frame.pack(pady=14)
    ctk.CTkButton(qty_frame, text="−", font=(app._ui_font_name, 16, "bold"), command=lambda: update_qty(-1), fg_color=accent, hover_color=accent_hover, text_color="#ffffff", width=60, height=40, corner_radius=10).pack(side=tk.LEFT, padx=12)
    tk.Label(qty_frame, textvariable=qty_var, font=(app._ui_font_name, 28, "bold"), bg=card_bg_color, fg=app.current_theme["button_fg"], width=5).pack(side=tk.LEFT, padx=12)
    ctk.CTkButton(qty_frame, text="+", font=(app._ui_font_name, 16, "bold"), command=lambda: update_qty(1), fg_color=accent, hover_color=accent_hover, text_color="#ffffff", width=60, height=40, corner_radius=10).pack(side=tk.LEFT, padx=12)

    def proceed():
        app.current_quantity = qty_var.get()
        app.checkout_items = [{"product": product, "quantity": int(app.current_quantity or 1)}]
        app.show_payment_method_screen()

    ctk.CTkButton(card, text="Continue to payment", font=app._ui_font_button, command=proceed, fg_color=accent, hover_color=accent_hover, text_color="#ffffff", corner_radius=10, height=44).pack(pady=(18, 28), padx=36, fill=tk.X)


def build_payment_method_content(app, parent, items, total):
    ctk.CTkLabel(parent, text="Step 3 of 3 – Choose payment method", font=app._ui_font_small, text_color=app.current_theme["fg"]).pack(pady=(10, 0))
    ctk.CTkLabel(parent, text="Choose Payment Method", font=app._ui_font_bold, text_color=app.current_theme["fg"]).pack(pady=6)

    card = ctk.CTkFrame(parent, fg_color=app.current_theme["button_bg"], border_width=1, border_color=app.current_theme.get("card_border", "#e2e8f0"), corner_radius=12)
    card.pack(padx=24, pady=10)

    summary_text = "\n".join(f"{item['product']['name']} x{int(item['quantity'])}" for item in items)
    ctk.CTkLabel(card, text=summary_text, font=app._ui_font_body, text_color=app.current_theme["button_fg"], wraplength=360, justify="center").pack(pady=(20, 8), padx=20)
    ctk.CTkLabel(card, text=f"Total: ₱{total:.2f}", font=app._ui_font_title, text_color=app.current_theme["button_fg"]).pack(pady=(0, 16), padx=20)

    ctk.CTkButton(card, text="Pay with Cash\nInsert coins or bills", font=app._ui_font_button, fg_color=app.current_theme.get("accent", "#1A948E"), hover_color=app.current_theme.get("accent_hover", "#15857B"), text_color="#ffffff", corner_radius=10, height=60, command=lambda: app.cash_payment_flow(total)).pack(pady=8, padx=20, fill=tk.X)
    ctk.CTkButton(card, text="Pay with RFID Card\nCashless payment", font=app._ui_font_button, fg_color=app.current_theme.get("accent", "#1A948E"), hover_color=app.current_theme.get("accent_hover", "#15857B"), text_color="#ffffff", corner_radius=10, height=60, command=lambda: app.rfid_payment_flow(total)).pack(pady=(8, 20), padx=20, fill=tk.X)
    ctk.CTkButton(parent, text="Back", font=app._ui_font_body, fg_color=app.current_theme["button_bg"], hover_color=app.current_theme.get("accent", "#1A948E"), text_color=app.current_theme["button_fg"], corner_radius=8, height=36, command=app.go_back_from_payment_method).pack(pady=10)


def build_cash_payment_content(app, parent, total_amount: float):
    content = ctk.CTkFrame(parent, fg_color=app.current_theme["bg"], corner_radius=0)
    content.pack(expand=True, fill=tk.BOTH)

    ctk.CTkLabel(content, text="Pay with Cash", font=app._ui_font_bold, text_color=app.current_theme["fg"]).pack(pady=(8, 4))
    ctk.CTkLabel(content, text="Cash pulses from bill/coin acceptors are read from GPIO. Buttons below remain for simulation.", font=app._ui_font_small, text_color=app.current_theme["fg"]).pack(pady=(0, 2))

    card = ctk.CTkFrame(content, fg_color=app.current_theme["button_bg"], border_width=1, border_color=app.current_theme.get("card_border", "#e2e8f0"), corner_radius=12)
    card.pack(padx=24, pady=8)
    ctk.CTkLabel(card, text=f"Total to Pay: ₱{total_amount:.2f}", font=app._ui_font_title, text_color=app.current_theme["button_fg"]).pack(pady=(16, 10), padx=20)

    amount_var = tk.DoubleVar(value=0.0)
    remaining_var = tk.DoubleVar(value=total_amount)
    ctk.CTkLabel(card, text="Amount Inserted:", font=app._ui_font_body, text_color=app.current_theme["button_fg"]).pack(pady=4, padx=20)
    tk.Label(card, textvariable=amount_var, font=(app._ui_font_name, 22, "bold"), bg=app.current_theme["button_bg"], fg=app.current_theme["button_fg"]).pack()
    ctk.CTkLabel(card, text="Remaining:", font=app._ui_font_body, text_color=app.current_theme["button_fg"]).pack(pady=(10, 4), padx=20)
    tk.Label(card, textvariable=remaining_var, font=(app._ui_font_name, 22, "bold"), bg=app.current_theme["button_bg"], fg=app.current_theme["button_fg"]).pack()

    btn_frame = ctk.CTkFrame(card, fg_color=app.current_theme["button_bg"], corner_radius=0)
    btn_frame.pack(pady=10, padx=20)

    def add_money(value):
        app.cash_session.add(value)
        current = app.cash_session.get_amount()
        amount_var.set(current)
        remaining_var.set(max(0.0, total_amount - current))

    for text, value in [("+₱1", 1), ("+₱5", 5), ("+₱10", 10), ("+₱20", 20)]:
        ctk.CTkButton(btn_frame, text=text, font=app._ui_font_body, fg_color=app.current_theme.get("accent", "#1A948E"), hover_color=app.current_theme.get("accent_hover", "#15857B"), text_color="#ffffff", corner_radius=8, width=70, height=34, command=lambda v=value: add_money(v)).pack(side=tk.LEFT, padx=5)

    def finish_if_enough():
        current = app.cash_session.get_amount()
        if current < total_amount:
            from tkinter import messagebox
            messagebox.showwarning("Not enough", "Please insert more cash.")
            return
        app.complete_purchase_cash(total_amount, current)

    ctk.CTkButton(card, text="Dispense product", font=app._ui_font_button, command=finish_if_enough, fg_color="#4CAF50", hover_color="#388E3C", text_color="#ffffff", corner_radius=10, height=44).pack(pady=(8, 14), padx=20, fill=tk.X)
    build_checkout_back_bar(app, parent, "Cancel and go back", app.show_payment_method_screen)

    app.start_cash_pulse_monitor(amount_var, remaining_var, total_amount)
