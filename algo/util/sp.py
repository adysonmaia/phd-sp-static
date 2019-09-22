from algo.util.metric import Metric


class SP_Solver():
    def __init__(self, input):
        self.input = input
        self.nodes = input.nodes
        self.apps = input.apps
        self.resources = input.resources
        self.metric = Metric(input)

    def get_cloud_index(self):
        return self.input.get_cloud_index()

    def get_cloud_node(self):
        return self.input.get_cloud_node()

    def get_core_index(self):
        return self.input.get_core_index()

    def get_core_node(self):
        return self.input.get_cloud_node()

    def get_net_delay(self, app_index, node_1_index, node_2_index):
        app = self.apps[app_index]
        node_1 = self.nodes[node_1_index]
        node_2 = self.nodes[node_2_index]
        return app.get_net_delay(node_1, node_2)

    def get_nb_users(self, app_index, node_index):
        return self.apps[app_index].get_nb_users(self.nodes[node_index])

    def get_nb_requests(self, app_index, node_index):
        return self.apps[app_index].get_nb_requests(self.nodes[node_index])

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
        cloud = self.get_cloud_index()

        for a in r_apps:
            app = self.apps[a]
            instances = [h for h in r_nodes if place[a, h] > 0]
            if len(instances) <= app.max_instances:
                continue

            if not place[a, cloud]:
                place[a, cloud] = 1
                instances.append(cloud)

            def node_load(h):
                return sum([load[a, b, h] for b in r_nodes])

            instances.sort(key=node_load, reverse=True)

            while len(instances) > app.max_instances:
                h = instances.pop()
                if h == cloud:
                    instances.insert(0, cloud)
                    continue
                place[a, h] = 0
                for b in r_nodes:
                    load[a, b, cloud] += load[a, b, h]
                    load[a, b, h] = 0

        return place, load
