import sys
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

# ──────────────────────────────────────────────
#  Explicit mapping: database product name → image filename
# ──────────────────────────────────────────────
PRODUCT_IMAGE_MAP = {
    "alcohol":              "GreenCross.png",
    "all night pads":       "All_Night_Pads.png",
    "panty liners":         "Panty_Liners.png",
    "regular w/ wings pads": "Regular_W_Wings_Pads.png",
    "regular w wings pads": "Regular_W_Wings_Pads.png",
    "napkin w/ wings":      "Regular_W_Wings_Pads.png",
    "napkin w wings":       "Regular_W_Wings_Pads.png",
    "napkin with wings":    "Regular_W_Wings_Pads.png",
    "non-wing pads":        "Non_Wing_Pads.png",
    "napkin w/o wings":     "Non_Wing_Pads.png",
    "napkin w o wings":     "Non_Wing_Pads.png",
    "napkin without wings": "Non_Wing_Pads.png",
    "mouthwash":            "Mouthwash.png",
    "tissues":              "Tissue.png",
    "wet wipes":            "Wet_Wipes.png",
    "deodorant":            "Deodorant.png",
    "soap":                 "Soap.png",
}

# ──────────────────────────────────────────────
#  Product descriptions (shown in detail modal)
# ──────────────────────────────────────────────
PRODUCT_DESCRIPTIONS = {
    "all night pads": (
        "Designed for overnight protection, these pads offer extra length and absorbency "
        "so you can sleep comfortably without worrying about leaks. Perfect for heavy flow nights."
    ),
    "panty liners": (
        "Ultra-thin and breathable, panty liners keep you feeling fresh and dry throughout the day. "
        "Ideal for light days, daily discharge, or as backup protection."
    ),
    "regular w/ wings pads": (
        "Wings wrap around your underwear for a secure, no-shift fit during daily activities. "
        "Offers reliable absorbency and comfort for regular flow days."
    ),
    "napkin w/ wings": (
        "Wings wrap around your underwear for a secure, no-shift fit during daily activities. "
        "Offers reliable absorbency and comfort for regular flow days."
    ),
    "non-wing pads": (
        "A simple, comfortable pad for light to regular flow. Easy to use and discreet, "
        "perfect for everyday protection when you need it most."
    ),
    "napkin w/o wings": (
        "A simple, comfortable pad for light to regular flow. Easy to use and discreet, "
        "perfect for everyday protection when you need it most."
    ),
    "alcohol": (
        "70% isopropyl alcohol — the gold standard for hand sanitizing. Kills 99.9% of bacteria "
        "and most viruses. Keep your hands clean anytime soap and water aren't available."
    ),
    "mouthwash": (
        "Freshen your breath and kill odor-causing bacteria with antiseptic mouthwash. "
        "Helps prevent gum disease and tooth decay when used as part of your daily oral care routine."
    ),
    "tissues": (
        "Soft, disposable tissues for sneezing, coughing, or wiping your hands. "
        "Always carry tissues to cover your mouth and prevent the spread of germs."
    ),
    "wet wipes": (
        "Pre-moistened wipes for quick clean-up on the go. Great for wiping hands, face, or surfaces "
        "when soap and water aren't available. Gentle on skin, tough on germs."
    ),
    "deodorant": (
        "Stay fresh and confident all day with roll-on deodorant. Controls sweat and odor "
        "so you can go about your daily activities feeling clean and comfortable."
    ),
    "soap": (
        "Antibacterial soap removes dirt, bacteria, and viruses from your hands effectively. "
        "Lather for at least 20 seconds—especially after using the restroom and before eating."
    ),
}

# ──────────────────────────────────────────────
#  Promotional carousel messages
# ──────────────────────────────────────────────
PROMO_MESSAGES = [
    "🌟  Stay fresh all day — try our Deodorant & Mouthwash!",
    "🩹  Period essentials in stock — All Night Pads, Panty Liners & more!",
    "🧼  Cleanliness is next to greatness — grab Soap, Alcohol & Wet Wipes!",
    "💚  Hygiene made easy — affordable prices, one tap away!",
]


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


_RESAMPLE = None
if _HAS_PIL:
    _RESAMPLE = getattr(Image, "Resampling", Image).LANCZOS


