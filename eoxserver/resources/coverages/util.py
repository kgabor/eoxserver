#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#          Stephan Krause <stephan.krause@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2011 EOX IT Services GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
# copies of the Software, and to permit persons to whom the Software is 
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#-------------------------------------------------------------------------------


import operator

from django.db.models import Min, Max
from django.contrib.gis.db.models import Union
from django.contrib.gis.geos import MultiPolygon, Polygon
from django.utils.timezone import is_naive, make_aware, get_current_timezone
from django.utils.dateparse import parse_datetime


def pk_equals(first, second):
    return first.pk == second.pk


def detect_circular_reference(eo_object, collection, supercollection_getter, equals=pk_equals):
    """Utility function to detect circular references in model hierarchies."""

    #print "Checking for circular reference: %s %s" %(eo_object, collection)
    if equals(eo_object, collection):
        #print "Circular reference detected: %s %s" %(eo_object, collection)
        return True

    for collection in supercollection_getter(collection):
        if detect_circular_reference(eo_object, collection, supercollection_getter, equals):
            return True

    return False


def collect_eo_metadata(qs, insert=None, exclude=None, bbox=False):
    """ Helper function to collect EO metadata from all EOObjects in a queryset, 
    plus additionals from a list and exclude others from a different list. If 
    bbox is `True` then the returned polygon will only be a minimal bounding box
    of the collected footprints.
    """

    values = qs.exclude(
        pk__in=[eo_object.pk for eo_object in exclude or ()]
    ).aggregate(
        begin_time=Min("begin_time"), end_time=Max("end_time"),
        footprint=Union("footprint")
    )

    begin_time, end_time, footprint = (
        values["begin_time"], values["end_time"], values["footprint"]
    )

    # workaround for Django 1.4 bug: aggregate times are strings
    if isinstance(begin_time, basestring):
        begin_time = parse_datetime(begin_time)

    if isinstance(end_time, basestring):
        end_time = parse_datetime(end_time)

    if begin_time and is_naive(begin_time):
        begin_time = make_aware(begin_time, get_current_timezone())
    if end_time and is_naive(end_time):
        end_time = make_aware(end_time, get_current_timezone())

    for eo_object in insert or ():
        if begin_time is None:
            begin_time = eo_object.begin_time
        elif eo_object.begin_time is not None:
            begin_time = min(begin_time, eo_object.begin_time)

        if end_time is None:
            end_time = eo_object.end_time
        elif eo_object.end_time is not None:
            end_time = max(end_time, eo_object.end_time)

        if footprint is None:
            footprint = eo_object.footprint
        elif eo_object.footprint is not None:
            footprint = footprint.union(eo_object.footprint)

    if not isinstance(footprint, MultiPolygon) and footprint is not None:
        footprint = MultiPolygon(footprint)

    if bbox and footprint is not None:
        footprint = MultiPolygon(Polygon.from_bbox(footprint.extent))

    return begin_time, end_time, footprint


def is_same_grid(coverages, epsilon=1e-10):
    """ Function to determine if the given coverages share the same base grid.
        Returns a boolean value, whether or not the coverages share a common 
        grid.
    """

    if len(coverages) < 2:
        raise ValueError("Not enough coverages given.")

    first = coverages[0]
    first_ext = first.extent
    first_res = first.resolution
    first_srid = first.srid
    first_proj = first.projection

    for other in coverages[1:]:
        other_ext = other.extent
        other_res = other.resolution

        # check projection/srid
        if first_srid != other.srid or first_proj != other.projection:
            return False

        # check dimensions
        if len(first_res) != len(other_res):
            return False

        # check offset vectors
        for a, b in zip(first_res, other_res):
            if abs(a - b) > epsilon:
                return False

        # check base grids
        diff_origins = tuple(map(operator.sub, first_ext[:2], other_ext[:2]))

        v = tuple(map(operator.div, diff_origins, other_res))

        if (abs(v[0] - round(v[0])) > epsilon 
            or abs(v[1] - round(v[1])) > epsilon):
            return False

    return True
