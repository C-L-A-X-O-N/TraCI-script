import traci, logging

import simulation.config
from util.converter import convert_to_latlong
from util.mqtt import registry
import os
import json
import random


def send_first_step_data(mqtt_client):
    logging.info(f"Sending first step data (zone {mqtt_client.zone})...")
    mqtt_client.publish_with_bounds("traci/lane/position", collect_lane_position(mqtt_client.zone))
    mqtt_client.publish_with_bounds("traci/traffic_light/position", collect_traffic_light_position())

def get_max_zone():
    max_zone = os.environ.get("MAX_ZONE", 9)
    try:
        max_zone = int(max_zone)
    except ValueError:
        max_zone = 9
    sqrt = int(max_zone ** 0.5)
    if sqrt * sqrt != max_zone:
        raise ValueError("MAX_ZONE must be a perfect square")
    return max_zone

def get_zones():
    zones = []
    bbox = traci.simulation.getNetBoundary()
    north_west, south_east = bbox
    lat_min, lon_min = convert_to_latlong(north_west[0], north_west[1])
    lat_max, lon_max = convert_to_latlong(south_east[0], south_east[1])
    max_zone = get_max_zone()
    sqr = int(max_zone ** 0.5)
    lat_step = (lat_max - lat_min) / sqr
    lon_step = (lon_max - lon_min) / sqr
    for i in range(sqr):
        for j in range(sqr):
            zone_lat_min = lat_min + i * lat_step
            zone_lon_min = lon_min + j * lon_step
            zone_lat_max = zone_lat_min + lat_step
            zone_lon_max = zone_lon_min + lon_step
            zones.append({
                "zone": i * sqr + j + 1,
                "lat_min": zone_lat_min,
                "lon_min": zone_lon_min,
                "lat_max": zone_lat_max,
                "lon_max": zone_lon_max
            })
    return zones

def get_zone_boundaries(zone):
    if zone is None:
        return None
    zone = int(zone)
    zones = get_zones()
    for z in zones:
        if int(z["zone"]) == zone:
            return {
                "lat_min": z["lat_min"],
                "lon_min": z["lon_min"],
                "lat_max": z["lat_max"],
                "lon_max": z["lon_max"]
            }
    return None

def get_zone_from_position(lat, lon):
    zones = get_zones()
    for z in zones:
        if (z["lat_min"] <= lat <= z["lat_max"]) and (z["lon_min"] <= lon <= z["lon_max"]):
            return z["zone"]
    return None

def collect_simulation_data(is_first_step: bool, blocked_vehicles: dict):
    clients = registry.get_clients()
    if len(clients) > 0:
        # Permet d'envoyer que une seul fois position des feux et des lanes qui ne change pa spendant la sumulation
        logging.debug("Collecting vehicles...")
        vehicles = collect_vehicle(blocked_vehicles)
        logging.debug("Collecting traffic light...")
        lights = collect_traffic_light_state()
        logging.debug("Collecting lanes...")
        lanes = collect_lane_state()

        for client in clients:
            logging.debug(f"Publishing data to zone {client.zone}...")
            client.publish_with_bounds("traci/vehicle/position", vehicles)
            client.publish_with_bounds("traci/traffic_light/state", lights)
            client.publish_with_bounds("traci/lane/state", lanes)

def collect_vehicle(blocked_vehicles: dict):
    vehicle_ids = traci.vehicle.getIDList()
    vehicle_data = []

    for vehicle in vehicle_ids:
        accident = False
        position = traci.vehicle.getPosition(vehicle)
        speed = traci.vehicle.getSpeed(vehicle)
        if (vehicle in blocked_vehicles):
            accident = True
        vehicle_data.append({
            "id": vehicle,
            "position": convert_to_latlong(position[0],position[1]),
            "angle": traci.vehicle.getAngle(vehicle),
            "speed": speed,
            "type": traci.vehicle.getTypeID(vehicle),
            "accident": accident
        })

    return vehicle_data

traffic_lights_position = None

def collect_traffic_light_position():
    global traffic_lights_position
    if traffic_lights_position is not None:
        return traffic_lights_position
    
    logging.info("Collecting traffic light position data...")
    
    import concurrent.futures

    traffic_light_ids = traci.trafficlight.getIDList()

    def process_traffic_light(traffic_light):
        data = []
        for link_group in traci.trafficlight.getControlledLinks(traffic_light):
            for in_lane, out_lane, via_lane in link_group:
                shape = traci.lane.getShape(in_lane)
                if not shape:
                    continue
                x_stop, y_stop = shape[-1]
                lat, lon = convert_to_latlong(x_stop, y_stop)

                data.append({
                    "id": traffic_light,
                    "in_lane": in_lane,
                    "out_lane": out_lane,
                    "via_lane": via_lane,
                    "position": [lat, lon],
                })
        return data

    traffic_light_data = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
        results = executor.map(process_traffic_light, traffic_light_ids)
        for res in results:
            traffic_light_data.extend(res)
            
    traffic_lights_position = traffic_light_data
    logging.info(f"Collected {len(traffic_lights_position)} traffic light position data")
    return traffic_light_data

