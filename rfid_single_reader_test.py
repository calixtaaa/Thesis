#!/usr/bin/env python3
"""Single MFRC522 RFID reader smoke test for Raspberry Pi.

This script validates the shared-reader setup used by the main app:
- one MFRC522 reader
- SPI0 CE0 (GPIO8) chip select
- GPIO5 reset pin

It polls for RFID tags/cards and prints UIDs. Optional DB lookup shows role metadata.
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
import time
from pathlib import Path

try:
    import tkinter as tk
except Exception:
    tk = None  # type: ignore

try:
    import RPi.GPIO as GPIO  # type: ignore
except Exception:
    GPIO = None  # type: ignore

try:
    from mfrc522 import MFRC522, SimpleMFRC522  # type: ignore
except Exception:
    MFRC522 = None
    SimpleMFRC522 = None

RFID_RST_PIN = 5
DB_PATH = Path(__file__).resolve().parent / "vending.db"


def _print_gpio_backend_fix(exc: Exception) -> None:
    print(_gpio_backend_fix_text(exc))


def _gpio_backend_fix_text(exc: Exception) -> str:
    msg = str(exc).strip()
    lines = [f"[ERR] GPIO init failed: {msg}"]
    if "peripheral base address" in msg.lower():
        lines.append("[HINT] Detected legacy RPi.GPIO backend issue (common on Raspberry Pi 5).")
    lines.extend(
        [
            "[FIX] In the same virtualenv, run:",
            "  pip uninstall -y RPi.GPIO",
            "  pip install rpi-lgpio",
            "[FIX] Ensure SPI is enabled:",
            "  sudo raspi-config nonint do_spi 0",
            "Then rerun: python rfid_single_reader_test.py",
        ]
    )
    return "\n".join(lines)


def _init_gpio() -> tuple[bool, str | None]:
    if GPIO is None:
        return False, "[ERR] RPi.GPIO not available. Run this script on Raspberry Pi OS."

    try:
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(RFID_RST_PIN, GPIO.OUT)
        GPIO.output(RFID_RST_PIN, GPIO.HIGH)
    except Exception as exc:
        return False, _gpio_backend_fix_text(exc)

    return True, None


def _pulse_reader_reset(pulses: int = 3, low_s: float = 0.08, high_s: float = 0.08) -> tuple[bool, str]:
    if GPIO is None:
        return False, "RPi.GPIO is not available."
    if pulses < 1:
        pulses = 1

    try:
        for _ in range(pulses):
            GPIO.output(RFID_RST_PIN, GPIO.LOW)
            time.sleep(max(0.01, low_s))
            GPIO.output(RFID_RST_PIN, GPIO.HIGH)
            time.sleep(max(0.01, high_s))
        return True, f"Pulsed RFID RST (GPIO{RFID_RST_PIN}) x{pulses}."
    except Exception as exc:
        return False, f"Failed to pulse RFID RST: {exc}"


def _create_mfrc522_reader():
    if MFRC522 is None:
        return None

    ctor_attempts = (
        {"bus": 0, "device": 0},
        {"dev": 0},
        {"device": 0},
        {"bus": 0, "dev": 0},
        {},
    )
    for kwargs in ctor_attempts:
        try:
            return MFRC522(**kwargs)
        except TypeError:
            continue
        except Exception:
            continue
    return None


def _close_reader_spi(reader) -> None:
    try:
        spi_obj = getattr(reader, "spi", None)
        if spi_obj is not None and hasattr(spi_obj, "close"):
            spi_obj.close()
    except Exception:
        pass


def _read_reader_register(reader, reg_addr: int) -> int | None:
    method_names = ("Read_MFRC522", "MFRC522_Read", "ReadReg", "read")
    for name in method_names:
        fn = getattr(reader, name, None)
        if fn is None:
            continue
        try:
            value = fn(reg_addr)
            if isinstance(value, (tuple, list)) and value:
                value = value[0]
            return int(value) & 0xFF
        except Exception:
            continue
    return None


def _probe_mfrc522_spi_link() -> tuple[bool, str]:
    if MFRC522 is None:
        return False, "MFRC522 backend is not available."

    # Brief reset pulse before probing the version register over SPI.
    _pulse_reader_reset(pulses=1, low_s=0.02, high_s=0.02)

    reader = _create_mfrc522_reader()
    if reader is None:
        return False, "Could not initialize MFRC522 reader on SPI0 CE0."

    try:
        version_reg = int(getattr(reader, "VersionReg", 0x37))
        value = _read_reader_register(reader, version_reg)
        if value is None:
            return False, "Reader API does not expose a known register-read method."
        if value in {0x00, 0xFF}:
            return False, (
                f"SPI probe FAIL: VersionReg=0x{value:02X}. "
                "Check CE0/SCK/MOSI/MISO wiring, power, and SPI enablement."
            )
        return True, f"SPI probe PASS: VersionReg=0x{value:02X}."
    except Exception as exc:
        return False, f"SPI probe error: {exc}"
    finally:
        _close_reader_spi(reader)


def _read_uid_low_level() -> str | None:
    if MFRC522 is None or GPIO is None:
        return None

    try:
        GPIO.output(RFID_RST_PIN, GPIO.LOW)
        time.sleep(0.01)
        GPIO.output(RFID_RST_PIN, GPIO.HIGH)
        time.sleep(0.01)
    except Exception:
        pass

    reader = _create_mfrc522_reader()

    if reader is None:
        return None

    try:
        if hasattr(reader, "MFRC522_Request") and hasattr(reader, "MFRC522_Anticoll"):
            req_cmd = getattr(reader, "PICC_REQIDL", 0x26)
            mi_ok = getattr(reader, "MI_OK", 0)
            status, _tag_type = reader.MFRC522_Request(req_cmd)
            if status != mi_ok:
                return None
            status, uid = reader.MFRC522_Anticoll()
            if status == mi_ok and uid:
                return "".join(f"{int(part) & 0xFF:02X}" for part in uid[:4])

        if hasattr(reader, "read_id_no_block"):
            uid_int = reader.read_id_no_block()
            if uid_int:
                return str(uid_int).strip().upper()
    except Exception:
        return None
    finally:
        _close_reader_spi(reader)

    return None


def _read_uid_simple() -> str | None:
    if SimpleMFRC522 is None:
        return None

    try:
        reader = SimpleMFRC522()
        uid_int, _text = reader.read_no_block()
        if uid_int:
            return str(uid_int).strip().upper()
    except Exception:
        return None
    return None


def _lookup_rfid_user(uid: str) -> tuple[str, float] | None:
    if not DB_PATH.exists():
        return None

    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            "SELECT role, balance FROM rfid_users WHERE UPPER(TRIM(rfid_uid)) = ? LIMIT 1",
            (uid.strip().upper(),),
        )
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        role = str(row[0] or "customer")
        balance = float(row[1] or 0.0)
        return role, balance
    except Exception:
        return None


def _read_uid() -> str | None:
    uid = _read_uid_low_level()
    if uid:
        return uid
    return _read_uid_simple()


class RFIDTestUI(tk.Tk):  # type: ignore[misc]
    def __init__(self, interval_s: float, no_db_lookup: bool):
        super().__init__()
        self.title("RFID Single Reader Test")
        self.geometry("780x460")
        self.configure(bg="#f5f7fa")

        self.interval_ms = int(max(50, interval_s * 1000))
        self.no_db_lookup = no_db_lookup
        self.last_uid = None
        self.last_ts = 0.0
        self.spi_probe_running = False
        self.spi_probe_interval_ms = 350
        self.last_spi_probe_state = None
        self.spi_probe_toggle_btns = []
        self.spi_probe_pass_count = 0
        self.spi_probe_fail_count = 0
        self.spi_probe_last_fail = "-"

        self.status_var = tk.StringVar(value="Waiting for RFID taps...")
        self.uid_var = tk.StringVar(value="-")
        self.role_var = tk.StringVar(value="-")
        self.balance_var = tk.StringVar(value="-")
        self.spi_pass_var = tk.StringVar(value="0")
        self.spi_fail_var = tk.StringVar(value="0")
        self.spi_last_fail_var = tk.StringVar(value="-")

        self.main_screen = tk.Frame(self, bg="#f5f7fa")
        self.main_screen.pack(fill=tk.BOTH, expand=True, padx=14, pady=14)

        tk.Label(
            self.main_screen,
            text="Single MFRC522 Reader Test",
            font=("Segoe UI", 18, "bold"),
            bg="#f5f7fa",
            fg="#0f172a",
        ).pack(anchor="w")

        tk.Label(
            self.main_screen,
            text="Wiring: CE0(GPIO8), RST(GPIO5), SCK(11), MOSI(10), MISO(9)",
            font=("Segoe UI", 10),
            bg="#f5f7fa",
            fg="#334155",
        ).pack(anchor="w", pady=(4, 12))

        controls = tk.Frame(self.main_screen, bg="#f5f7fa")
        controls.pack(fill=tk.X, pady=(0, 8))
        tk.Button(
            controls,
            text="Pulse RFID RST (GPIO5)",
            command=self._pulse_rst,
            font=("Segoe UI", 10, "bold"),
            bg="#0ea5e9",
            fg="#ffffff",
            activebackground="#0284c7",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            padx=12,
            pady=6,
        ).pack(side=tk.LEFT)
        tk.Button(
            controls,
            text="Probe SPI Link",
            command=self._probe_spi,
            font=("Segoe UI", 10, "bold"),
            bg="#16a34a",
            fg="#ffffff",
            activebackground="#15803d",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            padx=12,
            pady=6,
        ).pack(side=tk.LEFT, padx=(8, 0))
        main_spi_toggle_btn = tk.Button(
            controls,
            text="Start Continuous SPI Probe",
            command=self._toggle_spi_probe,
            font=("Segoe UI", 10, "bold"),
            bg="#f59e0b",
            fg="#111827",
            activebackground="#d97706",
            activeforeground="#111827",
            relief=tk.FLAT,
            padx=12,
            pady=6,
        )
        main_spi_toggle_btn.pack(side=tk.LEFT, padx=(8, 0))
        self.spi_probe_toggle_btns.append(main_spi_toggle_btn)
        tk.Button(
            controls,
            text="Troubleshooting Screen",
            command=self._show_troubleshooting_screen,
            font=("Segoe UI", 10, "bold"),
            bg="#334155",
            fg="#ffffff",
            activebackground="#1e293b",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            padx=12,
            pady=6,
        ).pack(side=tk.LEFT, padx=(8, 0))
        tk.Label(
            controls,
            text="(Safe line to pulse for wiring check)",
            font=("Segoe UI", 9),
            bg="#f5f7fa",
            fg="#475569",
        ).pack(side=tk.LEFT, padx=(10, 0))

        row = tk.Frame(self.main_screen, bg="#f5f7fa")
        row.pack(fill=tk.X)
        tk.Label(row, text="Status:", font=("Segoe UI", 10, "bold"), bg="#f5f7fa").grid(row=0, column=0, sticky="w")
        tk.Label(row, textvariable=self.status_var, font=("Segoe UI", 10), bg="#f5f7fa", fg="#0f766e").grid(row=0, column=1, sticky="w", padx=(8, 0))
        tk.Label(row, text="UID:", font=("Segoe UI", 10, "bold"), bg="#f5f7fa").grid(row=1, column=0, sticky="w", pady=(8, 0))
        tk.Label(row, textvariable=self.uid_var, font=("Consolas", 12, "bold"), bg="#f5f7fa", fg="#111827").grid(row=1, column=1, sticky="w", padx=(8, 0), pady=(8, 0))
        tk.Label(row, text="Role:", font=("Segoe UI", 10, "bold"), bg="#f5f7fa").grid(row=2, column=0, sticky="w", pady=(8, 0))
        tk.Label(row, textvariable=self.role_var, font=("Segoe UI", 10), bg="#f5f7fa").grid(row=2, column=1, sticky="w", padx=(8, 0), pady=(8, 0))
        tk.Label(row, text="Balance:", font=("Segoe UI", 10, "bold"), bg="#f5f7fa").grid(row=3, column=0, sticky="w", pady=(8, 0))
        tk.Label(row, textvariable=self.balance_var, font=("Segoe UI", 10), bg="#f5f7fa").grid(row=3, column=1, sticky="w", padx=(8, 0), pady=(8, 0))

        tk.Label(
            self.main_screen,
            text="Detected Tap Log",
            font=("Segoe UI", 11, "bold"),
            bg="#f5f7fa",
            fg="#0f172a",
        ).pack(anchor="w", pady=(16, 6))

        self.log_text = tk.Text(
            self.main_screen,
            height=11,
            bg="#ffffff",
            fg="#0f172a",
            insertbackground="#0f172a",
            font=("Consolas", 10),
            relief=tk.GROOVE,
            borderwidth=1,
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        self.troubleshoot_screen = self._build_troubleshooting_screen()

        self._append_log("RFID UI test started. Tap a card/tag to the reader.")
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(120, self._poll_rfid)

    def _build_troubleshooting_screen(self) -> tk.Frame:
        frame = tk.Frame(self, bg="#eef2ff")

        tk.Label(
            frame,
            text="Troubleshooting Screen",
            font=("Segoe UI", 18, "bold"),
            bg="#eef2ff",
            fg="#0f172a",
        ).pack(anchor="w", padx=14, pady=(14, 2))

        tk.Label(
            frame,
            text="Use this while physically probing wires and connectors.",
            font=("Segoe UI", 10),
            bg="#eef2ff",
            fg="#334155",
        ).pack(anchor="w", padx=14, pady=(0, 12))

        tools = tk.Frame(frame, bg="#eef2ff")
        tools.pack(fill=tk.X, padx=14, pady=(0, 10))

        tk.Button(
            tools,
            text="Pulse RFID RST (GPIO5)",
            command=self._pulse_rst,
            font=("Segoe UI", 10, "bold"),
            bg="#0ea5e9",
            fg="#ffffff",
            activebackground="#0284c7",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            padx=12,
            pady=6,
        ).pack(side=tk.LEFT)

        tk.Button(
            tools,
            text="Probe SPI Link",
            command=self._probe_spi,
            font=("Segoe UI", 10, "bold"),
            bg="#16a34a",
            fg="#ffffff",
            activebackground="#15803d",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            padx=12,
            pady=6,
        ).pack(side=tk.LEFT, padx=(8, 0))

        troubleshoot_spi_toggle_btn = tk.Button(
            tools,
            text="Start Continuous SPI Probe",
            command=self._toggle_spi_probe,
            font=("Segoe UI", 10, "bold"),
            bg="#f59e0b",
            fg="#111827",
            activebackground="#d97706",
            activeforeground="#111827",
            relief=tk.FLAT,
            padx=12,
            pady=6,
        )
        troubleshoot_spi_toggle_btn.pack(side=tk.LEFT, padx=(8, 0))
        self.spi_probe_toggle_btns.append(troubleshoot_spi_toggle_btn)

        status_row = tk.Frame(frame, bg="#eef2ff")
        status_row.pack(fill=tk.X, padx=14, pady=(0, 8))
        tk.Label(status_row, text="Live Status:", font=("Segoe UI", 10, "bold"), bg="#eef2ff", fg="#0f172a").pack(side=tk.LEFT)
        tk.Label(status_row, textvariable=self.status_var, font=("Segoe UI", 10), bg="#eef2ff", fg="#0f766e").pack(side=tk.LEFT, padx=(8, 0))

        stats_row = tk.Frame(frame, bg="#eef2ff")
        stats_row.pack(fill=tk.X, padx=14, pady=(0, 8))
        tk.Label(stats_row, text="SPI PASS:", font=("Segoe UI", 10, "bold"), bg="#eef2ff", fg="#166534").pack(side=tk.LEFT)
        tk.Label(stats_row, textvariable=self.spi_pass_var, font=("Consolas", 10, "bold"), bg="#eef2ff", fg="#166534").pack(side=tk.LEFT, padx=(6, 16))
        tk.Label(stats_row, text="SPI FAIL:", font=("Segoe UI", 10, "bold"), bg="#eef2ff", fg="#991b1b").pack(side=tk.LEFT)
        tk.Label(stats_row, textvariable=self.spi_fail_var, font=("Consolas", 10, "bold"), bg="#eef2ff", fg="#991b1b").pack(side=tk.LEFT, padx=(6, 16))
        tk.Label(stats_row, text="Last FAIL:", font=("Segoe UI", 10, "bold"), bg="#eef2ff", fg="#1e293b").pack(side=tk.LEFT)
        tk.Label(stats_row, textvariable=self.spi_last_fail_var, font=("Consolas", 10), bg="#eef2ff", fg="#1e293b").pack(side=tk.LEFT, padx=(6, 0))

        tips = [
            "Checklist:",
            "1) Confirm 3.3V and GND are stable at the reader.",
            "2) Lightly move CE0/SCK/MOSI/MISO wires while continuous probe is running.",
            "3) If status flips to FAIL, inspect connectors and re-seat wiring.",
            "4) Use reset pulse after reseating, then retest taps.",
        ]
        tk.Label(
            frame,
            text="\n".join(tips),
            font=("Segoe UI", 10),
            bg="#eef2ff",
            fg="#1e293b",
            justify=tk.LEFT,
            anchor="w",
        ).pack(fill=tk.X, padx=14, pady=(0, 12))

        tk.Button(
            frame,
            text="Back To RFID Test Screen",
            command=self._show_main_screen,
            font=("Segoe UI", 10, "bold"),
            bg="#334155",
            fg="#ffffff",
            activebackground="#1e293b",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            padx=12,
            pady=8,
        ).pack(anchor="w", padx=14, pady=(0, 14))

        return frame

    def _show_troubleshooting_screen(self) -> None:
        self.main_screen.pack_forget()
        self.troubleshoot_screen.pack(fill=tk.BOTH, expand=True)
        self.status_var.set("Troubleshooting screen active")

    def _show_main_screen(self) -> None:
        self.troubleshoot_screen.pack_forget()
        self.main_screen.pack(fill=tk.BOTH, expand=True, padx=14, pady=14)
        self.status_var.set("Waiting for RFID taps...")

    def _append_log(self, line: str) -> None:
        ts = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{ts}] {line}\n")
        self.log_text.see(tk.END)

    def _poll_rfid(self) -> None:
        try:
            uid = _read_uid()
            now = time.time()

            if uid and (uid != self.last_uid or (now - self.last_ts) > 1.5):
                self.uid_var.set(uid)
                self.status_var.set("RFID tap detected")
                role = "(not registered)"
                balance = "-"

                if not self.no_db_lookup:
                    user = _lookup_rfid_user(uid)
                    if user:
                        role, bal = user
                        balance = f"{bal:.2f}"

                self.role_var.set(role)
                self.balance_var.set(balance)
                self._append_log(f"UID={uid} role={role} balance={balance}")
                self.last_uid = uid
                self.last_ts = now
        except KeyboardInterrupt:
            self._append_log("Ctrl+C received. Closing UI.")
            self._on_close()
            return

        self.after(self.interval_ms, self._poll_rfid)

    def _on_close(self) -> None:
        self.spi_probe_running = False
        try:
            if GPIO is not None:
                GPIO.cleanup()
        except Exception:
            pass
        self.destroy()

    def _pulse_rst(self) -> None:
        ok, msg = _pulse_reader_reset(pulses=3)
        if ok:
            self.status_var.set("RST pulse sent")
            self._append_log(msg)
        else:
            self.status_var.set("RST pulse failed")
            self._append_log(msg)

    def _probe_spi(self) -> None:
        ok, msg = _probe_mfrc522_spi_link()
        self._update_spi_probe_stats(ok)
        if ok:
            self.status_var.set("SPI link PASS")
        else:
            self.status_var.set("SPI link FAIL")
        self._append_log(msg)

    def _update_spi_probe_stats(self, ok: bool) -> None:
        if ok:
            self.spi_probe_pass_count += 1
            self.spi_pass_var.set(str(self.spi_probe_pass_count))
            return

        self.spi_probe_fail_count += 1
        self.spi_fail_var.set(str(self.spi_probe_fail_count))
        self.spi_probe_last_fail = time.strftime("%H:%M:%S")
        self.spi_last_fail_var.set(self.spi_probe_last_fail)

    def _toggle_spi_probe(self) -> None:
        self.spi_probe_running = not self.spi_probe_running
        if self.spi_probe_running:
            for btn in self.spi_probe_toggle_btns:
                if btn.winfo_exists():
                    btn.configure(text="Stop Continuous SPI Probe", bg="#ef4444", activebackground="#dc2626")
            self.status_var.set("Continuous SPI probe running")
            self._append_log(f"Continuous SPI probe started ({self.spi_probe_interval_ms} ms interval).")
            self._probe_spi_loop_tick()
            return

        for btn in self.spi_probe_toggle_btns:
            if btn.winfo_exists():
                btn.configure(text="Start Continuous SPI Probe", bg="#f59e0b", activebackground="#d97706")
        self.status_var.set("Continuous SPI probe stopped")
        self._append_log("Continuous SPI probe stopped.")

    def _probe_spi_loop_tick(self) -> None:
        if not self.spi_probe_running:
            return

        try:
            ok, msg = _probe_mfrc522_spi_link()
        except KeyboardInterrupt:
            self._append_log("Ctrl+C received. Stopping continuous SPI probe.")
            self.spi_probe_running = False
            self._on_close()
            return

        self._update_spi_probe_stats(ok)

        if ok:
            self.status_var.set("SPI link PASS")
        else:
            self.status_var.set("SPI link FAIL")

        if self.last_spi_probe_state is None or self.last_spi_probe_state != ok:
            self._append_log(msg)
            self.last_spi_probe_state = ok

        self.after(self.spi_probe_interval_ms, self._probe_spi_loop_tick)


def _run_cli(interval_s: float, no_db_lookup: bool, once: bool) -> int:
    print("Single MFRC522 RFID test started.")
    print("Expected wiring: CE0(GPIO8), RST(GPIO5), SCK(11), MOSI(10), MISO(9), 3.3V, GND")
    print("Tap a card/tag to the shared reader... (Ctrl+C to stop)")

    last_uid = None
    last_ts = 0.0

    try:
        while True:
            uid = _read_uid()
            now = time.time()
            if uid and (uid != last_uid or (now - last_ts) > 1.5):
                msg = f"[RFID] UID={uid}"
                if not no_db_lookup:
                    user = _lookup_rfid_user(uid)
                    if user:
                        role, balance = user
                        msg += f" role={role} balance={balance:.2f}"
                    else:
                        msg += " role=(not registered)"
                print(msg)
                last_uid = uid
                last_ts = now
                if once:
                    return 0

            time.sleep(max(0.05, interval_s))
    except KeyboardInterrupt:
        print("\nStopped by user.")
        return 0


def _run_cli_probe_spi_continuous(interval_s: float) -> int:
    print("Continuous SPI probe started. Press Ctrl+C to stop.")
    print(f"Probe interval: {max(0.05, interval_s):.2f}s")

    last_state = None
    try:
        while True:
            ok, msg = _probe_mfrc522_spi_link()
            if last_state is None or last_state != ok:
                print(msg)
                last_state = ok
            time.sleep(max(0.05, interval_s))
    except KeyboardInterrupt:
        print("\nStopped by user.")
        return 0


def _run_ui(interval_s: float, no_db_lookup: bool) -> int:
    if tk is None:
        print("[ERR] Tkinter is not available. Install python3-tk or run without --ui.")
        return 1
    app = RFIDTestUI(interval_s=interval_s, no_db_lookup=no_db_lookup)
    try:
        app.mainloop()
    except KeyboardInterrupt:
        print("\nStopped by user (Ctrl+C).")
        try:
            app._on_close()
        except Exception:
            pass
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Test single shared MFRC522 RFID reader on CE0.")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Exit after first successful RFID tap.",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0.20,
        help="Polling interval in seconds (default: 0.20).",
    )
    parser.add_argument(
        "--no-db-lookup",
        action="store_true",
        help="Disable vending.db role/balance lookup for detected UIDs.",
    )
    parser.add_argument(
        "--ui",
        action="store_true",
        help="Launch a simple touchscreen-friendly UI instead of console output.",
    )
    parser.add_argument(
        "--pulse-rst",
        type=int,
        default=0,
        help="Pulse RFID reset line (GPIO5) N times, then exit (safe wiring check).",
    )
    parser.add_argument(
        "--probe-spi",
        action="store_true",
        help="Probe MFRC522 version register over SPI and print PASS/FAIL.",
    )
    parser.add_argument(
        "--probe-spi-continuous",
        action="store_true",
        help="Continuously probe MFRC522 SPI link until Ctrl+C.",
    )
    parser.add_argument(
        "--probe-spi-interval",
        type=float,
        default=0.35,
        help="Interval in seconds for --probe-spi-continuous (default: 0.35).",
    )
    args = parser.parse_args()

    if MFRC522 is None and SimpleMFRC522 is None:
        print("[ERR] mfrc522 package not available.")
        print("Install with: pip install mfrc522")
        return 1

    ok, err_msg = _init_gpio()
    if not ok:
        print(err_msg)
        return 1

    if args.pulse_rst > 0:
        ok, msg = _pulse_reader_reset(pulses=args.pulse_rst)
        print(msg)
        return 0 if ok else 1

    if args.probe_spi:
        ok, msg = _probe_mfrc522_spi_link()
        print(msg)
        return 0 if ok else 1

    if args.probe_spi_continuous:
        return _run_cli_probe_spi_continuous(args.probe_spi_interval)

    try:
        if args.ui:
            return _run_ui(args.interval, args.no_db_lookup)
        return _run_cli(args.interval, args.no_db_lookup, args.once)
    finally:
        try:
            if GPIO is not None:
                GPIO.cleanup()
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main())
