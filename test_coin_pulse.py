#!/usr/bin/env python3
"""
Test script to verify GPIO 19 is receiving coin acceptor pulses.
Run this while the coin acceptor is active to see real-time pulse detection.
"""

import time
import sys
import signal

try:
    import RPi.GPIO as GPIO
    ON_RPI = True
except ImportError:
    print("ERROR: RPi.GPIO not available. This test requires a Raspberry Pi.")
    sys.exit(1)

GPIO_PIN = 19  # Coin acceptor pulse input
PULSE_EDGE = "falling"  # falling, rising, or both
BOUNCETIME_MS = 50

pulse_count = 0
pulse_times = []


def pulse_callback(channel):
    """Called on each pulse detection."""
    global pulse_count
    pulse_count += 1
    current_time = time.time()
    pulse_times.append(current_time)
    
    # Keep only last 10 pulse times for rate calculation
    if len(pulse_times) > 10:
        pulse_times.pop(0)
    
    # Calculate pulse rate if we have enough samples
    if len(pulse_times) >= 2:
        time_span = pulse_times[-1] - pulse_times[0]
        if time_span > 0:
            rate = (len(pulse_times) - 1) / time_span
            print(f"[PULSE] Count: {pulse_count:4d} | Rate: {rate:.1f} pulses/sec")
        else:
            print(f"[PULSE] Count: {pulse_count:4d} | Rate: (calculating...)")
    else:
        print(f"[PULSE] Count: {pulse_count:4d} | Waiting for more samples...")


def main():
    global pulse_count
    
    print("=" * 60)
    print("GPIO 19 (Coin Acceptor Pulse) Monitor")
    print("=" * 60)
    print(f"Pin:       GPIO 19 (Physical Pin 35)")
    print(f"Edge:      {PULSE_EDGE.upper()}")
    print(f"Bouncetime: {BOUNCETIME_MS}ms")
    print(f"\nMonitoring for pulses... (Ctrl+C to exit)")
    print("=" * 60)
    print()
    
    try:
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(GPIO_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        # Determine edge constant
        if PULSE_EDGE == "rising":
            edge = GPIO.RISING
        elif PULSE_EDGE == "falling":
            edge = GPIO.FALLING
        else:
            edge = GPIO.BOTH
        
        # Add event detection
        GPIO.add_event_detect(
            GPIO_PIN,
            edge,
            callback=pulse_callback,
            bouncetime=BOUNCETIME_MS
        )
        
        print(f"✓ GPIO 19 event detection active on {edge} edge\n")
        
        # Monitor for pulses
        start_time = time.time()
        last_count = 0
        
        while True:
            time.sleep(1)
            elapsed = time.time() - start_time
            
            # Print status every 5 seconds
            if int(elapsed) % 5 == 0 and pulse_count > last_count:
                last_count = pulse_count
                # Status will be printed by callback
            elif pulse_count == 0 and int(elapsed) % 5 == 0:
                print(f"[STATUS] No pulses detected yet ({elapsed:.0f}s elapsed)")
    
    except KeyboardInterrupt:
        print("\n" + "=" * 60)
        print(f"Test stopped. Total pulses detected: {pulse_count}")
        if pulse_count > 0:
            elapsed = pulse_times[-1] - pulse_times[0] if len(pulse_times) > 1 else 0
            if elapsed > 0:
                avg_rate = (len(pulse_times) - 1) / elapsed if len(pulse_times) > 1 else 0
                print(f"Average pulse rate: {avg_rate:.1f} pulses/sec")
        print("=" * 60)
    
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        GPIO.cleanup()
        print("GPIO cleaned up.")


if __name__ == "__main__":
    main()
