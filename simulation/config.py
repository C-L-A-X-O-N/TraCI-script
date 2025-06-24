import os
import subprocess

from sumolib.net import readNet
from util.logger import logger

SUMO_CONFIG = os.path.join("data", "file.sumocfg")
OSM_FILE = os.path.join("data", "map.osm.xml")
NET_FILE = os.path.join("data", "map.net.xml")
ROU_FILE = os.path.join("data", "map.rou.xml")
TRIP_FILE = os.path.join("data", "map.trip.xml")
TRAIN_TRIP_FILE = os.path.join("data", "map.train_trip.xml")
TRAIN_ROU_FILE = os.path.join("data", "map.train.rou.xml")
BUS_TRIP_FILE = os.path.join("data", "map.bus_trip.xml")
BUS_ROU_FILE = os.path.join("data", "map.bus.rou.xml")
AMBULANCE_TRIP_FILE = os.path.join("data", "map.ambulance_trip.xml")
AMBULANCE_ROU_FILE = os.path.join("data", "map.ambulance.rou.xml")
SUMO_HOME = os.environ.get("SUMO_HOME")
SUMO_BINARY = os.path.join(SUMO_HOME, "bin", "sumo")
NET_READER = None
STEP_MAX = 300

command_osm_transformation = [
    "netconvert",
    "--osm-files", OSM_FILE,
    "--output-file", NET_FILE,
    "--output.street-names", "true",
    "--output.original-names", "true",
    "--tls.guess", "true",
    "--tls.discard-simple", "false",
    "--tls.default-type", "actuated",
    "--junctions.join", "true",
    "--proj.utm",
    "--no-warnings"
]

command_trip_creation = [
    "python",
    os.path.join(SUMO_HOME, "tools", "randomTrips.py"),
    "-n", NET_FILE,
    "-o", TRIP_FILE,
    "--random-departpos",
    "-b", "0",
    "-e", STEP_MAX.__str__(),
    "-p", "0.1",
    "--prefix", "veh_",
    "--vehicle-class", "private",
]


command_train_trip_creation = [
    "python",
    os.path.join(SUMO_HOME, "tools", "randomTrips.py"),
    "-n", NET_FILE,
    "-o", TRAIN_TRIP_FILE,
    "--random-departpos",
    "-b", "0",
    "-e", STEP_MAX.__str__(),
    "-p", "30", 
    "--vehicle-class", "tram",
    "--prefix", "train_",
    "--allow-fringe",
    "--validate"
]

command_train_rou_creation = [
    "duarouter",
    "--net-file", NET_FILE,
    "--route-files", TRAIN_TRIP_FILE,
    "--output-file", TRAIN_ROU_FILE
]

command_bus_trip_creation = [
    "python",
    os.path.join(SUMO_HOME, "tools", "randomTrips.py"),
    "-n", NET_FILE,
    "-o", BUS_TRIP_FILE,
    "--random-departpos",
    "-b", "0",
    "-e", STEP_MAX.__str__(),
    "-p", "15",
    "--vehicle-class", "bus",
    "--prefix", "bus_",
    "--allow-fringe",
    "--validate"
]

command_bus_rou_creation = [
    "duarouter",
    "--net-file", NET_FILE,
    "--route-files", BUS_TRIP_FILE,
    "--output-file", BUS_ROU_FILE,
    "--ignore-errors",
    "--no-warnings"
]

command_rou_creation = [
    "duarouter",
    "--net-file", NET_FILE,
    "--route-files", TRIP_FILE,
    "--output-file", ROU_FILE,
    "--ignore-errors",
    "--no-warnings"
]

command_ambulance_trip_creation = [
    "python",
    os.path.join(SUMO_HOME, "tools", "randomTrips.py"),
    "-n", NET_FILE,
    "-o", AMBULANCE_TRIP_FILE,
    "--random-departpos",
    "-b", "0",
    "-e", STEP_MAX.__str__(),
    "-p", "15",
    "--vehicle-class", "emergency",
    "--prefix", "emergency_",
    "--allow-fringe",
    "--validate"
]

command_ambulance_rou_creation = [
    "duarouter",
    "--net-file", NET_FILE,
    "--route-files", AMBULANCE_TRIP_FILE,
    "--output-file", AMBULANCE_ROU_FILE,
    "--ignore-errors",
    "--no-warnings"
]

