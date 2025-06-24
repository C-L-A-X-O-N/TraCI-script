import random
from util.logger import logger
import traci


def accidents_generator(blocked_vehicles: dict[str, int], step: int):

    vehicules_ids = traci.vehicle.getIDList()
    for vehicule in vehicules_ids:
        if traci.vehicle.getTypeID(vehicule) == "veh__private":
            if random.randint(1, 1000) == 1:
                logger.info(f"Accident generated for vehicle {vehicule} at step {step}")
                traci.vehicle.setSpeed(vehicule, 0)
                blocked_vehicles[vehicule] = step + 10

def accidents_liberator(blocked_vehicles: dict[str, int], step: int):

    for vehicule, step_liberator in list(blocked_vehicles.items()):
        if step_liberator == step:
            logger.info(f"Accident liberated for vehicle {vehicule} at step {step}")
            del blocked_vehicles[vehicule]
            traci.vehicle.setSpeed(vehicule, -1)

def set_traffic_light_state(light_id: str, state: str):
    logger.info(f"Setting traffic light {light_id} to state {state}")
    try:
        traci.trafficlight.setRedYellowGreenState(light_id, state)
    except Exception as e:
        logger.error(f"Failed to set traffic light {light_id}: {e}")
