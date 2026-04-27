# 12V Power Budget (Stepper + Solenoid Locks + Coin Acceptor)

Date: 2026-04-28

## What this is based on

This repository confirms the following architecture and hardware:
- 10x 28BYJ-48 stepper motors (12V variant)
- 2x 12V solenoid locks (Model 102)
- 1x 12V coin acceptor (WEIYU 1239/1239A class)
- Separate 12V PSU for motor/solenoid loads
- Common ground between Pi and 12V side

Important: the repo does not include exact current datasheets for the specific vendor part numbers.
So this budget uses conservative, commonly seen values for these classes of parts.

## Assumed current values (conservative)

- 28BYJ-48 12V stepper (one active motor):
  - Typical running estimate: 0.10 A
  - Conservative peak estimate: 0.20 A

- 12V Solenoid lock Model 102 (per lock):
  - Typical pull estimate: 0.80 A
  - Conservative pull-in peak: 1.20 A

- 12V coin acceptor module (always powered when machine is on):
  - Typical running estimate: 0.05 A
  - Conservative estimate: 0.15 A

## Runtime behavior considered

From current code behavior:
- Dispense loop drives one slot motor at a time.
- Door unlock is time-limited pulse (3.0 s).
- Coin acceptor is a continuous background load.
- In normal use, expect one motor and at most one lock active at once.

## Load scenarios

1) Normal expected overlap (1 motor + 1 lock + coin acceptor)
- I = 0.20 + 1.20 + 0.15 = 1.55 A (conservative)

2) Stress overlap (1 motor + 2 locks + coin acceptor)
- I = 0.20 + 1.20 + 1.20 + 0.15 = 2.75 A

3) Extra-future headroom case (2 motors + 2 locks + coin acceptor)
- I = 0.20 + 0.20 + 1.20 + 1.20 + 0.15 = 2.95 A

## PSU sizing rule

Use at least 50% headroom for inductive transient loads and wiring loss:

Required PSU current >= 1.5 x I_peak

Using I_peak = 2.95 A:
- Minimum practical PSU = 4.43 A
- Choose nearest standard size: 12V 5A

## Recommendation

- Recommended minimum for current build: 12V 5A
- Preferred for cleaner transients and future expansion: 12V 8A

So, you do not need two separate 12V PSUs by default.
A single quality 12V PSU is enough if it is at least 5A (8A preferred).

If the coin acceptor datasheet for your exact module revision lists more than 0.15 A,
recalculate with that value and treat 8A as the default pick.

## When to split into two separate 12V PSUs

Use separate 12V rails (or separate PSU units) if you observe any of these:
- Solenoid unlock causes motor stalls/skips
- Relay chatter during unlock
- 12V rail sag below ~11.4V during pulses
- Random resets/noise symptoms during inductive switching

If splitting supplies, keep grounds common for signal reference.

## Quick verification on real hardware

1. Put a DC clamp meter on the 12V output wire.
2. Trigger worst case: unlock while dispensing.
3. Record peak current and minimum voltage.
4. Keep at least 30-50% margin above measured peak.

If measured peak exceeds 3.5A, move directly to 12V 8A+.
