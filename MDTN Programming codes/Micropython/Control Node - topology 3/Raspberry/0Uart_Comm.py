#!/usr/bin/env python3
"""
uart_test_pi.py

Every 30 seconds:
  - Check if the PL011 UART (/dev/ttyAMA0) is open.
    • If open: print "UART Available", send "hello\n", print send message,
      then wait up to 2 s for a response and print what was received (or “No response”).
    • If not open: print "UART Not Available"
"""

import time
import serial

UART_PORT = "/dev/ttyAMA0"
BAUDRATE  = 115200
INTERVAL  = 30  # seconds
TIMEOUT   = 2   # seconds for read timeout

def main():
    try:
        ser = serial.Serial(UART_PORT, BAUDRATE, timeout=TIMEOUT)
    except serial.SerialException:
        ser = None

    while True:
        if ser and ser.is_open:
            print("UART Available")
            # 1) Send greeting
            print("Sent: hello")
            ser.write(b"hello\n")

            # 2) Await response
            resp = ser.readline().decode('utf-8', errors='ignore').strip()
            if resp:
                print(f"Received: {resp}")
            else:
                print("No response")
        else:
            print("UART Not Available")

        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()
