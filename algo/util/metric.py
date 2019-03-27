INF = float("inf")


class Metric():
    def __init__(self, input):
        self.input = input
        self.nodes = input.nodes
        self.apps = input.apps
        self.resources = input.resources
        self.CPU = input.get_cpu_resource().name

    def _get_nb_users(self, app_index, node_index):
        app = self.apps[app_index]
        node = self.nodes[node_index]
        return app.get_users(node)

    def _get_process_delay(self, place, load, app_index, node_index):
        r_nodes = range(len(self.nodes))
        app = self.apps[app_index]
        work_size = app.work_size
        cpu_k1, cpu_k2 = app.get_cpu_demand()

        proc_delay = 0
        node_load = sum([load[app_index, b, node_index] for b in r_nodes])
        # TODO: what is the value in case of node_load == 0 ?
        if node_load > 0:
            proc_delay_divisor = float(node_load * (cpu_k1 - work_size) + cpu_k2)
            if proc_delay_divisor > 0.0:
                proc_delay = app.work_size / proc_delay_divisor
            else:
                proc_delay = INF

        return proc_delay

    def _get_network_delay(self, app_index, node1_index, node2_index):
        app = self.apps[app_index]
        node_1 = self.nodes[node1_index]
        node_2 = self.nodes[node2_index]
        return app.get_net_delay(node_1, node_2)

    def _get_resource_demand(self, place, load, node_index, resource):
        r_apps = range(len(self.apps))
        r_nodes = range(len(self.nodes))

        demand = 0
        for a in r_apps:
            k1, k2 = self.apps[a].get_demand(resource)
            node_load = int(sum([load[a, b, node_index] for b in r_nodes]))
            demand += float(place[a, node_index] * (node_load * k1 + k2))

        return demand

    def get_max_deadline_violation(self, place, load):
        r_apps = range(len(self.apps))
        r_nodes = range(len(self.nodes))

        max_e = 0.0
        for a in r_apps:
            app = self.apps[a]
            for h in r_nodes:
                if not place[a, h]:
                    continue
                proc_delay = self._get_process_delay(place, load, a, h)
                for b in r_nodes:
                    if load[a, b, h] <= 0:
                        continue
                    net_delay = self._get_network_delay(a, b, h)
                    delay = net_delay + proc_delay
                    violation = delay - app.deadline
                    if violation > 0.0 and violation > max_e:
                        max_e = violation
        return max_e

    def get_qos_violation(self, place, load):
        return self.get_max_deadline_violation(place, load)

    def get_avg_deadline_violation(self, place, load):
        r_apps = range(len(self.apps))
        r_nodes = range(len(self.nodes))

        avg_e = 0.0
        count = 0
        for a in r_apps:
            app = self.apps[a]
            for h in r_nodes:
                if not place[a, h]:
                    continue
                proc_delay = self._get_process_delay(place, load, a, h)
                for b in r_nodes:
                    if load[a, b, h] <= 0:
                        continue
                    net_delay = self._get_network_delay(a, b, h)
                    delay = net_delay + proc_delay
                    violation = delay - app.deadline
                    if violation > 0.0:
                        avg_e += load[a, b, h] * violation
                        count += load[a, b, h]
        if count > 0:
            avg_e = avg_e / float(count)
        return avg_e

    def get_deadline_satisfaction(self, place, load):
        r_apps = range(len(self.apps))
        r_nodes = range(len(self.nodes))

        rate = 0.0
        count = 0
        for a in r_apps:
            app = self.apps[a]
            for h in r_nodes:
                if not place[a, h]:
                    continue
                proc_delay = self._get_process_delay(place, load, a, h)
                for b in r_nodes:
                    if load[a, b, h] <= 0:
                        continue
                    net_delay = self._get_network_delay(a, b, h)
                    delay = net_delay + proc_delay
                    if delay <= app.deadline:
                        rate += load[a, b, h]
                    count += load[a, b, h]
        if count > 0:
            rate = rate / float(count)
        return rate

    def get_avg_response_time(self, place, load):
        r_apps = range(len(self.apps))
        r_nodes = range(len(self.nodes))

        avg_rt = 0.0
        count = 0
        for a in r_apps:
            for h in r_nodes:
                if not place[a, h]:
                    continue
                proc_delay = self._get_process_delay(place, load, a, h)
                for b in r_nodes:
                    if load[a, b, h] <= 0:
                        continue
                    net_delay = self._get_network_delay(a, b, h)
                    delay = net_delay + proc_delay
                    avg_rt += load[a, b, h] * delay
                    count += load[a, b, h]
        if count > 0:
            avg_rt = avg_rt / float(count)
        return avg_rt

    def get_avg_resource_usage(self, place, load):
        r_nodes = range(len(self.nodes))

        avg = 0.0
        count = 0
        for h in r_nodes:
            node = self.nodes[h]
            for r in self.resources:
                demand = self._get_resource_demand(place, load, h, r)
                capacity = float(node.get_capacity(r))
                if capacity > 0.0:
                    avg += demand / capacity
                    count += 1

        if count > 0:
            avg = avg / count
        return avg

    def get_max_resource_usage(self, place, load):
        r_nodes = range(len(self.nodes))

        max_usage = 0
        for h in r_nodes:
            node = self.nodes[h]
            for r in self.resources:
                demand = self._get_resource_demand(place, load, h, r)
                capacity = float(node.get_capacity(r))
                if capacity > 0.0:
                    usage = demand / capacity
                    if usage > max_usage:
                        max_usage = usage

        return max_usage

    def get_overall_power_comsumption(self, place, load):
        r_nodes = range(len(self.nodes))

        total_power = 0.0
        for h in r_nodes:
            node = self.nodes[h]
            p_min, p_max = node.get_power_consumption()
            capacity = float(node.get_cpu_capacity())
            demand = self._get_resource_demand(place, load, h, self.CPU)
            power = 0.0
            if demand > 0.0 and capacity > 0.0:
                power = p_min + (p_max - p_min) * (demand / capacity)
            total_power += power

        return total_power

    def get_power_comsumption(self, place, load):
        return self.get_overall_power_comsumption(place, load)

    def get_overall_cost(self, place, load):
        r_apps = range(len(self.apps))
        r_nodes = range(len(self.nodes))

        total_cost = 0.0
        for a in r_apps:
            app = self.apps[a]

            for h in r_nodes:
                node = self.nodes[h]
                if not place[a, h]:
                    continue

                for r in self.resources:
                    k1, k2 = app.get_demand(r)
                    cost_1, cost_2 = node.get_cost(r)

                    node_load = int(sum([load[a, b, h] for b in r_nodes]))
                    demand = k1 * node_load + k2
                    total_cost += cost_1 * demand + cost_2

        return total_cost

    def get_cost(self, place, load):
        return self.get_overall_cost(place, load)
