# gmlEngine module

from lxml.etree import Element, SubElement, QName, tostring
from lxml import etree, html
from shapely.wkt import dumps, loads

## Set up namespaces
class XMLNamespaces:
        gml = 'http://www.opengis.net/gml/3.2'
        
def gmlMaker(shapely_geom):
    ## create Parent gml wrapper
    wrapper = Element(QName(XMLNamespaces.gml, 'Wrapper'), nsmap={'gml':XMLNamespaces.gml})
    # send geom to correct type
    if shapely_geom.type == 'MultiPoint':
        gml = shapely_mpt_to_gml(shapely_geom, wrapper)
    elif shapely_geom.type == 'MultiLineString':
        gml = shapely_mline_to_gml(shapely_geom, wrapper)
    elif shapely_geom.type == 'MultiPolygon':
        gml = shapely_mpoly_to_gml(shapely_geom, wrapper)
    elif shapely_geom.type == 'Polygon':
        gml = shapely_poly_to_gml(shapely_geom, wrapper)
    elif shapely_geom.type == 'LineString':
        gml = shapely_line_to_gml(shapely_geom, wrapper)
    else:
        gml = "ERROR"
    newgml = gml.getchildren()[0]
    return newgml

def gmlReplacer(newgml,file):
    tree = etree.parse(file)
    root = tree.getroot()
    nsmap = {k:v for k,v in root.nsmap.items() if k}

    gmlXP = '/gmi:MI_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:geographicElement/gmd:EX_BoundingPolygon/gmd:polygon/*'

    gml = (tree.xpath(gmlXP, namespaces=nsmap)[0])

    gmlparent = gml.getparent()
    #print(type(gmlparent))
    #print(gmlparent.tag)
    #print(tostring(gmlparent))

    #print('original gml len',len(tostring(gml)))

    #print('new gml len',len(tostring(newgml)))

    #delete old gml
    gmlparent.remove(gml)
    gmlparent.append(newgml)
    #print(len(tostring(root)))
    
    etree.ElementTree(root).write(file, pretty_print=True)

### --- GML Makers ---

def shapely_poly_to_gml(poly, wrapper):    
    polygon = SubElement(wrapper, QName(XMLNamespaces.gml, 'Polygon'))
    polygon.attrib[QName(XMLNamespaces.gml, 'id')] = 'polygon'
    polygon.attrib['srsName'] = "urn:ogc:def:crs:EPSG::4326"
    exterior = SubElement(polygon, QName(XMLNamespaces.gml, 'exterior'))
    linearRing = SubElement(exterior, QName(XMLNamespaces.gml, 'LinearRing'))
    posList = SubElement(linearRing, QName(XMLNamespaces.gml, 'posList'))
    posList.attrib['srsDimension'] = "2"
    posList.text = shapely_poly_to_poslist_text2(poly)
    return wrapper

def shapely_mpt_to_gml(multipoints, wrapper):    
    multipt = SubElement(wrapper, QName(XMLNamespaces.gml, 'MultiPoint'))
    multipt.attrib[QName(XMLNamespaces.gml, 'id')] = "points"
    multipt.attrib['srsName'] = "urn:ogc:def:crs:EPSG::4326"
    id = 1
    for i in range(0, len(multipoints.geoms)):
        g = multipoints.geoms[i]
        wkt1 = loads(g.wkt)
        wkt = dumps(wkt1, rounding_precision=6)
        #print('DUMPS', i, id, wkt)
        cleanedwkt1 = wkt.replace("POINT (", "")
        cleanedwkt2 = cleanedwkt1.replace(",", "")
        cleanedwkt3 = cleanedwkt2.replace(")", "")
        cleanedwkt4 = cleanedwkt3.replace("(", "")
        pointMember = SubElement(multipt, QName(XMLNamespaces.gml, 'pointMember'))
        point = SubElement(pointMember, QName(XMLNamespaces.gml, 'Point'))
        point.attrib[QName(XMLNamespaces.gml, 'id')] = 'point' + str(id)
        pos = SubElement(point, QName(XMLNamespaces.gml, 'pos'))
        pos.attrib['srsDimension'] = "2"
        pos.text = coord_flipper(cleanedwkt4)
    return wrapper

def shapely_mline_to_gml(mline, wrapper):    
    multiCurve = SubElement(wrapper, QName(XMLNamespaces.gml, 'MultiCurve'))
    multiCurve.attrib[QName(XMLNamespaces.gml, 'id')] = "transects"
    multiCurve.attrib['srsName'] = "urn:ogc:def:crs:EPSG::4326"
    ## create individual curve members for each line
    id = 1
    for line in mline:
        curveMember = SubElement(multiCurve, QName(XMLNamespaces.gml, 'curveMember'))
        curve = SubElement(curveMember, QName(XMLNamespaces.gml, 'Curve'))
        curve.attrib[QName(XMLNamespaces.gml, 'id')] = 'line' + str(id)
        segments = SubElement(curve, QName(XMLNamespaces.gml, 'segments'))
        lineStringSegment = SubElement(segments, QName(XMLNamespaces.gml, 'LineStringSegment'))
        posList = SubElement(lineStringSegment, QName(XMLNamespaces.gml, 'posList'))
        posList.attrib['srsDimension'] = "2"
        posList.text = shapely_line_to_poslist_text(line)
        id += 1
    return wrapper

