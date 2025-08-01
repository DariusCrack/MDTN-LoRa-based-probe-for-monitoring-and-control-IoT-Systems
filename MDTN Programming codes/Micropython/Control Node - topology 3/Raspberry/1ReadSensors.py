#!/usr/bin/env python3
import time
import random
import Adafruit_DHT

# Configuración del DHT22
DHT_SENSOR = Adafruit_DHT.DHT22
DHT_PIN = 4  # Cambia este pin al GPIO que uses

# Función para leer DHT22
def read_dht22():
    humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
    if humidity is None or temperature is None:
        return None, None
    return round(temperature, 2), round(humidity, 2)

# Función para simular otros sensores
def simulate_extra_sensors():
    return {
        'pressure_hPa': round(random.uniform(980.0, 1050.0), 1),
        'light_lux':    round(random.uniform(0, 1000), 1)
    }

def main(poll_interval=5):
    """
    Bucle principal:
    - Lee DHT22
    - Simula sensores
    - Imprime resultados
    """
    print("Iniciando lectura de sensores (DHT22 + simulados)...")
    try:
        while True:
            temp, hum = read_dht22()
            extras = simulate_extra_sensors()
            
            payload = {
                'temperature_C': temp,
                'humidity_%':   hum,
                **extras
            }
            
            print(payload)
            time.sleep(poll_interval)
    except KeyboardInterrupt:
        print("\nSensor loop detenido por el usuario.")

if __name__ == "__main__":
    main(poll_interval=30)  # lee cada 30 segundos
