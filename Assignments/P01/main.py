import json
import random

def randColor():
  r = lambda: random.randint(0,255)
  return ('#%02X%02X%02X' % (r(),r(),r()))


def makePoint(city):
  feature = {
    "type": "Feature",
    "properties": {
      "marker-color":randColor(),
    },
    "geometry": {
      "type": "Point",
      "coordinates": [0,0]
    }
  }

  for key,val in city.items():
    if key == 'latitude':
      feature['geometry']['coordinates'][1] = val
    elif key == 'longitude':
      feature['geometry']['coordinates'][0] = val
    else:
      feature['properties'][key] = val

  return feature
  

with open("cities.json") as f:
  data = json.load(f)

states = {}

for item in data:
  if not item["state"] in states:
    states[item["state"]] = []

  states[item["state"]].append(item)


hipoplist = []

for state,stateInfo in states.items():
  hipop=0
  hipopcity = {}
  for i in range(len(stateInfo)):
    if stateInfo[i].get('population') > hipop:
      hipop = stateInfo[i].get('population')
      hipopcity = stateInfo[i]
  hipoplist.append(hipopcity)

points = []
linecoords = []

for city in hipoplist:
  if city['longitude'] > -125:
    points.append(makePoint(city))
    linecoords.append([city['longitude'],city['latitude']])

def sortlong(val):
  return val[0]

linecoords.sort(key=sortlong)

linestr = {
  "type": "Feature",
  "properties": {
    "color": randColor()
  },
  "geometry": {
    "type": "LineString",
    "coordinates": [
    ]
  }
}

geo = {
  "type": "FeatureCollection",
  "features": []
}

for item in points:
  geo['features'].append(item)
for coord in linecoords:
  linestr["geometry"]["coordinates"].append(coord)
geo['features'].append(linestr)

with open("answer.geojson","w") as f:
  json.dump(geo,f,indent=4)