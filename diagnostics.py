"""
Hardware diagnostics module for integrated testing within the troubleshooting UI.
Wraps standalone test scripts and provides structured output for dashboard display.
"""

import time
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Optional, Dict, Any

try:
    import RPi.GPIO as GPIO
    ON_RPI = True
except ImportError:
    GPIO = None
    ON_RPI = False

try:
    from smbus2 import SMBus
except ImportError:
    try:
        from smbus import SMBus
    except ImportError:
        SMBus = None


@dataclass
class TestResult:
    """Result of a diagnostic test."""
    name: str
    status: str  # "PASS", "FAIL", "ERROR", "RUNNING", "PENDING"
    message: str
    timestamp: datetime
    duration_s: float = 0.0
    details: Optional[Dict[str, Any]] = None


class DiagnosticsRunner:
    """Runs hardware diagnostics and provides callbacks for UI updates."""

    def __init__(self):
        self.results: Dict[str, TestResult] = {}
        self.callbacks: Dict[str, list] = {
            "on_result_update": [],
            "on_test_start": [],
            "on_test_complete": [],
        }
        self.is_running = False

    def on_result_update(self, callback: Callable):
        """Register callback for result updates: callback(test_name, result)"""
        self.callbacks["on_result_update"].append(callback)

    def on_test_start(self, callback: Callable):
        """Register callback when test starts: callback(test_name)"""
        self.callbacks["on_test_start"].append(callback)

    def on_test_complete(self, callback: Callable):
        """Register callback when test finishes: callback(test_name, result)"""
        self.callbacks["on_test_complete"].append(callback)

    def _emit_event(self, event_name: str, *args, **kwargs):
        """Emit an event to all registered callbacks."""
        for callback in self.callbacks.get(event_name, []):
            try:
                callback(*args, **kwargs)
            except Exception as e:
                print(f"[Diagnostics] Callback error in {event_name}: {e}")

    def _create_result(self, name: str, status: str, message: str, duration_s: float = 0.0, details: Optional[Dict] = None) -> TestResult:
        result = TestResult(
            name=name,
            status=status,
            message=message,
            timestamp=datetime.now(),
            duration_s=duration_s,
            details=details or {},
        )
        self.results[name] = result
        self._emit_event("on_result_update", name, result)
        return result

    def test_gpio_pins(self, pins: Dict[str, int], output_test: bool = True) -> TestResult:
        """Test GPIO pins for connectivity."""
        test_name = "GPIO Pins"
        self._emit_event("on_test_start", test_name)
        start_time = time.time()

        if not ON_RPI:
            return self._create_result(test_name, "SKIP", "Not on Raspberry Pi", time.time() - start_time)

        try:
            if GPIO is None:
                return self._create_result(test_name, "FAIL", "GPIO library not available", time.time() - start_time)

            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)

            results_detail = []
            for label, pin in pins.items():
                try:
                    GPIO.setup(pin, GPIO.IN)
                    state = GPIO.input(pin)
                    results_detail.append(f"{label} (GPIO{pin}): {state}")
                except Exception as e:
                    results_detail.append(f"{label} (GPIO{pin}): ERROR - {e}")

            message = "GPIO pins readable"
            status = "PASS"
            duration = time.time() - start_time
            return self._create_result(test_name, status, message, duration, {"pins": results_detail})
        except Exception as e:
            return self._create_result(test_name, "ERROR", str(e), time.time() - start_time)
        finally:
            try:
                GPIO.cleanup()
            except Exception:
                pass
            self._emit_event("on_test_complete", test_name, self.results.get(test_name))

    def test_ir_sensor(self, pin: int = 26, duration_s: float = 3.0) -> TestResult:
        """Test IR break-beam sensor."""
        test_name = "IR Break-Beam Sensor"
        self._emit_event("on_test_start", test_name)
        start_time = time.time()

        if not ON_RPI:
            return self._create_result(test_name, "SKIP", "Not on Raspberry Pi", 0.0)

        try:
            if GPIO is None:
                return self._create_result(test_name, "FAIL", "GPIO library not available", time.time() - start_time)

            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

            readings = []
            deadline = time.time() + duration_s
            while time.time() < deadline:
                state = GPIO.input(pin)
                readings.append("BROKEN" if state == GPIO.LOW else "CLEAR")
                time.sleep(0.1)

            has_breaks = "BROKEN" in readings
            message = f"IR sensor responsive ({len(readings)} readings, {readings.count('BROKEN')} breaks detected)"
            status = "PASS" if has_breaks or readings else "WARN"
            duration = time.time() - start_time
            return self._create_result(test_name, status, message, duration, {"readings": readings[-10:], "break_count": readings.count("BROKEN")})
        except Exception as e:
            return self._create_result(test_name, "ERROR", str(e), time.time() - start_time)
        finally:
            try:
                GPIO.cleanup()
            except Exception:
                pass
            self._emit_event("on_test_complete", test_name, self.results.get(test_name))

    def test_i2c_devices(self, bus_num: int = 1) -> TestResult:
        """Scan for I2C devices (MCP23017 expanders, etc)."""
        test_name = "I2C Devices"
        self._emit_event("on_test_start", test_name)
        start_time = time.time()

        if not ON_RPI or SMBus is None:
            return self._create_result(test_name, "SKIP", "I2C not available", 0.0)

        try:
            bus = SMBus(bus_num)
            devices = []
            for addr in range(0x08, 0x78):
                try:
                    bus.read_byte(addr)
                    devices.append(f"0x{addr:02x}")
                except Exception:
                    pass
            bus.close()

            message = f"Found {len(devices)} I2C device(s): {', '.join(devices)}"
            status = "PASS" if devices else "WARN"
            duration = time.time() - start_time
            return self._create_result(test_name, status, message, duration, {"devices": devices})
        except Exception as e:
            return self._create_result(test_name, "ERROR", str(e), time.time() - start_time)
        finally:
            self._emit_event("on_test_complete", test_name, self.results.get(test_name))

    def test_mcp23017_leds(self, address: int = 0x20) -> TestResult:
        """Test MCP23017 LED outputs."""
        test_name = "MCP23017 LEDs"
        self._emit_event("on_test_start", test_name)
        start_time = time.time()

        if not ON_RPI or SMBus is None:
            return self._create_result(test_name, "SKIP", "I2C not available", 0.0)

        try:
            bus = SMBus(1)
            # Set port A as outputs, all low
            bus.write_byte_data(address, 0x00, 0x00)  # IODIRA
            bus.write_byte_data(address, 0x14, 0xFF)  # OLATA on
            time.sleep(0.2)
            bus.write_byte_data(address, 0x14, 0x00)  # OLATA off
            bus.close()

            message = "MCP23017 LED test completed"
            status = "PASS"
            duration = time.time() - start_time
            return self._create_result(test_name, status, message, duration)
        except Exception as e:
            return self._create_result(test_name, "ERROR", str(e), time.time() - start_time)
        finally:
            self._emit_event("on_test_complete", test_name, self.results.get(test_name))

    def run_all_tests(self, callback_progress: Optional[Callable] = None):
        """Run all diagnostics in a thread."""
        def _run():
            self.is_running = True
            tests = [
                ("GPIO Pins", lambda: self.test_gpio_pins({"IR_Break": 26, "Coin_Acceptor": 17})),
                ("IR Sensor", lambda: self.test_ir_sensor()),
                ("I2C Devices", lambda: self.test_i2c_devices()),
                ("MCP23017 LEDs", lambda: self.test_mcp23017_leds()),
            ]
            for idx, (name, test_fn) in enumerate(tests):
                if callback_progress:
                    callback_progress(idx + 1, len(tests))
                try:
                    test_fn()
                except Exception as e:
                    self._create_result(name, "ERROR", str(e), 0.0)
            self.is_running = False

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
