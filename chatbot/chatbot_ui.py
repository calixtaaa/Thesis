"""
Hygiene Hero — Chatbot UI for the vending machine (CustomTkinter).

Renders a beautiful chat interface with:
  • A cute robot avatar drawn on a Canvas (no external image required)
  • Typing indicator animation
  • Scrollable message bubbles
  • Quick-action suggestion chips
  • Full theme support (light/dark)
"""

import tkinter as tk
import time
import threading
import customtkinter as ctk
from pathlib import Path

from chatbot.engine import HygieneHeroBot

BASE_DIR = Path(__file__).resolve().parents[1]

# ── Singleton bot instance ────────────────────
_bot = HygieneHeroBot()


def _draw_robot_avatar(canvas, cx, cy, size=40, theme_name="light"):
    """Draw a cute robot mascot directly on a Canvas. No image file needed."""
    s = size
    half = s // 2

    # Colors
    if theme_name == "dark":
        body_color = "#22d3ee"
        face_color = "#0e7490"
        eye_color = "#ffffff"
        pupil_color = "#0f172a"
        mouth_color = "#ffffff"
        antenna_color = "#67e8f9"
        cheek_color = "#f472b6"
        outline_color = "#06b6d4"
    else:
        body_color = "#10b981"
        face_color = "#059669"
        eye_color = "#ffffff"
        pupil_color = "#0f172a"
        mouth_color = "#ffffff"
        antenna_color = "#34d399"
        cheek_color = "#f472b6"
        outline_color = "#047857"

    # Antenna stalk
    canvas.create_line(
        cx, cy - half + 2, cx, cy - half - 8,
        fill=antenna_color, width=2,
    )
    # Antenna bulb
    canvas.create_oval(
        cx - 4, cy - half - 12, cx + 4, cy - half - 4,
        fill=antenna_color, outline=outline_color, width=1,
    )

    # Head (rounded rectangle via oval)
    head_top = cy - half + 2
    head_bottom = cy + 4
    head_left = cx - half + 4
    head_right = cx + half - 4
    canvas.create_oval(
        head_left, head_top, head_right, head_bottom,
        fill=body_color, outline=outline_color, width=2,
    )

    # Face plate (inner area)
    face_pad = 6
    canvas.create_oval(
        head_left + face_pad, head_top + face_pad,
        head_right - face_pad, head_bottom - face_pad,
        fill=face_color, outline="", width=0,
    )

    # Eyes
    eye_y = head_top + (head_bottom - head_top) // 2 - 2
    eye_r = 5
    # Left eye (white)
    canvas.create_oval(
        cx - 10 - eye_r, eye_y - eye_r,
        cx - 10 + eye_r, eye_y + eye_r,
        fill=eye_color, outline="",
    )
    # Left pupil
    canvas.create_oval(
        cx - 10 - 2, eye_y - 2,
        cx - 10 + 2, eye_y + 2,
        fill=pupil_color, outline="",
    )
    # Right eye (white)
    canvas.create_oval(
        cx + 10 - eye_r, eye_y - eye_r,
        cx + 10 + eye_r, eye_y + eye_r,
        fill=eye_color, outline="",
    )
    # Right pupil
    canvas.create_oval(
        cx + 10 - 2, eye_y - 2,
        cx + 10 + 2, eye_y + 2,
        fill=pupil_color, outline="",
    )

    # Mouth (cute smile arc)
    mouth_y = eye_y + 8
    canvas.create_arc(
        cx - 7, mouth_y - 4, cx + 7, mouth_y + 4,
        start=200, extent=140,
        style=tk.ARC, outline=mouth_color, width=2,
    )

    # Cheeks (blush)
    canvas.create_oval(
        cx - 17, eye_y + 2, cx - 13, eye_y + 6,
        fill=cheek_color, outline="",
    )
    canvas.create_oval(
        cx + 13, eye_y + 2, cx + 17, eye_y + 6,
        fill=cheek_color, outline="",
    )

    # Body (small rectangle below head)
    body_top = head_bottom - 2
    body_bottom = cy + half - 2
    body_left = cx - half + 10
    body_right = cx + half - 10
    canvas.create_rectangle(
        body_left, body_top, body_right, body_bottom,
        fill=body_color, outline=outline_color, width=2,
    )

    # Medical cross on body
    cross_cy = (body_top + body_bottom) // 2
    canvas.create_rectangle(
        cx - 3, cross_cy - 6, cx + 3, cross_cy + 6,
        fill=eye_color, outline="",
    )
    canvas.create_rectangle(
        cx - 6, cross_cy - 3, cx + 6, cross_cy + 3,
        fill=eye_color, outline="",
    )

    # Arms (small stubs)
    canvas.create_rectangle(
        body_left - 6, body_top + 4, body_left, body_bottom - 4,
        fill=body_color, outline=outline_color, width=1,
    )
    canvas.create_rectangle(
        body_right, body_top + 4, body_right + 6, body_bottom - 4,
        fill=body_color, outline=outline_color, width=1,
    )


