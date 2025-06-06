import random

import traci


def accidents_generator(blocked_vehicles: dict[str, int], step: int):

    vehicules_ids = traci.vehicle.getIDList()
    for vehicule in vehicules_ids:
        if traci.vehicle.getTypeID(vehicule) == "veh__private":
            if random.randint(1, 1000) == 1:
                traci.vehicle.setSpeed(vehicule, 0)
                blocked_vehicles[vehicule] = step + 10

def accidents_liberator(blocked_vehicles: dict[str, int], step: int):

    for vehicule, step_liberator in list(blocked_vehicles.items()):
        if step_liberator == step:
            del blocked_vehicles[vehicule]
            traci.vehicle.setSpeed(vehicule, -1)
