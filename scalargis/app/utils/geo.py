import math
from functools import partial

import pyproj
from shapely.ops import transform
from shapely.wkt import loads


def dd2dms(longitude, latitude):
    # math.modf() splits whole number and decimal into tuple
    # eg 53.3478 becomes (0.3478, 53)
    split_degx = math.modf(longitude)

    # the whole number [index 1] is the degrees
    degrees_x = int(split_degx[1])

    # multiply the decimal part by 60: 0.3478 * 60 = 20.868
    # split the whole number part of the total as the minutes: 20
    # abs() absoulte value - no negative
    minutes_x = abs(int(math.modf(split_degx[0] * 60)[1]))

    # multiply the decimal part of the split above by 60 to get the seconds
    # 0.868 x 60 = 52.08, round excess decimal places to 2 places
    # abs() absoulte value - no negative
    seconds_x = abs(round(math.modf(split_degx[0] * 60)[0] * 60, 2))

    # repeat for latitude
    split_degy = math.modf(latitude)
    degrees_y = int(split_degy[1])
    minutes_y = abs(int(math.modf(split_degy[0] * 60)[1]))
    seconds_y = abs(round(math.modf(split_degy[0] * 60)[0] * 60, 2))

    # account for E/W & N/S
    if degrees_x < 0:
        EorW = "W"
    else:
        EorW = "E"

    if degrees_y < 0:
        NorS = "S"
    else:
        NorS = "N"

    dms = {
        "lon": str(abs(degrees_x)) + u"\u00b0 " + str(minutes_x) + "' " + str(seconds_x) + "\" " + EorW,
        "lat": str(abs(degrees_y)) + u"\u00b0 " + str(minutes_y) + "' " + str(seconds_y) + "\" " + NorS
      }

    return dms

def dd2dm(longitude, latitude):
    # math.modf() splits whole number and decimal into tuple
    # eg 53.3478 becomes (0.3478, 53)
    split_degx = math.modf(longitude)

    # the whole number [index 1] is the degrees
    degrees_x = int(split_degx[1])

    # multiply the decimal part by 60: 0.3478 * 60 = 20.868
    # abs() absoulte value - no negative
    minutes_x = abs(round(split_degx[0] * 60, 5))

    # repeat for latitude
    split_degy = math.modf(latitude)
    degrees_y = int(split_degy[1])
    minutes_y = abs(round(split_degy[0] * 60, 5))

    # account for E/W & N/S
    if degrees_x < 0:
        EorW = "W"
    else:
        EorW = "E"

    if degrees_y < 0:
        NorS = "S"
    else:
        NorS = "N"

    dm = {
        "lon": str(abs(degrees_x)) + u"\u00b0 " + str(minutes_x) + "' " + EorW,
        "lat": str(abs(degrees_y)) + u"\u00b0 " + str(minutes_y) + "' " + NorS
      }

    return dm


def transformGeom(geom, source_proj, dest_proj):
    project = partial(
        pyproj.transform,
        pyproj.Proj(init=source_proj),  # source coordinate system
        pyproj.Proj(init=dest_proj))  # destination coordinate system

    g2 = transform(project, geom)  # apply projection

    return g2


def getGeometryFromWKT(wkt):
    g = None
    if isinstance(wkt, list):
        if len(wkt) > 1:
            g = loads('GEOMETRYCOLLECTION({0})'.format(', '.join(wkt)))
        else:
            g = loads(wkt[0])
    else:
        g = loads(wkt)

    return g
