INF = float("inf")


class Metric():
    def __init__(self, input):
        self.input = input
        self.nodes = input.nodes
        self.apps = input.apps
        self.resources = input.resources
        self.CPU = input.get_cpu_resource().name
        self.filter = MetricFilter(input)

    def _get_nb_users(self, app_index, node_index):
        app = self.apps[app_index]
        node = self.nodes[node_index]
        return app.get_nb_users(node)

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

    def _get_resource_demand(self, place, load, node_index, resource_name):
        r_apps = range(len(self.apps))
        r_nodes = range(len(self.nodes))

        demand = 0
        for a in r_apps:
            k1, k2 = self.apps[a].get_demand(resource_name)
            node_load = int(sum([load[a, b, node_index] for b in r_nodes]))
            demand += float(place[a, node_index] * (node_load * k1 + k2))

        return demand

    def get_max_deadline_violation(self, place, load):
        r_apps = self.filter.get_r_apps()
        r_nodes = self.filter.get_r_nodes()

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
        r_apps = self.filter.get_r_apps()
        r_nodes = self.filter.get_r_nodes()

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
        r_apps = self.filter.get_r_apps()
        r_nodes = self.filter.get_r_nodes()

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
        r_apps = self.filter.get_r_apps()
        r_nodes = self.filter.get_r_nodes()

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
        r_nodes = self.filter.get_r_nodes()

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
        r_nodes = self.filter.get_r_nodes()

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
        r_nodes = self.filter.get_r_nodes()

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
        r_apps = self.filter.get_r_apps()
        r_nodes = self.filter.get_r_nodes()

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

    def get_avg_availability(self, place, load):
        r_apps = self.filter.get_r_apps()
        r_nodes = self.filter.get_r_nodes()
        nb_apps = len(r_apps)

        avg = 0.0
        for a in r_apps:
            app = self.apps[a]
            availability = 1.0
            for h in r_nodes:
                node = self.nodes[h]
                if not place[a, h]:
                    continue
                availability *= (1.0 - app.availability * node.availability)
            availability = 1.0 - availability
            avg += availability

        if nb_apps > 0:
            avg = avg / nb_apps
        return avg

    def get_max_unavailability(self, place, load):
        r_apps = self.filter.get_r_apps()
        r_nodes = self.filter.get_r_nodes()

        max_failure = 0.0
        for a in r_apps:
            app = self.apps[a]
            failure = 1.0
            for h in r_nodes:
                node = self.nodes[h]
                if not place[a, h]:
                    continue
                failure *= (1.0 - app.availability * node.availability)
            if failure > max_failure:
                max_failure = failure

        return max_failure

    def get_avg_unavailability(self, place, load):
        r_apps = self.filter.get_r_apps()
        r_nodes = self.filter.get_r_nodes()
        nb_apps = len(r_apps)

        avg = 0.0
        for a in r_apps:
            app = self.apps[a]
            unavailability = 1.0
            for h in r_nodes:
                node = self.nodes[h]
                if not place[a, h]:
                    continue
                unavailability *= (1.0 - app.availability * node.availability)
            avg += unavailability

        if nb_apps > 0:
            avg = avg / nb_apps
        return avg


class MetricFilter:
    def __init__(self, input):
        self.input = input
        self.clean()

    def clean(self):
        self.app_type = None
        self.node_type = None

    def set_app_type(self, type):
        self.app_type = type
        return self

    def set_node_type(self, type):
        self.node_type = type
        return self

    def get_r_apps(self):
        apps = self.input.apps
        r_apps = range(len(apps))

        if self.app_type is not None:
            r_apps = list(filter(lambda i: apps[i].type == self.app_type, r_apps))

        return r_apps

    def get_r_nodes(self):
        nodes = self.input.nodes
        r_nodes = range(len(nodes))

        if self.node_type is not None:
            r_nodes = list(filter(lambda i: nodes[i].type == self.node_type, r_nodes))

        return r_nodes
