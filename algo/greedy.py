import math
from algo import sp

INF = float("inf")
K1 = 0
K2 = 1
CPU = "CPU"
DEADLINE = "deadline"
MAX_INSTANCES = "max_instances"
REQUEST_RATE = "request_rate"
WORK_SIZE = "work_size"


class Greedy(sp.Decoder):

    def __init__(self, input):
        sp.Decoder.__init__(self, input)

    def solve(self):
        nb_apps = len(self.apps)
        r_apps = range(nb_apps)
        nb_nodes = len(self.nodes)
        r_nodes = range(nb_nodes)

        place = {(a, h): 0
                 for h in r_nodes
                 for a in r_apps}
        load = {(a, b, h): 0
                for h in r_nodes
                for b in r_nodes
                for a in r_apps}

        capacity = {(h, r): 0 for h in r_nodes for r in self.resources}

        s_apps = sorted(r_apps, key=lambda a: self.apps[a][DEADLINE])
        for a in s_apps:
            app = self.apps[a]
            bs = sorted(r_nodes, key=lambda b: self.users[a][b], reverse=True)
            for b in bs:
                if self.users[a][b] == 0:
                    continue

                total_requests = int(math.ceil(self.users[a][b] * app[REQUEST_RATE]))

                nodes_priority = list(r_nodes)
                nodes_priority.sort(key=lambda h: self.net_delay[a][b][h])
                for h in nodes_priority:
                    requests = total_requests
                    while requests > 0 and total_requests > 0:
                        fit = True
                        resources = {}
                        for r in self.resources:
                            value = (capacity[h, r]
                                     + requests * self.demand[a][r][K1]
                                     + (1 - place[a, h]) * self.demand[a][r][K2])
                            resources[r] = value
                            fit = fit and (value <= self.nodes[h][r])

                        if fit:
                            load[a, b, h] += requests
                            place[a, h] = 1
                            total_requests -= requests
                            requests = 0
                            for r in self.resources:
                                capacity[h, r] = resources[r]
                        else:
                            requests -= 1
                    if total_requests == 0:
                        break
        return self._decode_local_search(place, load)


def solve_sp(input):

    g = Greedy(input)
    result = g.solve()

    e = g.calc_qos_violation(*result)
    place = g.get_places(*result)
    distribution = g.get_distributions(*result)

    return e, place, distribution
