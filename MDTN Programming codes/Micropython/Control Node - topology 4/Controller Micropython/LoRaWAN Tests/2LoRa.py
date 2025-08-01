# lorawan_app.py

import time
import binascii
from machine import Pin, SPI
from ulora.core import ULoRa

# 1) Inicializar bus SPI con pines del T3-S3
spi = SPI(1,
          baudrate=5000000,
          polarity=0,
          phase=0,
          sck=Pin(5),
          mosi=Pin(6),
          miso=Pin(3))

# 2) Definir mapeo de pines para SX1276
pins = {
    "ss":    7,   # CS → GPIO7
    "reset": 8,   # RESET → GPIO8
    "dio0":  33   # DIO0 → GPIO33
    # "busy":  34   # Si lo quieres usar (no obligatorio)
    # "dio1":  34   # (opcional, no lo necesitamos para OTAA básico)
}

# 3) Crear la instancia ULoRa
print("Initializing ULoRa (SX1276)…")
radio = ULoRa(spi, pins)

# 4) Claves OTAA (llenar con tus valores de TTN)
dev_eui = binascii.unhexlify("70B3D57ED007135C")
app_eui = binascii.unhexlify("0000000000000000")
app_key = binascii.unhexlify("E7847552F5E659A09A96F25FAB667234")

print("Joining TTN via OTAA…")
radio.join(dev_eui=dev_eui, app_eui=app_eui, app_key=app_key, timeout_ms=20000)

if radio.has_joined():
    print("✅ Joined TTN! DevAddr = 0x%08X" % radio.dev_addr)
else:
    print("❌ Join failed")

# 5) Abrimos socket “ficticio” (ya no lo necesitamos, pues usamos radio.send/receive)
#    De aquí en adelante llamamos directamente a radio.send() y radio.receive()

counter = 0
while True:
    data = b"MSG%03d" % counter
    print("Sending uplink:", data)
    radio.send(data, port=1)
    counter += 1

    # Esperar un posible downlink en los siguientes 5 segundos
    down = radio.receive(timeout_ms=5000)
    if down:
        print("↓ Received downlink payload:", down)

    time.sleep(30)  # Rate‐limit TTN (1 uplink cada 30 s)
