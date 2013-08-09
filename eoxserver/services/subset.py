import logging

from django.utils.dateparse import parse_datetime, parse_date
from django.contrib.gis.geos import Polygon

from eoxserver.resources.coverages import crss
from eoxserver.services.exceptions import (
    InvalidAxisLabelException, InvalidSubsettingException
)


__all__ = ["Subsets", "Trim", "Slice"]

logger = logging.getLogger(__name__)


class Subsets(list):
    def __init__(self, iterable, allowed_types=None):
        self.allowed_types = allowed_types if allowed_types is not None else (Trim, Slice)
        # Do a manual insertion here to assure integrity
        for subset in iterable:
            self.append(subset)

    # List API
    
    def extend(self, iterable):
        for subset in iterable:
            self._check_subset(subset)
            super(Subsets, self).append(subset)


    def append(self, subset):
        self._check_subset(subset)
        super(Subsets, self).append(subset)


    def insert(self, i, subset):
        self._check_subset(subset)
        super(Subsets, self).insert(i, subset)

    # Subset related stuff

    @property
    def has_x(self):
        return any(map(lambda s: s.is_x, self))

    @property
    def has_y(self):
        return any(map(lambda s: s.is_y, self))

    @property
    def has_t(self):
        return any(map(lambda s: s.is_temporal, self))

    @property
    def xy_srid(self):
        xy_subsets = filter(lambda s: s.is_x or s.is_y, self)
        if not len(xy_subsets):
            return None

        all_crss = set(
            map(lambda s: s.crs, xy_subsets)
        )

        if len(all_crss) != 1:
            raise "all X/Y crss must be the same"

        xy_crs = iter(all_crss).next()
        if xy_crs is not None:
            return crss.parseEPSGCode(xy_crs, (crss.fromURL, crss.fromURN))
        return None


    def filter(self, queryset, containment="overlaps"):
        if not len(self):
            return queryset

        qs = queryset

        bbox = [None, None, None, None]
        srid = self.xy_srid
        if srid is None:
            srid = 4326
        max_extent = crss.crs_bounds(srid)
        tolerance = crss.crs_tolerance(srid)

        for subset in self:
            if isinstance(subset, Slice):
                is_slice = True
                value = subset.value
            elif isinstance(subset, Trim):
                is_slice = False
                low = subset.low
                high = subset.high

            if subset.is_temporal:
                if is_slice:
                    qs = qs.filter(
                        begin_time__lte=value,
                        end_time__gte=value
                    )
                elif low is None and high is not None:
                    qs = qs.filter(
                        begin_time__lte=high
                    )
                elif low is not None and high is None:
                    qs = qs.filter(
                        end_time__gte=low
                    )
                else:
                    qs = qs.exclude(
                        begin_time__gt=high
                    ).exclude(
                        end_time__lt=low
                    )

            else:
                if is_slice:
                    if subset.is_x:
                        line = Line(
                            (value, max_extent[1]),
                            (value, max_extent[3])
                        )
                    else:
                        line = Line(
                            (max_extent[0], value),
                            (max_extent[2], value)
                        )
                    line.srid = srid
                    if srid != 4326:
                        line.transform(4326)
                    qs = qs.filter(footprint__intersects=line)

                else:
                    if subset.is_x:
                        bbox[0] = subset.low
                        bbox[2] = subset.high
                    else:
                        bbox[1] = subset.low
                        bbox[3] = subset.high


        if bbox != [None, None, None, None]:
            bbox = map(
                lambda v: v[0] if v[0] is not None else v[1], zip(bbox, max_extent)
            )

            bbox[0] -= tolerance; bbox[1] -= tolerance
            bbox[2] += tolerance; bbox[3] += tolerance

            logger.debug("Applying BBox %s with containment '%s'." % (bbox, containment))

            poly = Polygon.from_bbox(bbox)
            poly.srid = srid

            if srid != 4326:
                poly.transform(4326)
            if containment == "overlaps":
                qs = qs.filter(footprint__intersects=poly)
            elif containment == "contains":
                qs = qs.filter(footprint__within=poly)

        return qs


        def matches(self, eo_object, containment="overlaps"):
            return True
            # TODO: implement


    def _check_subset(self, subset):
        if not isinstance(subset, Subset):
            raise ValueError("Supplied argument is not a subset.")

        if not isinstance(subset, self.allowed_types):
            raise InvalidSubsettingException(
                "Supplied subset is not allowed."
            )

        if self.has_x and subset.is_x:
            raise InvalidSubsettingException(
                "Multiple subsets for X-axis given."
            )

        if self.has_y and subset.is_y:
            raise InvalidSubsettingException(
                "Multiple subsets for Y-axis given."
            )

        if self.has_t and subset.is_temporal:
            raise InvalidSubsettingException(
                "Multiple subsets for time-axis given."
            )



class Subset(object):
    def __init__(self, axis, crs=None):
        axis = axis.lower()
        if axis not in all_axes:
            raise InvalidAxisLabelException(
                "Axis '%s' is not valid or supported." % axis
            )
        self.axis = axis
        self.crs = crs

    @property
    def is_temporal(self):
        return self.axis in temporal_axes

    @property
    def is_x(self):
        return self.axis in x_axes

    @property
    def is_y(self):
        return self.axis in y_axes


class Slice(Subset):
    def __init__(self, axis, value, crs=None):
        super(Slice, self).__init__(axis, crs)
        self.value = parse_quoted_temporal(value) if self.is_temporal else float(value)


class Trim(Subset):
    def __init__(self, axis, low=None, high=None, crs=None):
        super(Trim, self).__init__(axis, crs)
        dt = parse_quoted_temporal if self.is_temporal else float_or_star
        self.low = dt(low)
        self.high = dt(high)



temporal_axes = ("t", "time", "phenomenontime")
x_axes = ("x", "lon", "long")
y_axes = ("y", "lat")
all_axes = temporal_axes + x_axes + y_axes


def float_or_star(value):
    """
    """

    if value == "*":
        return None
    return float(value)


def parse_quoted_temporal(value):
    """ 
    """

    if value == "*":
        return None

    if not value[0] == '"' and not value[-1] == '"':
        raise ValueError("Temporal value needs to be quoted with double quotes.")

    value = value[1:-1]

    for parser in (parse_datetime, parse_date):
        temporal = parser(value)
        if temporal:
            return temporal

    raise ValueError("Could not parse '%s' to a temporal value" % value)
