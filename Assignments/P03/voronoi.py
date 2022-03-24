import geopandas as gp
import json
from shapely.ops import unary_union
from geovoronoi import voronoi_regions_from_coords, points_to_coords
from geovoronoi.plotting import subplot_for_map, plot_voronoi_polys_with_points_in_area


border = gp.read_file("data/us_border.geojson")
border = border.to_crs(epsg=3395)
bShape = unary_union(border.geometry)
cities = gp.read_file("data/cities.geojson")
cities = cities.to_crs(epsg=3395)
cCoord = points_to_coords(cities.geometry)
cty = cities["city"]

regions, rPts = voronoi_regions_from_coords(cCoord, bShape)

ufos = gp.read_file("data/ufos.geojson")
ufos = ufos.to_crs(epsg=3395)
uInd = gp.GeoSeries(ufos["geometry"])

ufoReg = []
for i in range(len(regions)):
    city = {"Region #": i, "City": cty[i], "UFOs": []}
    res = uInd.within(regions[i])
    for j in range(len(res)):
        ufo = []
        if res[j]:
            city["UFOs"].append({j: [ufos["geometry"][j].x,ufos["geometry"][j].y]})
    ufoReg.append(city)

json.dump(ufoReg, open("voroout.json","w"),indent=4,separators=(",",": "))
