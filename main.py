import csv
import random
import numpy as np
import sys
import input
import path
import genetic
import genetic_lp
import genetic_2
import greedy
import pso
import minlp
import cloud
import pprint
import time


def exp_4(args=[]):
    random.seed()
    np.random.seed()

    r_nodes = [9, 21]
    r_apps = range(10, 51, 10)
    r_users = range(1000, 10001, 3000)
    nb_runs = 30
    solutions = {"cloud": greedy.solve_sp, "greedy": greedy.solve_sp,
                 "genetic": genetic.solve_sp, "minlp": minlp.solve_sp}

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
                                    result = [float('inf')] * 4
                                values = [("milp", result[0]),
                                          ("milp-minlp", result[3])]
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
    nb_apps = 10
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

    start_time = time.time()
    solution = cloud.solve_sp(nodes, apps, users, resources, net_delay, apps_demand)
    elapsed_time = round(time.time() - start_time, 2)
    print("{} - {} - {}s".format("cloud", solution[0], elapsed_time))

    start_time = time.time()
    solution = greedy.solve_sp(nodes, apps, users, resources, net_delay, apps_demand)
    elapsed_time = round(time.time() - start_time, 2)
    print("{} - {} - {}s".format("greedy", solution[0], elapsed_time))

    # start_time = time.time()
    # solution = genetic.solve_sp(nodes, apps, users, resources, net_delay, apps_demand)
    # elapsed_time = round(time.time() - start_time, 2)
    # print("{} - {} - {}s".format("genetic", solution[0], elapsed_time))

    # start_time = time.time()
    # solution = genetic_lp.solve_sp(nodes, apps, users, resources, net_delay, apps_demand)
    # elapsed_time = round(time.time() - start_time, 2)
    # print("{} - {} - {}s".format("genetic lp", solution[0], elapsed_time))

    start_time = time.time()
    solution = genetic_2.solve_sp(nodes, apps, users, resources, net_delay, apps_demand)
    elapsed_time = round(time.time() - start_time, 2)
    print("{} - {} - {}s".format("genetic 2", solution[0], elapsed_time))

    # start_time = time.time()
    # solution = pso.solve_sp(nodes, apps, users, resources, net_delay, apps_demand)
    # elapsed_time = time.time() - start_time
    # print("{} - {} - {}s".format("pso", solution[0], elapsed_time))

    start_time = time.time()
    solution = minlp.solve_sp(nodes, apps, users, resources, net_delay, apps_demand)
    elapsed_time = round(time.time() - start_time, 2)
    print("{} - {} - {}s".format("milp", solution[0], elapsed_time))
    print("{} - {} - {}s".format("milp-minlp", solution[3], elapsed_time))

    # pp = pprint.PrettyPrinter(indent=4)
    # pp.pprint(solution[1])
    # pp.pprint(solution[2])


def exp_1(args=[]):
    random.seed()
    np.random.seed()

    r_nodes = [9, 21]
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
