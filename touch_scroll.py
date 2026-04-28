"""Touch-friendly scrolling support for CustomTkinter scrollable frames."""

from __future__ import annotations

import weakref
from typing import Any


_registered_frames: "weakref.WeakSet[Any]" = weakref.WeakSet()
_bound_roots: set[str] = set()
_drag_state = {
    "frame": None,
    "canvas": None,
    "last_x": None,
    "last_y": None,
}


def install_ctk_scroll_support(ctk_module: Any) -> None:
    """Patch CTkScrollableFrame so new instances gain touch and Linux wheel scrolling."""
    scrollable_cls = ctk_module.CTkScrollableFrame
    if getattr(scrollable_cls, "_touch_scroll_support_installed", False):
        return

    original_init = scrollable_cls.__init__

    def patched_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        _register_scrollable_frame(self)

    scrollable_cls.__init__ = patched_init
    scrollable_cls._touch_scroll_support_installed = True


def _register_scrollable_frame(scrollable_frame: Any) -> None:
    if scrollable_frame in _registered_frames:
        return

    _registered_frames.add(scrollable_frame)
    root = scrollable_frame.winfo_toplevel()
    root_key = str(root)
    if root_key in _bound_roots:
        return

    _bound_roots.add(root_key)
    root.bind_all("<ButtonPress-1>", _handle_press, add="+")
    root.bind_all("<B1-Motion>", _handle_motion, add="+")
    root.bind_all("<ButtonRelease-1>", _handle_release, add="+")
    root.bind_all("<MouseWheel>", _handle_mouse_wheel, add="+")
    root.bind_all("<Button-4>", _handle_mouse_wheel, add="+")
    root.bind_all("<Button-5>", _handle_mouse_wheel, add="+")


def _is_descendant(widget: Any, ancestor: Any) -> bool:
    current = widget
    while current is not None:
        if current == ancestor:
            return True
        current = getattr(current, "master", None)
    return False


def _find_target_frame(widget: Any) -> Any:
    for frame in list(_registered_frames):
        try:
            if frame.winfo_exists() and _is_descendant(widget, frame):
                return frame
        except Exception:
            continue
    return None


def _get_canvas(frame: Any) -> Any:
    return getattr(frame, "_parent_canvas", None)


def _handle_press(event: Any) -> None:
    frame = _find_target_frame(getattr(event, "widget", None))
    if frame is None:
        _drag_state["frame"] = None
        _drag_state["canvas"] = None
        return

    _drag_state["frame"] = frame
    _drag_state["canvas"] = _get_canvas(frame)
    _drag_state["last_x"] = getattr(event, "x_root", None)
    _drag_state["last_y"] = getattr(event, "y_root", None)


def _handle_motion(event: Any) -> None:
    frame = _drag_state.get("frame")
    canvas = _drag_state.get("canvas")
    if frame is None or canvas is None:
        return

    orientation = getattr(frame, "_orientation", "vertical")
    if orientation == "horizontal":
        last_x = _drag_state.get("last_x")
        if last_x is None:
            _drag_state["last_x"] = getattr(event, "x_root", None)
            return
        delta = getattr(event, "x_root", 0) - last_x
        if delta:
            _scroll_canvas(canvas, orientation, delta)
            _drag_state["last_x"] = getattr(event, "x_root", None)
        return

    last_y = _drag_state.get("last_y")
    if last_y is None:
        _drag_state["last_y"] = getattr(event, "y_root", None)
        return

    delta = getattr(event, "y_root", 0) - last_y
    if delta:
        _scroll_canvas(canvas, orientation, delta)
        _drag_state["last_y"] = getattr(event, "y_root", None)


def _handle_release(_event: Any) -> None:
    _drag_state["frame"] = None
    _drag_state["canvas"] = None
    _drag_state["last_x"] = None
    _drag_state["last_y"] = None


def _handle_mouse_wheel(event: Any) -> None:
    frame = _find_target_frame(getattr(event, "widget", None))
    if frame is None:
        return

    canvas = _get_canvas(frame)
    if canvas is None:
        return

    orientation = getattr(frame, "_orientation", "vertical")
    delta = getattr(event, "delta", 0)
    event_num = getattr(event, "num", None)

    if event_num == 4:
        delta = 120
    elif event_num == 5:
        delta = -120

    if delta == 0:
        return

    direction = -1 if delta > 0 else 1
    if orientation == "horizontal":
        canvas.xview_scroll(direction, "units")
    else:
        canvas.yview_scroll(direction, "units")


def _scroll_canvas(canvas: Any, orientation: str, delta_pixels: int) -> None:
    try:
        if orientation == "horizontal":
            view = canvas.xview()
            viewport = max(int(canvas.winfo_width()), 1)
            current = view[0] if view else 0.0
            canvas.xview_moveto(max(0.0, min(1.0, current - (delta_pixels / (viewport * 2.0)))))
        else:
            view = canvas.yview()
            viewport = max(int(canvas.winfo_height()), 1)
            current = view[0] if view else 0.0
            canvas.yview_moveto(max(0.0, min(1.0, current - (delta_pixels / (viewport * 2.0)))))
    except Exception:
        try:
            if orientation == "horizontal":
                canvas.xview_scroll(int(-delta_pixels / 8), "units")
            else:
                canvas.yview_scroll(int(-delta_pixels / 8), "units")
        except Exception:
            pass