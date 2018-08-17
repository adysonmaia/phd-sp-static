from docplex.mp.model import Model

# Constants
INF = float("inf")
DIST_FACTOR = 0.001
QUEUE_MIN_DIFF = 0.00001
E_MAX = 100000.0
K1 = 0
K2 = 1
CPU = "CPU"
DEADLINE = "deadline"
MAX_INSTANCES = "max_instances"
REQUEST_RATE = "request_rate"
WORK_SIZE = "work_size"


def solve_sp(nodes,
             apps,
             users,
             resources,
             net_delay,
             demand):

    # Auxiliar Variables
    nb_nodes = len(nodes)
    r_nodes = range(nb_nodes)
    nb_apps = len(apps)
    r_apps = range(nb_apps)
    nb_users = [sum(users[a]) for a in r_apps]
    max_load = [apps[a][REQUEST_RATE] * nb_users[a] for a in r_apps]

    mdl = Model(name='ServicePlacement')

    # Decision Variables
    dvar_place = mdl.binary_var_matrix(nb_apps, nb_nodes, name="I")
    dvar_flow_exists = mdl.binary_var_cube(nb_apps, nb_nodes, nb_nodes,
                                           name="F")
    dvar_distribution = mdl.continuous_var_cube(nb_apps, nb_nodes, nb_nodes,
                                                lb=0, ub=1, name="a")
    dvar_e = mdl.continuous_var(lb=0, ub=E_MAX, name="e")
    dvar_load_f = mdl.continuous_var_cube(nb_apps, nb_nodes, nb_nodes,
                                          lb=0, name="lf")
    dvar_load_e = mdl.continuous_var_matrix(nb_apps, nb_nodes,
                                            lb=0, name="le")

    # Decision Expresions
    dexpr_load = {(a, h): mdl.sum(dvar_distribution[a, b, h]
                                  * users[a][b] * apps[a][REQUEST_RATE]
                                  for b in r_nodes)
                  for a in r_apps for h in r_nodes}

    # Constraints
    # Number of Instances
    mdl.add_constraints(mdl.sum(dvar_place[a, h] for h in r_nodes)
                        >= 1
                        for a in r_apps)
    mdl.add_constraints(mdl.sum(dvar_place[a, h] for h in r_nodes)
                        <= apps[a][MAX_INSTANCES]
                        for a in r_apps)
    # Request Flow Existance
    mdl.add_constraints(dvar_flow_exists[a, b, h]
                        <= dvar_place[a, h] * users[a][b]
                        for a in r_apps
                        for b in r_nodes
                        for h in r_nodes)
    # Request Distribution Conservation
    mdl.add_constraints(users[a][b]
                        * (mdl.sum(dvar_distribution[a, b, h] for h in r_nodes)
                            - 1.0)
                        == 0.0
                        for a in r_apps
                        for b in r_nodes)
    # Request Distribution Existance
    mdl.add_constraints(dvar_distribution[a, b, h] <= dvar_flow_exists[a, b, h]
                        for a in r_apps
                        for b in r_nodes
                        for h in r_nodes)
    mdl.add_constraints(dvar_distribution[a, b, h]
                        >= dvar_flow_exists[a, b, h] * DIST_FACTOR
                        for a in r_apps
                        for b in r_nodes
                        for h in r_nodes)
    # Node Capacity
    mdl.add_constraints(mdl.sum(dexpr_load[a, h] * demand[a][r][K1]
                                + dvar_place[a, h] * demand[a][r][K2]
                                for a in r_apps)
                        <= nodes[h][r]
                        for h in r_nodes
                        for r in resources)
    # Queue Stability
    mdl.add_constraints(dexpr_load[a, h]
                        * (demand[a][CPU][K1] - apps[a][WORK_SIZE])
                        + dvar_place[a, h] * demand[a][CPU][K2]
                        >= dvar_place[a, h] * QUEUE_MIN_DIFF
                        for a in r_apps
                        for h in r_nodes)
    # Deadline
    mdl.add_constraints(dvar_load_f[a, b, h] * net_delay[a][b][h] * (demand[a][CPU][K1] - apps[a][WORK_SIZE])
                        + dvar_flow_exists[a, b, h] * (demand[a][CPU][K2] * net_delay[a][b][h] + apps[a][WORK_SIZE])
                        - dexpr_load[a, h] * apps[a][DEADLINE] * (demand[a][CPU][K1] - apps[a][WORK_SIZE])
                        - demand[a][CPU][K2] * apps[a][DEADLINE]
                        - dvar_load_e[a, h] * (demand[a][CPU][K1] - apps[a][WORK_SIZE])
                        - dvar_e * demand[a][CPU][K2] <= 0
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
    mdl.add_constraints(dvar_load_e[a, h] <= dvar_e * max_load[a]
                        for a in r_apps
                        for h in r_nodes)
    mdl.add_constraints(dvar_load_e[a, h] <= dexpr_load[a, h] * E_MAX
                        for a in r_apps
                        for h in r_nodes)
    mdl.add_constraints(dvar_load_e[a, h]
                        >= dvar_e * max_load[a]
                        + dexpr_load[a, h] * E_MAX - max_load[a] * E_MAX
                        for a in r_apps
                        for h in r_nodes)

    # Objective
    mdl.minimize(dvar_e)

    # mdl.float_precision = 3
    # mdl.print_information()

    # Solving
    if not mdl.solve():
        return None
    else:
        # mdl.print_solution()
        place = [[h for h in r_nodes if dvar_place[a, h].solution_value > 0]
                 for a in r_apps]
        distri = {(a, b, h): dvar_distribution[a, b, h].solution_value
                  for a in r_apps
                  for b in r_nodes
                  for h in r_nodes
                  if dvar_distribution[a, b, h].solution_value > 0}
        return mdl.objective_value, place, distri
