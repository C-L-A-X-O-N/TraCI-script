import os
import subprocess
import concurrent.futures
import threading
from sumolib.net import readNet
from util.logger import logger

SUMO_CONFIG = os.path.join("data", "file.sumocfg")
OSM_FILE = os.path.join("data", "nantes.osm")
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
STEP_MAX = 3000

# remove all *.rou and *.trip files if they exist
def remove_existing_files():
    files_to_remove = [
        ROU_FILE, TRIP_FILE, TRAIN_TRIP_FILE, TRAIN_ROU_FILE,
        BUS_TRIP_FILE, BUS_ROU_FILE, AMBULANCE_TRIP_FILE, AMBULANCE_ROU_FILE
    ]
    for file in files_to_remove:
        if os.path.exists(file):
            try:
                os.remove(file)
                logger.info(f"Fichier supprimé : {file}")
            except Exception as e:
                logger.error(f"Erreur lors de la suppression du fichier {file} : {e}")

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

# Verrous pour éviter les conflits de logging
print_lock = threading.Lock()

def thread_safe_print(message):
    with print_lock:
        print(message)

def run_command(command, success_message, error_prefix):
    try:
        subprocess.run(command, stdout=subprocess.DEVNULL, check=True)
        thread_safe_print(success_message)
        return True
    except subprocess.CalledProcessError as e:
        thread_safe_print(f"{error_prefix} : {e}")
        return False
    except FileNotFoundError:
        thread_safe_print(f"{error_prefix} - outil introuvable.")
        return False

def process_osm_tranformation():
    return run_command(
        command_osm_transformation,
        "Fichiers net générés avec succès.",
        "Erreur lors de l'exécution de netconvert"
    )

def process_trip_generation():
    return run_command(
        command_trip_creation,
        "Fichiers trip générés avec succès.",
        "Erreur lors de l'exécution de randomTrips"
    )

def process_rou_generation():
    return run_command(
        command_rou_creation,
        "Fichiers route générés avec succès.",
        "Erreur lors de l'exécution de duarouter"
    )

def process_train_trip_generation():
    return run_command(
        command_train_trip_creation,
        "Fichiers train trip générés avec succès.",
        "Erreur lors de randomTrips pour les trains"
    )

def process_train_rou_generation():
    return run_command(
        command_train_rou_creation,
        "Fichiers train route générés avec succès.",
        "Erreur lors de duarouter pour les trains"
    )

def process_bus_trip_generation():
    return run_command(
        command_bus_trip_creation,
        "Fichiers bus trip générés avec succès.",
        "Erreur lors de randomTrips pour les bus"
    )

def process_bus_rou_generation():
    return run_command(
        command_bus_rou_creation,
        "Fichiers bus route générés avec succès.",
        "Erreur lors de duarouter pour les bus"
    )

def process_ambulance_trip_generation():
    return run_command(
        command_ambulance_trip_creation,
        "Fichiers ambulance trip générés avec succès.",
        "Erreur lors de randomTrips pour les ambulances"
    )

def process_ambulance_rou_generation():
    return run_command(
        command_ambulance_rou_creation,
        "Fichiers ambulance route générés avec succès.",
        "Erreur lors de duarouter pour les ambulances"
    )

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
    remove_existing_files()
    logger.info("Début du traitement des fichiers...")
    
    # Étape 1: Conversion OSM -> NET (obligatoirement en premier)
    logger.info("Génération des fichiers NET à partir de OSM...")
    if not process_osm_tranformation():
        logger.error("Échec de la génération du fichier NET. Arrêt du processus.")
        return
    
    # Étape 2: Génération des fichiers TRIP en parallèle
    logger.info("Génération des fichiers TRIP en parallèle...")
    trip_tasks = {
        "trip_standard": process_trip_generation,
        "trip_train": process_train_trip_generation,
        "trip_bus": process_bus_trip_generation,
        "trip_ambulance": process_ambulance_trip_generation
    }
    
    # Compteurs pour le suivi
    total_trips = len(trip_tasks)
    completed_trips = 0
    successful_trips = 0
    
    trip_results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        future_to_task = {executor.submit(task): name for name, task in trip_tasks.items()}
        for future in concurrent.futures.as_completed(future_to_task):
            task_name = future_to_task[future]
            completed_trips += 1
            try:
                result = future.result()
                trip_results[task_name] = result
                
                if result:
                    successful_trips += 1
                    logger.info(f"✅ [{completed_trips}/{total_trips}] Génération de {task_name} terminée avec succès")
                else:
                    logger.warning(f"⚠️ [{completed_trips}/{total_trips}] Génération de {task_name} terminée avec des erreurs")
            except Exception as exc:
                logger.error(f"❌ [{completed_trips}/{total_trips}] {task_name} a généré une exception: {exc}")
                trip_results[task_name] = False
    
    logger.info(f"Génération des TRIP terminée: {successful_trips}/{total_trips} succès")
    
    # Étape 3: Génération des fichiers ROU en parallèle (uniquement pour les TRIP réussis)
    logger.info("Génération des fichiers ROU en parallèle...")
    rou_tasks = {}
    
    if trip_results.get("trip_standard", False):
        rou_tasks["rou_standard"] = process_rou_generation
        logger.debug("Ajout de la génération ROU standard à la file d'attente")
    if trip_results.get("trip_train", False):
        rou_tasks["rou_train"] = process_train_rou_generation
        logger.debug("Ajout de la génération ROU train à la file d'attente")
    if trip_results.get("trip_bus", False):
        rou_tasks["rou_bus"] = process_bus_rou_generation
        logger.debug("Ajout de la génération ROU bus à la file d'attente")
    if trip_results.get("trip_ambulance", False):
        rou_tasks["rou_ambulance"] = process_ambulance_rou_generation
        logger.debug("Ajout de la génération ROU ambulance à la file d'attente")
    
    # Compteurs pour le suivi des ROU
    total_rous = len(rou_tasks)
    completed_rous = 0
    successful_rous = 0
    
    if total_rous == 0:
        logger.warning("Aucun fichier ROU à générer - tous les TRIP ont échoué!")
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            future_to_task = {executor.submit(task): name for name, task in rou_tasks.items()}
            for future in concurrent.futures.as_completed(future_to_task):
                task_name = future_to_task[future]
                completed_rous += 1
                try:
                    result = future.result()
                    if result:
                        successful_rous += 1
                        logger.info(f"✅ [{completed_rous}/{total_rous}] Génération de {task_name} terminée avec succès")
                    else:
                        logger.warning(f"⚠️ [{completed_rous}/{total_rous}] Génération de {task_name} terminée avec des erreurs")
                except Exception as exc:
                    logger.error(f"❌ [{completed_rous}/{total_rous}] {task_name} a généré une exception: {exc}")
        
        logger.info(f"Génération des ROU terminée: {successful_rous}/{total_rous} succès")
    
    # Étape 4: Chargement du fichier NET
    logger.info("Chargement du fichier NET...")
    readNetFile()
    
    # Résumé final
    logger.info(f"Traitement des fichiers terminé: {successful_trips}/{total_trips} TRIP et {successful_rous}/{total_rous} ROU générés avec succès")