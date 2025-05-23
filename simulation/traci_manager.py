import traci
from simulation import config
from simulation.config import SUMO_HOME


def start_traci():
    binary = config.SUMO_BINARY
    cmd = [binary, "-n", config.NET_FILE, "-r", config.ROU_FILE]
    traci.start(cmd)

def close_traci():
    traci.close()