import traci
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def set_traffic_light_state(light_id: str, state: str):
    logger.info(f"Setting traffic light {light_id} to state {state}")
    try:
        traci.trafficlight.setRedYellowGreenState(light_id, state)
    except Exception as e:
        logger.error(f"Failed to set traffic light {light_id}: {e}")

def main():
    traci.init(port=8873, host="localhost")
    logger.info("Connected to SUMO")

    # IMPORTANT : avancer la simulation au moins une fois
    traci.simulationStep()

    light_ids = traci.trafficlight.getIDList()
    logger.info(f"Traffic light IDs: {light_ids}")

    if not light_ids:
        logger.warning("No traffic lights found!")
    else:
        set_traffic_light_state(light_ids[0], "GrGr")

    traci.close()

if __name__ == "__main__":
    main()
