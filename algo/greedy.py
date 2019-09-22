from algo.util.sp import SP_Solver
from algo.util.output import Output

INF = float("inf")


class Greedy(SP_Solver):
    def __init__(self, input):
        SP_Solver.__init__(self, input)

    def solve(self):
        r_nodes = list(range(len(self.nodes)))
        r_apps = list(range(len(self.apps)))

        nb_requests = {(a, b): self.get_nb_requests(a, b)
                       for b in r_nodes
                       for a in r_apps}

        place = {(a, h): 0
                 for a in r_apps
                 for h in r_nodes}
        load = {(a, b, h): 0
                for a in r_apps
                for b in r_nodes
                for h in r_nodes}

        resource_used = {(h, r): 0 for h in r_nodes for r in self.resources}
        app_load = {(a, h): 0
                    for h in r_nodes
                    for a in r_apps}

        r_apps.sort(key=lambda i: self.apps[i].deadline)
        for a in r_apps:
            selected_nodes = self._select_nodes(a)

            # r_nodes.sort(key=lambda b: nb_requests[a, b], reverse=True)
            for b in r_nodes:
                for _ in range(nb_requests[a, b]):
                    # selected_nodes.sort(key=lambda h: self.get_net_delay(a, b, h))
                    selected_nodes.sort(key=lambda h: self._node_priority(a, b, h, app_load))

                    for h in selected_nodes:
                        fit = True
                        resources = {}
                        for r in self.resources:
                            k1, k2 = self.apps[a].get_demand(r)
                            value = resource_used[h, r] + k1 + (1 - place[a, h]) * k2
                            capacity = self.nodes[h].get_capacity(r)
                            resources[r] = value
                            fit = fit and (value <= capacity)

                        if fit:
                            load[a, b, h] += 1
                            app_load[a, h] += 1
                            place[a, h] = 1
                            for r in self.resources:
                                resource_used[h, r] = resources[r]
                            break

        return self.local_search(place, load)

    def _select_nodes(self, a):
        app = self.apps[a]
        nb_nodes = len(self.nodes)
        r_nodes = range(nb_nodes)
        nb_instances = min(nb_nodes, app.max_instances)

        def avg_net_delay(h):
            avg_delay = 0.0
            count = 0
            for b in r_nodes:
                if self.get_nb_users(a, b) > 0:
                    avg_delay += self.get_net_delay(a, b, h)
                    count += 1
            if count > 0:
                avg_delay = avg_delay / float(count)
            return avg_delay

        # def avg_net_delay(h):
        #     avg_delay = 0.0
        #     for b in r_nodes:
        #         avg_delay += self.get_net_delay(a, b, h)
        #     return avg_delay / float(nb_nodes)

        nodes_delay = [avg_net_delay(h) for h in r_nodes]
        sorted_nodes = sorted(r_nodes, key=lambda h: nodes_delay[h])
        selected_nodes = sorted_nodes[:nb_instances]

        cloud = self.get_cloud_index()
        if cloud not in selected_nodes:
            selected_nodes.append(cloud)

        return selected_nodes

    def _node_priority(self, a, b, h, app_load):
        app = self.apps[a]
        work_size = app.work_size
        cpu_k1, cpu_k2 = app.get_cpu_demand()

        proc_delay = 0.0
        net_delay = self.get_net_delay(a, b, h)

        # new request + current load
        node_load = 1 + app_load[a, h]
        proc_delay_divisor = float(node_load * (cpu_k1 - work_size) + cpu_k2)
        if proc_delay_divisor > 0.0:
            proc_delay = work_size / proc_delay_divisor
        else:
            proc_delay = INF

        return net_delay + proc_delay


def solve(input):
    solver = Greedy(input)
    result = solver.solve()
    return Output(input).set_solution(*result)