def _pil_square_rgba_to_ctk(pil_src, box: int) -> ctk.CTkImage:
    """RGB CTkImage on a square canvas — avoids RGBA display issues on some Linux/Tk builds."""
    if not _HAS_PIL or _RESAMPLE is None:
        raise RuntimeError("Pillow is required for _pil_square_rgba_to_ctk")
    pil_img = pil_src.convert("RGBA")
    pil_img.thumbnail((box, box), _RESAMPLE)
    square = Image.new("RGBA", (box, box), (0, 0, 0, 0))
    ox = (box - pil_img.width) // 2
    oy = (box - pil_img.height) // 2
    square.paste(pil_img, (ox, oy), pil_img)
    rgb = Image.new("RGB", (box, box), (255, 255, 255))
    rgb.paste(square, mask=square.split()[3])
    return ctk.CTkImage(light_image=rgb, dark_image=rgb, size=(box, box))


def _load_product_image_tk(product_name: str, max_px: int) -> tk.PhotoImage | None:
    """Fallback when Pillow is missing (install `pillow` on the Pi for best results)."""
    img_path = _resolve_product_image_path(product_name)
    if not img_path:
        return None
    suf = img_path.suffix.lower()
    if suf not in (".png", ".gif", ".pgm", ".ppm"):
        return None
    try:
        ph = tk.PhotoImage(file=str(img_path))
        while max(ph.width(), ph.height()) > max_px:
            ph = ph.subsample(2, 2)
        return ph
    except Exception:
        return None


def _load_uniform_image(product_name, size=140):
    """Load a product image and force it into a uniform square with padding."""
    if not _HAS_PIL:
        return None

    cache_key = (product_name, size)
    if cache_key in _product_image_cache:
        return _product_image_cache[cache_key]

    img_path = _resolve_product_image_path(product_name)
    if not img_path:
        return None

    try:
        pil_img = Image.open(str(img_path)).convert("RGBA")

        # Resize to fit within size×size, maintaining aspect ratio
        pil_img.thumbnail((size, size), _RESAMPLE)

        # Create a transparent square canvas and paste centered
        canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        offset_x = (size - pil_img.width) // 2
        offset_y = (size - pil_img.height) // 2
        canvas.paste(pil_img, (offset_x, offset_y), pil_img)

        tk_img = ImageTk.PhotoImage(canvas)
        _product_image_cache[cache_key] = tk_img
        return tk_img
    except Exception:
        return None


# ══════════════════════════════════════════════
#  HEADER  (with breadcrumb + chatbot button)
# ══════════════════════════════════════════════

def build_main_menu_header(app, parent, *, ui_font, ui_font_title, ui_font_small):
    top = ctk.CTkFrame(parent, fg_color=app.current_theme["bg"], corner_radius=0)
    top.pack(side=tk.TOP, fill=tk.X)

    header = ctk.CTkFrame(top, fg_color=app.current_theme["bg"], corner_radius=0)
    header.pack(side=tk.TOP, fill=tk.X, pady=(2, 4), padx=10)

    # ── Left: Brand title ──
    title_block = ctk.CTkFrame(header, fg_color=app.current_theme["bg"], corner_radius=0)
    title_block.pack(side=tk.LEFT)
    ctk.CTkLabel(
        title_block,
        text="SyntaxError™",
        font=(ui_font, 20, "bold"),
        text_color=app.current_theme.get("nav_bg", "#8E4585"),
    ).pack(anchor="w")
    ctk.CTkLabel(
        title_block,
        text="Step 1 of 3  ·  Choose Products",
        font=(ui_font, 11),
        text_color=app.current_theme.get("muted", app.current_theme["fg"]),
    ).pack(anchor="w")

    # ── Right: Actions ──
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

    chatbot_btn = ctk.CTkButton(
        icons_frame,
        text="🤖 Ask Hygiene Hero",
        command=app.show_chatbot_screen,
        font=(ui_font, 14, "bold"),
        fg_color=app.current_theme.get("accent", "#50C878"),
        hover_color=app.current_theme.get("accent_hover", "#3DA863"),
        text_color="#ffffff",
        corner_radius=980,
        height=36,
    )
    chatbot_btn.pack(side=tk.RIGHT, padx=12, pady=0)

    app.create_theme_slider(icons_frame).pack(side=tk.RIGHT, padx=6, pady=0)


