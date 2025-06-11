from time import sleep

import traci, os, json

from simulation.config import readNetFile, STEP_MAX
from simulation.simulation_getter import collect_simulation_data, send_first_step_data
from simulation.simulation_setter import accidents_generator, accidents_liberator
from simulation.traci_manager import start_traci, close_traci
from util.mqtt import MqttClient, registry
from util.logger import logger

def on_init_request(msg, mqttClient):
    data = json.loads(msg.payload.decode('utf-8'))
    registry.add_client(data['host'], data['port'])

def run_simulation():
    commonMqtt = None
    try:
        commonMqtt = MqttClient(host=os.environ.get('MQTT_HOST', 'localhost'), port=int(os.environ.get('MQTT_PORT', 1883)), subscribes={
            "traci/node/start": on_init_request
        })
        readNetFile()
        start_traci()

        commonMqtt.publish("traci/start", "")

        is_first_step = True
        step_count = 0
        blocked_vehicles = {}

        # Tourne tant que il y a au moins un vehicule
        while traci.simulation.getMinExpectedNumber() > 0 and step_count < (STEP_MAX - 20) :
            try:
                while step_count<20:
                    logger.debug(f"Skipping step {step_count} for initialization.")
                    traci.simulationStep()
                    step_count += 1
                accidents_generator(blocked_vehicles, step_count)
                accidents_liberator(blocked_vehicles, step_count)
                collect_simulation_data(is_first_step, blocked_vehicles)
                traci.simulationStep()
                sleep(1)
                is_first_step = False
                step_count += 1
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
