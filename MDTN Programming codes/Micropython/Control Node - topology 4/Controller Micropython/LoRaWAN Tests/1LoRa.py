#
# File: send_simulated_temp.py
# Purpose: Join TTN (EU868) via OTAA and send a simulated temperature every 10 s
#

import time
import ustruct
import binascii
import machine
from network import LoRa
import socket
import urandom

# ————————————————————————————————————————————————————————————————————————————————
# 1) Copy your TTN OTAA credentials exactly as shown in the Device page
#
#    From your screenshot:
#      AppEUI: 00 00 00 00 00 00 00 00
#      DevEUI: 70 B3 D5 7E D0 07 13 5C
#      AppKey: 40 E3 D0 2C A7 B1 B7 DD DF C7 8C 4B A1 C3 40 99
#
#  Note: remove spaces and convert to raw bytes with binascii.unhexlify(…)
#———————————————————————————————————————————————————————————————————————————————

# (8 bytes, all zeros)
app_eui = binascii.unhexlify("0000000000000000")

# (8 bytes)
dev_eui = binascii.unhexlify("70B3D57ED007135C")

# (16 bytes)
app_key = binascii.unhexlify("40E3D02CA7B1B7DDDFC78C4BA1C34099")


# ————————————————————————————————————————————————————————————————————————————————
# 2) Initialize the LoRa radio and perform an OTAA join
#
#    - FREQ PLAN: EU868
#    - LoRaWAN version: 1.0.3
#———————————————————————————————————————————————————————————————————————————————

lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.EU868)

print("Starting OTAA join…")
lora.join(activation=LoRa.OTAA, auth=(dev_eui, app_eui, app_key), timeout=0)

# Wait until joined
while not lora.has_joined():
    time.sleep(2.5)
    print(".", end="")

print("\n✅ Joined TTN!")


# ————————————————————————————————————————————————————————————————————————————————
# 3) Create a raw LoRa socket for sending uplinks
#
#    We’ll use DR5 (SF7) for uplinks. Block=False so we don’t stall if no downlink arrives.
#———————————————————————————————————————————————————————————————————————————————

lora_sock = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
lora_sock.setsockopt(socket.SOL_LORA, socket.SO_DR, 5)   # DR=5 → SF7/BW125
lora_sock.setblocking(False)


# ————————————————————————————————————————————————————————————————————————————————
# 4) Simulation of “temperature” data
#
#    We’ll generate a pseudo-random temperature between 20.00 °C and 30.00 °C each cycle.
#    Then pack as a signed int16 of (temp × 100) in big‐endian order.
#
#    For example:
#      25.73 °C → int(25.73 * 100) = 2573 → b'\x0a\x0d' (0x0A0D in hex)
#———————————————————————————————————————————————————————————————————————————————

def get_simulated_temperature():
    """
    Returns a “fake” float temperature between 20.00 and 30.00
    Uses urandom.getrandbits to generate two bytes of randomness,
    then map that uniformally into the 20–30 °C range.
    """
    # Get a random 16-bit integer:
    r = urandom.getrandbits(16)  # 0..65535
    # Scale to [0.0 … 1.0):
    frac = r / 65535.0
    # Map into [20.00 … 30.00):
    temp = 20.0 + (10.0 * frac)
    return temp


def encode_temperature(temp_c):
    """
    Encode a float temperature (°C) into 2-byte signed int16 = (temp * 100).
    Big-endian packing (MSB first) → use ustruct.pack(">h", …)
    """
    # Multiply by 100 and round to nearest integer
    ti = int(temp_c * 100)
    # Pack as signed 16-bit big-endian
    return ustruct.pack(">h", ti)


# ————————————————————————————————————————————————————————————————————————————————
# 5) Main loop: every 10 seconds, simulate a temperature and send as a LoRaWAN uplink
#———————————————————————————————————————————————————————————————————————————————

SEND_INTERVAL_S = 10

while True:
    # 1) Simulate a temperature reading
    temp_c = get_simulated_temperature()
    print("Simulated temperature: %.2f °C" % temp_c)

    # 2) Encode into 2 bytes
    payload = encode_temperature(temp_c)
    #    If you’d like to send multiple fields, just concatenate more bytes:
    #    e.g. battery_voltage (uint16), humidity (uint8), etc.

    # 3) Send the uplink (non-blocking)
    try:
        lora_sock.send(payload)
        print("📡 Uplink sent: %s" % payload)
    except Exception as e:
        print("❌ Error sending uplink:", e)

    # 4) Optionally check for a downlink (nonblock). 
    #    If TTN has queued a downlink for us (e.g. a command), it will arrive here.
    #    We give TTN a short window to deliver (a few hundred ms). If none, recv() returns None.
    down = lora_sock.recv(64)  # up to 64 bytes; return None immediately if no data
    if down:
        print("⬇️  Downlink received (raw):", down)
        # TODO: decode your downlink bits → map to commands, etc.

    # 5) Sleep until next interval
    for i in range(SEND_INTERVAL_S):
        time.sleep(1)
    # Back to top of loop: simulate next temp and send again
