import RPi.GPIO as GPIO
import time

PIN = 17  # GPIO17 (Physical pin 11)

GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN, GPIO.OUT)

try:
    while True:
        GPIO.output(PIN, GPIO.HIGH)
        print("LED ON")
        time.sleep(1)

        GPIO.output(PIN, GPIO.LOW)
        print("LED OFF")
        time.sleep(1)

except KeyboardInterrupt:
    print("Program stopped")

finally:
    GPIO.cleanup()