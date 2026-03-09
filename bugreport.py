from __future__ import annotations

import json
import time
from pathlib import Path
import tkinter as tk
from tkinter import messagebox


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
    - `apply_theme_to_widget(widget)` (optional, used at end)
    """
    if getattr(app, "sidebar_holder", None) is not None and app.sidebar_holder.winfo_exists():
        app.sidebar_holder.destroy()
        app.sidebar_holder = None

    app.clear_screen()
    app.content_holder.configure(bg=app.current_theme["bg"])

    frame = tk.Frame(app.content_holder, bg=app.current_theme["bg"])
    frame.pack(expand=True, fill=tk.BOTH)

    # Top bar with back button
    top_bar = tk.Frame(frame, bg=app.current_theme["bg"])
    top_bar.pack(side=tk.TOP, fill=tk.X, pady=(8, 0), padx=10)
    back_btn = tk.Button(
        top_bar,
        text="← Back",
        font=getattr(app, "UI_FONT_BODY", ("Segoe UI", 12)),
        command=app.build_main_menu,
        bg=app.current_theme.get("button_bg", "#e5e7eb"),
        fg=app.current_theme.get("button_fg", "#111827"),
        relief=tk.FLAT,
        padx=14,
        pady=6,
        cursor="hand2",
    )
    back_btn.pack(side=tk.LEFT)
    hover_scale_btn(back_btn, normal_padx=14, normal_pady=6, hover_padx=18, hover_pady=10)

    card_bg = app.current_theme.get("card_bg", "#ffffff")
    card = tk.Frame(
        frame,
        bg=card_bg,
        highlightthickness=1,
        highlightbackground=app.current_theme.get("card_border", "#e2e8f0"),
        padx=16,
        pady=14,
    )
    # Use pack (not place) so the footer can reserve space
    card.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=12, pady=10)

    ui_font = getattr(app, "UI_FONT", "Segoe UI")
    ui_small = getattr(app, "UI_FONT_SMALL", (ui_font, 10))
    ui_body = getattr(app, "UI_FONT_BODY", (ui_font, 12))

    # Keep Submit/Cancel always visible; make the body scrollable
    btn_row = tk.Frame(card, bg=card_bg)
    btn_row.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))

    body_container = tk.Frame(card, bg=card_bg)
    body_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    scrollbar = tk.Scrollbar(body_container, orient="vertical")
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    canvas = tk.Canvas(
        body_container,
        bg=card_bg,
        highlightthickness=0,
        bd=0,
        yscrollcommand=scrollbar.set,
    )
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.configure(command=canvas.yview)

    body = tk.Frame(canvas, bg=card_bg)
    canvas.create_window((0, 0), window=body, anchor="nw")

    def _on_configure(_event=None):
        try:
            canvas.configure(scrollregion=canvas.bbox("all"))
        except Exception:
            pass

    body.bind("<Configure>", _on_configure)

    tk.Label(
        body,
        text="Report",
        font=(ui_font, 18, "bold"),
        bg=card_bg,
        fg=app.current_theme["fg"],
    ).pack(anchor="w", pady=(0, 10))

    tk.Label(
        body,
        text="What happened?",
        font=(ui_font, 12, "bold"),
        bg=card_bg,
        fg=app.current_theme["fg"],
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

    opts_wrap = tk.Frame(body, bg=card_bg)
    opts_wrap.pack(anchor="w", fill=tk.X, pady=(0, 10))
    for opt in options:
        rb = tk.Radiobutton(
            opts_wrap,
            text=opt,
            variable=selected,
            value=opt,
            font=ui_body,
            bg=card_bg,
            fg=app.current_theme["fg"],
            activebackground=card_bg,
            activeforeground=app.current_theme["fg"],
            selectcolor=card_bg,
            anchor="w",
            justify="left",
        )
        rb._bug_report = True
        rb.pack(anchor="w", pady=2)

    tk.Label(
        body,
        text="Additional explanation",
        font=ui_small,
        bg=card_bg,
        fg=app.current_theme.get("muted", app.current_theme["fg"]),
    ).pack(anchor="w", pady=(8, 4))

    txt = tk.Text(
        body,
        font=ui_body,
        height=4,
        wrap="word",
        bg=app.current_theme.get("search_bg", card_bg),
        fg=app.current_theme["fg"],
        insertbackground=app.current_theme["fg"],
        highlightthickness=1,
        highlightbackground=app.current_theme.get("card_border", "#e2e8f0"),
        relief=tk.FLAT,
    )
    txt._bug_report = True
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

    submit_btn = tk.Button(
        btn_row,
        text="Submit",
        font=(ui_font, 12, "bold"),
        command=submit,
        bg=app.current_theme.get("accent", "#1A948E"),
        fg="#ffffff",
        activebackground=app.current_theme.get("accent_hover", "#15857B"),
        activeforeground="#ffffff",
        relief=tk.FLAT,
        padx=22,
        pady=10,
        cursor="hand2",
    )
    submit_btn.pack(side=tk.LEFT)
    submit_btn.bind("<Enter>", lambda e: submit_btn.configure(bg=app.current_theme.get("accent_hover", "#15857B")) if submit_btn.winfo_exists() else None)
    submit_btn.bind("<Leave>", lambda e: submit_btn.configure(bg=app.current_theme.get("accent", "#1A948E")) if submit_btn.winfo_exists() else None)

    cancel_btn = tk.Button(
        btn_row,
        text="Cancel",
        font=(ui_font, 12, "bold"),
        command=app.build_main_menu,
        bg=app.current_theme.get("button_bg", "#e5e7eb"),
        fg=app.current_theme.get("button_fg", "#111827"),
        relief=tk.FLAT,
        padx=18,
        pady=10,
        cursor="hand2",
    )
    cancel_btn.pack(side=tk.LEFT, padx=10)

    app.add_theme_toggle_footer()
    try:
        app.apply_theme_to_widget(app.content_holder)
    except Exception:
        pass

