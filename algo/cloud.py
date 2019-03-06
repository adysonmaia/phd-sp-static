import math
from algo.greedy import Greedy

INF = float("inf")
K1 = 0
K2 = 1
CPU = "CPU"
DEADLINE = "deadline"
MAX_INSTANCES = "max_instances"
REQUEST_RATE = "request_rate"
WORK_SIZE = "work_size"


class Cloud(Greedy):

    def __init__(self, input):
        Greedy.__init__(self, input)

    def solve(self):
        nb_nodes = len(self.nodes)
        r_nodes = range(nb_nodes)
        nb_apps = len(self.apps)
        r_apps = range(nb_apps)

        requests = [[int(math.ceil(self.users[a][b] * self.apps[a][REQUEST_RATE]))
                     for b in r_nodes]
                    for a in r_apps]

        cloud = nb_nodes - 1
        place = {(a, h): 0 if h != cloud else 1
                 for a in r_apps
                 for h in r_nodes}
        distribution = {(a, b, h): 0 if h != cloud else requests[a][b]
                        for a in r_apps
                        for b in r_nodes
                        for h in r_nodes}

        return place, distribution


def solve_sp(input):
    solver = Cloud(input)
    result = solver.solve()

    e = solver.calc_qos_violation(*result)
    place = solver.get_places(*result)
    distribution = solver.get_distributions(*result)

    return e, place, distribution
