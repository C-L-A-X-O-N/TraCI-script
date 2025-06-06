from time import sleep

import traci

from simulation.config import process_files, STEP_MAX
from simulation.simulation_getter import collect_simulation_data
from simulation.simulation_setter import accidents_generator, accidents_liberator
from simulation.traci_manager import start_traci, close_traci
from util.mqtt import run_paho, stop_paho


def run_simulation():
    try:
        process_files()
        run_paho()
        start_traci()

        is_first_step = True
        step_count = 0
        blocked_vehicles = {}

        # Tourne tant que il y a au moins un vehicule
        while traci.simulation.getMinExpectedNumber() > 0 and step_count < (STEP_MAX - 20) :
            try:
                while step_count<20:
                    traci.simulationStep()
                    step_count += 1
                accidents_generator(blocked_vehicles, step_count)
                accidents_liberator(blocked_vehicles, step_count)
                collect_simulation_data(is_first_step, blocked_vehicles)
                traci.simulationStep()
                sleep(1)
                is_first_step = False
                step_count += 1
                print("toto")
            except traci.TraCIException as e:
                print(f"TraCI exception occurred: {e}")

        stop_paho()
        close_traci()
        run_simulation()

    finally:
        stop_paho()
        close_traci()
