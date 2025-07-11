from time import sleep

import traci, os, json, time

from simulation.config import readNetFile, STEP_MAX
from simulation.simulation_getter import collect_simulation_data, get_zones, collect_lane_position
from simulation.simulation_setter import accidents_generator, accidents_liberator, set_traffic_light_state
from simulation.traci_manager import start_traci, close_traci
from util.mqtt import MqttClient, registry
from util.logger import logger

def on_init_request(msg, mqttClient):
    data = json.loads(msg.payload.decode('utf-8'))
    registry.add_client(data['host'], data['port'], data['zone'] if 'zone' in data else None)

def on_traffic_light_state_change(msg, mqttClient):
    try:
        data = json.loads(msg.payload.decode("utf-8"))
        light_id = data["id"]
        state = data["state"]
        set_traffic_light_state(light_id, state)
    except Exception as e:
        logger.error(f"Error handling traffic light state change: {e}")

from simulation.simulation_setter import set_traffic_light_state

def on_traffic_light_state_change(msg, mqttClient):
    try:
        data = json.loads(msg.payload.decode("utf-8"))
        light_id = data["id"]
        state = data["state"]
        logger.info(f"[MQTT] Setting traffic light {light_id} to state {state}")
        set_traffic_light_state(light_id, state)
    except Exception as e:
        logger.error(f"Error handling traffic light state change: {e}")

def run_simulation():
    commonMqtt = None
    try:
        start_traci()
        readNetFile()

        logger.debug("Loading lanes position...")
        collect_lane_position()

        is_first_step = True
        step_count = 0
        blocked_vehicles = {}

        while step_count<100:
            logger.debug(f"Skipping step {step_count} for initialization.")
            traci.simulationStep()
            step_count += 1

        logger.info(f"Network boundary: {get_zones()}")

        def _on_co(_):
            commonMqtt.publish("traci/start", "")
        commonMqtt = MqttClient(host=os.environ.get('MQTT_HOST', 'localhost'), port=int(os.environ.get('MQTT_PORT', 1883)), zone=None, subscribes={
            "traci/node/start": on_init_request,
            "claxon/command/traffic_light/update": on_traffic_light_state_change  # AJOUT OBLIGATOIRE
        }, on_connect=_on_co)

        # Tourne tant que il y a au moins un vehicule
        while traci.simulation.getMinExpectedNumber() > 0 and step_count < (STEP_MAX - 20) :
            try:
                time_start = time.time()
                logger.info(f"Step {step_count} - Running simulation step...")
                logger.debug(f"Generating accidents for step {step_count}...")
                accidents_generator(blocked_vehicles, step_count)
                logger.debug(f"Releasing accidents for step {step_count}...")
                accidents_liberator(blocked_vehicles, step_count)
                logger.debug(f"Collecting simulation data for step {step_count}...")
                collect_simulation_data(is_first_step, blocked_vehicles)
                logger.debug(f"Publishing simulation data for step {step_count}...")
                traci.simulationStep()
                is_first_step = False
                step_count += 1
                if time.time() - time_start < 2:
                    sleep(2 - (time.time() - time_start))
                logger.info(f"Step {step_count} completed in {time.time() - time_start:.2f} seconds.")
                commonMqtt.publish("traci/step", json.dumps({
                    "step": step_count,
                }))
            except traci.TraCIException as e:
                logger.error(f"TraCI exception occurred: {e}")

        commonMqtt.stop_paho()
        registry.on_stop()
        close_traci()
        run_simulation()
    except KeyboardInterrupt:
        logger.info("Simulation interrupted by user.")

    finally:
        if commonMqtt != None:
            commonMqtt.stop_paho()
        registry.on_stop()
        close_traci()
