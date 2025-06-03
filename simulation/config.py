import os
import subprocess

from sumolib.net import readNet

OSM_FILE = os.path.join("data", "map.osm.xml")
NET_FILE = os.path.join("data", "map.net.xml")
ROU_FILE = os.path.join("data", "map.rou.xml")
TRIP_FILE = os.path.join("data", "map.trip.xml")
SUMO_HOME = os.environ.get("SUMO_HOME")
SUMO_BINARY = os.path.join(SUMO_HOME, "bin", "sumo")
NET_READER = None

command_osm_transformation = [
    "netconvert",
    "--osm-files", OSM_FILE,
    "--output-file", NET_FILE,
    "--output.street-names", "true",
    "--output.original-names", "true",
    "--tls.guess-signals",
    "--tls.discard-simple",
    "--tls.join",
    "--tls.default-type", "static",
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
    "-e", "300",
    "-p", "0.5",
    "--vehicle-class", "private",
]

command_rou_creation = [
    "duarouter",
    "--net-file", NET_FILE,
    "--route-files", TRIP_FILE,
    "--output-file", ROU_FILE,
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

def process_files():
    global NET_READER
    process_osm_tranformation()
    process_trip_generation()
    process_rou_generation()
    NET_READER = readNet(NET_FILE)