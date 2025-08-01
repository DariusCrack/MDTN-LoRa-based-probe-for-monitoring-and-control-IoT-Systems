from machine import UART
import time

# Setup UART for communication with Node 1 (Arduino)
uart2 = UART(2, baudrate=115200, tx=46, rx=45)  # Change TX and RX to match your configuration
time.sleep(2)  # Allow UART to stabilize

def control_gpio(pin, state):
    # Send the SET_GPIO command to Node 1 (Arduino)
    command = f"SET_GPIO {pin} {state}\n"
    uart2.write(command)  # Send the command
    print(f"Sent: {command.strip()}")

    # Wait for a response
    if uart2.any():
        response = uart2.read()  # Read incoming message
        print(f"Received (GPIO Control): {response.decode('utf-8').strip()}")  # Print the response in human-readable format

def get_metrics():
    # Send GET_METRICS command to Node 1 (Arduino) to request system metrics
    command = "GET_METRICS\n"
    uart2.write(command)  # Send the command
    print(f"Sent: {command.strip()}")

    # Wait for a response
    if uart2.any():
        response = uart2.read()  # Read incoming message
        print(f"Received (Metrics Data): {response.decode('utf-8').strip()}")  # Print the received metrics

while True:
    # Example of controlling GPIOs
    #control_gpio(33, 1)  # Turn GPIO33 ON
    #time.sleep(5)
    #control_gpio(15, 1)  # Turn GPIO33 OFF
    #time.sleep(5)
   # Get system metrics (temperature, CPU, memory, etc.)
    get_metrics()
    time.sleep(5)  # Wait 5 seconds before the next cycle