# ══════════════════════════════════════════════
#  PROMOTIONAL CAROUSEL  (auto-cycling banner)
# ══════════════════════════════════════════════

def build_promo_carousel(app, parent, *, grid_kw=None):
    """Auto-scrolling promotional banner above the product grid."""
    carousel_frame = ctk.CTkFrame(
        parent,
        fg_color=app.current_theme.get("nav_bg", "#8E4585"),
        corner_radius=12,
        height=48,
    )
    if grid_kw is not None:
        carousel_frame.grid(**grid_kw)
    else:
        carousel_frame.pack(fill=tk.X, padx=12, pady=(6, 8))
    carousel_frame.pack_propagate(False)

    promo_var = tk.StringVar(value=PROMO_MESSAGES[0])
    promo_label = ctk.CTkLabel(
        carousel_frame,
        textvariable=promo_var,
        font=(app._ui_font_name, 13, "bold"),
        text_color="#FFFFFF",
        anchor="center",
    )
    promo_label.pack(expand=True, fill=tk.BOTH, padx=16, pady=8)

    app._promo_index = 0

    def _cycle_promo():
        if not carousel_frame.winfo_exists():
            return
        app._promo_index = (app._promo_index + 1) % len(PROMO_MESSAGES)
        promo_var.set(PROMO_MESSAGES[app._promo_index])
        carousel_frame.after(4000, _cycle_promo)

    carousel_frame.after(4000, _cycle_promo)


# ══════════════════════════════════════════════
#  PRODUCT DETAIL MODAL  (pops up on card tap)
# ══════════════════════════════════════════════

