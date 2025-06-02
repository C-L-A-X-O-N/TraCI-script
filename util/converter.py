import simulation.config

def convert_to_latlong(x,y):
    lon, lat = simulation.config.NET_READER.convertXY2LonLat(x, y)
    return lat, lon