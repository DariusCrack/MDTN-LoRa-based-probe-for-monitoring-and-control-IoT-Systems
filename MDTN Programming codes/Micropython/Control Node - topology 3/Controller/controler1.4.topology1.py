from machine import UART
import time
import sys
import select

# UART Setup (TX=46, RX=45)
uart2 = UART(2, baudrate=115200, tx=46, rx=45)
time.sleep(2)

valid_gpios = [15, 16, 38, 39, 40]

MENU_INTERVAL = 27
last_menu_time = time.time()

input_buffer = ""  # Stores ongoing keyboard input
awaiting_gpio = False
gpio_action = None  # "on" or "off"

def print_menu():
    print("\n=== MENU OPTIONS ===")
    print("1. Request Metrics Manually")
    print("2. Reset Node")
    print("3. Turn GPIO ON")
    print("4. Turn GPIO OFF")
    print("5. Exit Program")
    print("====================")

def send_get_metrics():
    uart2.write("GET_METRICS\n")
    print(">> Sent: GET_METRICS")

def send_reset():
    uart2.write("RESET\n")
    print(">> Sent: RESET")

def send_gpio(pin, state):
    if pin not in valid_gpios:
        print(f"[Invalid GPIO] GPIO {pin} not supported.")
        return
    uart2.write(f"SET_GPIO {pin} {state}\n")
    print(f">> Sent: SET_GPIO {pin} {state}")

def handle_command(command):
    command = command.strip()

    if command == "1":
        send_get_metrics()

    elif command == "2":
        send_reset()

    elif command == "3":
        print("Enter a valid GPIO [15, 16, 38, 39, 40] number to turn ON (or 'c' to cancel):")
        gpio = input().strip()
        if gpio.lower() == "c":
            print("[CANCELLED] GPIO input cancelled.")
            return
        try:
            pin = int(gpio)
            send_gpio(pin, 1)
        except ValueError:
            print("[Error] Invalid GPIO number.")

    elif command == "4":
        print("Enter GPIO [15, 16, 38, 39, 40] number to turn OFF (or 'c' to cancel):")
        gpio = input().strip()
        if gpio.lower() == "c":
            print("[CANCELLED] GPIO input cancelled.")
            return
        try:
            pin = int(gpio)
            send_gpio(pin, 0)
        except ValueError:
            print("[Error] Invalid GPIO number.")

    elif command == "5":
        print(">> Exiting...")
        sys.exit()

    elif command == "":
        pass  # Ignore empty input

    else:
        print("[Invalid Option] Use 1-5.")

print(">> CONTROLLER ACTIVE - UART Listening Mode")

while True:
    now = time.time()

    # Periodic menu
    if now - last_menu_time >= MENU_INTERVAL:
        print_menu()
        last_menu_time = now

    # UART reception
    if uart2.any():
        try:
            data = uart2.read().decode('utf-8').strip()
            if data:
                print(f"[NODE] {data}")
        except Exception as e:
            print(f"[UART ERROR] {e}")

    # Non-blocking input handling
    if select.select([sys.stdin], [], [], 0.01)[0]:
        char = sys.stdin.read(1)
        if char == '\n':
            handle_command(input_buffer)
            input_buffer = ""
        else:
            input_buffer += char

    time.sleep(0.05)
