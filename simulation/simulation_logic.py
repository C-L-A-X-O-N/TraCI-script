import traci

from util.converter import convert_to_latlong
from util.mqtt import publish


def collect_simulation_data():
    publish("vehicle", collect_vehicle())
    publish("traffic_light", collect_traffic_light_position())
    publish("lane", collect_lane_position())

def collect_vehicle():
    vehicle_ids = traci.vehicle.getIDList()
    vehicle_data = []

    for vehicle in vehicle_ids:
        position = traci.vehicle.getPosition(vehicle)
        speed = traci.vehicle.getSpeed(vehicle)
        vehicle_data.append({
            "id": vehicle,
            "position": convert_to_latlong(position[0],position[1]),
            "angle": traci.vehicle.getAngle(vehicle),
            "speed": speed
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
                    "tls_id": traffic_light,
                    "in_lane": in_lane,
                    "out_lane": out_lane,
                    "via_lane": via_lane,
                    "stop_lat": lat,
                    "stop_lon": lon
                })
    return traffic_light_data

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

        lane_data.append({
            "id": lane,
            "shape": shape_data,
        })

    return lane_data