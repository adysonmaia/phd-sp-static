INF = float("inf")
POOL_SIZE = 0
K1 = 0
K2 = 1
CPU = "CPU"
DEADLINE = "deadline"
MAX_INSTANCES = "max_instances"
REQUEST_RATE = "request_rate"
WORK_SIZE = "work_size"


class Metric():
    def __init__(self, input):
        self.input = input
        self.nodes = input.nodes
        self.apps = input.apps
        self.users = input.users
        self.resources = input.resources
        self.net_delay = input.net_delay
        self.demand = input.apps_demand

    def get_qos_violation(self, place, load):
        r_apps = range(len(self.apps))
        r_nodes = range(len(self.nodes))

        e = 0.0
        for a in r_apps:
            app = self.apps[a]
            work_size = app[WORK_SIZE]
            deadline = app[DEADLINE]
            cpu_k1 = self.demand[a][CPU][K1]
            cpu_k2 = self.demand[a][CPU][K2]

            instances = list(filter(lambda h: place[a, h] > 0, r_nodes))
            bs = list(filter(lambda b: self.users[a][b] > 0, r_nodes))

            max_delay = 0.0
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
                        delay = self.net_delay[a][b][h] + proc_delay
                        if delay > max_delay:
                            max_delay = delay

            violation = max_delay - deadline
            if violation > 0.0 and violation > e:
                e = violation
        return e

    def get_avg_qos_violation(self, place, load):
        r_apps = range(len(self.apps))
        r_nodes = range(len(self.nodes))

        e = 0.0
        count = 0
        for a in r_apps:
            app = self.apps[a]
            work_size = app[WORK_SIZE]
            deadline = app[DEADLINE]
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
                        delay = self.net_delay[a][b][h] + proc_delay
                        if delay > deadline:
                            e += delay - deadline
                            count += 1
        if count > 0:
            return e / float(count)
        else:
            return 0.0

    def get_resource_wastage(self, place, load):
        r_apps = range(len(self.apps))
        r_nodes = range(len(self.nodes))

        wastage = 0
        for h in r_nodes:
            for r in self.resources:
                capacity = float(self.nodes[h][r])
                if capacity == 0.0 or capacity == INF:
                    continue
                used = 0
                for a in r_apps:
                    app_load = sum([load[a, b, h] for b in r_nodes])
                    r_k1 = self.demand[a][r][K1]
                    r_k2 = self.demand[a][r][K2]
                    used += place[a, h] * (r_k1 * app_load + r_k2)
                wastage += (capacity - used) / capacity
        return wastage

    def get_active_nodes(self, place, load):
        r_apps = range(len(self.apps))
        r_nodes = range(len(self.nodes))

        count = 0
        for h in r_nodes:
            instances = sum([place[a, h] for a in r_apps])
            if instances > 0:
                count += 1
        return count

    def get_cpu_consumption(self, place, load):
        r_apps = range(len(self.apps))
        r_nodes = range(len(self.nodes))

        consumption = 0
        for h in r_nodes:
            capacity = float(self.nodes[h][CPU])
            if capacity == 0.0 or capacity == INF:
                continue
            used = 0
            for a in r_apps:
                app_load = sum([load[a, b, h] for b in r_nodes])
                cpu_k1 = self.demand[a][CPU][K1]
                cpu_k2 = self.demand[a][CPU][K2]
                used += place[a, h] * (cpu_k1 * app_load + cpu_k2)
            consumption += used / capacity
        return consumption
