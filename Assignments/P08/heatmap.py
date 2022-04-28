import json
import pandas as pd
import geopandas as gp
import numpy as np
from shapely.geometry import mapping, shape
from shapely.validation import make_valid
import random
import math
from rich import print


class NpEncoder(json.JSONEncoder):  # json encoder to fix int64 issues
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NpEncoder, self).default(obj)


def hexa():  # generates a random hex color
    rand = random.randint(0, 16**6-1)
    hx = str(hex(rand))
    hx = '#'+hx[2:]
    return hx


def hueshift(color, deg):  # shifts a hue by a certain degree
    color = color[1:]  # "#000000" -> "000000" # 010203 -> [01,02,03]
    hexin = [int(color[i:i+2], 16) for i in range(0, len(color), 2)]
    cosA = math.cos(deg*math.pi/180)  # degree -> radians
    sinA = math.sin(deg*math.pi/180)
    rotmat = [
        [cosA + (1-cosA)/3,
            1/3*(1-cosA) - math.sqrt(1/3)*sinA,
            1/3*(1-cosA) + math.sqrt(1/3)*sinA],
        [1/3*(1-cosA) + math.sqrt(1/3)*sinA,
            cosA + 1/3*(1-cosA),
            1/3*(1-cosA) - math.sqrt(1/3)*sinA],
        [1/3*(1-cosA) - math.sqrt(1/3)*sinA,
            1/3*(1-cosA) + math.sqrt(1/3)*sinA,
            cosA + 1/3*(1-cosA)]
    ]
    hexout = [0, 0, 0]
    for i in range(3):
        hexout[i] = math.floor(abs(hexin[0]*rotmat[i][0]
                               + hexin[1]*rotmat[i][1]
                               + hexin[2]*rotmat[i][2]))
    hexout = '#%02x%02x%02x' % (hexout[0], hexout[1], hexout[2])
    return hexout


states = []
with open("states.geojson") as f:
    stDat = gp.read_file(f)
with open("states.geojson") as f:
    geo = json.load(f)
    for state in geo['features']:
        states.append(state['properties']['name'])
        state['properties'].update({
                                    "pop": 0,
                                    "fill": "",
                                    "fill-opacity": .66,
                                    "stroke": "#7d7d7d"})

# remake city json into a gdf for functionality
with open("cities.json") as f:
    citDat = json.load(f)

lat = []
lon = []
population = []
for pt in citDat:
    lat.append(pt["latitude"])
    lon.append(pt["longitude"])
    population.append(pt["population"])

citDat = gp.GeoDataFrame(population, geometry=gp.points_from_xy(lon, lat))
citDat.columns = ["population", "geometry"]

citList = []
"""
cityTemplate = {
  "type": "Feature",
  "properties": {
    "marker-color": hex(),
    "marker-size": "small"
    "population": pop
  },
  "geometry":  geometry
}
"""
citDat = citDat.assign(state="")
stDat = stDat.assign(population=0)
for i in range(len(citDat)):
    for j in range(len(stDat)):
        geom = make_valid(stDat.geometry[j])
        if citDat.geometry[i].within(geom):
            citDat.state[i] = stDat.name[j]
            stDat.population[j] += citDat.population[i]

    #
    ct = {
            "type": "Feature",
            "properties": {
                "marker-color": hexa(),
                "marker-size": "small",
                "pop": citDat.population[i]
            },
            "geometry":  mapping(citDat.geometry[i])
        }
    citList.append(ct)

for state in geo["features"]:
    stname = state["properties"]["name"]
    idx = stDat.query("name == @stname").index.tolist()
    state["properties"]["pop"] = stDat.population[idx[0]]
geo['features'] = sorted(geo['features'],
                         key=lambda x: x['properties']['pop'])

clr = "#ff2400"
for state in geo["features"]:
    if state["properties"]["pop"] == 0:
        state["properties"]["fill"] = "#ffffff"
    else:
        clr = hueshift(clr, 4)
        state["properties"]["fill"] = clr

for city in citList:
    geo["features"].append(city)

with open("heatmap.geojson", "w") as out:
    json.dump(geo, out, indent=4, cls=NpEncoder)
