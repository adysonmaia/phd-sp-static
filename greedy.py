import math

INF = float("inf")
K1 = 0
K2 = 1
CPU = "CPU"
DEADLINE = "deadline"
MAX_INSTANCES = "max_instances"
REQUEST_RATE = "request_rate"
WORK_SIZE = "work_size"


class Greedy:

    def __init__(self,
                 nodes,
                 apps,
                 users,
                 resources,
                 net_delay,
                 demand):

        self.nodes = nodes
        self.apps = apps
        self.users = users
        self.resources = resources
        self.net_delay = net_delay
        self.demand = demand

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

        r_apps.sort(key=lambda a: self.apps[a][DEADLINE])
        for a in r_apps:
            app = self.apps[a]
            bs = r_nodes[:]
            bs.sort(key=lambda b: self.users[a][b], reverse=True)
            for b in bs:
                if self.users[a][b] == 0:
                    continue

                total_requests = int(math.ceil(self.users[a][b] * app[REQUEST_RATE]))

                nodes_priority = r_nodes[:]
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

    def _decode_local_search(self, place, load):
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

    def calc_qos_violation(self, place, load):
        r_apps = range(len(self.apps))
        r_nodes = range(len(self.nodes))

        e = 0.0
        for a in r_apps:
            app = self.apps[a]
            work_size = app[WORK_SIZE]
            deadline = app[DEADLINE]
            cpu_k1 = self.demand[a][CPU][K1]
            cpu_k2 = self.demand[a][CPU][K2]

            instances = [h for h in r_nodes if place[a, h] > 0]
            bs = [b for b, nb_users in enumerate(self.users[a]) if nb_users > 0]

            max_delay = 0.0
            for h in instances:
                node_load = sum([load[a, b, h] for b in bs])
                proc_delay_divisor = float(node_load * (cpu_k1 - work_size) + cpu_k2)
                proc_delay = INF
                if proc_delay_divisor > 0.0:
                    proc_delay = app[WORK_SIZE] / proc_delay_divisor
                for b in bs:
                    if load[a, b, h] > 0:
                        delay = self.net_delay[a][b][h] + proc_delay
                        if delay > max_delay:
                            max_delay = delay

            violation = max_delay - deadline
            if violation > 0.0 and violation > e:
                e = violation
        return e

    def get_distributions(self, place, load):
        r_apps = range(len(self.apps))
        r_nodes = range(len(self.nodes))

        return {(a, b, h): place[a, h] * load[a, b, h]
                / math.ceil(self.users[a][b] * self.apps[a][REQUEST_RATE])
                for a in r_apps
                for b in r_nodes
                for h in r_nodes
                if load[a, b, h] > 0}

    def get_places(self, place, load=None):
        r_apps = range(len(self.apps))
        r_nodes = range(len(self.nodes))

        return [[h for h in r_nodes if place[a, h] > 0] for a in r_apps]


def solve_sp(nodes,
             apps,
             users,
             resources,
             net_delay,
             demand):

    g = Greedy(nodes, apps, users, resources, net_delay, demand)
    result = g.solve()

    e = g.calc_qos_violation(*result)
    place = g.get_places(*result)
    distribution = g.get_distributions(*result)

    return e, place, distribution
