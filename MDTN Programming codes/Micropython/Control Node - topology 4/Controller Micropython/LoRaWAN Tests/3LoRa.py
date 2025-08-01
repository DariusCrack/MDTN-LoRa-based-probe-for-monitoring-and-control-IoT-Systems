# main.py  (o tu script 3LoRa.py corregido)

from machine import SPI, Pin
import binascii
import time
from ulora.core import ULoRa


# 1) Inicializar SPI (p.ej. SPI(1, ...) con pines adecuados)
spi = SPI(1,
          baudrate=5000000,
          polarity=0,
          phase=0,
          sck=Pin(5),
          mosi=Pin(6),
          miso=Pin(3))

# 2) Definir los pines del SX1276 en tu T3-S3 LilyGo
pins = {
    "ss":    7,    # CS → GPIO7
    "reset": 8,    # RESET → GPIO8
    "dio0":  33    # DIO0 → GPIO33
}

# 3) Crear objeto ULoRa
radio = ULoRa(spi, pins)

# 4) Claves OTAA (en hexadecimal)
dev_eui = binascii.unhexlify("70B3D57ED007135C")
app_eui = binascii.unhexlify("0000000000000000")
app_key = binascii.unhexlify("E7847552F5E659A09A96F25FAB667234")

# 5) Unir vía OTAA (esperando hasta 20 segundos)
print("Joining TTN via OTAA…")
radio.join(dev_eui=dev_eui, app_eui=app_eui, app_key=app_key, timeout_ms=20000)

if radio.has_joined():
    print("✅ Joined TTN! DevAddr = 0x%08X" % radio.dev_addr)
else:
    print("❌ Join failed")

# 6) Enviar un uplink
counter = 0
while True:
    payload = b"MSG%03d" % counter
    print("Sending uplink:", payload)
    radio.send(payload, port=1)
    counter += 1

    # 7) Esperar un downlink en los siguientes 5 s
    down = radio.receive(timeout_ms=5000)
    if down:
        print("↓ Received downlink payload:", down)

    time.sleep(30)  # Cumple el rate‐limit de TTN (1 uplink cada 30 s)
