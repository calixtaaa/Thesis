import tkinter as tk

from database import get_all_products
from patchNotes import VERSION

UI_FONT = "Segoe UI"
UI_FONT_BODY = (UI_FONT, 12)
UI_FONT_SMALL = (UI_FONT, 10)
UI_FONT_BUTTON = (UI_FONT, 12, "bold")


def build_welcome_screen(app):
    if hasattr(app, "_apply_lcd_fit"):
        try:
            app._apply_lcd_fit(profile="customer")
        except Exception:
            pass
    if app.sidebar_holder is not None and app.sidebar_holder.winfo_exists():
        app.sidebar_holder.destroy()
        app.sidebar_holder = None
    app.clear_screen()
    app.configure(bg=app.current_theme["bg"])
    app.content_holder.configure(bg=app.current_theme["bg"])

    center = tk.Frame(app.content_holder, bg=app.current_theme["bg"])
    center.place(relx=0.5, rely=0.5, anchor="center")

    if app.welcome_icon is not None:
        icon_label = tk.Label(
            center,
            image=app.welcome_icon,
            bg=app.current_theme["bg"],
        )
        icon_label.pack(pady=(0, 16))
        icon_label.image = app.welcome_icon

    tk.Label(
        center,
        text="Welcome",
        font=(UI_FONT, 28, "bold"),
        bg=app.current_theme["bg"],
        fg=app.current_theme["fg"],
    ).pack(pady=(0, 2))

    tk.Label(
        center,
        text="Syntaxer",
        font=(UI_FONT, 24, "bold"),
        bg=app.current_theme["bg"],
        fg=app.current_theme["fg"],
    ).pack(pady=(0, 28))

    accent = app.current_theme.get("accent", "#1A948E")
    start_btn = tk.Button(
        center,
        text="Start Order",
        font=(UI_FONT, 14, "bold"),
        bg=accent,
        fg="#ffffff",
        activebackground=app.current_theme.get("accent_hover", accent),
        activeforeground="#ffffff",
        relief=tk.FLAT,
        padx=40,
        pady=12,
        cursor="hand2",
        command=app.build_main_menu,
    )
    start_btn.pack(pady=0)

    app.apply_theme_to_widget(app.content_holder)
    if start_btn.winfo_exists():
        try:
            start_btn.configure(
                bg=app.current_theme.get("accent", accent),
                fg="#ffffff",
                activebackground=app.current_theme.get("accent_hover", accent),
                activeforeground="#ffffff",
            )
        except tk.TclError:
            pass


def show_thank_you_screen(app):
    if app.sidebar_holder is not None and app.sidebar_holder.winfo_exists():
        app.sidebar_holder.destroy()
        app.sidebar_holder = None
    app.clear_screen()
    app.content_holder.configure(bg=app.current_theme["bg"])

    center = tk.Frame(app.content_holder, bg=app.current_theme["bg"])
    center.place(relx=0.5, rely=0.5, anchor="center")

    tk.Label(
        center,
        text="Thank you, come again!",
        font=(UI_FONT, 22, "bold"),
        bg=app.current_theme["bg"],
        fg=app.current_theme["fg"],
    ).pack(pady=(0, 24))

    def go_welcome():
        app.build_welcome_screen()

    ok_btn = tk.Button(
        center,
        text="OK",
        font=(UI_FONT, 12, "bold"),
        command=go_welcome,
        bg=app.current_theme.get("accent", "#1A948E"),
        fg="#ffffff",
        relief=tk.FLAT,
        padx=24,
        pady=8,
    )
    ok_btn.pack(pady=0)
    app.after(3500, go_welcome)


