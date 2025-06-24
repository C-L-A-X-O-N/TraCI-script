import json, os, logging
from util.logger import logger
import paho.mqtt.client as mqtt


class MqttClient:
    _on_disconnect = None
    _on_connect = None

    def __init__(self, host, port, zone, subscribes, on_disconnect=None, on_connect=None):
        self.host = host
        self.port = port
        self.subscribed_lanes = {}
        self.subscribed_traffic_lights = {}
        from simulation.simulation_getter import get_zone_boundaries
        bound = get_zone_boundaries(zone)
        if bound is not None:
            self.bounds = {
                "lat_min": bound["lat_min"],
                "lon_min": bound["lon_min"],
                "lat_max": bound["lat_max"],
                "lon_max": bound["lon_max"]
            }
        else:
            self.bounds = None
        self._on_disconnect = on_disconnect
        self._on_connect = on_connect
        self.zone = zone
        self.client = mqtt.Client()
        self.logger = logging.getLogger(__name__ + ":" + host + ":" + str(port))
        self.logger.info(f"Creating MQTT client for {host}:{port} with zone {zone} and bounds {self.bounds}")
        self.subscribes = subscribes
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
        self.logger.info("MQTT client is ready to receive messages.")

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
    
    def is_within_bounds(self, position):
        if self.bounds is None:
            return True
        lat, lon = position
        return (self.bounds["lat_min"] <= lat <= self.bounds["lat_max"] and
                self.bounds["lon_min"] <= lon <= self.bounds["lon_max"])

    def publish(self, topic, payload):
        self.client.publish(topic, json.dumps(payload))

    def publish_with_bounds(self, topic, payload):
        if self.bounds is None:
            self.logger.warning("No bounds set for this client, publishing without bounds.")
            self.publish(topic, payload)
            return
        
        self.logger.debug(f"Publishing to topic {topic} with bounds {self.bounds}")
        
        if topic == "traci/lane/state":
            new_payload = []
            d = self.subscribed_lanes.keys()
            for i in range(len(payload)):
                item = payload[i]
                if item["id"] in d:
                    new_payload.append(item)
            self.logger.debug(f"Filtered lane state payload size: {len(new_payload)} out of {len(payload)}")
            payload = new_payload
        elif topic == "traci/traffic_light/state":
            new_payload = []
            for i in range(len(payload)):
                item = payload[i]
                if "id" in item:
                    if item["id"] in self.subscribed_traffic_lights.keys():
                        new_payload.append(item)
            payload = new_payload
        elif isinstance(payload, list):
            new_payload = []
            for i in range(len(payload)):
                item = payload[i]
                if "position" in item:
                    position = item["position"]
                    if self.is_within_bounds(position):
                        new_payload.append(item)
                        if topic == "traci/traffic_light/position":
                            self.subscribed_traffic_lights[item["id"]] = True

            self.logger.debug(f"Filtered payload size: {len(new_payload)} out of {len(payload)}")
            payload = new_payload
        
        else:
            self.logger.warning("Payload does not contain position information, publishing without bounds.")
            self.logger.info(f"Payload type: {type(payload)}")
            
        self.publish(topic, payload)
                        

class MqttUpstreamRegistry:
    clients = []
    logger = logging.getLogger(__name__)

    def close_client(self, client):
        if client in self.clients:
            self.logger.info("Removing client " + str(client))
            self.clients.remove(client)
        else:
            self.logger.warning("Attempted to close a client that is not registered: " + str(client))

    def add_client(self, host, port, zone, subscribes=None):
        self.logger.info("New client registered at " + host + ":" + str(port))
        def on_disconnect(msg, client):
            client.stop_paho()

        from simulation.simulation_getter import send_first_step_data

        if subscribes is None:
            subscribes = {}
        subscribes['traci/node/stop'] = on_disconnect
        subscribes['traci/first_data'] = send_first_step_data
        # Create the client first with a placeholder for on_connect
        client = MqttClient(host, port, zone, subscribes=subscribes, on_disconnect=self.close_client, on_connect=None)
        self.logger.info(f"Client connected to {host}:{port}")
        send_first_step_data(client)
        self.clients.append(client)

    def get_clients(self):
        return self.clients
    
    def on_stop(self):
        self.logger.info("Stopping registered clients...")
        for client in self.clients:
            client.stop_paho()
    
registry = MqttUpstreamRegistry()