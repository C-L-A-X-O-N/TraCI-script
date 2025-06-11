import json, os
from util.logger import logger

import paho.mqtt.client as mqtt

client = mqtt.Client()

def run_paho():
    try:
        host = os.environ.get("MQTT_HOST", "localhost")
        port = int(os.environ.get("MQTT_PORT", "1900"))
        logger.info(f"Connecting to MQTT broker at {host}:{port}")
        client.connect(host, port, keepalive=60)
        client.on_connect = on_connect
        client.on_message = on_message
        client.enable_logger(logger)
        client.loop_start()
    except KeyboardInterrupt:
        stop_paho()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("Connected to MQTT broker successfully")
        client.subscribe("controller/command/get_init")
    else:
        logger.error(f"Failed to connect to MQTT broker, return code {rc}")

def on_message(client, userdata, msg):
    from simulation.simulation_getter import send_first_step_data
    
    topic = msg.topic
    payload = msg.payload.decode('utf-8')
    logger.debug(f"Received message on topic {topic}: {payload}")

    if topic == "controller/command/get_init":
        send_first_step_data()

def stop_paho():
    logger.info("Stopping MQTT client...")
    client.loop_stop()
    client.disconnect()

def publish(topic, payload):
    client.publish(topic, json.dumps(payload))