def build_chatbot_screen(app):
    """Build the full chatbot screen inside app.content_holder."""
    app._current_screen_builder = lambda: build_chatbot_screen(app)

    if app.sidebar_holder is not None and app.sidebar_holder.winfo_exists():
        app.sidebar_holder.destroy()
        app.sidebar_holder = None
    app.clear_screen()
    app.content_holder.configure(fg_color=app.current_theme["bg"])

    theme = app.current_theme
    theme_name = app.current_theme_name
    ui_font = app._ui_font_name

    # Reset bot conversation for fresh start each time
    _bot.reset()

    # ── Main container ────────────────────────
    main_frame = ctk.CTkFrame(app.content_holder, fg_color=theme["bg"], corner_radius=0)
    main_frame.pack(expand=True, fill=tk.BOTH)

    # ── Top bar ───────────────────────────────
    top_bar = ctk.CTkFrame(main_frame, fg_color=theme["bg"], corner_radius=0, height=56)
    top_bar.pack(side=tk.TOP, fill=tk.X, padx=0, pady=0)
    top_bar.pack_propagate(False)

    # Back button
    ctk.CTkButton(
        top_bar,
        text="← Back",
        font=(ui_font, 12, "bold"),
        command=app.build_main_menu,
        fg_color=theme.get("nav_bg", "#6366f1"),
        hover_color=theme.get("nav_hover", "#4f46e5"),
        text_color=theme.get("nav_fg", "#ffffff"),
        corner_radius=980,
        width=90,
        height=34,
    ).pack(side=tk.LEFT, padx=(12, 8), pady=10)

    # Robot avatar in header
    avatar_canvas = tk.Canvas(
        top_bar, width=44, height=44,
        bg=theme["bg"], highlightthickness=0, bd=0,
    )
    avatar_canvas.pack(side=tk.LEFT, padx=(4, 6), pady=6)
    _draw_robot_avatar(avatar_canvas, 22, 22, size=40, theme_name=theme_name)

    # Title
    title_block = ctk.CTkFrame(top_bar, fg_color=theme["bg"], corner_radius=0)
    title_block.pack(side=tk.LEFT, padx=(0, 8), pady=6)
    ctk.CTkLabel(
        title_block,
        text="Hygiene Hero",
        font=(ui_font, 15, "bold"),
        text_color=theme["fg"],
    ).pack(anchor="w")
    ctk.CTkLabel(
        title_block,
        text="Your friendly AI assistant • Offline",
        font=(ui_font, 9),
        text_color=theme.get("muted", theme["fg"]),
    ).pack(anchor="w")

    # Online status dot
    status_dot = tk.Canvas(
        top_bar, width=12, height=12,
        bg=theme["bg"], highlightthickness=0, bd=0,
    )
    status_dot.pack(side=tk.LEFT, padx=(0, 4), pady=18)
    status_dot.create_oval(2, 2, 10, 10, fill="#22c55e", outline="#16a34a", width=1)

    # ── Separator ─────────────────────────────
    sep = ctk.CTkFrame(main_frame, fg_color=theme.get("card_border", "#e2e8f0"), height=1, corner_radius=0)
    sep.pack(fill=tk.X, padx=0)

    # ── Chat messages area ────────────────────
    chat_frame = ctk.CTkScrollableFrame(
        main_frame,
        fg_color=theme["bg"],
        corner_radius=0,
        scrollbar_button_color=theme.get("search_border", "#cbd5e1"),
        scrollbar_button_hover_color=theme.get("accent", "#10b981"),
    )
    chat_frame.pack(expand=True, fill=tk.BOTH, padx=0, pady=0)

    # ── Quick action chips ────────────────────
    chips_frame = ctk.CTkFrame(main_frame, fg_color=theme["bg"], corner_radius=0, height=44)
    chips_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=0, pady=(0, 0))
    chips_frame.pack_propagate(False)

    chips_inner = ctk.CTkFrame(chips_frame, fg_color=theme["bg"], corner_radius=0)
    chips_inner.pack(side=tk.LEFT, padx=8, pady=6)

    chip_suggestions = [
        ("🧴 Products", "What products do you sell?"),
        ("💡 Hygiene Tip", "Give me a hygiene tip"),
        ("🔬 70% vs 40%", "Why is 70% alcohol better than 40%?"),
        ("🔧 How to use", "How do I use the machine?"),
        ("🩹 First Aid", "How do I treat a wound?"),
    ]

    def send_chip(text):
        _process_user_message(text)

    for label, msg in chip_suggestions:
        ctk.CTkButton(
            chips_inner,
            text=label,
            font=(ui_font, 9, "bold"),
            fg_color=theme.get("card_bg", "#ffffff"),
            hover_color=theme.get("button_bg", "#f1f5f9"),
            text_color=theme.get("accent", "#10b981"),
            border_width=1,
            border_color=theme.get("card_border", "#e2e8f0"),
            corner_radius=980,
            height=28,
            width=0,
            command=lambda m=msg: send_chip(m),
        ).pack(side=tk.LEFT, padx=3)

    # ── Input bar ─────────────────────────────
    input_bar = ctk.CTkFrame(main_frame, fg_color=theme.get("card_bg", "#ffffff"), corner_radius=0, height=56)
    input_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=0, pady=0)
    input_bar.pack_propagate(False)

    input_entry = ctk.CTkEntry(
        input_bar,
        placeholder_text="Ask Hygiene Hero anything...",
        font=(ui_font, 12),
        fg_color=theme.get("search_bg", "#f1f5f9"),
        text_color=theme["fg"],
        placeholder_text_color=theme.get("muted", "#64748b"),
        border_color=theme.get("search_border", "#cbd5e1"),
        corner_radius=980,
        height=38,
    )
    input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(12, 8), pady=8)

    send_btn = ctk.CTkButton(
        input_bar,
        text="Send",
        font=(ui_font, 12, "bold"),
        fg_color=theme.get("accent", "#10b981"),
        hover_color=theme.get("accent_hover", "#059669"),
        text_color="#ffffff",
        corner_radius=980,
        width=72,
        height=38,
        command=lambda: _process_user_message(input_entry.get()),
    )
    send_btn.pack(side=tk.RIGHT, padx=(0, 12), pady=8)

    # ── Message rendering helpers ─────────────
    _message_widgets = []

    def _add_message_bubble(sender, text, animate=False):
        """Add a chat bubble to the scrollable chat area."""
        is_bot = sender == "bot"
        bubble_bg = theme.get("accent", "#50C878") if is_bot else theme.get("nav_bg", "#8E4585")
        text_color = "#ffffff"

        row = ctk.CTkFrame(chat_frame, fg_color=theme["bg"], corner_radius=0)
        row.pack(fill=tk.X, padx=0, pady=3)

        if is_bot:
            # Small robot icon next to bot messages
            mini_canvas = tk.Canvas(
                row, width=28, height=28,
                bg=theme["bg"], highlightthickness=0, bd=0,
            )
            mini_canvas.pack(side=tk.LEFT, padx=(12, 4), pady=(4, 0), anchor="n")
            _draw_robot_avatar(mini_canvas, 14, 14, size=24, theme_name=theme_name)

        bubble = ctk.CTkFrame(
            row,
            fg_color=bubble_bg,
            corner_radius=16,
        )
        if is_bot:
            bubble.pack(side=tk.LEFT, padx=(0, 60), pady=2, anchor="w")
        else:
            bubble.pack(side=tk.RIGHT, padx=(60, 12), pady=2, anchor="e")

        msg_label = ctk.CTkLabel(
            bubble,
            text=text,
            font=(ui_font, 11),
            text_color=text_color,
            wraplength=380,
            justify="left",
        )
        msg_label.pack(padx=14, pady=10)

        _message_widgets.append(row)

        # Scroll to bottom
        try:
            chat_frame._parent_canvas.yview_moveto(1.0)
        except Exception:
            pass

    def _add_follow_up_suggestions(response_text):
        """Add dynamic follow-up suggestion chips based on the bot's response."""
        suggestions = []
        resp_lower = response_text.lower()

        if any(w in resp_lower for w in ["product", "sell", "soap", "alcohol", "tissue", "mask", "tinda"]):
            suggestions = [
                ("💡 Hygiene Tip", "Give me a hygiene tip"),
                ("🔧 How to use", "How do I use the machine?"),
                ("🛒 What do you sell?", "What products do you sell?"),
            ]
        elif any(w in resp_lower for w in ["tip", "hygiene", "wash", "clean", "payo"]):
            suggestions = [
                ("💡 Another Tip", "Give me another hygiene tip"),
                ("🧴 Products", "What products do you sell?"),
                ("🔬 70% vs 40%", "Why is 70% alcohol better than 40%?"),
            ]
        elif any(w in resp_lower for w in ["machine", "stuck", "report", "sira", "how to use", "payment", "change"]):
            suggestions = [
                ("🛒 Products", "What products do you sell?"),
                ("💡 Hygiene Tip", "Give me a hygiene tip"),
                ("🩹 First Aid", "How do I treat a wound?"),
            ]
        elif any(w in resp_lower for w in ["wound", "burn", "bleed", "first aid", "sugat"]):
            suggestions = [
                ("🧴 Products", "What products do you sell?"),
                ("💡 Hygiene Tip", "Give me a hygiene tip"),
                ("🔧 How to use", "How do I use the machine?"),
            ]
        elif any(w in resp_lower for w in ["soap", "wash that mouth", "sabon"]):
            suggestions = [
                ("🧴 About Soap", "Tell me about soap"),
                ("💡 Hygiene Tip", "Give me a hygiene tip"),
            ]
        else:
            suggestions = [
                ("🧴 Products", "What products do you sell?"),
                ("💡 Hygiene Tip", "Give me a hygiene tip"),
                ("🔧 How to use", "How do I use the machine?"),
            ]

        if not suggestions:
            return

        sug_row = ctk.CTkFrame(chat_frame, fg_color=theme["bg"], corner_radius=0)
        sug_row.pack(fill=tk.X, padx=0, pady=(2, 6))

        sug_inner = ctk.CTkFrame(sug_row, fg_color=theme["bg"], corner_radius=0)
        sug_inner.pack(side=tk.LEFT, padx=44, pady=2)

        for label, msg in suggestions:
            ctk.CTkButton(
                sug_inner,
                text=label,
                font=(ui_font, 9, "bold"),
                fg_color=theme.get("card_bg", "#ffffff"),
                hover_color=theme.get("button_bg", "#F0EFF4"),
                text_color=theme.get("accent", "#50C878"),
                border_width=1,
                border_color=theme.get("card_border", "#E8E5F0"),
                corner_radius=980,
                height=26,
                width=0,
                command=lambda m=msg: _process_user_message(m),
            ).pack(side=tk.LEFT, padx=3)

        _message_widgets.append(sug_row)

        try:
            chat_frame._parent_canvas.yview_moveto(1.0)
        except Exception:
            pass

    def _show_typing_indicator():
        """Show a typing animation bubble."""
        row = ctk.CTkFrame(chat_frame, fg_color=theme["bg"], corner_radius=0)
        row.pack(fill=tk.X, padx=0, pady=3)

        mini_canvas = tk.Canvas(
            row, width=28, height=28,
            bg=theme["bg"], highlightthickness=0, bd=0,
        )
        mini_canvas.pack(side=tk.LEFT, padx=(12, 4), pady=(4, 0), anchor="n")
        _draw_robot_avatar(mini_canvas, 14, 14, size=24, theme_name=theme_name)

        bubble = ctk.CTkFrame(
            row,
            fg_color=theme.get("card_bg", "#ffffff"),
            corner_radius=16,
            border_width=1,
            border_color=theme.get("card_border", "#e2e8f0"),
        )
        bubble.pack(side=tk.LEFT, padx=(0, 60), pady=2, anchor="w")

        dots_label = ctk.CTkLabel(
            bubble,
            text="●  ●  ●",
            font=(ui_font, 12),
            text_color=theme.get("muted", "#64748b"),
        )
        dots_label.pack(padx=16, pady=8)

        # Animate dots
        dot_states = ["●  ○  ○", "○  ●  ○", "○  ○  ●", "●  ●  ●"]
        _anim_data = {"idx": 0, "active": True}

        def _animate():
            if not _anim_data["active"]:
                return
            try:
                if dots_label.winfo_exists():
                    _anim_data["idx"] = (_anim_data["idx"] + 1) % len(dot_states)
                    dots_label.configure(text=dot_states[_anim_data["idx"]])
                    dots_label.after(300, _animate)
            except Exception:
                pass

        _animate()

        try:
            chat_frame._parent_canvas.yview_moveto(1.0)
        except Exception:
            pass

        return row, _anim_data

    def _process_user_message(text):
        """Handle user input: show message, get bot reply, display with typing animation."""
        text = text.strip()
        if not text:
            return

        # Clear input
        input_entry.delete(0, tk.END)

        # Show user message
        _add_message_bubble("user", text)

        # Show typing indicator
        typing_row, anim_data = _show_typing_indicator()

        def _get_reply():
            # Simulate slight thinking delay (makes it feel more natural)
            time.sleep(0.6)
            # Optional offline personalization (uses local SQLite + last RFID session)
            user_id = getattr(app, "_last_rfid_user_id", None)
            response = _bot.get_response(text, user_id=user_id)

            def _show_reply():
                # Remove typing indicator
                anim_data["active"] = False
                try:
                    if typing_row.winfo_exists():
                        typing_row.destroy()
                except Exception:
                    pass
                # Show bot reply
                _add_message_bubble("bot", response)
                # Show dynamic follow-up suggestions
                _add_follow_up_suggestions(response)

            try:
                app.after(0, _show_reply)
            except Exception:
                pass

        # Run in background thread so UI stays responsive
        thread = threading.Thread(target=_get_reply, daemon=True)
        thread.start()

    # Bind Enter key to send
    input_entry.bind("<Return>", lambda _e: _process_user_message(input_entry.get()))

    # ── Welcome message ───────────────────────
    _add_message_bubble(
        "bot",
        "Hi there! 👋 I'm Hygiene Hero, your friendly vending machine assistant!\n"
        "(Kamusta! Ako si Hygiene Hero, katulong mo sa makina!)\n\n"
        "I can help you with:\n"
        "🧴 Product info & benefits\n"
        "💡 Hygiene tips (English & Tagalog)\n"
        "🔧 Machine troubleshooting\n"
        "🩹 Basic first aid advice\n\n"
        "Tap a suggestion below or type your question!"
    )
    _add_follow_up_suggestions("welcome products tips")

    # Focus on input
    try:
        app.after(100, lambda: app._safe_focus(input_entry))
    except Exception:
        pass
