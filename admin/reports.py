import os
import sys
import subprocess
from pathlib import Path
from typing import List


BASE_DIR = Path(__file__).resolve().parent.parent


def get_downloads_dir() -> Path:
    """Return the user's Downloads directory."""
    return Path.home() / "Downloads"


def get_reports_dir() -> Path:
    """Return the folder where generated Excel reports are stored."""
    reports_dir = get_downloads_dir() / "Hygiene Vending Reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    return reports_dir


def list_sales_reports() -> List[Path]:
    """Return a list of available sales report Excel files, newest first."""
    pattern = "sales_report_*.xlsx"
    reports = sorted(
        get_reports_dir().glob(pattern),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return reports


def open_sales_report(path: Path) -> None:
    """Open the given Excel file with the system's default application."""
    try:
        if sys.platform.startswith("win"):
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.run(["open", str(path)], check=False)
        else:
            subprocess.run(["xdg-open", str(path)], check=False)
    except Exception as exc:
        print(f"[ADMIN] Failed to open report {path}: {exc}")
        raise