def build_main_menu(app):
    if hasattr(app, "_apply_lcd_fit"):
        try:
            app._apply_lcd_fit(profile="customer")
        except Exception:
            pass
    app.clear_screen()
    all_products = get_all_products()

    if app.sidebar_holder is not None and app.sidebar_holder.winfo_exists():
        app.sidebar_holder.destroy()
        app.sidebar_holder = None

    if not app.cart:
        sidebar_width = 220
        sidebar_bg = "#1A948E"
        strip_bg = "#14b8a6"
        app.sidebar_holder = tk.Frame(app, bg=sidebar_bg, width=sidebar_width)
        app.sidebar_holder.pack_propagate(False)
        app.sidebar_holder.pack(side=tk.RIGHT, fill=tk.Y)

        tk.Label(
            app.sidebar_holder,
            text="Menu",
            font=(UI_FONT, 12, "bold"),
            bg=sidebar_bg,
            fg="#ffffff",
        ).pack(anchor="w", padx=14, pady=(14, 10))

        hover_strip = "#2dd4bf"

        def make_nav_btn(text, cmd):
            b = tk.Button(
                app.sidebar_holder,
                text=text,
                anchor="w",
                font=(UI_FONT, 11, "bold"),
                command=cmd,
                bg=strip_bg,
                fg="#ffffff",
                activebackground=hover_strip,
                activeforeground="#ffffff",
                relief=tk.FLAT,
                padx=12,
                pady=10,
                cursor="hand2",
            )
            b.pack(fill=tk.X, padx=10, pady=4)

            def on_enter(_e):
                if b.winfo_exists():
                    b.configure(bg=hover_strip)

            def on_leave(_e):
                if b.winfo_exists():
                    b.configure(bg=strip_bg)

            def on_press(_e):
                if b.winfo_exists():
                    b.configure(bg=hover_strip)

            def on_release(_e):
                if b.winfo_exists():
                    b.configure(bg=strip_bg)

            b.bind("<Enter>", on_enter)
            b.bind("<Leave>", on_leave)
            b.bind("<ButtonPress-1>", on_press)
            b.bind("<ButtonRelease-1>", on_release)
            return b

        make_nav_btn("Dashboard", lambda: None)
        make_nav_btn("Staff", lambda: app.enter_restock_mode())
        make_nav_btn("Admin", lambda: app.enter_admin_dashboard())
        make_nav_btn("Back to main screen", lambda: app.show_thank_you_screen())

    main_row = tk.Frame(app.content_holder, bg=app.current_theme["bg"])
    main_row.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    left_part = tk.Frame(main_row, bg=app.current_theme["bg"])
    left_part.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    top = tk.Frame(left_part, bg=app.current_theme["bg"])
    top.pack(side=tk.TOP, fill=tk.X)

    header = tk.Frame(top, bg=app.current_theme["bg"])
    header.pack(side=tk.TOP, fill=tk.X, pady=(2, 4), padx=10)

    title_block = tk.Frame(header, bg=app.current_theme["bg"])
    title_block.pack(side=tk.LEFT)
    tk.Label(
        title_block,
        text="Syntax Error",
        font=(UI_FONT, 20, "bold"),
        bg=app.current_theme["bg"],
        fg=app.current_theme["fg"],
    ).pack(anchor="w")
    tk.Label(
        title_block,
        text="Main menu",
        font=UI_FONT_SMALL,
        bg=app.current_theme["bg"],
        fg=app.current_theme.get("muted", app.current_theme["fg"]),
    ).pack(anchor="w")

    icons_frame = tk.Frame(header, bg=app.current_theme["bg"])
    icons_frame.pack(side=tk.RIGHT)

    menu_btn = tk.Button(
        icons_frame,
        text="☰",
        command=app.show_role_menu,
        font=(UI_FONT, 16, "bold"),
        bg=app.current_theme["bg"],
        fg=app.current_theme["fg"],
        activebackground=app.current_theme["button_bg"],
        activeforeground=app.current_theme["fg"],
        relief=tk.FLAT,
        bd=0,
        cursor="hand2",
    )
    menu_btn._hamburger_btn = True
    menu_btn.pack(side=tk.RIGHT, padx=(0, 6), pady=0)

    app.create_theme_slider(icons_frame).pack(side=tk.RIGHT, padx=6, pady=0)

    products = all_products

    content_frame = tk.Frame(left_part, bg=app.current_theme["bg"])
    content_frame.pack(expand=True, fill=tk.BOTH)

    canvas = tk.Canvas(
        content_frame,
        bg=app.current_theme["bg"],
        highlightthickness=0,
    )
    scrollbar = tk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)

    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    grid = tk.Frame(canvas, bg=app.current_theme["bg"])
    canvas.create_window((0, 0), window=grid, anchor="nw")

    for col in range(2):
        grid.grid_columnconfigure(col, weight=1)

    card_bg = app.current_theme.get("card_bg", app.current_theme["button_bg"])
    card_border = app.current_theme.get("card_border", "#e2e8f0")
    selected_bg = "#bbf7d0" if app.current_theme_name == "light" else "#14532d"
    selected_border = app.current_theme.get("accent", "#1A948E")
    placeholder_bg = "#cbd5e1" if app.current_theme_name == "light" else "#475569"
    placeholder_size = 160

    def cart_has(p):
        return any(e["product"]["id"] == p["id"] for e in app.cart)

    def add_to_cart(p):
        if p["current_stock"] <= 0:
            return
        app.cart.append({"product": p, "quantity": 1})
        app.build_main_menu()

    def remove_from_cart(p):
        app.cart = [e for e in app.cart if e["product"]["id"] != p["id"]]
        app.build_main_menu()

    for idx, p in enumerate(products):
        in_cart = cart_has(p)
        r, c = idx // 2, idx % 2

        card = tk.Frame(
            grid,
            bg=selected_bg if in_cart else card_bg,
            highlightthickness=2,
            highlightbackground=selected_border if in_cart else card_border,
            bd=0,
        )
        card.grid(row=r, column=c, padx=10, pady=8, sticky="nsew")
        grid.grid_rowconfigure(r, weight=1)

        placeholder = tk.Frame(
            card,
            bg=placeholder_bg,
            width=placeholder_size,
            height=placeholder_size,
        )
        placeholder.pack(pady=(10, 8), padx=10, fill=tk.NONE)
        placeholder.pack_propagate(False)

        name_text = p["name"]
        if len(name_text) > 18:
            name_text = name_text[:18] + "…"
        tk.Label(
            card,
            text=name_text,
            font=UI_FONT_BODY,
            bg=card_bg,
            fg=app.current_theme["fg"],
            wraplength=placeholder_size + 40,
            justify="center",
        ).pack(padx=8, pady=(0, 2))
        tk.Label(
            card,
            text=f"₱{p['price']:.2f}",
            font=UI_FONT_SMALL,
            bg=card_bg,
            fg=app.current_theme.get("muted", app.current_theme["fg"]),
        ).pack(pady=(0, 6))

        if in_cart:
            action_btn = tk.Button(
                card,
                text="✕",
                font=(UI_FONT, 18, "bold"),
                fg="#ffffff",
                bg=app.current_theme.get("accent", "#1A948E"),
                activeforeground="#ffffff",
                activebackground=app.current_theme.get("accent_hover", "#0f766e"),
                relief=tk.FLAT,
                width=4,
                command=lambda prod=p: remove_from_cart(prod),
            )
        else:
            action_btn = tk.Button(
                card,
                text="+",
                font=(UI_FONT, 20, "bold"),
                fg="#ffffff",
                bg=app.current_theme.get("accent", "#1A948E"),
                activeforeground="#ffffff",
                activebackground=app.current_theme.get("accent_hover", "#15857B"),
                relief=tk.FLAT,
                width=4,
                state=tk.NORMAL if p["current_stock"] > 0 else tk.DISABLED,
                command=lambda prod=p: add_to_cart(prod),
            )
            action_btn._product_add_btn = True
        action_btn.pack(pady=(2, 12))

    def _set_scroll_region():
        try:
            if not canvas.winfo_exists() or not grid.winfo_exists():
                return
            bbox = canvas.bbox("all")
            if bbox:
                canvas.configure(scrollregion=bbox)
        except tk.TclError:
            pass

    def _on_frame_configure(_event):
        try:
            if not canvas.winfo_exists() or not grid.winfo_exists():
                return
            app.after(50, _set_scroll_region)
        except tk.TclError:
            pass

    grid.bind("<Configure>", _on_frame_configure)
    app.after(100, _set_scroll_region)

    def _on_mousewheel(event):
        try:
            if not canvas.winfo_exists():
                return
            delta = -1 * int(event.delta / 120)
            canvas.yview_scroll(delta, "units")
            y0, y1 = canvas.yview()
            if y1 > 1.0:
                canvas.yview_moveto(max(0.0, 1.0 - (y1 - y0)))
        except (tk.TclError, AttributeError):
            pass

    canvas.bind("<MouseWheel>", _on_mousewheel)

    # Order panel (dark green) – right of left_part, only when cart has items
    order_panel_width = 260
    panel_bg = "#0f766e" if app.current_theme_name == "light" else "#134e4a"
    if app.cart:
        order_panel = tk.Frame(main_row, bg=panel_bg, width=order_panel_width)
        order_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=0, pady=0)
        order_panel.pack_propagate(False)

        tk.Button(
            order_panel,
            text="Cancel",
            font=(UI_FONT, 11, "bold"),
            fg="#ffffff",
            bg=panel_bg,
            activeforeground="#ffffff",
            activebackground=app.current_theme.get("accent_hover", "#0f766e"),
            relief=tk.FLAT,
            padx=16,
            pady=8,
            command=lambda: (app.cart.clear(), app.build_main_menu()),
        ).pack(side=tk.TOP, fill=tk.X, padx=10, pady=(10, 8))

        for entry in app.cart:
            prod = entry["product"]
            qty_var = tk.IntVar(value=entry["quantity"])

            row = tk.Frame(order_panel, bg=panel_bg)
            row.pack(side=tk.TOP, fill=tk.X, padx=10, pady=4)

            tk.Label(
                row,
                text=prod["name"][:18] + ("…" if len(prod["name"]) > 18 else ""),
                font=UI_FONT_SMALL,
                bg=panel_bg,
                fg="#ffffff",
            ).pack(anchor="center")

            ctrl = tk.Frame(row, bg=panel_bg)
            ctrl.pack(anchor="center", pady=2)

            tk.Button(
                ctrl,
                text="-",
                font=(UI_FONT, 12, "bold"),
                fg="#ffffff",
                bg=panel_bg,
                relief=tk.FLAT,
                width=2,
                command=lambda e=entry: (e.update({"quantity": max(1, e["quantity"] - 1)}), app.build_main_menu()),
            ).pack(side=tk.LEFT, padx=(0, 6))
            lbl = tk.Label(ctrl, textvariable=qty_var, font=(UI_FONT, 12, "bold"), bg=panel_bg, fg="#ffffff", width=3)
            lbl.pack(side=tk.LEFT, padx=(0, 6))
            tk.Button(
                ctrl,
                text="+",
                font=(UI_FONT, 12, "bold"),
                fg="#ffffff",
                bg=panel_bg,
                relief=tk.FLAT,
                width=2,
                command=lambda e=entry: (e.update({"quantity": min(e["product"]["current_stock"], e["quantity"] + 1)}), app.build_main_menu()),
            ).pack(side=tk.LEFT)

        tk.Button(
            order_panel,
            text="Confirm Order",
            font=(UI_FONT, 12, "bold"),
            fg="#ffffff",
            bg=app.current_theme.get("accent", "#1A948E"),
            activeforeground="#ffffff",
            activebackground=app.current_theme.get("accent_hover", "#0f766e"),
            relief=tk.FLAT,
            padx=16,
            pady=10,
            command=lambda: app._confirm_cart_order(),
        ).pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(8, 12))

    # Footer
    bottom = tk.Frame(app.content_holder, bg=app.current_theme["bg"])
    bottom.pack(side=tk.BOTTOM, fill=tk.X, pady=(6, 8))

    accent = app.current_theme.get("accent", "#1A948E")
    accent_hover = app.current_theme.get("accent_hover", "#0f766e")
    reload_btn = tk.Button(
        bottom,
        text="Reload (RFID)",
        command=app.reload_card_flow,
        font=UI_FONT_BUTTON,
        bg=accent,
        fg="#ffffff",
        activebackground=accent_hover,
        activeforeground="#ffffff",
        relief=tk.FLAT,
        padx=14,
        pady=6,
        cursor="hand2",
    )
    reload_btn.pack(side=tk.LEFT, padx=(12, 6))
    reload_btn.bind(
        "<Enter>",
        lambda e: reload_btn.configure(bg=accent_hover) if reload_btn.winfo_exists() else None,
    )
    reload_btn.bind(
        "<Leave>",
        lambda e: reload_btn.configure(bg=accent) if reload_btn.winfo_exists() else None,
    )
    buy_btn = tk.Button(
        bottom,
        text="Buy RFID Card",
        command=app.buy_card_flow,
        font=UI_FONT_BUTTON,
        bg=accent,
        fg="#ffffff",
        activebackground=accent_hover,
        activeforeground="#ffffff",
        relief=tk.FLAT,
        padx=14,
        pady=6,
        cursor="hand2",
    )
    buy_btn.pack(side=tk.LEFT, padx=6)
    buy_btn.bind(
        "<Enter>",
        lambda e: buy_btn.configure(bg=accent_hover) if buy_btn.winfo_exists() else None,
    )
    buy_btn.bind(
        "<Leave>",
        lambda e: buy_btn.configure(bg=accent) if buy_btn.winfo_exists() else None,
    )

    tk.Button(
        bottom,
        text="How to use?",
        command=app.show_help_dialog,
        font=UI_FONT_BODY,
        bg=app.current_theme["bg"],
        fg=app.current_theme["fg"],
        activebackground=app.current_theme["button_bg"],
        activeforeground=app.current_theme["fg"],
        relief=tk.FLAT,
        highlightthickness=1,
        highlightbackground=app.current_theme.get("card_border", "#e2e8f0"),
        padx=12,
        pady=6,
        cursor="hand2",
    ).pack(side=tk.LEFT, padx=6)
    tk.Button(
        bottom,
        text="Patch Notes",
        command=app.show_patch_notes_dialog,
        font=UI_FONT_BODY,
        bg=app.current_theme["bg"],
        fg=app.current_theme["fg"],
        activebackground=app.current_theme["button_bg"],
        activeforeground=app.current_theme["fg"],
        relief=tk.FLAT,
        highlightthickness=1,
        highlightbackground=app.current_theme.get("card_border", "#e2e8f0"),
        padx=12,
        pady=6,
        cursor="hand2",
    ).pack(side=tk.LEFT, padx=6)

    # datetime label + version
    app.add_ph_datetime_label(bottom)
    tk.Label(
        bottom,
        text=f"SyntaxError™  ·  {VERSION}",
        font=UI_FONT_SMALL,
        bg=app.current_theme["bg"],
        fg=app.current_theme.get("muted", app.current_theme["fg"]),
    ).pack(side=tk.LEFT, padx=(12, 8))

    app.apply_theme_to_widget(app.content_holder)
    for b in (reload_btn, buy_btn):
        if b.winfo_exists():
            try:
                b.configure(
                    bg=app.current_theme.get("accent", "#1A948E"),
                    fg="#ffffff",
                    activebackground=app.current_theme.get("accent_hover", "#0f766e"),
                    activeforeground="#ffffff",
                )
            except tk.TclError:
                pass

