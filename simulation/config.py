import os
import subprocess

OSM_FILE = "data" + "/map.osm.xml"
NET_FILE = "data" + "/map.net.xml"
ROU_FILE = "data" + "/map.rou.xml"
TRIP_FILE = "data" + "/map.trip.xml"
SUMO_HOME = os.environ.get("SUMO_HOME")
SUMO_BINARY = SUMO_HOME + "bin/sumo"

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
    "python3",
    SUMO_HOME + "tools/randomTrips.py",
    "-n", NET_FILE,
    "-o", TRIP_FILE,
    "--random-departpos",
    "-b", "0",
    "-e", "3000",
    "-p", "1.5",
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
        subprocess.run(command_osm_transformation)
        print("Fichiers net générés avec succès.")
    except subprocess.CalledProcessError as e:
        print("Erreur lors de l'exécution de netconvert :", e)
    except FileNotFoundError:
        print("Netconvert introuvable. Vérifie que SUMO est bien installé et dans le PATH.")

def process_trip_generation():
    try:
        subprocess.run(command_trip_creation)
        print("Fichiers trip générés avec succès.")
    except subprocess.CalledProcessError as e:
        print("Erreur lors de l'exécution de randomTrips :", e)
    except FileNotFoundError:
        print("randomTrips introuvable.")

def process_rou_generation():
    try:
        subprocess.run(command_rou_creation)
        print("Fichiers route générés avec succès.")
    except subprocess.CalledProcessError as e:
        print("Erreur lors de l'exécution de duarouter :", e)
    except FileNotFoundError:
        print("duarouter introuvable.")

def process_files():
    process_osm_tranformation()
    process_trip_generation()
    process_rou_generation()