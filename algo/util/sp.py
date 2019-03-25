import math
import algo.util.constant as const
from algo.util.metric import Metric

K1 = const.K1
K2 = const.K2
MAX_INSTANCES = const.MAX_INSTANCES
REQUEST_RATE = const.REQUEST_RATE
WORK_SIZE = const.WORK_SIZE


class SP_Solver():
    def __init__(self, input):
        self.input = input
        self.nodes = input.nodes
        self.apps = input.apps
        self.users = input.users
        self.resources = input.resources
        self.net_delay = input.net_delay
        self.demand = input.apps_demand
        self.metric = Metric(input)

    def solve(self):
        r_nodes = range(len(self.nodes))
        r_apps = range(len(self.apps))

        place = {(a, h): 0
                 for a in r_apps
                 for h in r_nodes}
        load = {(a, b, h): 0
                for a in r_apps
                for b in r_nodes
                for h in r_nodes}
        return self.local_search(place, load)

    def local_search(self, place, load):
        r_apps = range(len(self.apps))
        nb_nodes = len(self.nodes)
        r_nodes = range(nb_nodes)
        cloud = nb_nodes - 1

        for a in r_apps:
            app = self.apps[a]
            instances = [h for h in r_nodes if place[a, h] > 0]
            if len(instances) <= app[MAX_INSTANCES]:
                continue

            if not place[a, cloud]:
                place[a, cloud] = 1
                instances.append(cloud)

            def node_load(h): return sum([load[a, b, h] for b in r_nodes])
            instances.sort(key=node_load, reverse=True)

            while len(instances) > app[MAX_INSTANCES]:
                h = instances.pop()
                if h == cloud:
                    instances.insert(0, cloud)
                    continue
                place[a, h] = 0
                for b in r_nodes:
                    load[a, b, cloud] += load[a, b, h]
                    load[a, b, h] = 0

        return place, load

    def is_valid_solution(self, place, load):
        r_apps = range(len(self.apps))
        r_nodes = range(len(self.nodes))

        for a in r_apps:
            app = self.apps[a]
            users = self.users[a]

            nb_instances = sum([place[a, h] for h in r_nodes])
            if nb_instances > app[MAX_INSTANCES] or nb_instances == 0:
                return False
            for b in r_nodes:
                requests = int(math.ceil(users[b] * app[REQUEST_RATE]))
                total_load = int(sum([load[a, b, h] for h in r_nodes]))
                if requests != total_load:
                    return False
                for h in r_nodes:
                    if load[a, b, h] > 0 and not place[a, h]:
                        return False

        for h in r_nodes:
            for r in self.resources:
                demand = 0
                for a in r_apps:
                    k1 = self.demand[a][r][K1]
                    k2 = self.demand[a][r][K2]
                    node_load = int(sum([load[a, b, h] for b in r_nodes]))
                    demand += float(place[a, h] * (node_load * k1 + k2))
                    if node_load > 0 and not place[a, h]:
                        return False
                if demand > self.nodes[h][r]:
                    return False

        return True
