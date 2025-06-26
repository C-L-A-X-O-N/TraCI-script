import random
from util.logger import logger
import traci
from util.converter import convert_to_latlong
from simulation.simulation_getter import get_zone_from_position


def accidents_generator(blocked_vehicles: dict[str, dict], step: int):
    vehicules_ids = traci.vehicle.getIDList()
    for vehicule in vehicules_ids:
        if traci.vehicle.getTypeID(vehicule) == "veh__private":
            if random.randint(1, 1000) == 1:
                logger.info("accident....")
                position = traci.vehicle.getPosition(vehicule)
                lat_lon = convert_to_latlong(position[0], position[1])
                zone = get_zone_from_position(lat_lon[0], lat_lon[1])
                logger.info("zone : " + str(zone))
                logger.debug(f"Accident generated for vehicle {vehicule} at step {step}")
                traci.vehicle.setSpeed(vehicule, 0)
                duration = 10  # Durée de l'accident en pas de simulation
                blocked_vehicles[vehicule] = {
                    "step_end": step + duration,
                    "start_time": step,
                    "position": lat_lon,
                    "zone": zone,
                    "type": traci.vehicle.getTypeID(vehicule),
                    "duration": duration
                }


def accidents_liberator(blocked_vehicles: dict[str, dict], step: int):
    for vehicule, accident_data in list(blocked_vehicles.items()):
        if accident_data["step_end"] == step:
            logger.debug(f"Accident liberated for vehicle {vehicule} at step {step}")
            del blocked_vehicles[vehicule]
            traci.vehicle.setSpeed(vehicule, -1)
