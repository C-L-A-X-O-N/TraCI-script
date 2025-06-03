from time import sleep

import traci

from simulation.config import process_files
from simulation.simulation_logic import collect_simulation_data
from simulation.traci_manager import start_traci, close_traci
from util.mqtt import run_paho, stop_paho


def run_simulation():
    try:
        run_paho()
        process_files()
        start_traci()

        is_first_step = True
        step_count = 0

        # Tourne tant que il y a au moins un vehicule
        while traci.simulation.getMinExpectedNumber() > 0:
            print(step_count)
            collect_simulation_data(is_first_step)
            sleep(0.1)
            traci.simulationStep()
            is_first_step = False
            step_count += 1

        stop_paho()
        close_traci()
        run_simulation()

    finally:
        stop_paho()
        close_traci()
