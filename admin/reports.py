import os
import logging
import sys
import subprocess
from pathlib import Path
from typing import List


def get_downloads_dir() -> Path:
    """Return the user's Downloads directory."""
    home = Path.home()
    candidates = [home / "Downloads"]

    user_profile = os.environ.get("USERPROFILE")
    if user_profile:
        candidates.append(Path(user_profile) / "Downloads")

    one_drive = os.environ.get("OneDrive")
    if one_drive:
        candidates.append(Path(one_drive) / "Downloads")

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return candidates[0]


def get_reports_dir() -> Path:
    """Return the folder where generated Excel reports are stored."""
    reports_dir = get_downloads_dir() / "Hygiene Vending Reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    return reports_dir


def list_sales_reports() -> List[Path]:
    """Return a list of available sales report Excel files, newest first."""
    pattern = "sales_report_*.xlsx"
    reports: List[Path] = []
    for report_path in get_reports_dir().glob(pattern):
        try:
            report_path.stat()
        except OSError:
            continue
        reports.append(report_path)

    reports.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return reports


def open_sales_report(path: Path) -> None:
    """Open the given Excel file with the system's default application."""
    path = Path(path)
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"Report file not found: {path}")

    try:
        if sys.platform.startswith("win"):
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.run(["open", str(path)], check=True)
        else:
            subprocess.run(["xdg-open", str(path)], check=True)
    except Exception as exc:
        logging.exception("Failed to open report %s", path)
        raise

