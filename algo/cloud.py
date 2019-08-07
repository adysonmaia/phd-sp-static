from algo.util.sp import SP_Solver
from algo.util.output import Output


class Cloud(SP_Solver):

    def __init__(self, input):
        SP_Solver.__init__(self, input)

    def solve(self):
        r_nodes = range(len(self.nodes))
        r_apps = range(len(self.apps))

        requests = [[self.get_nb_requests(a, h)
                     for h in r_nodes]
                    for a in r_apps]

        cloud = self.get_cloud_index()
        place = {(a, h): 0 if h != cloud else 1
                 for a in r_apps
                 for h in r_nodes}
        load = {(a, b, h): 0 if h != cloud else requests[a][b]
                for a in r_apps
                for b in r_nodes
                for h in r_nodes}

        return place, load


def solve(input):
    solver = Cloud(input)
    result = solver.solve()
    return Output(input).set_solution(*result)
