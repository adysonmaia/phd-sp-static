import sys
import signal
import random
import math
import time
import numpy as np
import tkinter as tk
from util import generator, point
from algo.util.kmedoids import KMedoids


NODE_SIZE = 1
BS_SIZE = NODE_SIZE
USER_SIZE = 0.1
APP_SIZE = 0.2
APP_SHIFT = 0.12
REQ_FLOW_ADJUST = BS_SIZE / 2
TOP_BS_SPACE = 4 * BS_SIZE
SCALE_ADJUST = 1
TRANSLATION_ADJUST = 5
# colors in http://www.science.smith.edu/dftwiki/index.php/Color_Charts_for_TKinter
DEFAULT_NODE_COLOR = "gray90"
CLUSTER_COLORS = ["red", "green4", "blue", "purple", "orange", "yellow2", "brown"]


def rgb_to_hex_color(rgb):
    """Convert a RGB color into HTML hex format
    Args:
        rgb (tuple): RGB color (r,g,b)
    Returns:
        color: string in HTML hex format
    """
    return '#%02x%02x%02x' % rgb


class Map:
    def __init__(self, master, width, height):
        self.width = width
        self.height = height
        self.canvas = tk.Canvas(master, width=width, height=height)
        self.scale = (1.0, 1.0)
        self.translation = (0.0, 0.0)
        self.app_color = {}

    def _transform_points(self, points):
        """Scale and translate a list of points
        Args:
            points (list): [x1, y1, x2, y2, ...]
        Returns:
            points: transformed points
        """
        transformed = []
        for i in range(len(points)):
            p = points[i]
            t_p = p * self.scale[i % 2] + self.translation[i % 2]
            transformed.append(t_p)
        return transformed

    def draw(self, input, clusters, app_id):
        self.canvas.delete(tk.ALL)

        self._init_draw(input, clusters, app_id)

        self._draw_nodes()
        self._draw_users()

        self.canvas.pack()

    def _init_draw(self, input, clusters, app_id):
        """initialize the data before drawing the map
        """
        self.input = input
        self.clusters = clusters
        self.selected_app = input.apps[app_id]

        if not input.bs_bound_box:
            nb_bs = len(input.get_bs_nodes())
            input.bs_bound_box = point.calc_rect_bound_box(nb_bs)

        min_p, max_p = input.bs_bound_box
        min_p.y -= TOP_BS_SPACE
        x_diff = float(max_p.x - min_p.x)
        y_diff = float(max_p.y - min_p.y)

        # set the core and cloud position in the canvas
        core_node = input.get_core_node()
        x = min_p.x + x_diff / 3.0
        y = min_p.y + TOP_BS_SPACE / 3.0
        core_node.point = point.Point2D(x, y)

        cloud_node = input.get_cloud_node()
        x = min_p.x + 2 * (x_diff / 3.0)
        y = min_p.y + TOP_BS_SPACE / 3.0
        cloud_node.point = point.Point2D(x, y)

        # set linear transformations parameters to adjust the map size
        scale_x = self.width / x_diff - SCALE_ADJUST
        scale_y = self.height / y_diff - SCALE_ADJUST
        self.scale = (scale_x, scale_y)

        trans_x = -1.0 * scale_x * min_p.x + TRANSLATION_ADJUST
        trans_y = -1.0 * scale_y * min_p.y + TRANSLATION_ADJUST
        self.translation = (trans_x, trans_y)

        # set the color for each node
        app_clusters = clusters[app_id]
        nb_clusters = len(app_clusters)
        self.cluster_color = [None] * nb_clusters
        for i in range(nb_clusters):
            if i < len(CLUSTER_COLORS):
                color = CLUSTER_COLORS[i]
            else:
                color = tuple(random.randrange(256) for _ in range(3))
                color = rgb_to_hex_color(color)
            self.cluster_color[i] = color

        self.node_color = [DEFAULT_NODE_COLOR for _ in input.nodes]
        for node in input.nodes:
            for c_id, c in enumerate(app_clusters):
                if node.id in c:
                    self.node_color[node.id] = self.cluster_color[c_id]

    def _draw_nodes(self):
        """Draw all nodes
        """
        for node in self.input.nodes:
            self._draw_node(node)

    def _draw_users(self):
        """Draw users of selected application
        """
        for user in self.selected_app.users:
            self._draw_user(user)

    def _draw_node(self, node):
        """Draw a node
        """
        if node.is_base_station():
            self._draw_bs_node(node)
        else:
            self._draw_not_bs_node(node)

    def _draw_bs_node(self, node):
        """Draw a Base Station node as a Hexagonal
        """
        center = node.point.to_pixel()
        size = BS_SIZE
        points = []
        for i in range(6):
            x = center.x + size * math.cos(math.radians(60 * i - 30))
            y = center.y + size * math.sin(math.radians(60 * i - 30))
            points.append(x)
            points.append(y)
        points = self._transform_points(points)
        color = self.node_color[node.id]
        self.canvas.create_polygon(points, fill=color, outline="gray")

    def _draw_not_bs_node(self, node):
        center = node.point.to_pixel()
        radius = NODE_SIZE
        points = [center.x - radius, center.y - radius,
                  center.x + radius, center.y + radius]
        points = self._transform_points(points)
        self.canvas.create_oval(points, fill="white", outline="gray")

        text_p = [center.x, center.y + 1.25 * radius]
        text_p = self._transform_points(text_p)
        self.canvas.create_text(text_p, text=node.type, fill="black")

    def _draw_user(self, user):
        """Draw a User as a circle
        """
        center = user.point.to_pixel()
        radius = USER_SIZE
        points = [center.x - radius, center.y - radius,
                  center.x + radius, center.y + radius]
        points = self._transform_points(points)
        color = self.node_color[user.node_id]
        self.canvas.create_oval(points, fill=color, outline="gray")


