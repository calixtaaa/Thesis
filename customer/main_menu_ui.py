import tkinter as tk

import bugreport
import customtkinter as ctk


def build_main_menu_header(app, parent, *, ui_font, ui_font_title, ui_font_small):
    top = ctk.CTkFrame(parent, fg_color=app.current_theme["bg"], corner_radius=0)
    top.pack(side=tk.TOP, fill=tk.X)

    header = ctk.CTkFrame(top, fg_color=app.current_theme["bg"], corner_radius=0)
    header.pack(side=tk.TOP, fill=tk.X, pady=(2, 4), padx=10)

    title_block = ctk.CTkFrame(header, fg_color=app.current_theme["bg"], corner_radius=0)
    title_block.pack(side=tk.LEFT)
    ctk.CTkLabel(
        title_block,
        text="Syntax Error",
        font=ui_font_title,
        text_color=app.current_theme["fg"],
    ).pack(anchor="w")
    ctk.CTkLabel(
        title_block,
        text="Main menu",
        font=ui_font_small,
        text_color=app.current_theme.get("muted", app.current_theme["fg"]),
    ).pack(anchor="w")

    icons_frame = ctk.CTkFrame(header, fg_color=app.current_theme["bg"], corner_radius=0)
    icons_frame.pack(side=tk.RIGHT)

    menu_btn = ctk.CTkButton(
        icons_frame,
        text="☰",
        command=app.show_role_menu,
        font=(ui_font, 16, "bold"),
        fg_color="transparent",
        hover_color=app.current_theme["button_bg"],
        text_color=app.current_theme["fg"],
        width=40,
        height=36,
        corner_radius=8,
    )
    menu_btn._hamburger_btn = True
    menu_btn.pack(side=tk.RIGHT, padx=(0, 6), pady=0)

    app.create_theme_slider(icons_frame).pack(side=tk.RIGHT, padx=6, pady=0)


def build_main_menu_products(app, parent, products):
    content_frame = ctk.CTkFrame(parent, fg_color=app.current_theme["bg"], corner_radius=0)
    content_frame.pack(expand=True, fill=tk.BOTH)

    scroll_frame = ctk.CTkScrollableFrame(
        content_frame,
        fg_color=app.current_theme["bg"],
        corner_radius=0,
    )
    scroll_frame.pack(fill=tk.BOTH, expand=True)

    grid = scroll_frame
    for col in range(2):
        grid.grid_columnconfigure(col, weight=1)

    app._cart_card_bg = app.current_theme.get("card_bg", app.current_theme["button_bg"])
    app._cart_card_border = app.current_theme.get("card_border", "#e2e8f0")
    app._cart_selected_bg = "#bbf7d0" if app.current_theme_name == "light" else "#14532d"
    app._cart_selected_border = app.current_theme.get("accent", "#1A948E")
    app._product_placeholder_bg = "#cbd5e1" if app.current_theme_name == "light" else "#475569"
    app._product_placeholder_size = 160
    app._product_card_refs = {}

    for idx, product in enumerate(products):
        build_product_card(app, grid, product, idx)


def build_product_card(app, grid, product, idx):
    in_cart = app._cart_has_product(product)
    row_index, column_index = idx // 2, idx % 2

    card = ctk.CTkFrame(
        grid,
        fg_color=app._cart_selected_bg if in_cart else app._cart_card_bg,
        border_width=2,
        border_color=app._cart_selected_border if in_cart else app._cart_card_border,
        corner_radius=12,
    )
    card.grid(row=row_index, column=column_index, padx=10, pady=8, sticky="nsew")

    placeholder = ctk.CTkFrame(
        card,
        fg_color=app._product_placeholder_bg,
        width=app._product_placeholder_size,
        height=app._product_placeholder_size,
        corner_radius=8,
    )
    placeholder.pack(pady=(10, 8), padx=10, fill=tk.NONE)
    placeholder.pack_propagate(False)

    name_text = product["name"]
    if len(name_text) > 18:
        name_text = name_text[:18] + "…"
    ctk.CTkLabel(
        card,
        text=name_text,
        font=app._ui_font_body,
        text_color=app.current_theme["fg"],
        wraplength=app._product_placeholder_size + 40,
        justify="center",
    ).pack(padx=8, pady=(0, 2))
    ctk.CTkLabel(
        card,
        text=f"₱{product['price']:.2f}",
        font=app._ui_font_small,
        text_color=app.current_theme.get("muted", app.current_theme["fg"]),
    ).pack(pady=(0, 6))

    action_btn = build_product_card_button(app, card, product, in_cart)
    action_btn.pack(pady=(2, 12))
    app._product_card_refs[product["id"]] = {
        "card": card,
        "btn": action_btn,
        "product": product,
        "add_cmd": lambda prod=product: app._add_product_to_cart(prod),
    }


