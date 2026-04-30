from __future__ import annotations

import json
import os
import platform
import time
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


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


def _load_env_file(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    try:
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    except Exception:
        return out
    return out


def push_bug_report_to_supabase(*, base_dir: Path, report_payload: dict) -> bool:
    """
    Best-effort: push bug report to Supabase so the website dashboard can see it in realtime.
    Uses supabase.env (service_role) when present. Safe to call offline (returns False).
    """
    env_path = base_dir / "supabase.env"
    env = _load_env_file(env_path)
    supabase_url = (env.get("SUPABASE_URL") or "").rstrip("/")
    service_key = (env.get("SUPABASE_SERVICE_ROLE_KEY") or "").strip()
    if not supabase_url or not service_key:
        return False

    endpoint = f"{supabase_url}/rest/v1/bug_reports"
    # Strip nulls so NOT NULL defaults (created_at) can apply.
    payload = {k: v for k, v in dict(report_payload).items() if v is not None}
    payload.setdefault("machine_id", platform.node() or os.getenv("COMPUTERNAME") or "machine")

    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Prefer": "return=minimal",
    }
    req = Request(endpoint, data=data, headers=headers, method="POST")
    try:
        with urlopen(req, timeout=8) as resp:
            _ = resp.read()
        return True
    except (HTTPError, URLError, OSError, ValueError):
        return False


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
        base_dir = Path(getattr(app, "BASE_DIR", Path(__file__).resolve().parent))
        path = save_bug_report(
            base_dir=Path(getattr(app, "BASE_DIR", Path(__file__).resolve().parent)),
            version=version,
            theme=getattr(app, "current_theme_name", ""),
            category=category,
            details=details,
        )
        # Also push to Supabase when configured (so website dashboard sees it live).
        pushed = push_bug_report_to_supabase(
            base_dir=base_dir,
            report_payload={
                "timestamp_ms": int(time.time() * 1000),
                "version": version,
                "theme": getattr(app, "current_theme_name", ""),
                "category": category,
                "details": (details or "").strip(),
                "status": "open",
            },
        )
        # Keep UX simple: do not show sync status to the user.
        _ = pushed
        messagebox.showinfo("Report", "Thank you! Your report was submitted.")
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

