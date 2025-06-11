import traci, os
from simulation import config
from simulation.config import SUMO_HOME
from util.logger import logger

def start_traci():
    host = os.environ.get("SUMO_HOST", "localhost")
    port = int(os.environ.get("SUMO_PORT", 8873))
    logger.info(f"Connecting to SUMO at {host}:{port}...")
    traci.init(port=port, host=host)
    logger.info("TraCI connection established successfully.")

def close_traci():
    logger.info("Closing TraCI connection...")
    traci.close()