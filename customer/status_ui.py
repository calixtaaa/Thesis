import customtkinter as ctk


def build_wait_screen_content(app, text):
    frame = ctk.CTkFrame(app.content_holder, fg_color=app.current_theme["bg"], corner_radius=0)
    frame.pack(expand=True, fill="both")
    card = ctk.CTkFrame(
        frame,
        fg_color=app.current_theme.get("card_bg", app.current_theme["button_bg"]),
        border_width=1,
        border_color=app.current_theme.get("card_border", "#e2e8f0"),
        corner_radius=16,
    )
    card.place(relx=0.5, rely=0.5, anchor="center")

    ctk.CTkLabel(
        card,
        text=text,
        font=app._ui_font_bold,
        text_color=app.current_theme["fg"],
        justify="center",
        wraplength=520,
    ).pack(pady=(36, 12), padx=40)

    ctk.CTkLabel(
        card,
        text="Please wait...",
        font=app._ui_font_body,
        text_color=app.current_theme.get("muted", app.current_theme["fg"]),
    ).pack(pady=(0, 28), padx=40)


def build_dispensing_screen_content(app):
    frame = ctk.CTkFrame(app.content_holder, fg_color=app.current_theme["bg"], corner_radius=0)
    frame.pack(expand=True, fill="both")
    card = ctk.CTkFrame(
        frame,
        fg_color=app.current_theme.get("card_bg", app.current_theme["button_bg"]),
        border_width=2,
        border_color=app.current_theme.get("accent", "#1A948E"),
        corner_radius=16,
    )
    card.place(relx=0.5, rely=0.5, anchor="center")

    ctk.CTkLabel(
        card,
        text="⏳  Dispensing product...",
        font=app._ui_font_title,
        text_color=app.current_theme.get("accent", "#1A948E"),
    ).pack(pady=(32, 8), padx=52)

    ctk.CTkLabel(
        card,
        text="Please wait - do not remove items\nuntil the machine finishes.",
        font=app._ui_font_body,
        text_color=app.current_theme["fg"],
        justify="center",
    ).pack(pady=(0, 32), padx=52)


def build_success_screen_content(app, title, message, on_ok=None):
    frame = ctk.CTkFrame(app.content_holder, fg_color=app.current_theme["bg"], corner_radius=0)
    frame.pack(expand=True, fill="both")
    card = ctk.CTkFrame(
        frame,
        fg_color=app.current_theme.get("card_bg", app.current_theme["button_bg"]),
        border_width=2,
        border_color=app.current_theme.get("accent", "#1A948E"),
        corner_radius=12,
    )
    card.place(relx=0.5, rely=0.5, anchor="center")

    ctk.CTkLabel(
        card,
        text=title,
        font=app._ui_font_title,
        text_color=app.current_theme.get("accent", "#1A948E"),
        justify="center",
        wraplength=520,
    ).pack(pady=(20, 8), padx=32)

    ctk.CTkLabel(
        card,
        text=message,
        font=app._ui_font_body,
        text_color=app.current_theme["fg"],
        justify="center",
        wraplength=520,
    ).pack(padx=32, pady=(0, 20))

    ctk.CTkButton(
        card,
        text="OK",
        font=app._ui_font_button,
        command=on_ok or app.build_main_menu,
        fg_color=app.current_theme.get("accent", "#1A948E"),
        hover_color=app.current_theme.get("accent_hover", "#15857B"),
        text_color="#ffffff",
        corner_radius=10,
        width=120,
        height=40,
    ).pack(pady=(0, 20))
