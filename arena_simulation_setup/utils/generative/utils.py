import io
import itertools
import os
import attrs
import shapely
import yaml

import PIL.Image
import PIL.ImageDraw

import arena_simulation_setup.world


Point = tuple[float, float]
Line = tuple[Point, Point]
Polygon = list[Point]


@attrs.define
class GeneratedWorld:
    rooms: list[Polygon]
    doors: list[Polygon]
    width: float
    height: float
    resolution: float

    def to_zones_yaml(self) -> str:
        return yaml.safe_dump([
            {'polygon': [list(point) for point in room]}
            for room
            in self.rooms
        ])

    def to_walls(self, pad: float = 0, connect: tuple[float, float] | None = None) -> list[Line]:
        doors = shapely.make_valid(shapely.MultiPolygon([shapely.Polygon(door) for door in self.doors]))

        all_walls: list[Line] = []
        for room in self.rooms:
            walls = shapely.LineString(shapely.Polygon(room).exterior.coords)
            reduced = walls.difference(doors)

            if isinstance(reduced, shapely.LineString):
                reduced = shapely.MultiLineString([reduced])

            if isinstance(reduced, shapely.MultiLineString):
                for geom in reduced.geoms:
                    pts = list(geom.coords)
                    for i in range(1, len(pts)):
                        start = pts[i - 1]
                        end = pts[i]
                        all_walls.append(
                            (
                                (start[0], start[1]),
                                (end[0], end[1])
                            )
                        )

        if connect is not None:
            all_pts = [shapely.Point(pt) for wall in all_walls for pt in wall]
            for pt_a, pt_b in itertools.combinations(all_pts, 2):
                dist = pt_a.distance(pt_b)
                if dist > connect[0] and dist < connect[1]:
                    # todo check if wall already exists
                    start = pt_a.coords[0]
                    end = pt_b.coords[0]
                    all_walls.append(
                        (
                            (start[0], start[1]),
                            (end[0], end[1])
                        )
                    )

        all_walls.extend([
            ((-pad, -pad), (-pad, self.height + pad)),
            ((-pad, -pad), (self.width + pad, -pad)),
            ((self.width + pad, -pad), (self.width + pad, self.height + pad)),
            ((-pad, self.height + pad), (self.width + pad, self.height + pad))
        ])

        return all_walls

    def to_walls_yaml(self, walls: list[Line]) -> str:
        return yaml.safe_dump({
            'walls': [
                [list(start), list(end)]
                for start, end
                in walls
            ]
        })

    def to_map_yaml(self, origin: tuple[float, float, float] = (0, 0, 0)) -> str:
        return yaml.safe_dump({
            'free_thresh': 0.196,
            'image': 'map.png',
            'negate': 0,
            'occupied_thresh': 0.65,
            'origin': list(origin),
            'resolution': self.resolution,
        })

    def to_map_png(self, pad: int) -> bytes:
        img = PIL.Image.new(
            'RGB',
            (2 * pad + int(self.width / self.resolution), 2 * pad + int(self.height / self.resolution)),
            color='black'
        )

        scaling_factor = 1 / self.resolution

        def tf(shape):
            shape = shapely.affinity.scale(shape, scaling_factor, -scaling_factor, origin=(0, 0))
            shape = shapely.affinity.translate(shape, 0, self.height * scaling_factor)
            shape = shapely.affinity.translate(shape, pad, pad)
            return shape

        draw = PIL.ImageDraw.Draw(img)
        for room in self.rooms:
            poly = tf(shapely.Polygon(room))
            draw.polygon(list(poly.exterior.coords), fill='white', outline='black')

        for door in self.doors:
            poly = tf(shapely.Polygon(door))
            draw.polygon(list(poly.exterior.coords), fill='white')

        # draw padding
        draw.polygon([[0, 0], [img.width, 0], [img.width, pad], [0, pad]], fill='black')
        draw.polygon([[0, 0], [pad, 0], [pad, img.height], [0, img.height]], fill='black')
        draw.polygon([[img.width - pad, 0], [img.width, 0], [img.width, img.height], [img.width - pad, img.height]], fill='black')
        draw.polygon([[0, img.height - pad], [pad, img.height - pad], [pad, img.height], [0, img.height]], fill='black')

        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        return img_bytes.getvalue()

    def save_to(self, world_name: str, pad: int = 5):
        world = arena_simulation_setup.world.World(world_name)
        os.makedirs(world.map.path, exist_ok=True)

        with open(world.map.zones, 'w') as f:
            f.write(self.to_zones_yaml())
        with open(world.map.walls, 'w') as f:
            f.write(self.to_walls_yaml(self.to_walls(pad * self.resolution)))
        with open(world.map.map_yaml, 'w') as f:
            f.write(
                self.to_map_yaml((
                    pad * self.resolution,
                    pad * self.resolution,
                    0
                ))
            )
        with open(os.path.join(world.map.path, 'map.png'), 'wb') as f:
            f.write(self.to_map_png(pad))

        os.makedirs(world.scenario.base_dir(), exist_ok=True)
        with open(world.scenario('default.json').path, 'w') as f:
            f.write('{}')
