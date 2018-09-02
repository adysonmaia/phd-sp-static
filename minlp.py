from docplex.mp.model import Model
from collections import namedtuple
import math

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


class MINLP:
    def __init__(self,
                 nodes,
                 apps,
                 users,
                 resources,
                 net_delay,
                 demand,
                 time_limit=0):

        self.nodes = nodes
        self.apps = apps
        self.users = users
        self.resources = resources
        self.net_delay = net_delay
        self.demand = demand
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

        # Objective
        mdl.minimize(dvar_e)

        # mdl.float_precision = 3
        # mdl.print_information()

        if self.time_limit > 0:
            mdl.context.cplex_parameters.timelimit = self.time_limit

        # Solving
        if not mdl.solve():
            if self.time_limit <= 0:
                return INF, None, None, INF

            SV = namedtuple("SolutionValue", ["solution_value"])
            OV = namedtuple("ObjectiveValue", ["objective_value"])
            cloud = nb_nodes - 1
            dvar_place = {(a, h): SV(0 if b != cloud else 1)
                          for a in r_apps
                          for h in r_nodes}
            dvar_distribution = {(a, b, h): SV(0 if h != cloud else requests[a][b])
                                 for a in r_apps
                                 for b in r_nodes
                                 for h in r_nodes}
            mdl = OV(INF)
        # else:
        #     mdl.print_solution()

        place = [[h for h in r_nodes if dvar_place[a, h].solution_value > 0]
                 for a in r_apps]
        distri = {(a, b, h):
                  dvar_distribution[a, b, h].solution_value
                  / float(requests[a][b])
                  for a in r_apps
                  for b in r_nodes
                  for h in r_nodes
                  if (dvar_distribution[a, b, h].solution_value > 0
                      and requests[a][b] > 0)}
        relaxed_value = mdl.objective_value
        original_value = self._calc_original_qos_violation(dvar_place,
                                                           dvar_distribution)
        return relaxed_value, place, distri, original_value

    def _calc_original_qos_violation(self, dvar_place, dvar_distribution):
        r_apps = range(len(self.apps))
        r_nodes = range(len(self.nodes))

        e = 0.0
        for a in r_apps:
            app = self.apps[a]
            work_size = app[WORK_SIZE]
            deadline = app[DEADLINE]
            cpu_k1 = self.demand[a][CPU][K1]
            cpu_k2 = self.demand[a][CPU][K2]

            instances = [h for h in r_nodes if dvar_place[a, h].solution_value > 0]
            bs = [b for b, nb_users in enumerate(self.users[a]) if nb_users > 0]

            max_delay = 0.0
            for h in instances:
                node_load = sum([dvar_distribution[a, b, h].solution_value for b in bs])
                proc_delay_divisor = float(node_load * (cpu_k1 - work_size) + cpu_k2)
                proc_delay = INF
                if proc_delay_divisor > 0.0:
                    proc_delay = app[WORK_SIZE] / proc_delay_divisor
                for b in bs:
                    if dvar_distribution[a, b, h].solution_value > 0:
                        delay = self.net_delay[a][b][h] + proc_delay
                        if delay > max_delay:
                            max_delay = delay

            violation = max_delay - deadline
            if violation > 0.0 and violation > e:
                e = violation
        return e


def solve_sp(nodes,
             apps,
             users,
             resources,
             net_delay,
             demand,
             time_limit=0):
    model = MINLP(nodes, apps, users, resources, net_delay, demand, time_limit)
    return model.solve()