def collect_traffic_light_state():
    traffic_light_ids = traci.trafficlight.getIDList()
    traffic_light_data = []

    for traffic_light in traffic_light_ids:
        traffic_light_data.append({
            "id": traffic_light,
            "state": traci.trafficlight.getRedYellowGreenState(traffic_light)
        })

    return traffic_light_data

def classify_lane(allowed):
    if any(v in allowed for v in ["passenger", "private", "hov", "vip", "evehicle", "taxi"]):
        return "car"
    if any(v in allowed for v in ["bus", "coach"]):
        return "public_transport"
    if any(v in allowed for v in ["tram"]):
        return "train"
    if any(v in allowed for v in ["motorcycle", "moped"]):
        return "2_wheeler"
    if "bicycle" in allowed:
        return "bike"
    if "pedestrian" in allowed:
        return "pedestrian"
    return "unknown"

lanes_position = None

def collect_lane_position(zone=None, batch_size=1000, cache_file="lane_positions_cache.json"):
    global lanes_position
    logging.info(f"Collecting lane position data for zone {zone}...")
    cache_file = f"lane_positions_cache.{get_max_zone()}.json"
    if lanes_position is not None:
        if zone is not None and str(zone) in lanes_position:
            logging.info(f"Returning {len(lanes_position[str(zone)])} lanes for zone {zone}")
            return lanes_position[str(zone)]
        # Merge all lane lists if zone is None or not found
        merged = []
        for lane_list in lanes_position.values():
            merged.extend(lane_list)
        logging.info(f"Returning {len(merged)} lanes for all zones")
        return merged

    # Try to load from cache
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r") as f:
                lanes_position = json.load(f)
                logging.info(f"Loaded lane position data from cache")
                return lanes_position
        except Exception as e:
            logging.warning(f"Failed to load lane position cache: {e}")

    logging.info("Collecting lane position data...")

    lane_ids = traci.lane.getIDList()
    lane_data_by_zone = {}

    import concurrent.futures

    def process_batch(batch):
        batch_data = []
        for lane in batch:
            shapes = traci.lane.getShape(lane)
            if not shapes:
                continue
            zones = {}
            shape_data = []
            for shape in shapes:
                [x, y] = convert_to_latlong(shape[0], shape[1])
                shape_data.append((x, y))
                zone = get_zone_from_position(x, y)
                if zone is not None:
                    zones[zone] = True

            edgeID = traci.lane.getEdgeID(lane)
            edge = simulation.config.NET_READER.getEdge(edgeID) if edgeID in simulation.config.NET_READER._id2edge else None
            priority = edge.getPriority() if edge is not None else 0

            lane_info = {
                "id": lane,
                "shape": shape_data,
                "zones": list(zones.keys()),
                "priority": priority,
                "type": classify_lane(traci.lane.getAllowed(lane))
            }
            for zone in zones.keys():
                batch_data.append((zone, lane_info))
        return batch_data

    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
        futures = []
        for i in range(0, len(lane_ids), batch_size):
            batch = lane_ids[i:i+batch_size]
            futures.append(executor.submit(process_batch, batch))
        for i, future in enumerate(futures):
            for zone, lane_info in future.result():
                if str(zone) not in lane_data_by_zone:
                    lane_data_by_zone[str(zone)] = []
                lane_data_by_zone[str(zone)].append(lane_info)
            logging.info(f"Processed lanes {i * batch_size} to {min((i + 1) * batch_size, len(lane_ids))}")

    lanes_position = lane_data_by_zone

    # Save to cache
    try:
        with open(cache_file, "w") as f:
            json.dump(lanes_position, f)
        logging.info(f"Saved lane position data to cache")
    except Exception as e:
        logging.warning(f"Failed to save lane position cache: {e}")

    return collect_lane_position(zone=zone)

zone_selected = 1

def collect_lane_state(batch_size=10000):
    import concurrent.futures
    global lanes_position, zone_selected

    lanes = lanes_position[str(zone_selected)]
    zone_selected += 1
    if zone_selected > len(lanes_position):
        zone_selected = 1
    lane_data = []

    def process_batch(batch):
        batch_data = []
        for lane in batch:
            lane = lane["id"]
            occupancy = None
            # 1 chance sur 3 de récupérer l'occupancy
            if random.randint(1, 3) == 1:
                try:
                    occupancy = traci.lane.getLastStepOccupancy(lane)
                except Exception:
                    occupancy = None
            batch_data.append({
                "id": lane,
                "traffic_jam": occupancy,
            })
        return batch_data

    max_workers = min(32, (len(lanes) // batch_size) + 1)
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for i in range(0, len(lanes), batch_size):
            batch = lanes[i:i+batch_size]
            futures.append(executor.submit(process_batch, batch))
        for future in concurrent.futures.as_completed(futures):
            lane_data.extend(future.result())

    return lane_data
