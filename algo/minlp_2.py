import math
from docplex.mp.model import Model
import algo.util.constant as const
from algo.util.output import Output
from algo.util.sp import SP_Solver

# Constants
INF = const.INF
K1 = const.K1
K2 = const.K2
CPU = const.CPU
REQUEST_RATE = const.REQUEST_RATE
MAX_INSTANCES = const.MAX_INSTANCES
WORK_SIZE = const.WORK_SIZE
DEADLINE = const.DEADLINE
QUEUE_MIN_DIFF = 0.00001


class MINLP_2(SP_Solver):
    def __init__(self, input, time_limit=0):
        SP_Solver.__init__(self, input)
        self.time_limit = time_limit

    def solve(self):
        # Auxiliar Variables
        nb_nodes = len(self.nodes)
        r_nodes = range(nb_nodes)
        nb_apps = len(self.apps)
        r_apps = range(nb_apps)

        requests = [[int(math.ceil(self.users[a][b] * self.apps[a][REQUEST_RATE]))
                     for b in r_nodes]
                    for a in r_apps]
        max_load = [sum(requests[a]) for a in r_apps]

        mdl = Model(name='ServicePlacement')

        # Decision Variables
        dvar_place = mdl.binary_var_matrix(nb_apps, nb_nodes, name="p")
        dvar_distribution = mdl.integer_var_cube(nb_apps, nb_nodes, nb_nodes,
                                                 lb=0, name="d")
        dvar_e = mdl.continuous_var(lb=0, name="e")
        dvar_load_d = mdl.integer_var_cube(nb_apps, nb_nodes, nb_nodes,
                                           lb=0, name="ld")

        # Decision Expresions
        dexpr_load = {(a, h): mdl.sum(dvar_distribution[a, b, h] for b in r_nodes)
                      for a in r_apps
                      for h in r_nodes}

        # Constraints
        # Number of Instances
        mdl.add_constraints(mdl.sum(dvar_place[a, h] for h in r_nodes)
                            >= 1
                            for a in r_apps)
        mdl.add_constraints(mdl.sum(dvar_place[a, h] for h in r_nodes)
                            <= self.apps[a][MAX_INSTANCES]
                            for a in r_apps)
        # Request Distribution Conservation
        mdl.add_constraints(mdl.sum(dvar_distribution[a, b, h] for h in r_nodes)
                            == requests[a][b]
                            for a in r_apps
                            for b in r_nodes)
        # Request Distribution Existance
        mdl.add_constraints(dvar_distribution[a, b, h]
                            <= dvar_place[a, h] * requests[a][b]
                            for a in r_apps
                            for b in r_nodes
                            for h in r_nodes)
        # Node Capacity
        mdl.add_constraints(mdl.sum(dexpr_load[a, h] * self.demand[a][r][K1]
                                    + dvar_place[a, h] * self.demand[a][r][K2]
                                    for a in r_apps)
                            <= self.nodes[h][r]
                            for h in r_nodes
                            for r in self.resources)
        # Queue Stability
        mdl.add_constraints(dexpr_load[a, h]
                            * (self.demand[a][CPU][K1] - self.apps[a][WORK_SIZE])
                            + dvar_place[a, h] * self.demand[a][CPU][K2]
                            >= dvar_place[a, h] * QUEUE_MIN_DIFF
                            for a in r_apps
                            for h in r_nodes)
        # Deadline
        cpu_k1 = [self.demand[a][CPU][K1] for a in r_apps]
        cpu_k2 = [self.demand[a][CPU][K2] for a in r_apps]
        work_size = [self.apps[a][WORK_SIZE] for a in r_apps]
        deadline = [self.apps[a][DEADLINE] for a in r_apps]
        net_delay = self.net_delay

        mdl.add_constraints(dvar_load_d[a, b, h] * (cpu_k1[a] - work_size[a]) * (net_delay[a][b][h] - deadline[a])
                            + dvar_distribution[a, b, h] * (work_size[a] + cpu_k2[a] * (net_delay[a][b][h] - deadline[a]))
                            <= dvar_e
                            for a in r_apps
                            for b in r_nodes
                            for h in r_nodes)

        # Deadline - Linearization of Bilinear Term 1
        mdl.add_constraints(dvar_load_d[a, b, h]
                            >= max_load[a] * dvar_distribution[a, b, h]
                            + requests[a][b] * dexpr_load[a, h]
                            - max_load[a] * requests[a][b]
                            for a in r_apps
                            for b in r_nodes
                            for h in r_nodes)
        mdl.add_constraints(dvar_load_d[a, b, h]
                            <= max_load[a] * dvar_distribution[a, b, h]
                            for a in r_apps
                            for b in r_nodes
                            for h in r_nodes)
        mdl.add_constraints(dvar_load_d[a, b, h]
                            <= requests[a][b] * dexpr_load[a, h]
                            for a in r_apps
                            for b in r_nodes
                            for h in r_nodes)

        # for a in r_apps:
        #     for b in range(nb_nodes - 2):
        #         for h in range(nb_nodes - 2):
        #             if self.net_delay[a][b][h] > self.apps[a][DEADLINE]:
        #                 mdl.add_constraint(dvar_distribution[a, b, h] == 0)

        # Objective
        mdl.minimize(dvar_e)

        # mdl.float_precision = 3
        # mdl.print_information()

        if self.time_limit > 0:
            mdl.context.cplex_parameters.timelimit = self.time_limit

        cloud = nb_nodes - 1
        objective_value = INF
        place = {(a, h): 0 if h != cloud else 1
                 for a in r_apps
                 for h in r_nodes}
        distribution = {(a, b, h): 0 if h != cloud else requests[a][b]
                        for a in r_apps
                        for b in r_nodes
                        for h in r_nodes}

        # Solving
        if mdl.solve():
            objective_value = mdl.objective_value
            for a in r_apps:
                for h in r_nodes:
                    place[a, h] = int(dvar_place[a, h].solution_value)
                    for b in r_nodes:
                        distribution[a, b, h] = int(dvar_distribution[a, b, h].solution_value)

        return objective_value, place, distribution


def solve_sp(input, time_limit=300):
    solver = MINLP_2(input, time_limit)
    result = list(solver.solve())
    output = Output(input)
    output.e_relaxed = result.pop(0)
    output.set_solution(*result)
    return output
