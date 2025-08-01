# Archivo: loopback_test_t3s3.py

from machine import UART
import time

# Configuramos UART1 a 115200 bps. TX en pin 41, RX en pin 42.
uart = UART(1, 115200, tx=41, rx=42)

# Pequeña espera para que el UART esté listo
time.sleep(1)

print("=== T3S3 Loopback Test ===")
print("Señal enviada --> Señal recibida (si conecta 41⇄42)")

# Mensaje de prueba
test_msg = b"PING_T3S3\n"

# Enviamos el mensaje
uart.write(test_msg)
print("Enviado:", test_msg)

# Damos un breve margen para que el dato regrese por el loopback
time.sleep(0.2)

# Intentamos leer lo que haya llegado
if uart.any():
    recibido = uart.read()
    print("Recibido:", recibido)
    if recibido == test_msg:
        print("→ Loopback OK en T3S3 (41⇄42)")
    else:
        print("→ Datos recibidos no coinciden")
else:
    print("→ No se recibió nada. Verifica puente 41⇄42 o baudios.")