def draw_map(input, clusters, app_id=0):
    root = tk.Tk()
    root.title("Service Placement")

    def exit_gracefully(signum, frame):
        root.quit()
        root.destroy()

    signal.signal(signal.SIGINT, exit_gracefully)
    signal.signal(signal.SIGTERM, exit_gracefully)

    map = Map(root, 800, 700)
    map.draw(input, clusters, app_id)
    root.mainloop()

    return root


def create_clusters(input, nb_clusters):
    r_nodes = range(len(input.nodes))

    clusters = [None for _ in input.apps]
    for app in input.apps:
        distances = [[app.get_net_delay(i, j)
                      for j in input.nodes]
                     for i in input.nodes]

        kmedoids = KMedoids()
        features = list(filter(lambda h: app.get_nb_users(input.nodes[h]) > 0, r_nodes))
        nb_clusters = min(len(features), app.max_instances, nb_clusters)
        print(app.id, app.max_instances, len(features), nb_clusters)

        clusters[app.id] = kmedoids.fit(nb_clusters, features, distances)

    return clusters


def create_clusters_score(input):
    r_nodes = range(len(input.nodes))
    kmedoids = KMedoids()

    clusters = [None for _ in input.apps]
    for app in input.apps:
        distances = [[app.get_net_delay(i, j)
                      for j in input.nodes]
                     for i in input.nodes]
        features = list(filter(lambda h: app.get_nb_users(input.nodes[h]) > 0, r_nodes))

        max_score = -1
        max_nb_clusters = min(len(features), app.max_instances)
        for nb_clusters in range(1, max_nb_clusters + 1):
            app_clusters = kmedoids.fit(nb_clusters, features, distances)
            score = kmedoids.silhouette_score(app_clusters, distances)
            if score > max_score:
                max_score = score
                clusters[app.id] = app_clusters
        print(app.id, app.max_instances, len(features), len(clusters[app.id]))

    return clusters


def main(args=[]):
    # good seeds: 3, 9, 12, 13, 17, 21, 26, 29
    seed = 13
    random.seed(seed)
    np.random.seed(seed)

    nb_nodes = 102
    nb_apps = 3
    nb_users = 1000
    nb_clusters = 4
    if len(args) >= 3:
        nb_nodes, nb_users, nb_clusters = map(lambda i: int(i), args)

    input_filename = "input.json"
    input = generator.InputGenerator().gen_from_file(
        input_filename, nb_nodes, nb_apps, nb_users
    )

    # clusters = create_clusters(input, nb_clusters)
    clusters = create_clusters_score(input)

    app_id = 0
    draw_map(input, clusters, app_id)


if __name__ == '__main__':
    main(sys.argv[1:])
