import math

INF = float("inf")
POOL_SIZE = 0
K1 = 0
K2 = 1
CPU = "CPU"
DEADLINE = "deadline"
MAX_INSTANCES = "max_instances"
REQUEST_RATE = "request_rate"
WORK_SIZE = "work_size"


class Decoder():
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

    def fitness(self, coding):
        data_decoded = self.decode(coding)
        return self.calc_qos_violation(*data_decoded)

    def decode(self, coding):
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

        return (place, load)

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