def shapely_line_to_gml(line, wrapper):    
    curve = SubElement(wrapper, QName(XMLNamespaces.gml, 'Curve'))
    curve.attrib[QName(XMLNamespaces.gml, 'id')] = "transect"
    curve.attrib['srsName'] = "urn:ogc:def:crs:EPSG::4326"
    segments = SubElement(curve, QName(XMLNamespaces.gml, 'segments'))
    lineStringSegment = SubElement(segments, QName(XMLNamespaces.gml, 'LineStringSegment'))
    posList = SubElement(lineStringSegment, QName(XMLNamespaces.gml, 'posList'))
    posList.attrib['srsDimension'] = "2"
    posList.text = shapely_line_to_poslist_text2(line)
    return wrapper

def shapely_mpoly_to_gml(mpoly, wrapper):    
    multiSurf = SubElement(wrapper, QName(XMLNamespaces.gml, 'MultiSurface'))
    multiSurf.attrib[QName(XMLNamespaces.gml, 'id')] = "features"
    multiSurf.attrib['srsName'] = "urn:ogc:def:crs:EPSG::4326"
    ## create individual polygon members for each line
    id = 1
    for poly in mpoly:
        surfaceMember = SubElement(multiSurf, QName(XMLNamespaces.gml, 'surfaceMember'))
        polygon = SubElement(surfaceMember, QName(XMLNamespaces.gml, 'Polygon'))
        polygon.attrib[QName(XMLNamespaces.gml, 'id')] = 'poly' + str(id)
        exterior = SubElement(polygon, QName(XMLNamespaces.gml, 'exterior'))
        linearRing = SubElement(exterior, QName(XMLNamespaces.gml, 'LinearRing'))
        posList = SubElement(linearRing, QName(XMLNamespaces.gml, 'posList'))
        posList.attrib['srsDimension'] = "2"
        posList.text = shapely_poly_to_poslist_text2(poly)
        id += 1
    return wrapper

### Helper functions to turn shapely geoms into raw text for GML

def coord_flipper(raw_coord_list):
    coordList = (raw_coord_list).split()
    flip_tup = [(coordList[i], coordList[i-1]) for i in range(1, len(coordList), 2)]
    flip_list = list(sum(flip_tup, ()))
    flip_str = " ".join(str(x) for x in flip_list)
    return flip_str

def shapely_multipoints_to_pos_text(line):
    ## turn shapely multipoints into pos
    wkt = dumps(line, rounding_precision=6)
    cleanedwkt1 = wkt.replace("LINESTRING (", "")
    cleanedwkt2 = cleanedwkt1.replace(",", "")
    cleanedwkt3 = cleanedwkt2.replace(")", "")
    raw_coord_list = cleanedwkt3.replace("(", "")
    flipped_coord_list = coord_flipper(raw_coord_list)
    return flipped_coord_list

def shapely_line_to_poslist_text(line):
    ## turn shapely line into coord list
    wkt = dumps(line, rounding_precision=6)
    cleanedwkt1 = wkt.replace("LINESTRING (", "")
    cleanedwkt2 = cleanedwkt1.replace(",", "")
    cleanedwkt3 = cleanedwkt2.replace(")", "")
    raw_coord_list = cleanedwkt3.replace("(", "")
    flipped_coord_list = coord_flipper(raw_coord_list)
    return flipped_coord_list

def shapely_line_to_poslist_text2(line):
    ## turn shapely line into gml poslist
    posList = ''
    for coordPair in list(line.coords):
        if posList == '':
            posList += str(coordPair[1]) + ' '
            posList += str(coordPair[0])
        else:
            posList += ' ' + str(coordPair[1])
            posList += ' ' + str(coordPair[0])
    return posList

def shapely_poly_to_poslist_text(poly):
    ## turn shapely polygon into coord list
    wkt = dumps(poly, rounding_precision=6)
    #print(wkt)
    cleanedwkt1 = wkt.replace("POLYGON (", "")
    cleanedwkt2 = cleanedwkt1.replace(",", "")
    cleanedwkt3 = cleanedwkt2.replace(")", "")
    raw_coord_list = cleanedwkt3.replace("(", "")
    flipped_coord_list = coord_flipper(raw_coord_list)
    return flipped_coord_list

def shapely_poly_to_poslist_text2(poly):
    ## turn shapely polygon into gml poslist
    posList = ''
    for coordPair in list(poly.exterior.coords):
        if posList == '':
            posList += str(coordPair[1]) + ' '
            posList += str(coordPair[0])
        else:
            posList += ' ' + str(coordPair[1])
            posList += ' ' + str(coordPair[0])
    return posList
                           
def get_rounded_geom(geom):
    ##
    wkt_6 = dumps(geom, rounding_precision=6)
    roundedGeom = loads(wkt_6)
    return roundedGeom