import math
import random
from sklearn import datasets

DEFAULT_HEX_SIZE = 1
DEFAULT_NB_BLOBS = 4
# DEFAULT_NB_BLOBS = 1


class Point:
    def __init__(self):
        pass

    def get_distance(self, point):
        return 0.0


class Point2D(Point):
    def __init__(self, x, y):
        Point.__init__(self)
        self.x = x
        self.y = y

    def get_distance(self, point):
        if isinstance(point, HexPoint):
            point = point.to_pixel()

        return math.sqrt((self.x - point.x) ** 2 + (self.y - point.y) ** 2)

    def to_hex(self, hex_size=DEFAULT_HEX_SIZE):
        # https://www.redblobgames.com/grids/hexagons/#pixel-to-hex
        q = (0.58 * self.x - 0.34 * self.y) / float(hex_size)
        r = 0.67 * self.y / float(hex_size)
        return HexPoint(q, r, hex_size).round()

    def to_pixel(self):
        return self


class Point3D(Point):
    def __init__(self, x, y, z):
        Point.__init__(self)
        self.x = x
        self.y = y
        self.z = z

    def get_distance(self, point):
        return math.sqrt((self.x - point.x) ** 2
                         + (self.y - point.y) ** 2
                         + (self.z - point.z) ** 2)

    def to_hex(self, hex_size=DEFAULT_HEX_SIZE):
        return HexPoint(self.x, self.z, hex_size)


class HexPoint(Point):
    def __init__(self, q, r, size=DEFAULT_HEX_SIZE):
        Point.__init__(self)
        self.q = q
        self.r = r
        self.size = size

    def __eq__(self, other):
        if not isinstance(other, HexPoint) or other is None:
            return False
        return (self.q == other.q and self.r == other.r and self.size == other.size)

    def get_neighbors(self):
        # https://www.redblobgames.com/grids/hexagons/#neighbors-axial
        directions = [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)]
        neighbors = [HexPoint(self.q + d[0], self.r + d[1], self.size)
                     for d in directions]
        return neighbors

    def is_neighbor(self, point):
        return self.get_distance(point) == 1

    def to_pixel(self):
        x = self.size * (1.73 * self.q + 0.86 * self.r)
        y = self.size * (1.5 * self.r)
        return Point2D(x, y)

    def to_cube(self):
        return Point3D(self.q, -self.q-self.r, self.r)

    def round(self):
        point = self.to_cube()
        rx = round(point.x)
        rz = round(point.z)
        ry = round(point.y)

        x_diff = abs(rx - point.x)
        y_diff = abs(ry - point.y)
        z_diff = abs(rz - point.z)

        if x_diff > y_diff and x_diff > z_diff:
            rx = -ry-rz
        elif y_diff > z_diff:
            ry = -rx-rz
        else:
            rz = -rx-ry

        self.q = int(rx)
        self.r = int(rz)
        return self

    def get_distance(self, point):
        if isinstance(point, Point2D):
            point = point.to_hex(self.size)

        p1 = self.to_cube()
        p2 = point.to_cube()

        return (abs(p1.x - p2.x) + abs(p1.y - p2.y) + abs(p1.z - p2.z)) / 2.0


def gen_hex_map(nb_points, hex_size=DEFAULT_HEX_SIZE):
    # https://www.redblobgames.com/grids/hexagons/#range
    delta_sqrt = math.sqrt(9 + 12 * (nb_points - 1))
    if delta_sqrt > 3:
        size = (delta_sqrt - 3) / 6.0
    else:
        size = 0
    size = int(math.ceil(size))

    points = []
    count = 0
    for q in range(-size, size + 1):
        for r in range(max(-size, -size-q), min(size, size-q) + 1):
            if count < nb_points:
                points.append(HexPoint(q, r, hex_size))
                count += 1
    return points


def gen_rect_map(nb_points, hex_size=DEFAULT_HEX_SIZE):
    columns = int(math.floor(math.sqrt(nb_points)))
    rows = columns
    remaining = nb_points - rows * columns

    points = [HexPoint(c - math.floor(r / 2.0), r, hex_size)
              for r in range(rows)
              for c in range(columns)]

    # add the remaining points that are not in the square
    for i in range(remaining):
        r = int(math.floor(i / float(columns)))
        c = i - r * columns
        r += rows

        point = HexPoint(c - math.floor(r / 2.0), r, hex_size)
        points.append(point)

    return points


