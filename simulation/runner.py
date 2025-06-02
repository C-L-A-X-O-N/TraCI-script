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

        # Tourne tant que il y a au moins un vehicule
        while traci.simulation.getMinExpectedNumber() > 0:
            collect_simulation_data(is_first_step)
            sleep(0.5)
            traci.simulationStep()
            is_first_step = False

        stop_paho()
        close_traci()
        run_simulation()

    finally:
        stop_paho()
        close_traci()
