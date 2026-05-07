# I2C Bus Troubleshooting Guide (MCP23017 errno 121)

## Problem Statement
`i2cdetect -y 1` successfully detects MCP23017 expander boards (0x20, 0x21, 0x22), but running `stepper_mcp.py` or `main.py` fails with:
```
errno 121 - Remote I/O error
I2C remote I/O error while probing/configuring 0x20, 0x21, or 0x22
```

This means the Pi can see the bus level transaction, but the MCP chip is **not ACKing** the register read/write command. This is a **hardware connectivity issue**, not a software bug.

---

## Root Causes & Fixes

### 1. **SDA/SCL Lines Swapped or Loose**
**Symptom:** I2C detection works but reads fail immediately.

**Check:**
- Measure voltage on GPIO2 (SDA) and GPIO3 (SCL) with multimeter
  - Should idle at ~1.5–3.3V (pulled up by 1.8k resistors on Pi)
  - Should **not** be 0V or floating
- Verify physical wire connections:
  - Pi GPIO2 (Physical pin 3) → MCP SDA
  - Pi GPIO3 (Physical pin 5) → MCP SCL
  - Use multimeter continuity check: Pi pin → MCP pin should ring continuously

**Fix:**
- Reseat all SDA/SCL wires on breadboard or solder joints
- If cold solder joint suspected, reflow solder or use new wire
- Try swapping SDA/SCL intentionally to rule out (will definitely fail), then swap back

---

### 2. **Missing or Broken Common Ground**
**Symptom:** Intermittent failures or errno 121 on multiple devices.

**Check:**
- Measure voltage between Pi GND and SMPS GND with multimeter (should read 0 ohms/0V)
- Measure voltage between Pi GND and each MCP VSS pin (should read 0 ohms/0V)
- Measure voltage between SMPS GND and each MCP VSS pin (should read 0 ohms/0V)
- Inspect all GND wires for corrosion, loose connections, or breaks

**Fix:**
- Add multiple GND wires if layout is spread out:
  - Pi GND → breadboard/rail
  - SMPS GND → same rail
  - MCP VSS pins → same rail (multiple wires to different MCP boards)
- Check solder joints on GND pins (should be shiny and solid)
- Use thicker gauge GND wire if dealing with high current

---

### 3. **MCP VDD Power Failure (3.3V Missing)**
**Symptom:** Chip detectable by `i2cdetect` but fails on first register operation.

**Check:**
- Measure voltage at MCP VDD pin with multimeter
  - Should read 3.3V ±5% (i.e., 3.135V to 3.465V)
  - If reading below 3.0V, investigate power supply
- Check Pi's 3.3V rail is stable (no brown-out)
- Count how many MCP boards are on the same 3.3V line
  - Each MCP draws ~0.1A max; pi 3.3V regulator can typically supply ~0.5A

**Fix:**
- If voltage is low, check:
  - No solder bridges on Pi 3.3V line
  - 3.3V pins are properly soldered to power rail
  - Pi power supply is adequate (should deliver ≥2–3A total)
- If Pi is over-loaded, reduce number of MCP boards or add external 3.3V regulator

---

### 4. **Missing RESET Pull-Up Resistor**
**Symptom:** Device address shows in `i2cdetect`, but reads fail unpredictably.

**Check:**
- Inspect MCP board: look for resistor on RESET pin
- Measure resistance between RESET pin and 3.3V line
  - Should be 4.7kΩ to 10kΩ (not open circuit, not 0Ω)
- If no resistor present, RESET pin is floating and chip initialization fails

**Fix:**
- **Add resistor:** Connect 4.7kΩ–10kΩ resistor from MCP RESET pin to 3.3V
  - Use small resistor and breadboard if PCB soldering is risky
  - Verify resistance with multimeter after adding

---

### 5. **Address Straps (A0, A1, A2) Misconfigured**
**Symptom:** Device detected at wrong address or address conflicts.

**Check:**
- Verify strap settings on each MCP23017 chip:
  - **MCP #1 (address 0x20):** A0=GND, A1=GND, A2=GND
  - **MCP #2 (address 0x21):** A0=3.3V, A1=GND, A2=GND
  - **MCP #3 (address 0x22):** A0=GND, A1=3.3V, A2=GND
- Measure voltage at each strap pin with multimeter:
  - Should read 0V (tied to GND) or 3.3V (tied to 3.3V)
  - Should **not** be floating
- Run `i2cdetect -y 1` and note actual addresses seen

**Fix:**
- If strap voltage is floating (1.5V–2V), tie it explicitly:
  - Use wire or resistor to connect to GND or 3.3V
  - Do not rely on PCB default (trace may be weak)
