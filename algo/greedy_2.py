import copy
import math
from algo.util.output import Output
from algo.util.sp import SP_Solver
from docplex.mp.model import Model


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


class Greedy_2(SP_Solver):
    def __init__(self, input, time_limit=0):
        SP_Solver.__init__(self, input)
        self.time_limit = time_limit

    def solve(self):
        # Auxiliar Variables
        nb_nodes = len(self.nodes)
        r_nodes = range(nb_nodes)
        nb_apps = len(self.apps)
        r_apps = range(nb_apps)

        place = {(a, h): 0
                 for a in r_apps
                 for h in r_nodes}
        distribution = {(a, b, h): 0
                        for a in r_apps
                        for b in r_nodes
                        for h in r_nodes}

        s_apps = sorted(r_apps, key=lambda a: self.apps[a][DEADLINE])
        current_capacity = copy.deepcopy(self.nodes)
        for app_index in s_apps:
            result = self._solve_app(app_index, current_capacity)
            for h in r_nodes:
                place[app_index, h] = result[0][h]
                for b in r_nodes:
                    distribution[app_index, b, h] = result[1][b, h]
            self._update_nodes_capacity(place, distribution, current_capacity)

        # return self.local_search(place, distribution)
        return place, distribution

    def _solve_app(self, app_index, nodes):
        # Auxiliar Variables
        nb_nodes = len(nodes)
        r_nodes = range(nb_nodes)

        requests = [int(math.ceil(self.users[app_index][b] * self.apps[app_index][REQUEST_RATE]))
                    for b in r_nodes]
        max_load = sum(requests)

        cpu_k1 = self.demand[app_index][CPU][K1]
        cpu_k2 = self.demand[app_index][CPU][K2]
        work_size = self.apps[app_index][WORK_SIZE]
        deadline = self.apps[app_index][DEADLINE]
        net_delay = self.net_delay[app_index]

        mdl = Model(name='ServicePlacement')

        # Decision Variables
        dvar_place = mdl.binary_var_list(nb_nodes, name="I")
        dvar_flow_exists = mdl.binary_var_matrix(nb_nodes, nb_nodes, name="F")
        dvar_distribution = mdl.integer_var_matrix(nb_nodes, nb_nodes, lb=0, name="a")
        dvar_e = mdl.continuous_var(lb=0, ub=E_MAX, name="e")
        dvar_load_f = mdl.integer_var_matrix(nb_nodes, nb_nodes, lb=0, name="lf")
        dvar_load_e = mdl.continuous_var_list(nb_nodes, lb=0.0, name="le")

        # Decision Expresions
        dexpr_load = {h: mdl.sum(dvar_distribution[b, h] for b in r_nodes)
                      for h in r_nodes}

        # Constraints
        # Number of Instances
        mdl.add_constraint(mdl.sum(dvar_place[h] for h in r_nodes) >= 1)
        mdl.add_constraint(mdl.sum(dvar_place[h] for h in r_nodes)
                           <= self.apps[app_index][MAX_INSTANCES])
        # Request Flow Existance
        mdl.add_constraints(dvar_flow_exists[b, h]
                            <= dvar_place[h] * requests[b]
                            for b in r_nodes
                            for h in r_nodes)
        # Request Distribution Conservation
        mdl.add_constraints(mdl.sum(dvar_distribution[b, h] for h in r_nodes)
                            == requests[b]
                            for b in r_nodes)
        # Request Distribution Existance
        mdl.add_constraints(dvar_distribution[b, h]
                            <= dvar_flow_exists[b, h] * requests[b]
                            for b in r_nodes
                            for h in r_nodes)
        mdl.add_constraints(dvar_distribution[b, h]
                            >= dvar_flow_exists[b, h]
                            for b in r_nodes
                            for h in r_nodes)
        # Node Capacity
        mdl.add_constraints(dexpr_load[h] * self.demand[app_index][r][K1]
                            + dvar_place[h] * self.demand[app_index][r][K2]
                            <= nodes[h][r]
                            for h in r_nodes
                            for r in self.resources)
        # Queue Stability
        mdl.add_constraints(dexpr_load[h]
                            * (cpu_k1 - work_size)
                            + dvar_place[h] * cpu_k2
                            >= dvar_place[h] * QUEUE_MIN_DIFF
                            for h in r_nodes)
        # Deadline
        mdl.add_constraints(dvar_load_f[b, h] * net_delay[b][h] * (cpu_k1 - work_size)
                            + dvar_flow_exists[b, h] * (cpu_k2 * net_delay[b][h] + work_size)
                            - dexpr_load[h] * deadline * (cpu_k1 - work_size)
                            - cpu_k2 * deadline
                            - dvar_load_e[h] * (cpu_k1 - work_size)
                            - dvar_e * cpu_k2 <= 0
                            for b in r_nodes
                            for h in r_nodes)

        # Deadline - Linearization of Quadratic Term 1
        mdl.add_constraints(dvar_load_f[b, h]
                            >= max_load * (dvar_flow_exists[b, h] - 1)
                            + dexpr_load[h]
                            for b in r_nodes
                            for h in r_nodes)
        mdl.add_constraints(dvar_load_f[b, h]
                            <= dvar_flow_exists[b, h] * max_load
                            for b in r_nodes
                            for h in r_nodes)
        mdl.add_constraints(dvar_load_f[b, h] <= dexpr_load[h]
                            for b in r_nodes
                            for h in r_nodes)
        # Deadline - Linearization of Quadratic Term 2
        mdl.add_constraints(dvar_load_e[h]
                            >= dvar_e * max_load
                            + E_MAX * (dexpr_load[h] - max_load)
                            for h in r_nodes)
        mdl.add_constraints(dvar_load_e[h] <= dvar_e * max_load
                            for h in r_nodes)
        mdl.add_constraints(dvar_load_e[h] <= dexpr_load[h] * E_MAX
                            for h in r_nodes)

        # for b in range(nb_nodes - 2):
        #     for h in range(nb_nodes - 2):
        #         if net_delay[b][h] > deadline:
        #             mdl.add_constraint(dvar_distribution[b, h] == 0)

        # Objective
        mdl.minimize(dvar_e)

        # mdl.float_precision = 3
        # mdl.print_information()

        if self.time_limit > 0:
            mdl.context.cplex_parameters.timelimit = self.time_limit

        cloud = nb_nodes - 1
        objective_value = INF
        place = {h: 0 if h != cloud else 1
                 for h in r_nodes}
        distribution = {(b, h): 0 if h != cloud else requests[b]
                        for b in r_nodes
                        for h in r_nodes}

        # Solving
        if mdl.solve():
            objective_value = mdl.objective_value
            for h in r_nodes:
                place[h] = int(dvar_place[h].solution_value)
                for b in r_nodes:
                    distribution[b, h] = int(dvar_distribution[b, h].solution_value)

        return place, distribution, objective_value

    def _update_nodes_capacity(self, place, distribution, result):
        nb_nodes = len(self.nodes)
        r_nodes = range(nb_nodes)
        nb_apps = len(self.apps)
        r_apps = range(nb_apps)

        for h in r_nodes:
            requests = [sum([distribution[a, b, h] for b in r_nodes])
                        for a in r_apps]
            for r in self.resources:
                demands = [place[a, h] * (self.demand[a][r][K1] * requests[a] + self.demand[a][r][K2])
                           for a in r_apps]
                result[h][r] = self.nodes[h][r] - sum(demands)
        return result


def solve_sp(input, time_limit=600):
    solver = Greedy_2(input, time_limit)
    result = solver.solve()
    return Output(input).set_solution(*result)
