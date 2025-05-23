import json
import logging
from logging import Logger

import paho.mqtt.client as mqtt

client = mqtt.Client()

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
)

def run_paho():
    logger.info("indifsdnsndjsndsdnosinisnosondisbin")
    try:
        client.connect("localhost", 1900, keepalive=60)
        client.enable_logger(logger)
        client.loop_start()
    except KeyboardInterrupt:
        stop_paho()

def stop_paho():
    client.loop_stop()
    client.disconnect()

def publish(topic, payload):
    client.publish(topic, json.dumps(payload))

