import numpy as np
from docplex.mp.model import Model
from algo.util.sp import SP_Solver
from algo.util.output import Output

INF = float("inf")
E_MAX = 1000.0
QUEUE_MIN_DIFF = 0.00001
TIME_LIMIT = 600


class MILP(SP_Solver):
    def __init__(self, input, time_limit=0):
        SP_Solver.__init__(self, input)
        self.time_limit = time_limit

    def solve(self):
        # Auxiliar Variables
        nb_nodes = len(self.nodes)
        r_nodes = range(nb_nodes)
        nb_apps = len(self.apps)
        r_apps = range(nb_apps)

        requests = [[app.get_nb_requests(node)
                     for node in self.nodes]
                    for app in self.apps]
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
                            <= self.apps[a].max_instances
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
        mdl.add_constraints(mdl.sum(np.dot([dexpr_load[a, h], dvar_place[a, h]],
                                           self.apps[a].get_demand(r))
                                    for a in r_apps)
                            <= self.nodes[h].get_capacity(r)
                            for h in r_nodes
                            for r in self.resources)
        # Queue Stability
        mdl.add_constraints(dexpr_load[a, h]
                            * (self.apps[a].get_cpu_demand_k1() - self.apps[a].work_size)
                            + dvar_place[a, h] * self.apps[a].get_cpu_demand_k2()
                            >= dvar_place[a, h] * QUEUE_MIN_DIFF
                            for a in r_apps
                            for h in r_nodes)
        # Deadline
        cpu_ws = [app.get_cpu_demand_k1() - app.work_size for app in self.apps]
        cpu_k2 = [app.get_cpu_demand_k2() for app in self.apps]
        work_size = [app.work_size for app in self.apps]
        deadline = [app.deadline for app in self.apps]

        mdl.add_constraints(dvar_load_f[a, b, h] * self.get_net_delay(a, b, h) * cpu_ws[a]
                            + dvar_flow_exists[a, b, h] * (cpu_k2[a] * self.get_net_delay(a, b, h) + work_size[a])
                            - dexpr_load[a, h] * deadline[a] * cpu_ws[a]
                            - cpu_k2[a] * deadline[a]
                            - dvar_load_e[a, h] * cpu_ws[a]
                            - dvar_e * cpu_k2[a] <= 0
                            for a in r_apps
                            for b in r_nodes
                            for h in r_nodes)

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

        # Objective
        mdl.minimize(dvar_e)

        # mdl.float_precision = 3
        # mdl.print_information()

        if self.time_limit > 0:
            mdl.context.cplex_parameters.timelimit = self.time_limit

        cloud = self.get_cloud_index()
        obj_value = INF
        place = {(a, h): 0 if h != cloud else 1
                 for a in r_apps
                 for h in r_nodes}
        load = {(a, b, h): 0 if h != cloud else requests[a][b]
                for a in r_apps
                for b in r_nodes
                for h in r_nodes}

        # Solving
        if mdl.solve():
            obj_value = mdl.objective_value
            for a in r_apps:
                for h in r_nodes:
                    place[a, h] = int(dvar_place[a, h].solution_value)
                    for b in r_nodes:
                        load[a, b, h] = int(dvar_distribution[a, b, h].solution_value)

        return place, load, obj_value


def solve(input, time_limit=TIME_LIMIT):
    solver = MILP(input, time_limit)
    result = list(solver.solve())
    output = Output(input)
    output.e_relaxed = result.pop()
    output.set_solution(*result)
    return output
