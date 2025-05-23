from sumolib.net import readNet

from simulation.config import NET_FILE

net = readNet(NET_FILE)

def convert_to_latlong(x,y):

    lon, lat = net.convertXY2LonLat(x, y)
    return lat, lon