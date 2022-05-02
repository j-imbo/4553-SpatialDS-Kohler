from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from math import radians, degrees, cos, sin, asin, sqrt, pow, atan2
import os
from random import randint

from helper import CountryReader
from helper import Feature
from helper import FeatureCollection

"""
countries with "and" or consecutive caps dont work
"""

origins = ["*"]

app = FastAPI(
    title="Globull",
    description="",
    version="0.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

cDB = CountryReader("countries.geojson")


def centroid(poly):
    xList = [vert[0] for vert in poly]
    yList = [vert[1] for vert in poly]
    pLen = len(poly)
    x = sum(xList)/pLen
    y = sum(yList)/pLen
    return (x, y)


def cbearing(ptA, ptB):
    if (type(ptA) != tuple) or (type(ptB) != tuple):
        raise TypeError("Only tuples allowed as coords >:(")
    latA = radians(ptA[0])
    latB = radians(ptB[0])
    lon = radians(ptB[1]-ptA[1])
    x = sin(lon) * cos(latB)
    y = (cos(latA)*sin(latB)) - (sin(latA)*cos(latB)*cos(lon))
    bear = atan2(x, y)
    bear = degrees(bear)
    compass = (bear+360) % 360
    return compass


def ctCent(name):
    ctPoly = cDB.getPolygons(name)
    lg = lgPoly(ctPoly["geometry"]["coordinates"])
    return centroid(lg)


def ctPoly(name):
    # name = name.lower().title()
    poly = cDB.getPolygons(name)
    lg = lgPoly(poly["geometry"]["coordinates"])
    return lg


def DistancePointLine(px, py, x1, y1, x2, y2):
    LineMag = lineMag(x1, y1, x2, y2)
    if LineMag < 0.00000001:
        return 9999
    u1 = ((px-x1)*(x2-x1)) + ((py-y1)*(y2-y1))
    u = u1/(pow(LineMag, 2))

    if (u < 0.00001) or (u > 1):
        ix = lineMag(px, py, x1, y1)
        iy = lineMag(px, py, x2, y2)
        if ix > iy:
            return iy
        else:
            return ix
    else:
        ix = x1 + u*(x2-x1)
        iy = y1 + u*(y2-y1)
        return lineMag(px, py, ix, iy)


def haversine(lon1, lat1, lon2, lat2, units="miles"):
    rad = {"km": 6371, "miles": 3956}
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2-lon1
    dlat = lat2-lat1
    a = sin(dlat/2)**2 + cos(lat1)*cos(lat2) * sin(dlon/2)**2
    return (2*asin(sqrt(a)) * rad[units])


def lgPoly(polys):
    i = 0
    max = 0
    idx = 0
    for poly in polys:
        if len(poly[0]) > max:
            max = len(poly[0])
            idx = i
        i += 1
    return polys[idx][0]


def lineMag(x1, y1, x2, y2):
    return sqrt(pow((x2-x1), 2) + pow((y2-y1), 2))


@app.get("/")
async def docs_redirect():
    return RedirectResponse(url="/docs")


@app.get("/country_names/")
async def getCountryNames():
    names = cDB.getNames()
    if names:
        return names
    else:
        return {"Error": "Empty or no list of countries... :,("}


@app.get("/country/{country_name}")
async def getCountry(country_name, coords_only: bool = False):
    name = country_name  # .lower().title()
    polys = cDB.getPolygons(name)
    if not polys:
        return {"Error": f"Country {name} didn't exist! :,("}

    lg = lgPoly(polys["geometry"]["coordinates"])
    if coords_only:
        return lg

    f = Feature(coords=lg, properties={"name": name})
    fc = FeatureCollection()
    fc.addFeature(feature=f)
    return fc


@app.get("/countryCenter/{country_name}")
async def countryCenter(country_name, raw: bool = False):
    name = country_name  # .lower().title()
    fc = FeatureCollection()
    cents = []
    poly = cDB.getPolygons(name)
    lg = lgPoly(poly["geometry"]["coordinates"])
    centroi = centroid(lg)
    if raw:
        return centroi

    feature = Feature(coords=centroi, type="Point",
                      properties={"name": poly["properties"]["name_long"]})
    cents.append(centroi)
    fc.addFeature(feature=feature)

    return fc.to_json()


@app.get("/country_lookup/{key}")
async def getCountryPartialMatch(key):
    key = key.lower()
    partial = []
    names = cDB.getNames()
    for name in names:
        low = name.lower()
        if low.contains(key):
            partial.append(name)
    return partial


@app.get("/line_between/")
async def getLineBetween(start: str = None, end: str = None):
    p1 = ctCent(start)
    p2 = ctCent(end)
    f = Feature(coords=[[p1, p2]], type="LineString",
                properties={"from": start, "to": end})
    return f.to_json()


@app.get("/property/{country}")
async def getProperty(country, key: str = None, allKeys: bool = False):
    # country = country.lower().title()
    data = cDB.getProperties(country)
    if key:
        return data[key]

    if allKeys:
        return list(data.keys())

    return data


@app.get("/randomCountry/")
async def getRandomCountry():
    names = cDB.getNames()
    idx = randint(0, len(names))
    ctry = names[idx]
    print(ctry)
    poly = ctPoly(ctry)

    names = names.sort()

    country = cDB.getPolygons(ctry)
    lg = lgPoly(country["geometry"]["coordinates"])

    center = centroid(lg)

    return {"name": ctry, "poly": poly, "center": center}


@app.get("/bbox/{country}")
async def getBbox(country, raw: bool = False):
    # country = country.lower().title()
    bbox = cDB.getBbox(country)

    if raw:
        return bbox

    w, s, e, n = tuple(bbox)
    poly = [[w, s], [e, s], [e, n], [w, n], [w, s]]
    f = Feature(coords=[poly], properties={"country": country}).to_json()
    return f


@app.get("/bboxCenter/{country}")
async def getbboxCenter(country, raw: bool = False):
    # country = country.lower().title()
    bbox = cDB.getBbox(country)

    w, s, e, n = tuple(bbox)
    center = [(w+e)/2, (n+s)/2]

    if raw:
        return center

    f = Feature(coords=center, properties={"country": country}).to_json()

    return f


@app.get("/centroidRelations/")
async def centroidRelations(start: str, end: str):
    lon1, lat1 = ctCent(start)
    lon2, lat2 = ctCent(end)

    f = Feature(
        coords=[["lon1,lat1"], ["lon2,lat2"]],
        type="LineString",
        properties={"from": start, "to": end}
    )
    distance = haversine(lon1, lat1, lon2, lat2)
    bearing = cbearing((lat1, lon1), (lat2, lon2))
    f = f.to_json()
    return {"distance": distance, "bearing": bearing, "line": f}


@app.get("/borderRelations/")
async def borderRelations(start: str, end: str):
    pl1 = ctPoly(start)
    pl2 = ctPoly(end)
    min = 999999
    closest = {}
    touching = []
    for p1 in pl1:
        lon1, lat1 = p1
        for p2 in pl2:
            lon2, lat2 = p2
            d = haversine(lon1, lat1, lon2, lat2)
            if d == 0:
                touching.append(p2)
            if d < min:
                min = d
                closest = {"points": [p1, p2], "distance": d}

    if len(touching) > 0:
        closest = {"points": [], "distance": 0}
    return {"closest": closest, "touching": touching}


@app.get("/lengthLine/{country}")
async def lengthLine(country):
    # country = country.lower().title()
    pol = ctPoly(country)
    max = -999999
    for p1 in pol:
        lon1, lat1 = p1
        for p2 in pol:
            lon2, lat2 = p2
            d = haversine(lon1, lat1, lon2, lat2)
            if d == 0:
                continue
            if d > max:
                max = d
                maxp1 = p1
                maxp2 = p2
                maxd = d
    f = Feature(coords=[maxp1, maxp2], type="LineString",
                properties={"country": country, "distance": maxd})
    return f.to_json()


@app.get("/cardinal/{degrees}")
async def cardinal(degrees, raw: bool = False):
    dir = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
           "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    degrees = int(float(degrees))
    ix = int((degrees+11.25)/22.5)
    d = dir[ix % 16]
    if raw:
        return d
    else:
        return f"<img src='./images/{d}.png'>"


if __name__ == "__main__":
    uvicorn.run("api:app", host="127.0.0.1", port=8080,
                log_level="debug", reload=True)
