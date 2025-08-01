#!/usr/bin/env python3
import os
import json
import time
import threading
import logging
import re

import paho.mqtt.client as mqtt
from AlLoRa.Connectors.Serial_connector import Serial_connector
from AlLoRa.Nodes.Gateway import Gateway

# Configuration
BROKER_HOST   = "localhost"
BROKER_PORT   = 1883
TOPIC_BASE    = "t3s3"
GATEWAY_ID    = "T3S3-GATEWAY-001"
BASE_DIR      = "/home/pi/Desktop/RPi_GW/Results/da5a08dc"
GATEWAY_FILE  = os.path.join(BASE_DIR, "metrics_LilyGo.json")
LORA_CONFIG   = "LoRa.json"

# Map original keys to flat fields
FIELD_MAP = {
    "CPU":      "cpu",
    "Mem":      "mem",
    "Temp":     "temp",
    "Uptime":   "uptime",
    "Batt":     "batt",
    "WiFiRSSI": "wifi_rssi",
    "PingRTT":  "ping_rtt",
    "Joined":   "joined",
    "Online":   "online",
    "LoRaRSSI": "lora_rssi",
    "LoRaSNR":  "lora_snr",
    "DataRate": "datarate",
    "FPort":    "fport"
}

logging.basicConfig(
    level    = logging.INFO,
    format   = "%(asctime)s [%(levelname)s] %(message)s",
    datefmt  = "%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger()

# MQTT setup
client = mqtt.Client(client_id=GATEWAY_ID, clean_session=False)
client.will_set(f"{TOPIC_BASE}/{GATEWAY_ID}/status", "offline", qos=1, retain=True)
client.connect(BROKER_HOST, BROKER_PORT)
client.loop_start()
client.publish(f"{TOPIC_BASE}/{GATEWAY_ID}/status", "online", qos=1, retain=True)

def extract_number(val):
    if isinstance(val, (int, float)):
        return val
    m = re.match(r"-?\d+(?:\.\d+)?", str(val))
    if not m:
        return None
    s = m.group(0)
    return float(s) if "." in s else int(s)

def publish_flat(metrics):
    payload = {"device_id": GATEWAY_ID, "ts": int(time.time()*1000)}
    for key, raw_val in metrics.items():
        fld = FIELD_MAP.get(key)
        if fld:
            num = extract_number(raw_val)
            if num is not None:
                payload[fld] = num
    topic = f"{TOPIC_BASE}/{GATEWAY_ID}/metrics"
    client.publish(topic, json.dumps(payload), qos=1)
    logger.info(f"Published to {topic}: {payload}")

def extract_inner_json(text):
    start = text.find('{"CPU"')
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(text)):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                return text[start:i+1]
    return None

# Regex to quote numeric+unit values, e.g. 240MHz -> "240MHz"
unit_re = re.compile(r'("(?P<key>[A-Za-z0-9_]+)":)(?P<val>-?\d+(?:\.\d+)?(?:[^\d,}\]\"])+)')

def process_file():
    raw = open(GATEWAY_FILE, "r", encoding="utf-8").read()
    inner = extract_inner_json(raw)
    if not inner:
        logger.error("Could not locate inner JSON")
        return

    # Quote all suffix-containing numbers
    def quote_unit(m):
        return f'{m.group(1)}"{m.group("val")}"'
    cleaned = unit_re.sub(quote_unit, inner)

    try:
        metrics = json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error(f"Parsing inner JSON failed: {e} → {cleaned}")
        return

    publish_flat(metrics)

def watch_loop():
    last = 0
    while True:
        if os.path.isfile(GATEWAY_FILE):
            m = os.path.getmtime(GATEWAY_FILE)
            if m > last:
                last = m
                process_file()
        time.sleep(1)

def main():
    # start AlLoRa gateway listener
    connector = Serial_connector(reset_function=lambda: None)
    gw = Gateway(connector, config_file=LORA_CONFIG, debug_hops=False)
    threading.Thread(
        target=gw.check_digital_endpoints,
        kwargs={'print_file_content': True, 'save_files': True},
        daemon=True
    ).start()

    # watch the LilyGo metrics file
    threading.Thread(target=watch_loop, daemon=True).start()

    logger.info("LilyGo gateway running. Ctrl+C to exit.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping LilyGo gateway")
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()

