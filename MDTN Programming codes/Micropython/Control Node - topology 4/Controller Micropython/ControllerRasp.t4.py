from machine import UART
import time
import sys
import select

uart = UART(1, baudrate=115200, tx=41, rx=42, timeout=100)
buffer = b""
partial = b""
last_metrics_time = time.ticks_ms()
last_command_time = time.ticks_ms()

COMMAND_INTERVAL_MS = 22000
METRICS_INTERVAL_MS = 30000

def handle_uart_data():
    global partial
    if uart.any():
        data = uart.read()
        if data:
            partial += data
            if b"</RPI_METRICS>" in partial or b"</CMD_RESPONSE>" in partial:
                try:
                    decoded = partial.decode()
                    if "<RPI_METRICS>" in decoded:
                        print("\n📡 Métricas recibidas del Raspberry Pi:")
                        print("----------------------------------------")
                        content = decoded.split("<RPI_METRICS>")[1].split("</RPI_METRICS>")[0]
                        for line in content.strip().splitlines():
                            print(line)
                        print("----------------------------------------")
                    elif "<CMD_RESPONSE>" in decoded:
                        print("\n📥 Respuesta del Raspberry Pi:")
                        print("----------------------------------------")
                        content = decoded.split("<CMD_RESPONSE>")[1].split("</CMD_RESPONSE>")[0]
                        print(content.strip())
                        print("----------------------------------------")
                except Exception as e:
                    print("Error al decodificar:", e)
                partial = b""

def check_for_command_input():
    # Detectar entrada de comando sin bloquear
    if select.select([sys.stdin], [], [], 0)[0]:
        cmd = sys.stdin.readline().strip()
        if cmd:
            uart.write(f"[CMD]{cmd}\n".encode())
            print("✅ Comando enviado al Raspberry Pi.")

# Bucle principal
while True:
    now = time.ticks_ms()
    
    handle_uart_data()

    if time.ticks_diff(now, last_command_time) > COMMAND_INTERVAL_MS:
        print("\n⌨️ Puedes escribir un comando para enviar al Raspberry Pi (esperando input)...")
        last_command_time = now

    check_for_command_input()

    time.sleep(0.1)
