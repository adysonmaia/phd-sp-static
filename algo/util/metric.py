import algo.util.constant as const

INF = const.INF
K1 = const.K1
K2 = const.K2
CPU = const.CPU
DEADLINE = const.DEADLINE
WORK_SIZE = const.WORK_SIZE


class Metric():
    def __init__(self, input):
        self.input = input
        self.nodes = input.nodes
        self.apps = input.apps
        self.users = input.users
        self.resources = input.resources
        self.net_delay = input.net_delay
        self.demand = input.apps_demand

    def _get_response_time(self, place, load):
        r_apps = range(len(self.apps))
        r_nodes = range(len(self.nodes))

        rt = {(a, b, h): -1 for a in r_apps for b in r_nodes for h in r_nodes}
        for a in r_apps:
            app = self.apps[a]
            work_size = app[WORK_SIZE]
            cpu_k1 = self.demand[a][CPU][K1]
            cpu_k2 = self.demand[a][CPU][K2]

            instances = list(filter(lambda h: place[a, h] > 0, r_nodes))
            bs = list(filter(lambda b: self.users[a][b] > 0, r_nodes))

            for h in instances:
                node_load = sum([load[a, b, h] for b in bs])
                if node_load == 0.0:
                    continue
                proc_delay_divisor = float(node_load * (cpu_k1 - work_size) + cpu_k2)
                proc_delay = INF
                if proc_delay_divisor > 0.0:
                    proc_delay = app[WORK_SIZE] / proc_delay_divisor
                for b in bs:
                    if load[a, b, h] > 0:
                        rt[a, b, h] = self.net_delay[a][b][h] + proc_delay

        return rt

    def _get_deadline_violation(self, place, load):
        r_apps = range(len(self.apps))
        r_nodes = range(len(self.nodes))

        rt = self._get_response_time(place, load)

        e = {(a, b, h): rt[a, b, h] - self.app[a][DEADLINE]
             if rt[a, b, h] > self.app[a][DEADLINE] else 0
             for a in r_apps
             for b in r_nodes
             for h in r_nodes}

        return e

    def _get_resource_usage(self, place, load):
        r_apps = range(len(self.apps))
        r_nodes = range(len(self.nodes))

        ru = {(h, r): 0 for h in r_nodes for r in self.resources}

        for h in r_nodes:
            demand = sum([load[a, b, h] * place[a, h]
                          for a in r_apps
                          for b in r_nodes])

            for r in self.resources:
                capacity = float(self.nodes[h][r])
                if capacity > 0.0:
                    ru[h, r] = demand / capacity

        return ru

    def get_max_deadline_violation(self, place, load):
        e = self._get_deadline_violation(place, load)
        return max(e.values())

    def get_qos_violation(self, place, load):
        return self.get_max_deadline_violation(place, load)

    def get_avg_deadline_violation(self, place, load):
        e = self._get_deadline_violation(place, load)

        count = 0
        avg = 0
        for key, value in e.items():
            a, b, h = key
            if value <= 0.0:
                continue
            weight = load[a, b, h]
            avg += weight * value
            count += weight

        if count > 0:
            avg = avg / float(count)
        return avg

    def get_avg_response_time(self, place, load):
        rt = self._get_response_time(place, load)

        count = 0
        avg = 0
        for key, value in rt.items():
            a, b, h = key
            if value < 0.0:
                continue
            weight = load[a, b, h]
            avg += weight * value
            count += weight

        if count > 0:
            avg = avg / float(count)
        return avg

    def get_avg_resource_usage(self, place, load):
        r_nodes = range(len(self.nodes))
        ru = self._get_resource_usage(place, load)

        def node_usage(h):
            return max([ru[h, r] for r in self.resources])

        usage = [node_usage(h) for h in r_nodes]
        avg = 0.0
        count = float(len(usage))
        if count > 0:
            avg = sum(usage) / count

        return avg

    def get_max_resource_usage(self, place, load):
        ru = self._get_resource_usage(place, load)
        return max(ru.values())
