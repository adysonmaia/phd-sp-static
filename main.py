import csv
import random
import numpy as np
import sys
import input
import path
import genetic
import greedy
import minlp


def exp_4(args=[]):
    random.seed()
    np.random.seed()

    r_nodes = [21]
    r_apps = range(10, 31, 10)
    r_users = range(100, 1001, 300)
    nb_runs = 1
    solutions = {"greedy": greedy.solve_sp, "genetic": genetic.solve_sp, "minlp": minlp.solve_sp}

    results = []
    with open("output/result_exp_4.csv", "w") as csv_file:
        field_names = ["nodes", "apps", "users", "run", "solution", "value"]
        writer = csv.DictWriter(csv_file, fieldnames=field_names)
        writer.writeheader()

        for nb_nodes in r_nodes:
            for nb_apps in r_apps:
                for nb_users in r_users:
                    for run in range(nb_runs):
                        apps = input.gen_rand_apps(nb_apps, nb_nodes, nb_users)
                        apps_demand = [a["demand"] for a in apps]
                        apps_link_delay = [a["delay"] for a in apps]
                        apps_users = [a["users"] for a in apps]

                        graphs = input.gen_net_graphs(nb_nodes, apps_link_delay)
                        net_delay = [path.calc_net_delay(g) for g in graphs]
                        nodes = input.gen_nodes_capacity(nb_nodes)
                        resources = nodes[0].keys()
                        users = input.gen_rand_users(nb_nodes, apps_users)

                        for title, funct in solutions.iteritems():
                            result = funct(nodes, apps, users, resources,
                                           net_delay, apps_demand)
                            values = None
                            if title == "minlp":
                                if not result:
                                    result = [float('inf')] * 3
                                values = [("minlp - relaxed", result[0]),
                                          ("minlp - original", result[3])]
                            else:
                                values = [(title, result[0])]

                            for solution, obj_value in values:
                                row = {"nodes": nb_nodes,
                                       "apps": nb_apps,
                                       "users": nb_users,
                                       "run": run,
                                       "solution": solution,
                                       "value": obj_value}
                                writer.writerow(row)
                                results.append(row)
                                print(row)


def exp_3(args=[]):
    random.seed()
    np.random.seed()

    nb_nodes = 21
    nb_apps = 30
    nb_users = 1000
    # nb_runs = 30
    nb_runs = 1

    r_gen = range(50, 501, 50)
    r_pop = range(100, 501, 100)

    results = []
    with open("output/result_exp_3.csv", "w") as csv_file:
        field_names = ["nb_gens", "pop_size", "run", "value"]
        writer = csv.DictWriter(csv_file, fieldnames=field_names)
        writer.writeheader()

        for run in range(nb_runs):
            apps = input.gen_rand_apps(nb_apps, nb_nodes, nb_users)
            apps_demand = [a["demand"] for a in apps]
            apps_link_delay = [a["delay"] for a in apps]
            apps_users = [a["users"] for a in apps]

            graphs = input.gen_net_graphs(nb_nodes, apps_link_delay)
            net_delay = [path.calc_net_delay(g) for g in graphs]
            nodes = input.gen_nodes_capacity(nb_nodes)
            resources = nodes[0].keys()
            users = input.gen_rand_users(nb_nodes, apps_users)

            for gen in r_gen:
                for pop in r_pop:
                        result = genetic.solve_sp(nodes, apps, users, resources,
                                                  net_delay, apps_demand,
                                                  nb_generations=gen,
                                                  population_size=pop)
                        obj_value = result[0]
                        row = {"nb_gens": gen,
                               "pop_size": pop,
                               "run": run,
                               "value": obj_value}

                        writer.writerow(row)
                        results.append(row)
                        print(row)


def exp_2(args=[]):
    random.seed(1)
    np.random.seed(1)

    nb_nodes = 21
    # nb_nodes = 9
    nb_apps = 20
    nb_users = 1000
    if len(args) >= 3:
        nb_nodes, nb_apps, nb_users = map(lambda i: int(i), args)

    apps = input.gen_rand_apps(nb_apps, nb_nodes, nb_users)
    apps_demand = [a["demand"] for a in apps]
    apps_link_delay = [a["delay"] for a in apps]
    apps_users = [a["users"] for a in apps]

    graphs = input.gen_net_graphs(nb_nodes, apps_link_delay)
    net_delay = [path.calc_net_delay(g) for g in graphs]
    nodes = input.gen_nodes_capacity(nb_nodes)
    resources = nodes[0].keys()
    users = input.gen_rand_users(nb_nodes, apps_users)

    # greedy_solution = greedy.solve_sp(nodes, apps, users, resources, net_delay, apps_demand)
    # print("greedy", greedy_solution[0])
    genetic_solution = genetic.solve_sp(nodes, apps, users, resources, net_delay, apps_demand)
    print("genetic", genetic_solution[0])
    # minlp_solution = minlp.solve_sp(nodes, apps, users, resources, net_delay, apps_demand)
    # if minlp_solution:
    #     print("minlp - relaxed", minlp_solution[0])
    #     print("minlp - original", minlp_solution[3])
    # else:
    #     print("minlp - relaxed", float('inf'))
    #     print("minlp - original", float('inf'))


def exp_1(args=[]):
    random.seed()
    np.random.seed()

    r_nodes = [9, 21, 39]
    r_apps = range(10, 51, 10)
    r_users = range(1000, 10001, 3000)
    nb_runs = 30
    solutions = {"greedy": greedy.solve_sp, "genetic": genetic.solve_sp}

    results = []
    with open("output/result_exp_1.csv", "w") as csv_file:
        field_names = ["nodes", "apps", "users", "run", "solution", "value"]
        writer = csv.DictWriter(csv_file, fieldnames=field_names)
        writer.writeheader()

        for nb_nodes in r_nodes:
            for nb_apps in r_apps:
                for nb_users in r_users:
                    for run in range(nb_runs):
                        apps = input.gen_rand_apps(nb_apps, nb_nodes, nb_users)
                        apps_demand = [a["demand"] for a in apps]
                        apps_link_delay = [a["delay"] for a in apps]
                        apps_users = [a["users"] for a in apps]

                        graphs = input.gen_net_graphs(nb_nodes, apps_link_delay)
                        net_delay = [path.calc_net_delay(g) for g in graphs]
                        nodes = input.gen_nodes_capacity(nb_nodes)
                        resources = nodes[0].keys()
                        users = input.gen_rand_users(nb_nodes, apps_users)

                        for solution, funct in solutions.iteritems():
                            result = funct(nodes, apps, users, resources,
                                           net_delay, apps_demand)
                            obj_value = result[0]
                            row = {"nodes": nb_nodes,
                                   "apps": nb_apps,
                                   "users": nb_users,
                                   "run": run,
                                   "solution": solution,
                                   "value": obj_value}

                            writer.writerow(row)
                            results.append(row)
                            print(row)


if __name__ == '__main__':
    args = sys.argv[1:]
    experiment = args[0] if args else 'exp_2'
    if experiment in locals():
        exp_func = locals()[experiment]
        exp_func(args[1:])
