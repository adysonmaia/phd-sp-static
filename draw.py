import sys
import signal
import random
import math
import time
import numpy as np
import tkinter as tk
from util import generator, point
import algo


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
APP_COLORS = ["red", "green4", "blue", "purple", "orange", "yellow2", "brown"]


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

    def draw(self, input, output=None):
        self.canvas.delete(tk.ALL)

        self._init_draw(input, output)

        self._draw_nodes()
        self._draw_users()
        self._draw_placement()
        # self._draw_distribution()

        self.canvas.pack()

    def _init_draw(self, input, output):
        """initialize the data before drawing the map
        """
        self.input = input
        self.output = output

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

        # set the color for each application
        self.app_color = {}
        for i in range(len(input.apps)):
            app = input.apps[i]
            if i < len(APP_COLORS):
                color = APP_COLORS[i]
            else:
                color = tuple(random.randrange(256) for _ in range(3))
                color = rgb_to_hex_color(color)
            self.app_color[app.id] = color

    def _draw_nodes(self):
        """Draw all nodes
        """
        for node in self.input.nodes:
            self._draw_node(node)

    def _draw_users(self):
        """Draw all nodes
        """
        for app in self.input.apps:
            print("{} {} : nb users = {} - color = {}".format(
                app.id, app.type, len(app.users), self.app_color[app.id])
            )
            for user in app.users:
                self._draw_user(user)

    def _draw_placement(self):
        """Draw placement decision
        """
        if not self.output:
            return

        for app in self.input.apps:
            count = 0
            for node in self.input.nodes:
                if self.output.place[app.id, node.id]:
                    count += 1
            print("{} {} : nb instances = {} - color = {}".format(
                app.id, app.type, count, self.app_color[app.id])
            )

        for node in self.input.nodes:
            shift = 0
            for app in self.input.apps:
                if self.output.place[app.id, node.id]:
                    self._draw_app_place(app, node, shift)
                    shift += APP_SHIFT

    def _draw_distribution(self):
        """Draw load distribution decision
        """
        if not self.output:
            return
        for app in self.input.apps:
            for source in self.input.nodes:
                for target in self.input.nodes:
                    if self.output.load[app.id, source.id, target.id] > 0:
                        self._draw_req_flow(app, source, target)

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
        self.canvas.create_polygon(points, fill="white", outline="gray60")
        # self.canvas.create_polygon(points, fill="gray95", outline="gray")

    def _draw_not_bs_node(self, node):
        center = node.point.to_pixel()
        radius = NODE_SIZE
        points = [center.x - radius, center.y - radius,
                  center.x + radius, center.y + radius]
        points = self._transform_points(points)
        self.canvas.create_oval(points, fill="white", outline="gray60")

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
        color = self.app_color[user.app_id]
        self.canvas.create_oval(points, fill=color, outline="gray")

    def _draw_app_place(self, app, node, shift=0):
        """Draw an App Instance as a rectangle
        """
        center = node.point.to_pixel()
        size = APP_SIZE
        points = [center.x - size + shift, center.y - size + shift,
                  center.x + size + shift, center.y + size + shift]
        points = self._transform_points(points)
        color = self.app_color[app.id]
        self.canvas.create_rectangle(points, fill=color, outline="black")

    def _draw_req_flow(self, app, source_node, target_node):
        """Draw a Request Flow of an application
        """
        percentage = (app.id + 1) / float(len(self.input.apps))
        color = self.app_color[app.id]
        if source_node != target_node:
            p1 = source_node.point.to_pixel()
            p2 = target_node.point.to_pixel()
            shift = REQ_FLOW_ADJUST * percentage
            points = [p1.x + shift, p1.y, p2.x + shift, p2.y]
            points = self._transform_points(points)
            color = self.app_color[app.id]
            self.canvas.create_line(points, fill=color, arrow=tk.LAST)
        else:
            center = source_node.point.to_pixel()
            radius = REQ_FLOW_ADJUST * percentage
            points = [center.x - radius, center.y - radius,
                      center.x + radius, center.y + radius]
            points = self._transform_points(points)
            self.canvas.create_oval(points, outline=color)


def draw_map(input, output):
    root = tk.Tk()
    root.title("Service Placement")

    def exit_gracefully(signum, frame):
        root.quit()
        root.destroy()

    signal.signal(signal.SIGINT, exit_gracefully)
    signal.signal(signal.SIGTERM, exit_gracefully)

    map = Map(root, 800, 700)
    map.draw(input, output)
    root.mainloop()

    return root


def print_output(solver, output):
    if not output:
        return
    metric = output.metric
    metrics = [("max e", metric.get_qos_violation),
               ("cost", metric.get_cost),
               ("avg avail", metric.get_avg_availability)]

    print(solver.__name__)
    print("\t {:15} : {} s".format("time", output.elapsed_time))
    print("\t {:15} : {}".format("valid", output.is_valid()))

    for m_title, m_func in metrics:
        value = m_func(*output.get_vars())
        print("\t {:15} : {}".format(m_title, value))


def main(args=[]):
    # good seeds: 3, 9, 12, 13, 17, 21, 26, 29
    # good seeds x2: 3, 13, 26
    seed = 26
    random.seed(seed)
    np.random.seed(seed)

    nb_nodes = 102
    nb_apps = 3
    nb_users = 10000
    if len(args) >= 3:
        nb_nodes, nb_apps, nb_users = map(lambda i: int(i), args)

    input_filename = "input.json"
    input = generator.InputGenerator().gen_from_file(
        input_filename, nb_nodes, nb_apps, nb_users
    )

    # solver = algo.genetic
    # solver = algo.genetic_cluster
    # solver = algo.cluster
    solver = algo.genetic_mo
    # solver = algo.greedy
    # solver = algo.cloud
    # solver = algo.bootstrap

    output = None
    start_time = time.time()
    output = solver.solve(input)
    output.elapsed_time = round(time.time() - start_time, 4)

    print_output(solver, output)
    draw_map(input, output)


if __name__ == '__main__':
    main(sys.argv[1:])
