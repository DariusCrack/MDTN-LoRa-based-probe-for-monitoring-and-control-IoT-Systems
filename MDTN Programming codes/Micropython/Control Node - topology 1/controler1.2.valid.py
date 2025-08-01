from machine import UART
import time

# Setup UART for communication with Node 1 (Arduino)
uart2 = UART(2, baudrate=115200, tx=46, rx=45)  # Change TX and RX to match your configuration
time.sleep(2)  # Allow UART to stabilize

# Define valid GPIOs for control (extended to include more pins)
valid_gpios = [33, 15, 16, 17, 18, 19, 21, 22, 23, 25, 26, 27, 32, 34, 35, 36, 39]

def control_gpio(pin, state):
    if pin not in valid_gpios:
        print(f"GPIO {pin} is not available for control.")
        return
    
    # Send the SET_GPIO command to Node 1 (Arduino)
    command = f"SET_GPIO {pin} {state}\n"
    uart2.write(command)  # Send the command
    print(f"Sent: {command.strip()}")

    # Wait for a response
    time.sleep(3)
    if uart2.any():
        response = uart2.read()  # Read incoming message
        print(f"Received (GPIO Control): {response.decode('utf-8').strip()}")  # Print the response in human-readable format

def reset_node1():
    # Send the RESET command to Node 1 (Arduino)
    command = "RESET\n"
    uart2.write(command)  # Send the command
    print(f"Sent: {command.strip()}")

    # Wait for a response
    time.sleep(3)
    if uart2.any():
        response = uart2.read()  # Read incoming message
        print(f"Received (Reset): {response.decode('utf-8').strip()}")  # Print the response

def get_metrics():
    # Send GET_METRICS command to Node 1 (Arduino) to request system metrics
    command = "GET_METRICS\n"
    uart2.write(command)  # Send the command
    print(f"Sent: {command.strip()}")
    
    # Wait for a response
    time.sleep(3)
    if uart2.any():
        response = uart2.read()  # Read incoming message
        print(f"Received (Metrics Data): {response.decode('utf-8').strip()}")  # Print the received metrics

def user_input():
    print("\nSelect an option:")
    print("1. Get Metrics")
    print("2. Turn GPIO ON")
    print("3. Turn GPIO OFF")
    print("4. Reset Node 1")
    print("5. Exit")
    
    option = input("Enter your choice: ")
    
    if option == "1":
        get_metrics()
    elif option == "2" or option == "3":
        gpio = int(input("Enter GPIO number (33, 15, 16, etc.): "))
        state = 1 if option == "2" else 0
        control_gpio(gpio, state)
    elif option == "4":
        reset_node1()
    elif option == "5":
        print("Exiting...")
        return False
    else:
        print("Invalid option, please try again.")
    return True

while True:
    # Allow user to select GPIO control or metrics request
    if not user_input():
        break
    time.sleep(1)  # Add a small delay to avoid input flooding