def calc_hex_bound_box(nb_points, hex_size=DEFAULT_HEX_SIZE):
    delta_sqrt = math.sqrt(9 + 12 * (nb_points - 1))
    if delta_sqrt > 3:
        distance = (delta_sqrt - 3) / 6.0
    else:
        distance = 0
    distance = int(math.ceil(distance))

    w = 1.73 * distance * hex_size + 0.86 * hex_size
    h = 1.5 * distance * hex_size + hex_size

    min_p = Point2D(-w, -h)
    max_p = Point2D(w, h)

    return [min_p, max_p]


def calc_rect_bound_box(nb_points, hex_size=DEFAULT_HEX_SIZE):
    min_p = Point2D(-0.86 * hex_size, -hex_size)

    columns = int(math.floor(math.sqrt(nb_points)))
    rows = columns
    # add rows for the remaining points that are not in the square
    rows += int(math.floor(nb_points / float(columns) - rows))

    w = 1.73 * hex_size * columns
    h = (rows - 1) * (1.5 * hex_size) + hex_size
    max_p = Point2D(w, h)

    return [min_p, max_p]


def gen_2d_points_blob(nb_points, bound_box, nb_centers=DEFAULT_NB_BLOBS, hex_size=DEFAULT_HEX_SIZE):
    centers = 1 + random.randrange(nb_centers)
    cluster_std = [hex_size * random.uniform(0.1, 1.0) for _ in range(centers)]
    # cluster_std = 1.0
    center_box = [max(bound_box[0].x, bound_box[0].y),
                  min(bound_box[1].x, bound_box[1].y)]

    points, labels = datasets.make_blobs(n_samples=nb_points, n_features=2,
                                         cluster_std=cluster_std, centers=centers,
                                         center_box=center_box)
    return _bound_points(points, bound_box)


def gen_2d_points_uniform(nb_points, bound_box, hex_size=DEFAULT_HEX_SIZE):
    points = [[random.uniform(bound_box[0].x, bound_box[1].x),
               random.uniform(bound_box[0].y, bound_box[1].y)]
              for _ in range(nb_points)]
    return _bound_points(points, bound_box)


def gen_2d_points_circle(nb_points, bound_box):
    center_x = random.uniform(bound_box[0].x, bound_box[1].x / 2.0)
    center_y = random.uniform(bound_box[0].y, bound_box[1].y / 2.0)
    noise = random.uniform(0.0, 0.05)
    width = bound_box[1].x - bound_box[0].x
    height = bound_box[1].y - bound_box[0].y
    scale = [width * random.uniform(0.1, 1.0), height * random.uniform(0.1, 1.0)]
    factor = random.random()

    points, labels = datasets.make_circles(n_samples=nb_points, noise=noise,
                                           factor=factor)
    points = map(lambda p: [(p[0] + 1) / 2.0, (p[1] + 1) / 2.0], points)
    points = map(lambda p: [p[0] * scale[0] + center_x, p[1] * scale[1] + center_y], points)
    return _bound_points(points, bound_box)


def gen_2d_points_moon(nb_points, bound_box):
    center_x = random.uniform(bound_box[0].x, bound_box[1].x / 2.0)
    center_y = random.uniform(bound_box[0].y, bound_box[1].y / 2.0)
    noise = random.uniform(0.0, 0.05)
    width = bound_box[1].x - bound_box[0].x
    height = bound_box[1].y - bound_box[0].y
    scale = [width * random.uniform(0.1, 1.0), height * random.uniform(0.1, 1.0)]

    points, labels = datasets.make_moons(n_samples=nb_points, noise=noise)
    points = map(lambda p: [(p[0] + 1) / 3.0, (p[1] + 0.5) / 1.5], points)
    points = map(lambda p: [p[0] * scale[0] + center_x, p[1] * scale[0] + center_y], points)
    return _bound_points(points, bound_box)


def _bound_points(points, bound_box):
    def _bound(point):
        x = point[0]
        y = point[1]

        x = max(bound_box[0].x, min(bound_box[1].x, x))
        y = max(bound_box[0].y, min(bound_box[1].y, y))
        return Point2D(x, y)
    return [_bound(p) for p in points]