def _show_product_detail_modal(app, product):
    """Full-screen overlay showing product details with Add to Cart."""
    overlay = ctk.CTkFrame(
        app.content_holder,
        fg_color=app.current_theme["bg"],
        corner_radius=0,
    )
    overlay.place(relx=0, rely=0, relwidth=1, relheight=1)

    def _close():
        overlay.destroy()

    # ── Top bar ──
    top_bar = ctk.CTkFrame(overlay, fg_color=app.current_theme["bg"], corner_radius=0)
    top_bar.pack(fill=tk.X, padx=16, pady=(12, 0))

    ctk.CTkButton(
        top_bar,
        text="← Back",
        font=(app._ui_font_name, 13, "bold"),
        fg_color="transparent",
        hover_color=app.current_theme["button_bg"],
        text_color=app.current_theme.get("nav_bg", "#8E4585"),
        corner_radius=8,
        height=36,
        command=_close,
    ).pack(side=tk.LEFT)

    ctk.CTkLabel(
        top_bar,
        text="Product Details",
        font=(app._ui_font_name, 16, "bold"),
        text_color=app.current_theme["fg"],
    ).pack(side=tk.LEFT, padx=12)

    # ── Scrollable content (responsive for small screens) ──
    scroll_body = ctk.CTkScrollableFrame(
        overlay,
        fg_color=app.current_theme["bg"],
        corner_radius=0,
    )
    scroll_body.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

    # ── Image ──
    img_holder = ctk.CTkFrame(
        scroll_body,
        fg_color=app.current_theme.get("card_bg", "#FFFFFF"),
        corner_radius=16,
        border_width=2,
        border_color=app.current_theme.get("card_border", "#E8E5F0"),
    )
    img_holder.pack(pady=(16, 12), padx=40)

    preview_bg = app.current_theme.get("card_bg", "#FFFFFF")
    detail_img_ok = False
    if _HAS_PIL:
        try:
            img_path = _resolve_product_image_path(product["name"])
            if img_path:
                pil_img = Image.open(str(img_path)).convert("RGBA")
                ctk_img = _pil_square_rgba_to_ctk(pil_img, 200)
                lbl = ctk.CTkLabel(img_holder, image=ctk_img, text="", fg_color="transparent")
                lbl._ctk_img_ref = ctk_img
                lbl.pack(padx=20, pady=20)
                detail_img_ok = True
        except Exception as ex:
            print(
                f"[UI] Detail modal image failed for {product.get('name')!r}: {ex}",
                file=sys.stderr,
            )
    if not detail_img_ok:
        tkph = _load_product_image_tk(product["name"], 200)
        if tkph is not None:
            lbl = tk.Label(
                img_holder,
                image=tkph,
                bd=0,
                bg=preview_bg,
                highlightthickness=0,
            )
            lbl.tk_img_ref = tkph
            lbl.pack(padx=20, pady=20)
            detail_img_ok = True
    if not detail_img_ok:
        ctk.CTkLabel(img_holder, text="\U0001f5bc\ufe0f", font=(app._ui_font_name, 48)).pack(padx=20, pady=20)

    # ── Product info ──
    ctk.CTkLabel(
        scroll_body,
        text=product["name"],
        font=(app._ui_font_name, 22, "bold"),
        text_color=app.current_theme["fg"],
    ).pack(pady=(4, 2))

    ctk.CTkLabel(
        scroll_body,
        text=f"\u20b1{product['price']:.2f}",
        font=(app._ui_font_name, 20, "bold"),
        text_color=app.current_theme.get("price_color", "#8E4585"),
    ).pack(pady=(0, 6))

    details_text = (product.get("details") or "").strip() if hasattr(product, "get") else ""
    if details_text:
        ctk.CTkLabel(
            scroll_body,
            text=details_text,
            font=(app._ui_font_name, 12),
            text_color=app.current_theme.get("muted", "#7A7491"),
            wraplength=520,
            justify="center",
        ).pack(pady=(0, 10))

    stock_text = f"In Stock: {product['current_stock']}" if product["current_stock"] > 0 else "Out of Stock"
    stock_color = app.current_theme.get("accent", "#50C878") if product["current_stock"] > 0 else app.current_theme.get("status_error", "#E74C3C")
    ctk.CTkLabel(
        scroll_body,
        text=stock_text,
        font=(app._ui_font_name, 13),
        text_color=stock_color,
    ).pack(pady=(0, 8))

    # ── Product description (how it helps the user) ──
    desc = PRODUCT_DESCRIPTIONS.get(product["name"].strip().lower(), "")
    if desc:
        desc_card = ctk.CTkFrame(
            scroll_body,
            fg_color=app.current_theme.get("card_bg", "#FFFFFF"),
            corner_radius=12,
            border_width=1,
            border_color=app.current_theme.get("card_border", "#E8E5F0"),
        )
        desc_card.pack(fill=tk.X, padx=40, pady=(0, 12))

        ctk.CTkLabel(
            desc_card,
            text="\U0001f4a1 How this helps you",
            font=(app._ui_font_name, 13, "bold"),
            text_color=app.current_theme.get("accent", "#50C878"),
            anchor="w",
        ).pack(padx=16, pady=(12, 4), anchor="w")

        ctk.CTkLabel(
            desc_card,
            text=desc,
            font=(app._ui_font_name, 12),
            text_color=app.current_theme.get("muted", "#7A7491"),
            wraplength=400,
            justify="left",
            anchor="w",
        ).pack(padx=16, pady=(0, 12), anchor="w")

    # ── Action buttons ──
    btn_row = ctk.CTkFrame(overlay, fg_color=app.current_theme["bg"], corner_radius=0)
    btn_row.pack(fill=tk.X, padx=40, pady=(0, 16))

    in_cart = app._cart_has_product(product)

    if in_cart:
        ctk.CTkButton(
            btn_row,
            text="✕  Remove from Cart",
            font=(app._ui_font_name, 15, "bold"),
            fg_color=app.current_theme.get("btn_remove", "#E74C3C"),
            hover_color=app.current_theme.get("btn_remove_hover", "#C0392B"),
            text_color="#ffffff",
            corner_radius=14,
            height=48,
            command=lambda: (app._remove_product_from_cart(product), _close()),
        ).pack(fill=tk.X, pady=4)
    else:
        ctk.CTkButton(
            btn_row,
            text="＋  Add to Cart",
            font=(app._ui_font_name, 15, "bold"),
            fg_color=app.current_theme.get("btn_add", "#50C878"),
            hover_color=app.current_theme.get("btn_add_hover", "#3DA863"),
            text_color="#ffffff",
            corner_radius=14,
            height=48,
            state=tk.NORMAL if product["current_stock"] > 0 else tk.DISABLED,
            command=lambda: (app._add_product_to_cart(product), _close()),
        ).pack(fill=tk.X, pady=4)

    ctk.CTkButton(
        btn_row,
        text="Cancel",
        font=(app._ui_font_name, 13),
        fg_color="transparent",
        hover_color=app.current_theme["button_bg"],
        text_color=app.current_theme.get("muted", "#7A7491"),
        border_width=1,
        border_color=app.current_theme.get("card_border", "#E8E5F0"),
        corner_radius=14,
        height=40,
        command=_close,
    ).pack(fill=tk.X, pady=4)


