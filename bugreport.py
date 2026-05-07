from __future__ import annotations

import json
import os
import platform
import time
import random
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


def _safe_focus(widget) -> None:
    """
    Theme toggles / screen rebuilds can destroy widgets while callbacks are running.
    Guard focus changes to avoid TclError: bad window path name.
    """
    try:
        if widget is None:
            return
        try:
            exists = bool(widget.winfo_exists())
        except Exception:
            exists = False
        if not exists:
            return
        widget.focus_set()
    except Exception:
        return


def _default_reports_path(base_dir: Path) -> Path:
    reports_dir = base_dir / "bug_reports"
    return reports_dir / "bug_reports.ndjson"


def save_bug_report(
    *,
    base_dir: Path,
    version: str,
    theme: str,
    email: str,
    ticket_number: str,
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
        "email": (email or "").strip(),
        "ticket_number": (ticket_number or "").strip(),
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


def fetch_bug_reports_from_supabase(*, base_dir: Path, email: str) -> list[dict]:
    """
    Fetch bug reports for a given email (best-effort).
    Uses supabase.env (service_role) when present. Returns [] if offline/unconfigured.
    """
    email = (email or "").strip()
    if not email:
        return []
    env_path = base_dir / "supabase.env"
    env = _load_env_file(env_path)
    supabase_url = (env.get("SUPABASE_URL") or "").rstrip("/")
    service_key = (env.get("SUPABASE_SERVICE_ROLE_KEY") or "").strip()
    if not supabase_url or not service_key:
        return []

    # Minimal columns for the Updates screen
    select_cols = "created_at,ticket_number,email,category,status,details,fixed_at,fixed_by,machine_id"
    # URL encoding: keep it simple (email is safe in query when quoted/encoded minimally)
    endpoint = f"{supabase_url}/rest/v1/bug_reports?select={select_cols}&email=eq.{email}&order=created_at.desc&limit=50"

    headers = {
        "Content-Type": "application/json",
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
    }
    req = Request(endpoint, headers=headers, method="GET")
    try:
        with urlopen(req, timeout=8) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        data = json.loads(raw) if raw else []
        return data if isinstance(data, list) else []
    except (HTTPError, URLError, OSError, ValueError, json.JSONDecodeError):
        return []


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

    ctk.CTkLabel(
        body,
        text="Email for updates",
        font=ui_small,
        text_color=app.current_theme.get("muted", app.current_theme["fg"]),
    ).pack(anchor="w", pady=(0, 4))

    # Persist the last entered email across theme toggles / screen rebuilds.
    last_email = str(getattr(app, "_updates_email", "") or "")
    email_var = tk.StringVar(value=last_email)
    try:
        email_var.trace_add("write", lambda *_a: setattr(app, "_updates_email", email_var.get()))
    except Exception:
        pass
    scale = float(getattr(app, "_lcd_scale", 1.0) or 1.0)
    email_entry = ctk.CTkEntry(
        body,
        textvariable=email_var,
        width=int(320 * scale),
        height=int(38 * scale),
        fg_color=app.current_theme.get("search_bg", card_bg),
        text_color=app.current_theme["fg"],
        border_width=1,
        border_color=app.current_theme.get("card_border", "#e2e8f0"),
        corner_radius=8,
        placeholder_text="you@example.com",
    )
    email_entry.pack(anchor="w", pady=(0, 12))

    # Touch-friendly typing: show virtual keyboard when user taps the email field.
    try:
        email_entry.bind("<FocusIn>", lambda _e: app.show_virtual_keyboard(email_entry))
        email_entry.bind("<Button-1>", lambda _e: app.show_virtual_keyboard(email_entry))
    except Exception:
        pass

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
        email = (email_var.get() or "").strip()
        if not email:
            messagebox.showwarning("Report", "you forgot to put your email for your update")
            _safe_focus(email_entry)
            return

        # Ticket format: BR-YYYYMMDD-HHMMSS-XXXX
        stamp = time.strftime("%Y%m%d-%H%M%S")
        suffix = f"{random.randint(0, 9999):04d}"
        ticket_number = f"BR-{stamp}-{suffix}"

        details = txt.get("1.0", "end").strip()
        category = selected.get() or "Other"
        base_dir = Path(getattr(app, "BASE_DIR", Path(__file__).resolve().parent))
        path = save_bug_report(
            base_dir=Path(getattr(app, "BASE_DIR", Path(__file__).resolve().parent)),
            version=version,
            theme=getattr(app, "current_theme_name", ""),
            email=email,
            ticket_number=ticket_number,
            category=category,
            details=details,
        )
        # Also push to Supabase when configured (so website dashboard sees it live).
        pushed = push_bug_report_to_supabase(
            base_dir=base_dir,
            report_payload={
                "timestamp_ms": int(time.time() * 1000),
                "ticket_number": ticket_number,
                "version": version,
                "theme": getattr(app, "current_theme_name", ""),
                "email": email,
                "category": category,
                "details": (details or "").strip(),
                "status": "open",
            },
        )
        # Keep UX simple: do not show sync status to the user.
        _ = pushed
        messagebox.showinfo("Report", f"Thank you! Your report was submitted.\nTicket: {ticket_number}")
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


def show_report_updates_screen(app, *, version: str):
    """
    In-app Updates screen: check report ticket status (open/fixed) by email.
    """
    app._current_screen_builder = lambda: show_report_updates_screen(app, version=version)
    if getattr(app, "sidebar_holder", None) is not None and app.sidebar_holder.winfo_exists():
        app.sidebar_holder.destroy()
        app.sidebar_holder = None

    app.clear_screen()
    app.content_holder.configure(fg_color=app.current_theme["bg"])

    theme = app.current_theme
    ui_font = getattr(app, "UI_FONT", "Segoe UI")
    ui_small = getattr(app, "UI_FONT_SMALL", (ui_font, 10))
    ui_body = getattr(app, "UI_FONT_BODY", (ui_font, 12))

    frame = ctk.CTkFrame(app.content_holder, fg_color=theme["bg"])
    frame.pack(expand=True, fill=tk.BOTH)

    top_bar = ctk.CTkFrame(frame, fg_color=theme["bg"])
    top_bar.pack(side=tk.TOP, fill=tk.X, pady=(8, 0), padx=10)
    ctk.CTkButton(
        top_bar,
        text="← Back",
        font=ui_body,
        command=app.build_main_menu,
        fg_color=theme.get("button_bg", "#e5e7eb"),
        hover_color=theme.get("accent", "#1A948E"),
        text_color=theme.get("button_fg", "#111827"),
        corner_radius=8,
        height=36,
    ).pack(side=tk.LEFT)

    card_bg = theme.get("card_bg", "#ffffff")
    card = ctk.CTkFrame(
        frame,
        fg_color=card_bg,
        corner_radius=10,
        border_width=1,
        border_color=theme.get("card_border", "#e2e8f0"),
    )
    card.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=12, pady=10)

    body = ctk.CTkScrollableFrame(card, fg_color=card_bg)
    body.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=16, pady=(14, 14))

    ctk.CTkLabel(
        body,
        text="Updates",
        font=(ui_font, 18, "bold"),
        text_color=theme["fg"],
    ).pack(anchor="w", pady=(0, 6))
    ctk.CTkLabel(
        body,
        text="Enter the email you used when submitting a report to see your ticket status.",
        font=ui_small,
        text_color=theme.get("muted", theme["fg"]),
    ).pack(anchor="w", pady=(0, 10))

    # Persist last entered email across theme toggles / rebuilds.
    last_email = str(getattr(app, "_updates_email", "") or "")
    email_var = tk.StringVar(value=last_email)
    try:
        email_var.trace_add("write", lambda *_a: setattr(app, "_updates_email", email_var.get()))
    except Exception:
        pass
    row = ctk.CTkFrame(body, fg_color="transparent")
    row.pack(fill=tk.X, pady=(0, 10))
    scale = float(getattr(app, "_lcd_scale", 1.0) or 1.0)
    email_entry = ctk.CTkEntry(
        row,
        textvariable=email_var,
        width=int(320 * scale),
        height=int(38 * scale),
        fg_color=theme.get("search_bg", card_bg),
        text_color=theme["fg"],
        border_width=1,
        border_color=theme.get("card_border", "#e2e8f0"),
        corner_radius=8,
        placeholder_text="you@example.com",
    )
    email_entry.pack(side=tk.LEFT, padx=(0, 10))

    # Touch-friendly typing: show virtual keyboard when user taps the email field.
    try:
        email_entry.bind("<FocusIn>", lambda _e: app.show_virtual_keyboard(email_entry))
        email_entry.bind("<Button-1>", lambda _e: app.show_virtual_keyboard(email_entry))
    except Exception:
        pass

    results_wrap = ctk.CTkFrame(body, fg_color=card_bg)
    results_wrap.pack(fill=tk.BOTH, expand=True)

    def render_results(rows: list[dict]):
        for w in results_wrap.winfo_children():
            w.destroy()
        if not rows:
            ctk.CTkLabel(
                results_wrap,
                text="No tickets found for this email.",
                font=ui_body,
                text_color=theme.get("muted", theme["fg"]),
            ).pack(anchor="w", pady=6)
            return

        for r in rows:
            ticket = str(r.get("ticket_number") or "—")
            status = str(r.get("status") or "open").lower()
            category = str(r.get("category") or "—")
            created_at = str(r.get("created_at") or "")
            details = str(r.get("details") or "").strip()
            status_color = theme.get("status_success", "#27AE60") if status == "fixed" else theme.get("status_error", "#C0392B")

            item = ctk.CTkFrame(
                results_wrap,
                fg_color=theme.get("search_bg", card_bg),
                corner_radius=10,
                border_width=1,
                border_color=theme.get("card_border", "#e2e8f0"),
            )
            item.pack(fill=tk.X, pady=6)

            top = ctk.CTkFrame(item, fg_color="transparent")
            top.pack(fill=tk.X, padx=12, pady=(10, 0))
            ctk.CTkLabel(top, text=ticket, font=(ui_font, 12, "bold"), text_color=theme["fg"]).pack(side=tk.LEFT)
            ctk.CTkLabel(top, text=status.upper(), font=(ui_font, 11, "bold"), text_color=status_color).pack(side=tk.RIGHT)

            ctk.CTkLabel(
                item,
                text=f"{category} · {created_at[:19].replace('T',' ')}",
                font=ui_small,
                text_color=theme.get("muted", theme["fg"]),
            ).pack(anchor="w", padx=12, pady=(2, 8))

            if details:
                # Show the user's issue description (wrapped, readable on 7-inch LCD).
                ctk.CTkLabel(
                    item,
                    text=details,
                    font=(ui_font, int(12 * scale)),
                    text_color=theme["fg"],
                    wraplength=int(620 * scale),
                    justify="left",
                ).pack(anchor="w", padx=12, pady=(0, 10))

    def refresh():
        email = (email_var.get() or "").strip()
        try:
            setattr(app, "_updates_email", email)
        except Exception:
            pass
        if not email:
            messagebox.showwarning("Updates", "you forgot to put your email for your update")
            _safe_focus(email_entry)
            return
        base_dir = Path(getattr(app, "BASE_DIR", Path(__file__).resolve().parent))
        rows = fetch_bug_reports_from_supabase(base_dir=base_dir, email=email)
        try:
            if results_wrap.winfo_exists():
                render_results(rows)
        except Exception:
            # Screen may have been closed while request was running.
            return

        # Also keep a copy of results so theme toggles can re-render without retyping.
        try:
            setattr(app, "_updates_last_rows", rows)
        except Exception:
            pass

    ctk.CTkButton(
        row,
        text="Check",
        font=(ui_font, 12, "bold"),
        command=refresh,
        fg_color=theme.get("accent", "#1A948E"),
        hover_color=theme.get("accent_hover", "#15857B"),
        text_color="#ffffff",
        corner_radius=980,
        height=int(38 * scale),
        width=int(120 * scale),
    ).pack(side=tk.LEFT)

    # If we already have an email and/or cached results, keep them on theme toggle.
    try:
        cached = getattr(app, "_updates_last_rows", None)
    except Exception:
        cached = None
    if last_email and isinstance(cached, list) and cached:
        try:
            render_results(cached)
        except Exception:
            pass

    app.add_theme_toggle_footer()