- If addresses don't match expected, update `MCP23017_ADDRESSES` env var in `run_stepper_mcp.txt` or `main.py`

---

### 6. **Intermittent Connection (Marginal/Cold Joint)**
**Symptom:** `i2cdetect -y 1` sometimes shows devices, sometimes doesn't. Errno 121 on first run, but works after reboot.

**Check:**
- Run repeated detection to confirm intermittency:
  ```bash
  for i in {1..10}; do
    echo "=== Attempt $i ==="
    i2cdetect -y 1
    sleep 1
  done
  ```
  - If addresses disappear/reappear, suspect loose wire or cold joint
- Inspect solder joints visually:
  - Shiny, smooth solder = good
  - Dull, grainy, or blob-like solder = cold joint
- Try gently wiggling wires to see if detection fails

**Fix:**
- Reseat all connections (remove and re-insert)
- If soldered, reflow suspected cold joints with soldering iron
- Replace worn/kinked wires
- If using breadboard, move to different row (may have weak contacts)

---

### 7. **I2C Bus Hung or Requires Reset**
**Symptom:** Device detection and reads work initially, then all fail. Reboot fixes it.

**Check:**
- Stop all Python scripts accessing I2C:
  ```bash
  pkill -f "stepper_mcp\|main\.py"
  ```
- Retry `i2cdetect -y 1`

**Fix:**
- Power cycle the Raspberry Pi (reboot)
- Or unplug MCP boards for 10 seconds, re-insert, and retry
- If problem persists, check for other I2C devices interfering (EEPROM, sensor, etc.)

---

## Hardware Checklist

Before running software, physically verify:

- [ ] **SDA/SCL wired:** Pi GPIO2 → MCP SDA, Pi GPIO3 → MCP SCL
- [ ] **Continuity check:** Measure 0Ω resistance between each Pi pin and MCP pin
- [ ] **Common ground:** Pi GND = SMPS GND = all MCP VSS pins
- [ ] **3.3V voltage:** Measure 3.3V ±5% at each MCP VDD pin
- [ ] **RESET pull-up:** Resistor (4.7k–10k) present between MCP RESET and 3.3V
- [ ] **A0/A1/A2 straps:** Measure voltage at each strap pin (should be 0V or 3.3V, not floating)
- [ ] **No cold solder joints:** Inspect solder visually (shiny, smooth)
- [ ] **No loose wires:** Wiggle each connection; should not shift or disconnect

---

## Quick Diagnostic Workflow

1. **Power cycle:**
   ```bash
   sudo reboot
   ```

2. **Detect devices:**
   ```bash
   sudo apt install -y i2c-tools
   i2cdetect -y 1
   ```
   - If devices show 0x20, 0x21, 0x22 (or expected addresses), move to step 3
   - If no devices, check power and ground first

3. **Run stepper test:**
   ```bash
   source venv/bin/activate
   export DISPLAY=:0
   export MCP23017_ADDRESSES=0x20,0x21,0x22
   python stepper_mcp.py
   ```
   - If "MCP setup failed" or errno 121, refer to section above matching symptom

4. **If errno 121 persists:**
   - Measure voltages (SDA/SCL, 3.3V, GND continuity)
   - Verify address straps
   - Check RESET pull-up resistor
   - Reflow solder or reseat connections

5. **Once working:**
   - Run `Detect MCP` button in stepper_mcp.py UI
   - Verify "Detected MCP: 0x20, 0x21, 0x22" status line
   - Test individual slots with stepper_mcp.py before running main.py

---

## Power Supply Specs (Reference)

For this project:
- **12V PSU:** 12V / 12.5A SMPS (150W continuous)
- **All ULN2003 boards:** +12V from SMPS (not Pi 5V)
- **All solenoid locks:** +12V from SMPS
- **MCP23017 logic:** 3.3V from Pi
- **Common ground:** Pi GND must equal SMPS GND (use multiple wires)

---

## When to Escalate

If all above checks pass but errno 121 persists:
1. Swap a known-working MCP board to verify chip isn't defective
2. Try a shorter I2C bus (reduce wire length, remove breadboard if possible)
3. Check if I2C pull-up resistors on bus are correct (Pi has 1.8kΩ internal on GPIO2/3)
4. Consider external 2.2kΩ pull-ups if bus is very long or has many devices

---

## References

- [MCP23017 Datasheet](https://www.microchip.com/en-us/product/MCP23017)
- [Raspberry Pi 5 GPIO Documentation](https://www.raspberrypi.com/documentation/computers/os.html)
- Linux errno 121 = `EREMOTEIO` (remote I/O error, typically NACK on bus)
