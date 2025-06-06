import traci, os
from simulation import config
from simulation.config import SUMO_HOME

import logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
)

def start_traci():
    host = os.environ.get("SUMO_HOST", "localhost")
    port = int(os.environ.get("SUMO_PORT", 8813))
    logger.info(f"Connecting to SUMO at {host}:{port}...")
    traci.init(port=port, host=host)

def close_traci():
    traci.close()