# ══════════════════════════════════════════════
#  PRODUCT GRID  (2.5D cards, uniform images)
# ══════════════════════════════════════════════

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

    # Carousel scrolls with the grid so touch / wheel gestures apply to one surface.
    build_promo_carousel(
        app,
        scroll_frame,
        grid_kw={
            "row": 0,
            "column": 0,
            "columnspan": 2,
            "sticky": "ew",
            "padx": 12,
            "pady": (6, 8),
        },
    )

    app._cart_card_bg = app.current_theme.get("card_bg", app.current_theme["button_bg"])
    app._cart_card_border = app.current_theme.get("card_border", "#E8E5F0")
    app._cart_selected_bg = app.current_theme.get("selected_bg", "#D5F5E3")
    app._cart_selected_border = app.current_theme.get("selected_border", app.current_theme.get("accent", "#50C878"))
    app._product_placeholder_bg = "#F0EFF4" if app.current_theme_name == "light" else "#242440"
    app._product_placeholder_size = 160
    app._product_card_refs = {}

    for idx, product in enumerate(products):
        build_product_card(app, grid, product, idx)


def build_product_card(app, grid, product, idx):
    in_cart = app._cart_has_product(product)
    row_index, column_index = idx // 2 + 1, idx % 2

    # 2.5D card: thicker border, larger corner radius, soft shadow effect
    card = ctk.CTkFrame(
        grid,
        fg_color=app._cart_selected_bg if in_cart else app._cart_card_bg,
        border_width=3 if in_cart else 2,
        border_color=app._cart_selected_border if in_cart else app._cart_card_border,
        corner_radius=18,
    )
    card.grid(row=row_index, column=column_index, padx=10, pady=8, sticky="nsew")

    # Make card clickable → product detail modal
    def _on_card_tap(event=None, p=product):
        _show_product_detail_modal(app, p)

    card.bind("<Button-1>", _on_card_tap)

    # ── Product image (uniform size) ──
    placeholder = ctk.CTkFrame(
        card,
        fg_color=app._product_placeholder_bg,
        width=app._product_placeholder_size,
        height=app._product_placeholder_size,
        corner_radius=12,
    )
    placeholder.pack(pady=(12, 8), padx=12, fill=tk.NONE)
    placeholder.pack_propagate(False)
    placeholder.bind("<Button-1>", _on_card_tap)

    sz = app._product_placeholder_size - 20
    image_placed = False
    if _HAS_PIL:
        try:
            img_path = _resolve_product_image_path(product["name"])
            if img_path:
                pil_img = Image.open(str(img_path)).convert("RGBA")
                ctk_img = _pil_square_rgba_to_ctk(pil_img, sz)
                img_label = ctk.CTkLabel(
                    placeholder, image=ctk_img, text="", fg_color="transparent",
                )
                img_label._ctk_img_ref = ctk_img
                img_label.place(relx=0.5, rely=0.5, anchor="center")
                img_label.bind("<Button-1>", _on_card_tap)
                image_placed = True
        except Exception as ex:
            print(
                f"[UI] Product card image failed for {product.get('name')!r}: {ex}",
                file=sys.stderr,
            )
    if not image_placed:
        tkph = _load_product_image_tk(product["name"], sz)
        if tkph is not None:
            lbl = tk.Label(
                placeholder,
                image=tkph,
                bd=0,
                bg=app._product_placeholder_bg,
                highlightthickness=0,
            )
            lbl.tk_img_ref = tkph
            lbl.place(relx=0.5, rely=0.5, anchor="center")
            lbl.bind("<Button-1>", _on_card_tap)

    # ── Product name ──
    name_text = product["name"]
    if len(name_text) > 20:
        name_text = name_text[:20] + "…"
    name_label = ctk.CTkLabel(
        card,
        text=name_text,
        font=(app._ui_font_name, 13, "bold"),
        text_color=app.current_theme["fg"],
        wraplength=app._product_placeholder_size + 40,
        justify="center",
    )
    name_label.pack(padx=8, pady=(0, 2))
    name_label.bind("<Button-1>", _on_card_tap)

    # ── Price (plum colored) ──
    price_label = ctk.CTkLabel(
        card,
        text=f"₱{product['price']:.2f}",
        font=(app._ui_font_name, 14, "bold"),
        text_color=app.current_theme.get("price_color", "#8E4585"),
    )
    price_label.pack(pady=(0, 6))
    price_label.bind("<Button-1>", _on_card_tap)

    # ── Stock indicator ──
    if product["current_stock"] <= 0:
        ctk.CTkLabel(
            card,
            text="Out of Stock",
            font=(app._ui_font_name, 10),
            text_color=app.current_theme.get("status_error", "#E74C3C"),
        ).pack(pady=(0, 4))

    # ── Quick-add button ──
    action_btn = build_product_card_button(app, card, product, in_cart)
    action_btn.pack(pady=(2, 14))
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
            text="✕  Remove",
            font=(app._ui_font_name, 12, "bold"),
            text_color="#ffffff",
            fg_color=app.current_theme.get("btn_remove", "#E74C3C"),
            hover_color=app.current_theme.get("btn_remove_hover", "#C0392B"),
            width=100,
            height=36,
            corner_radius=980,
            command=lambda prod=product: app._remove_product_from_cart(prod),
        )

    action_btn = ctk.CTkButton(
        card,
        text="＋  Add",
        font=(app._ui_font_name, 12, "bold"),
        text_color="#ffffff",
        fg_color=app.current_theme.get("btn_add", "#50C878"),
        hover_color=app.current_theme.get("btn_add_hover", "#3DA863"),
        width=100,
        height=36,
        corner_radius=980,
        state=tk.NORMAL if product["current_stock"] > 0 else tk.DISABLED,
        command=lambda prod=product: app._add_product_to_cart(prod),
    )
    action_btn._product_add_btn = True
    return action_btn


