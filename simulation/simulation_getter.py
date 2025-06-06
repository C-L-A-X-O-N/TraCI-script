import traci

import simulation.config
from util.converter import convert_to_latlong
from util.mqtt import publish


def send_first_step_data():
    publish("traci/lane/position", collect_lane_position())
    publish("traci/traffic_light/position", collect_traffic_light_position())

def collect_simulation_data(is_first_step: bool, blocked_vehicles: dict):

    # Permet d'envoyer que une seul fois position des feux et des lanes qui ne change pa spendant la sumulation
    if is_first_step:
        send_first_step_data()

    publish("traci/vehicle/position", collect_vehicle(blocked_vehicles))
    publish("traci/traffic_light/state", collect_traffic_light_state())
    publish("traci/lane/state", collect_lane_state())

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

def collect_traffic_light_position():
    traffic_light_ids = traci.trafficlight.getIDList()
    traffic_light_data = []

    for traffic_light in traffic_light_ids:
        for link_group in traci.trafficlight.getControlledLinks(traffic_light):
            for in_lane, out_lane, via_lane in link_group:
                shape = traci.lane.getShape(in_lane)
                if not shape:
                    continue
                x_stop, y_stop = shape[-1]
                lat, lon = convert_to_latlong(x_stop, y_stop)

                traffic_light_data.append({
                    "id": traffic_light,
                    "in_lane": in_lane,
                    "out_lane": out_lane,
                    "via_lane": via_lane,
                    "stop_lat": lat,
                    "stop_lon": lon
                })
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

def collect_lane_position():
    lane_ids = traci.lane.getIDList()
    lane_data = []

    for lane in lane_ids:
        shapes = traci.lane.getShape(lane)
        if not shapes:
            continue
        shape_data = []
        for shape in shapes:
            shape_data.append((convert_to_latlong(shape[0], shape[1])))


        edgeID = traci.lane.getEdgeID(lane)

        edge = simulation.config.NET_READER.getEdge(edgeID) if edgeID in simulation.config.NET_READER._id2edge else None
        priority = edge.getPriority() if edge is not None else 0

        lane_data.append({
            "id": lane,
            "shape": shape_data,
            "priority": priority,
            "type": classify_lane(traci.lane.getAllowed(lane))
        })

    return lane_data

def collect_lane_state():
    lane_ids = traci.lane.getIDList()
    lane_data = []

    for lane in lane_ids:
        lane_data.append({
            "id": lane,
            "traffic_jam": traci.lane.getLastStepOccupancy(lane),
        })

    return lane_data
