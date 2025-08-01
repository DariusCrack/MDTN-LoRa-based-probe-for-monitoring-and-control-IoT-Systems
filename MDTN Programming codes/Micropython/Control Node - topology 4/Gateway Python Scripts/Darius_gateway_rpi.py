#!/usr/bin/env python3
import os
import time
import json
import threading
import logging
import re

import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO

from AlLoRa.Connectors.Serial_connector import Serial_connector
from AlLoRa.Nodes.Gateway import Gateway

# ——— CONFIGURATION ———
BROKER_HOST = "localhost"
BROKER_PORT = 1883

TOPIC_BASE  = "t3s3"
RPI_ID      = "RASPBERRYPI-001"
BASE_DIR    = "/home/pi/Desktop/RPi_GW/Results/da5a08dc"
RPI_FILE    = os.path.join(BASE_DIR, "metrics_Rpi.json")

# ——— LOGGER ———
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)5s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger()

# ——— MQTT SETUP ———
client = mqtt.Client(client_id=RPI_ID, clean_session=False)
status_topic = f"{TOPIC_BASE}/{RPI_ID}/status"
client.will_set(status_topic, "offline", qos=1, retain=True)
client.connect(BROKER_HOST, BROKER_PORT)
client.loop_start()
client.publish(status_topic, "online", qos=1, retain=True)

# subscribe for future downlink (not used yet)
client.subscribe(f"{TOPIC_BASE}/+/control", qos=1)
client.on_message = lambda c,u,m: log.info(f"DOWNLINK {m.topic}: {m.payload}")

def reset_esp32():
    """noop or reset your ESP32 if you share GPIO"""
    PIN = 23
    GPIO.setmode(GPIO.BCM)
    try:
        GPIO.setup(PIN, GPIO.OUT)
    except RuntimeError:
        GPIO.cleanup(PIN)
        GPIO.setup(PIN, GPIO.OUT)
    GPIO.output(PIN, GPIO.LOW)
    time.sleep(0.1)
    GPIO.output(PIN, GPIO.HIGH)
    GPIO.cleanup(PIN)
    log.info("ESP32 reset")

def publish_metrics(data: dict):
    """Publish one flattened JSON payload to MQTT."""
    payload = {
        "device_id": RPI_ID,
        "ts":         int(time.time() * 1000),
        **data
    }
    topic = f"{TOPIC_BASE}/{RPI_ID}/metrics"
    client.publish(topic, json.dumps(payload), qos=1)
    log.info(f"Published {topic} → {payload}")

# ——— PARSING LOGIC ———
# First group: numeric patterns
patterns = [
    (re.compile(r"Cpu\(s\):\s*([\d\.]+) us,\s*([\d\.]+) sy"), ["cpu_user","cpu_sys"]),
    (re.compile(r"load average:\s*([\d\.]+),\s*([\d\.]+),\s*([\d\.]+)"), ["load1","load5","load15"]),
    (re.compile(r"CPU Current Freq:\s*(\d+)"), ["cpu_freq_cur"]),
    (re.compile(r"CPU Min Freq:\s*(\d+)"), ["cpu_freq_min"]),
    (re.compile(r"CPU Max Freq:\s*(\d+)"), ["cpu_freq_max"]),
    (re.compile(r"temp=([\d\.]+)'C"), ["cpu_temp"]),
    (re.compile(r"Mem:\s+\S+\s+(\d+)\s+(\d+)\s+(\d+)"), ["ram_total","ram_used","ram_free"]),
    (re.compile(r"Swap:\s+(\d+)\s+(\d+)"), ["swap_total","swap_used"]),
    (re.compile(r"/dev/root.*\s+(\d+)%"), ["disk_used_pct"]),
    (re.compile(r"Network RX Bytes:\s*(\d+)"), ["net_rx"]),
    (re.compile(r"Network TX Bytes:\s*(\d+)"), ["net_tx"]),
    (re.compile(r"gpu=(\d+)"), ["gpu_mem"]),
    (re.compile(r"volt=([\d\.]+)V"), ["voltage"]),
    (re.compile(r"throttled=(0x[0-9A-Fa-f]+)"), ["throttled"]),
    (re.compile(r"Uptime:\s*up\s*(\d+)\s*hours?,\s*(\d+)\s*minutes?"), ["uptime_s","_uptime_m"]),  # will convert
]

# Second group: pure-text fields
def parse_text_fields(line: str, out: dict):
    if line.startswith("Kernel:"):
        out["kernel"] = line.partition("Kernel:")[2].strip()
    if line.startswith("IP Address:"):
        out["ip_address"] = line.partition("IP Address:")[2].strip()
    if line.startswith("MAC Address:"):
        out["mac_address"] = line.partition("MAC Address:")[2].strip()
    if line.startswith("Interface:"):
        out["interface"] = line.partition("Interface:")[2].strip()
    if line.startswith("Link State:"):
        out["link_state"] = line.partition("Link State:")[2].strip()
    if line.startswith("Ping"):
        # e.g. "Ping 8.8.8.8: Offline"
        out["ping"] = line.partition(":")[2].strip()

def process_rpi_file():
    """Read the Pi’s text metrics, apply patterns, then publish."""
    try:
        raw = open(RPI_FILE, "r", encoding="utf-8").read()
    except Exception as e:
        log.error(f"Cannot read '{RPI_FILE}': {e}")
        return

    data = {}
    for line in raw.splitlines():
        # try numeric patterns
        for regex, keys in patterns:
            m = regex.search(line)
            if not m:
                continue
            vals = m.groups()
            for k_name, val in zip(keys, vals):
                if k_name == "uptime_s":
                    # convert h,m to seconds
                    h, m = map(int, vals)
                    data["uptime_s"] = h*3600 + m*60
                elif k_name.startswith("_"):
                    # skip temporary
                    pass
                else:
                    # numeric
                    data[k_name] = float(val) if "." in val else int(val)
            break
        # pure-text fields
        parse_text_fields(line, data)

    publish_metrics(data)

# ——— FILE WATCHER ———
def watch_loop():
    last = 0
    log.info("Starting RPi file watcher")
    while True:
        if os.path.isfile(RPI_FILE):
            m = os.path.getmtime(RPI_FILE)
            if m > last:
                last = m
                try:
                    process_rpi_file()
                except Exception as e:
                    log.error(f"Error processing RPi file: {e}")
        time.sleep(1)

def main():
    # start LoRa listener to keep metrics_Rpi.json updated
    conn = Serial_connector(reset_function=reset_esp32)
    gw   = Gateway(conn, config_file="LoRa.json", debug_hops=False)
    threading.Thread(
        target=gw.check_digital_endpoints,
        kwargs={"print_file_content": True, "save_files": True},
        daemon=True
    ).start()

    # start watching the RPi file
    threading.Thread(target=watch_loop, daemon=True).start()

    log.info("gateway_rpi.py running—Ctrl+C to stop")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log.info("Shutting down…")
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()