def build_product_card_button(app, card, product, in_cart):
    if in_cart:
        return ctk.CTkButton(
            card,
            text="✕",
            font=(app._ui_font_name, 18, "bold"),
            text_color="#ffffff",
            fg_color=app.current_theme.get("accent", "#1A948E"),
            hover_color=app.current_theme.get("accent_hover", "#0f766e"),
            width=60,
            height=36,
            corner_radius=8,
            command=lambda prod=product: app._remove_product_from_cart(prod),
        )

    action_btn = ctk.CTkButton(
        card,
        text="+",
        font=(app._ui_font_name, 20, "bold"),
        text_color="#ffffff",
        fg_color=app.current_theme.get("accent", "#1A948E"),
        hover_color=app.current_theme.get("accent_hover", "#15857B"),
        width=60,
        height=36,
        corner_radius=8,
        state=tk.NORMAL if product["current_stock"] > 0 else tk.DISABLED,
        command=lambda prod=product: app._add_product_to_cart(prod),
    )
    action_btn._product_add_btn = True
    return action_btn


def build_main_menu_footer(app, *, version, hover_scale_btn):
    bottom = ctk.CTkFrame(app.content_holder, fg_color=app.current_theme["bg"], corner_radius=0)
    bottom.pack(side=tk.BOTTOM, fill=tk.X, pady=(6, 8))
    actions_row = ctk.CTkFrame(bottom, fg_color=app.current_theme["bg"], corner_radius=0)
    actions_row.pack(side=tk.TOP, fill=tk.X)
    info_row = ctk.CTkFrame(bottom, fg_color=app.current_theme["bg"], corner_radius=0)
    info_row.pack(side=tk.TOP, fill=tk.X, pady=(6, 0))

    accent = app.current_theme.get("accent", "#1A948E")
    accent_hover = app.current_theme.get("accent_hover", "#0f766e")
    ctk.CTkButton(
        actions_row,
        text="Reload (RFID)",
        command=app.reload_card_flow,
        font=app._ui_font_button,
        fg_color=accent,
        hover_color=accent_hover,
        text_color="#ffffff",
        corner_radius=10,
        height=36,
    ).pack(side=tk.LEFT, padx=(12, 6))
    ctk.CTkButton(
        actions_row,
        text="Buy RFID Card",
        command=app.buy_card_flow,
        font=app._ui_font_button,
        fg_color=accent,
        hover_color=accent_hover,
        text_color="#ffffff",
        corner_radius=10,
        height=36,
    ).pack(side=tk.LEFT, padx=6)
    ctk.CTkButton(
        actions_row,
        text="Report",
        command=lambda: bugreport.show_bug_report_screen(app, version=version, hover_scale_btn=hover_scale_btn),
        font=app._ui_font_body,
        fg_color="transparent",
        hover_color=app.current_theme["button_bg"],
        text_color=app.current_theme["fg"],
        border_width=1,
        border_color=app.current_theme.get("card_border", "#e2e8f0"),
        corner_radius=8,
        height=36,
    ).pack(side=tk.LEFT, padx=6)
    ctk.CTkButton(
        actions_row,
        text="How to use?",
        command=app.show_help_dialog,
        font=app._ui_font_body,
        fg_color="transparent",
        hover_color=app.current_theme["button_bg"],
        text_color=app.current_theme["fg"],
        border_width=1,
        border_color=app.current_theme.get("card_border", "#e2e8f0"),
        corner_radius=8,
        height=36,
    ).pack(side=tk.LEFT, padx=6)
    ctk.CTkButton(
        actions_row,
        text="Patch Notes",
        command=app.show_patch_notes_dialog,
        font=app._ui_font_body,
        fg_color="transparent",
        hover_color=app.current_theme["button_bg"],
        text_color=app.current_theme["fg"],
        border_width=1,
        border_color=app.current_theme.get("card_border", "#e2e8f0"),
        corner_radius=8,
        height=36,
    ).pack(side=tk.LEFT, padx=6)

    app.add_ph_datetime_label(info_row)
    ctk.CTkLabel(
        info_row,
        text=f"SyntaxError™  ·  {version}",
        font=app._ui_font_small,
        text_color=app.current_theme.get("muted", app.current_theme["fg"]),
    ).pack(side=tk.LEFT, padx=(12, 8))