def process_osm_tranformation():
    try:
        subprocess.run(command_osm_transformation, stdout=subprocess.DEVNULL, check=True)
        print("Fichiers net générés avec succès.")
    except subprocess.CalledProcessError as e:
        print("Erreur lors de l'exécution de netconvert :", e)
    except FileNotFoundError:
        print("Netconvert introuvable. Vérifie que SUMO est bien installé et dans le PATH.")

def process_trip_generation():
    try:
        subprocess.run(command_trip_creation, stdout=subprocess.DEVNULL, check=True)
        print("Fichiers trip générés avec succès.")
    except subprocess.CalledProcessError as e:
        print("Erreur lors de l'exécution de randomTrips :", e)
    except FileNotFoundError:
        print("randomTrips introuvable.")

def process_rou_generation():
    try:
        subprocess.run(command_rou_creation, stdout=subprocess.DEVNULL, check=True)
        print("Fichiers route générés avec succès.")
    except subprocess.CalledProcessError as e:
        print("Erreur lors de l'exécution de duarouter :", e)
    except FileNotFoundError:
        print("duarouter introuvable.")

def process_train_trip_generation():
    try:
        subprocess.run(command_train_trip_creation, stdout=subprocess.DEVNULL, check=True)
        print("Fichiers train trip générés avec succès.")
    except subprocess.CalledProcessError as e:
        print("Erreur lors de randomTrips pour les trains :", e)
    except FileNotFoundError:
        print("randomTrips introuvable.")

def process_train_rou_generation():
    try:
        subprocess.run(command_train_rou_creation, stdout=subprocess.DEVNULL, check=True)
        print("Fichiers train route générés avec succès.")
    except subprocess.CalledProcessError as e:
        print("Erreur lors de duarouter pour les trains :", e)
    except FileNotFoundError:
        print("duarouter introuvable.")

def process_bus_trip_generation():
    try:
        subprocess.run(command_bus_trip_creation, stdout=subprocess.DEVNULL, check=True)
        print("Fichiers bus trip générés avec succès.")
    except subprocess.CalledProcessError as e:
        print("Erreur lors de randomTrips pour les bus :", e)
    except FileNotFoundError:
        print("randomTrips introuvable.")

def process_bus_rou_generation():
    try:
        subprocess.run(command_bus_rou_creation, stdout=subprocess.DEVNULL, check=True)
        print("Fichiers bus route générés avec succès.")
    except subprocess.CalledProcessError as e:
        print("Erreur lors de duarouter pour les bus :", e)
    except FileNotFoundError:
        print("duarouter introuvable.")

def process_ambulance_trip_generation():
    try:
        subprocess.run(command_ambulance_trip_creation, stdout=subprocess.DEVNULL, check=True)
        #print("Fichiers ambulance trip générés avec succès.")
    except subprocess.CalledProcessError as e:
        print("Erreur lors de randomTrips pour les ambulances :", e)
    except FileNotFoundError:
        print("randomTrips introuvable.")

def process_ambulance_rou_generation():
    try:
        subprocess.run(command_ambulance_rou_creation, stdout=subprocess.DEVNULL, check=True)
        #print("Fichiers ambulance route générés avec succès.")
    except subprocess.CalledProcessError as e:
        print("Erreur lors de duarouter pour les ambulances :", e)
    except FileNotFoundError:
        print("duarouter introuvable.")

def readNetFile():
    global NET_READER
    if NET_READER is None:
        try:
            NET_READER = readNet(NET_FILE)
            logger.info("Fichier NET chargé avec succès.")
        except Exception as e:
            logger.error(f"Erreur lors du chargement du fichier NET : {e}")
    return NET_READER

def process_files():
    logger.info("Début du traitement des fichiers...")
    logger.info("Génération des fichiers NET à partir de OSM...")
    process_osm_tranformation()
    logger.info("Génération des fichiers TRIP...")
    process_trip_generation()
    logger.info("Génération des fichiers ROU...")
    process_rou_generation()
    logger.info("Génération des fichiers TRAIN TRIP...")
    process_train_trip_generation()
    logger.info("Génération des fichiers TRAIN ROU...")
    process_train_rou_generation()
    logger.info("Génération des fichiers BUS TRIP...")
    process_bus_trip_generation()
    logger.info("Génération des fichiers BUS ROU...")
    process_bus_rou_generation()
    logger.info("Génération des fichiers AMBULANCE TRIP...")
    process_ambulance_trip_generation()
    logger.info("Génération des fichiers AMBULANCE ROU...")
    process_ambulance_rou_generation()
    logger.info("Chargement du fichier NET...")
    readNetFile()