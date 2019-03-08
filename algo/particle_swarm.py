import math
from algo.util.output import Output
from algo.util.sp import SP_Solver
from algo.util.pso import PSO, PSO_Decoder

# Constants
X_MIN = -1.0
X_MAX = 1.0
INF = float("inf")

K1 = 0
K2 = 1
CPU = "CPU"
DEADLINE = "deadline"
MAX_INSTANCES = "max_instances"
REQUEST_RATE = "request_rate"
WORK_SIZE = "work_size"


class SP_Decoder(SP_Solver, PSO_Decoder):
    def __init__(self, input):

        SP_Solver.__init__(self, input)
        PSO_Decoder.__init__(self)

        nb_apps = len(self.apps)
        r_apps = range(nb_apps)
        nb_nodes = len(self.nodes)
        r_nodes = range(nb_nodes)

        self.requests = []
        for a in r_apps:
            for b in r_nodes:
                nb_requests = int(math.ceil(self.users[a][b] * self.apps[a][REQUEST_RATE]))
                self.requests += ([(a, b)] * nb_requests)

        self.nb_dimensions = len(self.apps) * len(self.requests)

    def stopping_criteria(self, best_coding, best_cost):
        print("best: {}".format(best_cost))
        return best_cost == 0.0

    def get_cost(self, coding):
        data_decoded = self.decode(coding)
        return self.calc_qos_violation(*data_decoded)

    def decode(self, coding):
        nb_apps = len(self.apps)
        r_apps = range(nb_apps)
        nb_nodes = len(self.nodes)
        r_nodes = range(nb_nodes)
        nb_requests = len(self.requests)
        r_requests = range(nb_requests)
        cloud = nb_nodes - 1

        place = {(a, h): 0
                 for h in r_nodes
                 for a in r_apps}
        load = {(a, b, h): 0
                for h in r_nodes
                for b in r_nodes
                for a in r_apps}

        selected_nodes = []
        for a in r_apps:
            start = a * nb_nodes
            end = start + nb_nodes + 1
            priority = coding[start:end]
            nodes = sorted(r_nodes, key=lambda v: priority[v], reverse=True)
            max_nodes = min(nb_nodes, self.apps[a][MAX_INSTANCES])
            selected_nodes.append(nodes[:max_nodes])

        capacity = {(h, r): 0 for h in r_nodes for r in self.resources}

        start = nb_apps * nb_nodes
        end = start + nb_requests + 1
        priority = coding[start:end]

        s_requests = sorted(r_requests, key=lambda v: priority[v], reverse=True)
        for req in s_requests:
            a, b = self.requests[req]
            nodes = list(selected_nodes[a])
            nodes.sort(key=lambda h: self._node_priority(coding, a, b, h, place, load))
            nodes.append(cloud)
            for h in nodes:
                fit = True
                resources = {}
                for r in self.resources:
                    value = (capacity[h, r]
                             + self.demand[a][r][K1]
                             + (1 - place[a, h]) * self.demand[a][r][K2])
                    resources[r] = value
                    fit = fit and (value <= self.nodes[h][r])

                if fit:
                    load[a, b, h] += 1
                    place[a, h] = 1
                    for r in self.resources:
                        capacity[h, r] = resources[r]
                    break

        return self.local_search(place, load)

    def _node_priority(self, coding, a, b, h, place, load):
        nb_nodes = len(self.nodes)
        r_nodes = range(nb_nodes)

        cloud_delay = self.net_delay[a][b][nb_nodes - 1]
        node_delay = self.net_delay[a][b][h]
        delay = (cloud_delay - node_delay) / cloud_delay

        max_load = sum([load[a, b, v] for v in r_nodes])
        max_load = float(max_load) if max_load > 0 else 1.0

        return delay + load[a, b, h] / max_load


def solve_sp(input, nb_particles=100, max_iteration=100):
    decoder = SP_Decoder(input)
    pso = PSO(decoder, nb_particles, max_iteration)
    position, cost = pso.solve()

    result = decoder.decode(position)
    return Output(input).set_solution(*result)
