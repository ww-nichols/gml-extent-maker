# geomEngine module

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, MultiPoint, LineString, MultiLineString, Polygon, MultiPolygon, GeometryCollection, box
from shapely.ops import linemerge, transform
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as feature
import json
import geojson as gjson
import itertools as it

from bokeh.plotting import figure, show, output_file
from bokeh.palettes import Category10
from bokeh.sampledata.sample_geojson import geojson
from bokeh.models import GeoJSONDataSource
from bokeh.io import output_notebook

# Takes Data Fram with columns Longitude and Latitude and returns a shapely multipoint
def mpointmaker(df):
    geometry = [Point(xy) for xy in zip(df.Longitude, df.Latitude)]
    multipoint = MultiPoint(geometry)
    return multipoint

# Takes Data Frame with columns Longitude and Latitude and returns a shapely line
def linemaker(df):
    geometry = [Point(xy) for xy in zip(df.Longitude, df.Latitude)]
    geodf = gpd.GeoDataFrame(df, geometry=geometry)
    rawline = geodf['geometry'].tolist()
    line = LineString(rawline)
    return line

# take a shapely line and returns the total number of coordinates
def len_line(l):
    return len(l.coords)

# takes a shapely MultiLineString and tolerance (default 0.0075) and iterates through lines, merging lines end point of line i is within tolerance of beginning point of line i+1
def merge_multiLine(ml, tol=0.0075):
    ml2 = linemerge(ml)
    snappedLineList = []
    workingLineList = []
    emptyFlag = True
    for i in range(0,len(ml2)):
        currentLineList = ml2[i].coords[:]
        if emptyFlag == True:
            workingLineList.extend(currentLineList)
            emptyFlag = False
        else:
            if Point(workingLineList[-1]).distance(Point(currentLineList[0])) < tol:
                workingLineList.extend(currentLineList)
            else:
                snappedLineList.append(LineString(workingLineList))
                workingLineList = currentLineList
    snappedLine = MultiLineString(snappedLineList)
    return snappedLine

# take a shapely MultiLineString and returns the total number of coordinates
def len_multiline(ml):
    count = 0
    for l in ml.geoms:
        count += len_line(l)
    return count

# take a shapely polygon and returns the total number of coordinates
def len_polygon(p):
    return len(p.exterior.coords)

# take a shapely multipolygon and returns the total number of coordinates
def len_multipoly(mp):
    count = 0
    countPolys = 0
    for p in mp.geoms:
        count += len(p.exterior.coords)
        countPolys += 1
    return countPolys, count

# takes shapely geometry object and returns # of geometries and # of coords
# needs abstraction and support for geometry collections
def len_geom(geom):
    countCoords = 0
    countGeoms = 0
    if (geom.geom_type == 'Point') or (geom.geom_type == 'LineString'):
        countCoords += len(geom.coords)
        countGeoms += 1
    elif geom.geom_type == 'Polygon':
        countCoords += len(geom.exterior.coords)
        countGeoms += 1
    elif (geom.geom_type == 'MultiPoint') or (geom.geom_type == 'MultiLineString'):
        for geometry in geom.geoms:
            countCoords += len(geometry.coords)
            countGeoms += 1
    elif (geom.geom_type == 'MultiPolygon'):
        for geometry in geom.geoms:
            countCoords += len(geometry.exterior.coords)
            countGeoms += 1
    else:
        print(type(geom), geom.geom_type,'Geom Type not supported')
    return countCoords, 'coords', countGeoms, 'geoms', geom.geom_type

def plot_geoms(geom):
    if checkCollection(geom) == False:
        geom = makeCollection(geom)
    #bokeh interactive plot
    bokeh_plot(geom)
    
    #matplotlib plot with coastlines of spatial extent
    
    fig = plt.figure()
    plt.subplot(2, 1, 1)
    ax = plt.axes(projection=ccrs.PlateCarree())
    bbox = box(*(geom.bounds))
    extent = bbox.buffer(0.5)
    bounds = [extent.bounds[0],extent.bounds[2],extent.bounds[1],extent.bounds[3]]
    ax.set_extent(bounds, ccrs.PlateCarree())
    ax.coastlines()
    if (geom.geom_type == 'MultiPoint') or (geom.geom_type == 'Point'):
        ax.scatter([pt.x for pt in geom],
                   [pt.y for pt in geom],
                   color='red')
    else:
        ax.add_geometries(geom, ccrs.PlateCarree(), edgecolor='red', facecolor='none')
    gridslines = ax.gridlines(draw_labels=True)
    plt.show()

    #matplotlib plot with coastlines of Gulf of Mexico
        
    plt.subplot(2, 1, 2)
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_extent([-98,-80,18,32], ccrs.PlateCarree())
    ax.coastlines()
    if (geom.geom_type == 'MultiPoint') or (geom.geom_type == 'Point'):
        ax.scatter([pt.x for pt in geom],
                   [pt.y for pt in geom],
                   color='red')
    else:
        ax.add_geometries(geom, ccrs.PlateCarree(), edgecolor='red', facecolor='none')
    gridslines = ax.gridlines(draw_labels=True)

    plt.show()
    
def checkCollection(geom):
    if ((geom.geom_type == 'Point') or (geom.geom_type == 'LineString')
        or (geom.geom_type == 'Polygon')):
        return False
    else:
        return True
    
def makeCollection(geom):
    if checkCollection(geom) == False:
        if geom.geom_type == 'Point':
            newGeom = MultiPoint([geom])
        elif geom.geom_type == 'LineString':
            newGeom = MultiLineString([geom])
        elif geom.geom_type == 'Polygon':
            newGeom = MultiPolygon([geom])
        return newGeom
    else:
        return geom
    
