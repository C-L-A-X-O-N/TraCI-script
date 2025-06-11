import json, os, logging
from util.logger import logger
import paho.mqtt.client as mqtt


class MqttClient:
    client = None
    logger = None
    host = None
    port = None
    subscribes = {}
    _on_disconnect = None
    _on_connect = None

    def __init__(self, host, port, subscribes, on_disconnect=None, on_connect=None):
        self.host = host
        self.port = port
        self.client = mqtt.Client()
        self.logger = logging.getLogger(__name__ + ":" + host + ":" + str(port))
        self.subscribes = subscribes
        self._on_disconnect = on_disconnect
        self._on_connect = on_connect
        self.run_paho()
        

    def run_paho(self):
        try:
            self.logger.info(f"Connecting to MQTT broker at {self.host}:{self.port}")
            self.client.connect(self.host, self.port, keepalive=60)
            self.client.on_connect = self.on_connect
            self.client.on_message = self.on_message
            self.client.enable_logger(self.logger)
            self.client.loop_start()
        except KeyboardInterrupt:
            self.stop_paho()

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.logger.info("Connected to MQTT broker successfully")
            for topic in self.subscribes.keys():
                self.logger.info("Subscribed to topic " + topic)
                client.subscribe(topic)
        else:
            self.logger.error(f"Failed to connect to MQTT broker, return code {rc}")
        self._on_connect(self) if self._on_connect else None
        self.logger.debug("MQTT client is ready to receive messages.")

    def on_message(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode('utf-8')
        self.logger.debug(f"Received message on topic {topic}: {payload}")

        for t, func in self.subscribes.items():
            if topic == t:
                func(msg, self)

    def stop_paho(self):
        self.logger.info("Stopping MQTT client...")
        self.client.loop_stop()
        self.client.disconnect()
        self._on_disconnect(self) if self._on_disconnect else None

    def publish(self, topic, payload):
        self.client.publish(topic, json.dumps(payload))

class MqttUpstreamRegistry:
    clients = []
    logger = logging.getLogger(__name__)

    def close_client(self, client):
        if client in self.clients:
            self.logger.debug("Removing client " + str(client))
            self.clients.remove(client)
        else:
            self.logger.warning("Attempted to close a client that is not registered: " + str(client))

    def add_client(self, host, port, subscribes=None):
        self.logger.debug("New client registered at " + host + ":" + str(port))
        def on_disconnect(msg, client):
            client.stop_paho()

        def on_connect(client):
            self.logger.info(f"Client connected to {host}:{port}")
            from simulation.simulation_getter import send_first_step_data
            send_first_step_data(client)
            self.clients.append(client)

        if subscribes is None:
            subscribes = {}
        subscribes['traci/node/stop'] = on_disconnect
        client = MqttClient(host, port, subscribes=subscribes, on_disconnect=self.close_client, on_connect=lambda c: on_connect(client))


    def get_clients(self):
        return self.clients
    
    def on_stop(self):
        self.logger.info("Stopping registered clients...")
        for client in self.clients:
            client.stop_paho()
    
registry = MqttUpstreamRegistry()