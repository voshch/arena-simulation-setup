from shapely import LineString, MultiLineString
from shapely.geometry import Point, Polygon

from arena_simulation_setup.shared import Position, Wall


def line_pairs(geom: MultiLineString | LineString | Polygon):
    """
    Creates an iterator for all line segments of a MultiLineString.
    """
    if isinstance(geom, Polygon):
        yield from line_pairs(geom.exterior)
        for interior_ring in geom.interiors:
            yield from line_pairs(interior_ring)
        return

    if isinstance(geom, LineString):
        geom = MultiLineString((geom,))

    for line in geom.geoms:
        coords = list(line.coords)
        if len(coords) >= 2:
            for start, end in zip(coords[:-1], coords[1:]):
                yield Point(start), Point(end)


def to_corners(geom: Polygon) -> list[Position]:
    return [Position(x=pt[0], y=pt[1]) for pt in geom.exterior.coords]


def to_walls(geom) -> list[Wall]:
    return [
        Wall(
            start=Position(x=start.x, y=start.y),
            end=Position(x=end.x, y=end.y)
        )
        for (start, end) in line_pairs(geom)
    ]
