import math
from algo.util.metric import Metric


class Output:
    def __init__(self, input, place=None, load=None):
        self.input = input
        self.place = place
        self.load = load
        self.metric = Metric(input)

    def set_solution(self, place, load):
        self.place = place
        self.load = load
        return self

    def get_vars(self):
        return self.place, self.load

    def get_qos_violation(self):
        return self.metric.get_qos_violation(self.place, self.load)

    def is_valid(self):
        r_apps = range(len(self.input.apps))
        r_nodes = range(len(self.input.nodes))
        place = self.place
        load = self.load
        apps = self.input.apps
        nodes = self.input.nodes
        resources = self.input.resources

        for a in r_apps:
            app = apps[a]
            nb_instances = sum([place[a, h] for h in r_nodes])
            if nb_instances > app.max_instances or nb_instances == 0:
                return False
            for b in r_nodes:
                node_b = nodes[b]
                rate = app.request_rate
                nb_users = app.get_nb_users(node_b)
                requests = int(math.ceil(nb_users * rate))
                total_load = int(sum([load[a, b, h] for h in r_nodes]))
                if requests != total_load:
                    return False
                for h in r_nodes:
                    if load[a, b, h] > 0 and not place[a, h]:
                        return False

        for h in r_nodes:
            node = nodes[h]
            for r in resources:
                demand = 0
                for a in r_apps:
                    app = apps[a]
                    k1, k2 = app.get_demand(r)
                    node_load = int(sum([load[a, b, h] for b in r_nodes]))
                    demand += float(place[a, h] * (node_load * k1 + k2))
                    if node_load > 0 and not place[a, h]:
                        return False
                if demand > node.get_capacity(r):
                    return False

        return True
