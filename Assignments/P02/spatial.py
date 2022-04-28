import csv
import pandas as pd
import numpy as np
import geopandas as gp
from shapely.geometry import Point
import json
# from math import pi,sin,cos,asin,sqrt

"""def haversine(lat1, lon1, lat2, lon2):
    dLat = (lat2 - lat1) * pi / 180.0
    dLon = (lon2 - lon1) * pi / 180.0
    lat1 = lat1*pi/180.0
    lat2 = lat2*pi/180.0
    a = (pow(sin(dLat/2),2) + pow(sin(dLon/2),2) * cos(lat1) * cos(lat2))
    c = 2 * asin(sqrt(a))
    return c*3950"""

f = open("cities.geojson")
data = json.load(f)

points = []
ctnames = []
for feature in data["features"]:
    if feature["geometry"]["type"] == "Point":
        points.append(feature["geometry"]["coordinates"])
        ctnames.append(feature["properties"]["city"])

cities = []
# ctdist = []
for point in points:
    cities.append(Point(point))
    """ctdist.append()
    for pt in points:
        ds = haversine(point.x,point.y,pt.x,pt.y)
        ctdist.append()"""

gs = gp.GeoSeries(cities)

with open("distance.csv", "w", newline='') as out:
    writer = csv.writer(out)
    row = []
    for i in range(len(cities)):
        writer.writerow(gs.distance(cities[i], align=False))

uf = open("ufos.csv")
ufos = pd.read_csv(uf)
gu = gp.GeoDataFrame(ufos, geometry=gp.points_from_xy(ufos.lon, ufos.lat))

# turn point arrays into geoseries
gsU = gu.geometry

# loop thru cities for 100 closest ufos
ufodist = []
for i in range(len(gs)):
    a = gsU.distance(gs[i])
    a = a.values  # just distances for sorting
    a = np.sort(a)
    hundo = a[0:100]  # get top 100
    avg = np.average(hundo)
    ct = {
        "city": ctnames[i],
        "lon": gs[i].x,
        "lat": gs[i].y,
        "avgdist": avg
    }
    ufodist.append(ct)

json.dump(ufodist, open("ufoavg.json", "w"), indent=4, separators=(",", ": "))
