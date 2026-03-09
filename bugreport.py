from __future__ import annotations

import json
import time
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk


def _default_reports_path(base_dir: Path) -> Path:
    reports_dir = base_dir / "bug_reports"
    return reports_dir / "bug_reports.ndjson"


def save_bug_report(
    *,
    base_dir: Path,
    version: str,
    theme: str,
    category: str,
    details: str,
) -> Path:
    """Append a bug report entry as NDJSON. Returns the saved file path."""
    path = _default_reports_path(base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "timestamp": int(time.time() * 1000),
        "version": version,
        "theme": theme,
        "category": category,
        "details": (details or "").strip(),
    }
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=True) + "\n")
    return path


def show_bug_report_screen(app, *, version: str, hover_scale_btn):
    """
    In-app Bug Report screen (reference: category + explanation + submit).

    Expects `app` to expose:
    - `current_theme`, `current_theme_name`
    - `content_holder`, `sidebar_holder`
    - `clear_screen()`, `build_main_menu()`, `add_theme_toggle_footer()`
    """
    app._current_screen_builder = lambda: show_bug_report_screen(app, version=version, hover_scale_btn=hover_scale_btn)
    if getattr(app, "sidebar_holder", None) is not None and app.sidebar_holder.winfo_exists():
        app.sidebar_holder.destroy()
        app.sidebar_holder = None

    app.clear_screen()
    app.content_holder.configure(fg_color=app.current_theme["bg"])

    frame = ctk.CTkFrame(app.content_holder, fg_color=app.current_theme["bg"])
    frame.pack(expand=True, fill=tk.BOTH)

    # Top bar with back button
    top_bar = ctk.CTkFrame(frame, fg_color=app.current_theme["bg"])
    top_bar.pack(side=tk.TOP, fill=tk.X, pady=(8, 0), padx=10)
    ctk.CTkButton(
        top_bar,
        text="← Back",
        font=getattr(app, "UI_FONT_BODY", ("Segoe UI", 12)),
        command=app.build_main_menu,
        fg_color=app.current_theme.get("button_bg", "#e5e7eb"),
        hover_color=app.current_theme.get("accent", "#1A948E"),
        text_color=app.current_theme.get("button_fg", "#111827"),
        corner_radius=8,
        height=36,
    ).pack(side=tk.LEFT)

    card_bg = app.current_theme.get("card_bg", "#ffffff")
    card = ctk.CTkFrame(
        frame,
        fg_color=card_bg,
        corner_radius=10,
        border_width=1,
        border_color=app.current_theme.get("card_border", "#e2e8f0"),
    )
    card.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=12, pady=10)

    ui_font = getattr(app, "UI_FONT", "Segoe UI")
    ui_small = getattr(app, "UI_FONT_SMALL", (ui_font, 10))
    ui_body = getattr(app, "UI_FONT_BODY", (ui_font, 12))

    # Keep Submit/Cancel always visible; make the body scrollable
    btn_row = ctk.CTkFrame(card, fg_color=card_bg)
    btn_row.pack(side=tk.BOTTOM, fill=tk.X, padx=16, pady=(10, 14))

    body = ctk.CTkScrollableFrame(card, fg_color=card_bg)
    body.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=16, pady=(14, 0))

    ctk.CTkLabel(
        body,
        text="Report",
        font=(ui_font, 18, "bold"),
        text_color=app.current_theme["fg"],
    ).pack(anchor="w", pady=(0, 10))

    ctk.CTkLabel(
        body,
        text="What happened?",
        font=(ui_font, 12, "bold"),
        text_color=app.current_theme["fg"],
    ).pack(anchor="w", pady=(0, 8))

    options = [
        "UI not responding / Freeze",
        "Theme / colors wrong",
        "Buttons / navigation issue",
        "Data not updating (stock, reports, etc.)",
        "RFID / payment issue",
        "Other",
    ]
    selected = tk.StringVar(value=options[0])

    opts_wrap = ctk.CTkFrame(body, fg_color=card_bg)
    opts_wrap.pack(anchor="w", fill=tk.X, pady=(0, 10))
    for opt in options:
        ctk.CTkRadioButton(
            opts_wrap,
            text=opt,
            variable=selected,
            value=opt,
            font=ui_body,
            text_color=app.current_theme["fg"],
            fg_color=app.current_theme.get("accent", "#1A948E"),
            hover_color=app.current_theme.get("accent_hover", "#15857B"),
        ).pack(anchor="w", pady=2)

    ctk.CTkLabel(
        body,
        text="Additional explanation",
        font=ui_small,
        text_color=app.current_theme.get("muted", app.current_theme["fg"]),
    ).pack(anchor="w", pady=(8, 4))

    txt = ctk.CTkTextbox(
        body,
        font=ui_body,
        height=100,
        wrap="word",
        fg_color=app.current_theme.get("search_bg", card_bg),
        text_color=app.current_theme["fg"],
        border_width=1,
        border_color=app.current_theme.get("card_border", "#e2e8f0"),
        corner_radius=8,
    )
    txt.pack(fill=tk.X, pady=(0, 14))

    def submit():
        details = txt.get("1.0", "end").strip()
        category = selected.get() or "Other"
        path = save_bug_report(
            base_dir=Path(getattr(app, "BASE_DIR", Path(__file__).resolve().parent)),
            version=version,
            theme=getattr(app, "current_theme_name", ""),
            category=category,
            details=details,
        )
        messagebox.showinfo("Report", f"Thank you! Your report was saved.\n\n{path}")
        app.build_main_menu()

    ctk.CTkButton(
        btn_row,
        text="Submit",
        font=(ui_font, 12, "bold"),
        command=submit,
        fg_color=app.current_theme.get("accent", "#1A948E"),
        hover_color=app.current_theme.get("accent_hover", "#15857B"),
        text_color="#ffffff",
        corner_radius=8,
        height=40,
    ).pack(side=tk.LEFT)

    ctk.CTkButton(
        btn_row,
        text="Cancel",
        font=(ui_font, 12, "bold"),
        command=app.build_main_menu,
        fg_color=app.current_theme.get("button_bg", "#e5e7eb"),
        hover_color=app.current_theme.get("accent", "#1A948E"),
        text_color=app.current_theme.get("button_fg", "#111827"),
        corner_radius=8,
        height=40,
    ).pack(side=tk.LEFT, padx=10)

    app.add_theme_toggle_footer()

