from machine import UART
import time
import gc

# Setup UART for communication with Node 1 (Arduino)
uart2 = UART(2, baudrate=115200, tx=46, rx=45)  # Change TX and RX to match your configuration
time.sleep(2)  # Allow UART to stabilize

# Define valid GPIOs for control
valid_gpios = [33, 15, 16]


gc.collect()
print(f"Free memory: {gc.mem_free()} bytes")


def control_gpio(pin, state):
    if pin not in valid_gpios:
        print(f"GPIO {pin} is not available for control.")
        return
    
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

    if uart2.any():
        response = uart2.read()
        #print(f"Raw Response (GPIO Control): {response}")
    try:
        print(f"Received (Metrics Data): {response.decode('utf-8').strip()}") 
    except UnicodeError as e:
        print(f"Error decoding response: {e}")
        
def user_input():
    print("\nSelect an option:")
    print("1. Get Metrics")
    print("2. Turn GPIO ON")
    print("3. Turn GPIO OFF")
    print("4. Exit")
    
    option = input("Enter your choice: ")
    
    if option == "1":
        get_metrics()
    elif option == "2" or option == "3":
        gpio = int(input("Enter GPIO number (33, 15, 16): "))
        state = 1 if option == "2" else 0
        control_gpio(gpio, state)
    elif option == "4":
        print("Exiting...")
        return False
    else:
        print("Invalid option, please try again.")
    return True

while True:
    # Obtain metrics every 30 seconds
    print("\nGetting system metrics...")
    get_metrics()
    time.sleep(10)  # Wait for 30 seconds before the next metrics request
    
    # Allow user to select GPIO control or metrics request
    if not user_input():
        break
    time.sleep(1)  # Add a small delay to avoid input flooding
