import math
import algo.util.constant as const
from algo.greedy import Greedy
from algo.util.output import Output

REQUEST_RATE = const.REQUEST_RATE


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
        load = {(a, b, h): 0 if h != cloud else requests[a][b]
                for a in r_apps
                for b in r_nodes
                for h in r_nodes}

        return place, load


def solve_sp(input):
    solver = Cloud(input)
    result = solver.solve()
    return Output(input).set_solution(*result)