def bokeh_plot(geom):
    geo_source = GeoJSONDataSource(geojson=(gpd.GeoSeries([geom]).to_json()))
    p = figure()
    if (geom.geom_type == 'MultiPolygon') or (geom.geom_type == 'Polygon'):
        geo_source = GeoJSONDataSource(geojson=(gpd.GeoSeries([geom]).to_json()))
        p.patches('xs', 'ys', source=geo_source, fill_color="white",
        fill_alpha=0.7, line_color="red",)
    elif (geom.geom_type == 'MultiLineString') or (geom.geom_type == 'LineString'):
        for g, color in zip(geom, it.cycle(Category10[10])):
            jsonGeom = json.loads(gpd.GeoSeries([g]).to_json())
            table = jsonGeom['features'][0]['geometry']['coordinates']
            df = pd.DataFrame(table)
            df.columns = ['Longitude', 'Latitude']
            p.line(df['Longitude'], df['Latitude'], color=color, line_width=3)
    elif (geom.geom_type == 'MultiPoint') or (geom.geom_type == 'Point'):
        pts = []
        for pt in geom:
            pts.append(pt)
        geomCollect = gjson.GeometryCollection(pts)
        geo_source = GeoJSONDataSource(geojson=gjson.dumps(geomCollect))
        p.circle('x', 'y', source=geo_source, color="red", size=5)
    else:
        print('not implemented for this geom type')
    show(p)
    
def geom_comparison_bokeh_plot(original_geom, processed_geom):
    ## plot 2 geometries on same bokeh plot, for comparing original vs simplified geoms
    
    if checkCollection(original_geom) == False:
        geom = makeCollection(original_geom)
    if checkCollection(processed_geom) == False:
        geom = makeCollection(processed_geom)
        
    orig_geo_source = GeoJSONDataSource(geojson=(gpd.GeoSeries([original_geom]).to_json()))
    proc_geo_source = GeoJSONDataSource(geojson=(gpd.GeoSeries([processed_geom]).to_json()))
 
    p = figure()
    
    ## original geom
    if (original_geom.geom_type == 'MultiPolygon') or (original_geom.geom_type == 'Polygon'):
        geo_source = GeoJSONDataSource(geojson=(gpd.GeoSeries([geom]).to_json()))
        p.patches('xs', 'ys', source=geo_source, fill_color="white",
        fill_alpha=0.7, line_color="red",)
    elif (original_geom.geom_type == 'MultiLineString') or (original_geom.geom_type == 'LineString'):
        for g, color in zip(original_geom, it.cycle(Category10[10])):
            jsonGeom = json.loads(gpd.GeoSeries([g]).to_json())
            table = jsonGeom['features'][0]['geometry']['coordinates']
            df = pd.DataFrame(table)
            df.columns = ['Longitude', 'Latitude']
            p.line(df['Longitude'], df['Latitude'], color=color, line_width=3)
    elif (original_geom.geom_type == 'MultiPoint') or (original_geom.geom_type == 'Point'):
        pts = []
        for pt in original_geom:
            pts.append(pt)
        geomCollect = gjson.GeometryCollection(pts)
        geo_source = GeoJSONDataSource(geojson=gjson.dumps(geomCollect))
        p.circle('x', 'y', source=geo_source, color="red", size=5)
    else:
        print('not implemented for this geom type')    
    
    # processed geom
    if (processed_geom.geom_type == 'MultiPolygon') or (processed_geom.geom_type == 'Polygon'):
        geo_source = GeoJSONDataSource(geojson=(gpd.GeoSeries([processed_geom]).to_json()))
        p.patches('xs', 'ys', source=geo_source, fill_color="white",
        fill_alpha=0.7, line_color="blue",)
    elif (processed_geom.geom_type == 'MultiLineString') or (geom.geom_type == 'LineString'):
        for g in processed_geom:
            jsonGeom = json.loads(gpd.GeoSeries([g]).to_json())
            table = jsonGeom['features'][0]['geometry']['coordinates']
            df = pd.DataFrame(table)
            df.columns = ['Longitude', 'Latitude']
            p.line(df['Longitude'], df['Latitude'], color="blue", line_width=3)
    elif (processed_geom.geom_type == 'MultiPoint') or (processed_geom.geom_type == 'Point'):
        pts = []
        for pt in processed_geom:
            pts.append(pt)
        geomCollect = gjson.GeometryCollection(pts)
        geo_source = GeoJSONDataSource(geojson=gjson.dumps(geomCollect))
        p.circle('x', 'y', source=geo_source, color="blue", size=5)
    else:
        print('not implemented for this geom type')    

    show(p) 
    
def check_valid(geom):
    return()

def latlontomercator_math(row):
    x_lon = row['x']
    y_lat = row['y']

    # longitudes are a one step transformation
    x_mer = list(map(lambda x: x * 20037508.34 / 180, x_lon))

    # latitudes are a two step transformation
    y_mer_aux = list(map(lambda y: math.log(math.tan((90 + y) * math.pi / 360))
                                    / (math.pi / 180), y_lat))
    y_mer = list(map(lambda y: y * 20037508.34 / 180, y_mer_aux))

    return(x_mer, y_mer)

def remove_z(geom):
    return transform(lambda x, y, z=None: (x, y), geom)

def convert2ptsList(geom):
    pointsList = []
    if (geom.geom_type == 'MultiLineString'):
        for line in geom:
            for x, y in line.coords:
                pt_x = x
                pt_y = y
                newPoint = Point(pt_x,pt_y)
                pointsList.append(newPoint)             
    return pointsList

