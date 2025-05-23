from simulation.config import process_osm_tranformation, process_trip_generation, process_files
from simulation.traci_manager import start_traci, close_traci
from simulation.simulation_logic import collect_simulation_data, collect_lane
import traci

from util.mqtt import run_paho, stop_paho


def run_simulation():
    try:
        run_paho()
        process_files()
        start_traci()

        # Tourne tant que il y a au moins un vehicule
        while traci.simulation.getMinExpectedNumber() > 0:
            collect_simulation_data()
            traci.simulationStep()

    finally:
        stop_paho()
        close_traci()
