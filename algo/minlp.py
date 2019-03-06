import math
from docplex.mp.model import Model
from algo import sp

# Constants
INF = float("inf")
QUEUE_MIN_DIFF = 0.00001
# E_MAX = 100000.0
E_MAX = 1000.0
K1 = 0
K2 = 1
CPU = "CPU"
DEADLINE = "deadline"
MAX_INSTANCES = "max_instances"
REQUEST_RATE = "request_rate"
WORK_SIZE = "work_size"


class MINLP(sp.Decoder):
    def __init__(self, input, time_limit=0):

        sp.Decoder.__init__(self, input)
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
        dvar_place = mdl.binary_var_matrix(nb_apps, nb_nodes, name="I")
        dvar_flow_exists = mdl.binary_var_cube(nb_apps, nb_nodes, nb_nodes,
                                               name="F")
        dvar_distribution = mdl.integer_var_cube(nb_apps, nb_nodes, nb_nodes,
                                                 lb=0, name="a")
        dvar_e = mdl.continuous_var(lb=0, ub=E_MAX, name="e")
        dvar_load_f = mdl.integer_var_cube(nb_apps, nb_nodes, nb_nodes,
                                           lb=0, name="lf")
        dvar_load_e = mdl.continuous_var_matrix(nb_apps, nb_nodes,
                                                lb=0.0, name="le")

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
        # Request Flow Existance
        mdl.add_constraints(dvar_flow_exists[a, b, h]
                            <= dvar_place[a, h] * requests[a][b]
                            for a in r_apps
                            for b in r_nodes
                            for h in r_nodes)
        # Request Distribution Conservation
        mdl.add_constraints(mdl.sum(dvar_distribution[a, b, h] for h in r_nodes)
                            == requests[a][b]
                            for a in r_apps
                            for b in r_nodes)
        # Request Distribution Existance
        mdl.add_constraints(dvar_distribution[a, b, h]
                            <= dvar_flow_exists[a, b, h] * requests[a][b]
                            for a in r_apps
                            for b in r_nodes
                            for h in r_nodes)
        mdl.add_constraints(dvar_distribution[a, b, h]
                            >= dvar_flow_exists[a, b, h]
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
        mdl.add_constraints(dvar_load_f[a, b, h] * net_delay[a][b][h] * (cpu_k1[a] - work_size[a])
                            + dvar_flow_exists[a, b, h] * (cpu_k2[a] * net_delay[a][b][h] + work_size[a])
                            - dexpr_load[a, h] * deadline[a] * (cpu_k1[a] - work_size[a])
                            - cpu_k2[a] * deadline[a]
                            - dvar_load_e[a, h] * (cpu_k1[a] - work_size[a])
                            - dvar_e * cpu_k2[a] <= 0
                            for a in r_apps
                            for b in r_nodes
                            for h in r_nodes)

        # mdl.add_constraints(dvar_load_f[a, b, h] * self.net_delay[a][b][h] * (self.demand[a][CPU][K1] - self.apps[a][WORK_SIZE])
        #                     + dvar_flow_exists[a, b, h] * (self.demand[a][CPU][K2] * self.net_delay[a][b][h] + self.apps[a][WORK_SIZE])
        #                     - dexpr_load[a, h] * self.apps[a][DEADLINE] * (self.demand[a][CPU][K1] - self.apps[a][WORK_SIZE])
        #                     - self.demand[a][CPU][K2] * self.apps[a][DEADLINE]
        #                     - dvar_load_e[a, h] * (self.demand[a][CPU][K1] - self.apps[a][WORK_SIZE])
        #                     - dvar_e * self.demand[a][CPU][K2] <= 0
        #                     for a in r_apps
        #                     for b in r_nodes
        #                     for h in r_nodes)

        # Deadline - Linearization of Quadratic Term 1
        mdl.add_constraints(dvar_load_f[a, b, h]
                            >= max_load[a] * (dvar_flow_exists[a, b, h] - 1)
                            + dexpr_load[a, h]
                            for a in r_apps
                            for b in r_nodes
                            for h in r_nodes)
        mdl.add_constraints(dvar_load_f[a, b, h]
                            <= dvar_flow_exists[a, b, h] * max_load[a]
                            for a in r_apps
                            for b in r_nodes
                            for h in r_nodes)
        mdl.add_constraints(dvar_load_f[a, b, h] <= dexpr_load[a, h]
                            for a in r_apps
                            for b in r_nodes
                            for h in r_nodes)
        # Deadline - Linearization of Quadratic Term 2
        mdl.add_constraints(dvar_load_e[a, h]
                            >= dvar_e * max_load[a]
                            + E_MAX * (dexpr_load[a, h] - max_load[a])
                            for a in r_apps
                            for h in r_nodes)
        mdl.add_constraints(dvar_load_e[a, h] <= dvar_e * max_load[a]
                            for a in r_apps
                            for h in r_nodes)
        mdl.add_constraints(dvar_load_e[a, h] <= dexpr_load[a, h] * E_MAX
                            for a in r_apps
                            for h in r_nodes)

        # for a in r_apps:
        #     for b in range(nb_nodes - 2):
        #         for h in range(nb_nodes - 2):
        #             if self.net_delay[a][b][h] > self.apps[a][DEADLINE]:
        #                 mdl.add_constraint(dvar_distribution[a, b, h] == 0)

        # for a in r_apps:
        #     for h in range(nb_nodes - 2):
        #         if self.users[a][h] == 0:
        #             mdl.add_constraint(dvar_place[a, h] == 0)
        #             for b in range(nb_nodes - 2):
        #                 mdl.add_constraint(dvar_distribution[a, b, h] == 0)
        #                 mdl.add_constraint(dvar_flow_exists[a, b, h] == 0)

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
    solver = MINLP(input, time_limit)
    result = list(solver.solve())

    e_relaxed = result.pop(0)
    e_original = solver.calc_qos_violation(*result)
    place = solver.get_places(*result)
    distribution = solver.get_distributions(*result)

    return e_relaxed, place, distribution, e_original
