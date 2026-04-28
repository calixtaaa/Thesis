"""
Tiny UI timing helpers for Tkinter/CustomTkinter.

Goal: reduce expensive redraw work during fast scroll/resize by debouncing or throttling callbacks.
Does NOT touch GPIO/coin/RFID logic.
"""

from __future__ import annotations

import time


def debounce_tk(widget, delay_ms: int, fn):
    """
    Return a Tk callback that debounces `fn` using widget.after/after_cancel.
    """

    token = {"after_id": None}

    def _wrapped(*args, **kwargs):
        try:
            if token["after_id"] is not None:
                widget.after_cancel(token["after_id"])
        except Exception:
            token["after_id"] = None

        def _run():
            token["after_id"] = None
            fn(*args, **kwargs)

        token["after_id"] = widget.after(int(delay_ms), _run)

    return _wrapped


def throttle_tk(interval_ms: int, fn):
    """
    Return a callback that runs at most once per interval.
    """

    last = {"t": 0.0}

    def _wrapped(*args, **kwargs):
        now = time.monotonic() * 1000.0
        if now - last["t"] < float(interval_ms):
            return
        last["t"] = now
        return fn(*args, **kwargs)

    return _wrapped

