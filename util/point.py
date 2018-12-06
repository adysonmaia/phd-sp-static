import math

DEFAULT_HEX_SIZE = 1


class Point2D:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def to_hex(self, hex_size=DEFAULT_HEX_SIZE):
        # https://www.redblobgames.com/grids/hexagons/#pixel-to-hex
        q = (0.58 * self.x - 0.34 * self.y) / float(hex_size)
        r = 0.67 * self.y / float(hex_size)
        return HexPoint(q, r, hex_size).round()


class Point3D:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def to_hex(self, hex_size=DEFAULT_HEX_SIZE):
        return HexPoint(self.x, self.z, hex_size)


class HexPoint:
    def __init__(self, q, r, size=DEFAULT_HEX_SIZE):
        self.q = q
        self.r = r
        self.size = size

    def get_neighbors(self):
        # https://www.redblobgames.com/grids/hexagons/#neighbors-axial
        directions = [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)]
        neighbors = [HexPoint(self.q + d[0], self.r + d[1], self.size)
                     for d in directions]
        return neighbors

    def to_pixel(self):
        x = self.size * (math.sqrt(3) * self.q + math.sqrt(3)/2.0 * self.r)
        y = self.size * (3/2.0 * self.r)
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

        self.q = int(rz)
        self.r = int(rz)
        return self

    def get_distance(self, point):
        p1 = self.to_cube()
        p2 = point.to_cube()

        return (abs(p1.x - p2.x) + abs(p1.y - p2.y) + abs(p1.z - p2.z)) / 2.0


def gen_hex_map(nb_points, hex_size=DEFAULT_HEX_SIZE):
    # https://www.redblobgames.com/grids/hexagons/#range
    delta_sqrt = math.sqrt(9 + 12*(nb_points - 1))
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


def gen_rect_map(rows, columns, hex_size=DEFAULT_HEX_SIZE):
    points = [HexPoint(c - math.floor(r / 2.0), r, hex_size)
              for r in range(rows)
              for c in range(columns)]
    return points