# ══════════════════════════════════════════════
#  FOOTER  (navigation buttons + info bar)
# ══════════════════════════════════════════════

def build_main_menu_footer(app, *, version, hover_scale_btn):
    bottom = ctk.CTkFrame(app.content_holder, fg_color=app.current_theme["bg"], corner_radius=0)
    bottom.pack(side=tk.BOTTOM, fill=tk.X, pady=(6, 8))
    actions_row = ctk.CTkFrame(bottom, fg_color=app.current_theme["bg"], corner_radius=0)
    actions_row.pack(side=tk.TOP, fill=tk.X)
    info_row = ctk.CTkFrame(bottom, fg_color=app.current_theme["bg"], corner_radius=0)
    info_row.pack(side=tk.TOP, fill=tk.X, pady=(6, 0))

    nav_bg = app.current_theme.get("nav_bg", "#8E4585")
    nav_fg = app.current_theme.get("nav_fg", "#ffffff")
    nav_hover = app.current_theme.get("nav_hover", "#723670")
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
        text="Report",
        command=lambda: bugreport.show_bug_report_screen(app, version=version, hover_scale_btn=hover_scale_btn),
        font=app._ui_font_body,
        fg_color="transparent",
        hover_color=app.current_theme.get("search_bg", "#F0EFF4"),
        text_color=app.current_theme.get("nav_bg", "#8E4585"),
        border_width=1,
        border_color=app.current_theme.get("nav_bg", "#8E4585"),
        corner_radius=980,
        height=36,
    ).pack(side=tk.LEFT, padx=6)
    ctk.CTkButton(
        actions_row,
        text="How to use?",
        command=app.show_help_dialog,
        font=app._ui_font_body,
        fg_color="transparent",
        hover_color=app.current_theme.get("search_bg", "#F0EFF4"),
        text_color=app.current_theme.get("nav_bg", "#8E4585"),
        border_width=1,
        border_color=app.current_theme.get("nav_bg", "#8E4585"),
        corner_radius=980,
        height=36,
    ).pack(side=tk.LEFT, padx=6)
    ctk.CTkButton(
        actions_row,
        text="Patch Notes",
        command=app.show_patch_notes_dialog,
        font=app._ui_font_body,
        fg_color="transparent",
        hover_color=app.current_theme.get("search_bg", "#F0EFF4"),
        text_color=app.current_theme.get("nav_bg", "#8E4585"),
        border_width=1,
        border_color=app.current_theme.get("nav_bg", "#8E4585"),
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
