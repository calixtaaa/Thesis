import tkinter as tk
from pathlib import Path

import bugreport
import customtkinter as ctk

try:
    from PIL import Image, ImageTk
    _HAS_PIL = True
except ImportError:
    _HAS_PIL = False

BASE_DIR = Path(__file__).resolve().parents[1]
PRODUCT_IMAGES_DIR = BASE_DIR / "images" / "Products"

_product_image_cache = {}

PRODUCT_IMAGE_MAP = {
    "alcohol": "GreenCross.png",
}

def _resolve_product_image_path(product_name):
    """Return the Path to the product image file, or None."""
    if not PRODUCT_IMAGES_DIR.exists():
        return None
    name_lower = product_name.strip().lower()
    mapped = PRODUCT_IMAGE_MAP.get(name_lower)
    if mapped:
        p = PRODUCT_IMAGES_DIR / mapped
        if p.exists():
            return p
    for img_file in PRODUCT_IMAGES_DIR.iterdir():
        if img_file.stem.strip().lower() == name_lower and img_file.suffix.lower() in (".png", ".jpg", ".jpeg", ".gif"):
            return img_file
    for img_file in PRODUCT_IMAGES_DIR.iterdir():
        if name_lower in img_file.stem.strip().lower() and img_file.suffix.lower() in (".png", ".jpg", ".jpeg", ".gif"):
            return img_file
    return None


def _load_product_image(product_name, size=140):
    """Load a product image from images/Products/ matching the product name."""
    if not _HAS_PIL:
        return None

    cache_key = (product_name, size)
    if cache_key in _product_image_cache:
        return _product_image_cache[cache_key]

    if not PRODUCT_IMAGES_DIR.exists():
        return None

    name_lower = product_name.strip().lower()

    mapped = PRODUCT_IMAGE_MAP.get(name_lower)
    if mapped:
        path = PRODUCT_IMAGES_DIR / mapped
        if path.exists():
            try:
                pil_img = Image.open(str(path))
                pil_img = pil_img.resize((size, size), Image.LANCZOS)
                tk_img = ImageTk.PhotoImage(pil_img)
                _product_image_cache[cache_key] = tk_img
                return tk_img
            except Exception:
                pass

    for img_file in PRODUCT_IMAGES_DIR.iterdir():
        if img_file.stem.strip().lower() == name_lower and img_file.suffix.lower() in (".png", ".jpg", ".jpeg", ".gif"):
            try:
                pil_img = Image.open(str(img_file))
                pil_img = pil_img.resize((size, size), Image.LANCZOS)
                tk_img = ImageTk.PhotoImage(pil_img)
                _product_image_cache[cache_key] = tk_img
                return tk_img
            except Exception:
                return None

    for img_file in PRODUCT_IMAGES_DIR.iterdir():
        if name_lower in img_file.stem.strip().lower() and img_file.suffix.lower() in (".png", ".jpg", ".jpeg", ".gif"):
            try:
                pil_img = Image.open(str(img_file))
                pil_img = pil_img.resize((size, size), Image.LANCZOS)
                tk_img = ImageTk.PhotoImage(pil_img)
                _product_image_cache[cache_key] = tk_img
                return tk_img
            except Exception:
                return None

    return None


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
    app._cart_selected_bg = app.current_theme.get("selected_bg", "#d1fae5")
    app._cart_selected_border = app.current_theme.get("selected_border", app.current_theme.get("accent", "#10b981"))
    app._product_placeholder_bg = "#e2e8f0" if app.current_theme_name == "light" else "#334155"
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
        corner_radius=14,
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

    if _HAS_PIL:
        try:
            img_path = _resolve_product_image_path(product["name"])
            if img_path:
                sz = app._product_placeholder_size - 20
                pil_img = Image.open(str(img_path))
                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(sz, sz))
                img_label = ctk.CTkLabel(
                    placeholder, image=ctk_img, text="", fg_color="transparent",
                )
                img_label._ctk_img_ref = ctk_img
                img_label.place(relx=0.5, rely=0.5, anchor="center")
        except Exception:
            pass

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
        font=(app._ui_font_name, 13, "bold"),
        text_color=app.current_theme.get("price_color", app.current_theme.get("accent", "#10b981")),
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
            fg_color=app.current_theme.get("btn_remove", "#ef4444"),
            hover_color=app.current_theme.get("btn_remove_hover", "#dc2626"),
            width=60,
            height=36,
            corner_radius=980,
            command=lambda prod=product: app._remove_product_from_cart(prod),
        )

    action_btn = ctk.CTkButton(
        card,
        text="+",
        font=(app._ui_font_name, 20, "bold"),
        text_color="#ffffff",
        fg_color=app.current_theme.get("btn_add", "#10b981"),
        hover_color=app.current_theme.get("btn_add_hover", "#059669"),
        width=60,
        height=36,
        corner_radius=980,
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

    nav_bg = app.current_theme.get("nav_bg", "#6366f1")
    nav_fg = app.current_theme.get("nav_fg", "#ffffff")
    nav_hover = app.current_theme.get("nav_hover", "#4f46e5")
    accent = app.current_theme.get("accent", "#10b981")
    accent_hover = app.current_theme.get("accent_hover", "#059669")
    ctk.CTkButton(
        actions_row,
        text="Reload (RFID)",
        command=app.reload_card_flow,
        font=app._ui_font_button,
        fg_color=nav_bg,
        hover_color=nav_hover,
        text_color=nav_fg,
        corner_radius=980,
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
        corner_radius=980,
        height=36,
    ).pack(side=tk.LEFT, padx=6)
    ctk.CTkButton(
        actions_row,
        text="Report",
        command=lambda: bugreport.show_bug_report_screen(app, version=version, hover_scale_btn=hover_scale_btn),
        font=app._ui_font_body,
        fg_color="transparent",
        hover_color=app.current_theme.get("search_bg", "#f1f5f9"),
        text_color=app.current_theme.get("nav_bg", "#6366f1"),
        border_width=1,
        border_color=app.current_theme.get("nav_bg", "#6366f1"),
        corner_radius=980,
        height=36,
    ).pack(side=tk.LEFT, padx=6)
    ctk.CTkButton(
        actions_row,
        text="How to use?",
        command=app.show_help_dialog,
        font=app._ui_font_body,
        fg_color="transparent",
        hover_color=app.current_theme.get("search_bg", "#f1f5f9"),
        text_color=app.current_theme.get("nav_bg", "#6366f1"),
        border_width=1,
        border_color=app.current_theme.get("nav_bg", "#6366f1"),
        corner_radius=980,
        height=36,
    ).pack(side=tk.LEFT, padx=6)
    ctk.CTkButton(
        actions_row,
        text="Patch Notes",
        command=app.show_patch_notes_dialog,
        font=app._ui_font_body,
        fg_color="transparent",
        hover_color=app.current_theme.get("search_bg", "#f1f5f9"),
        text_color=app.current_theme.get("nav_bg", "#6366f1"),
        border_width=1,
        border_color=app.current_theme.get("nav_bg", "#6366f1"),
        corner_radius=980,
        height=36,
    ).pack(side=tk.LEFT, padx=6)

    app.add_ph_datetime_label(info_row)
    ctk.CTkLabel(
        info_row,
        text=f"SyntaxError™  ·  {version}",
        font=app._ui_font_small,
        text_color=app.current_theme.get("muted", app.current_theme["fg"]),
    ).pack(side=tk.LEFT, padx=(12, 8))
