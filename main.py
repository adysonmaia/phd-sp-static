import csv
import random
import numpy as np
import input
import path
import genetic
import greedy


# def main():
#     random.seed(1)
#     np.random.seed(1)
#
#     nb_nodes = 21
#     # nb_nodes = 9
#     nb_apps = 100
#     nb_users = 10000
#
#     apps = input.gen_rand_apps(nb_apps, nb_nodes, nb_users)
#     apps_demand = [a["demand"] for a in apps]
#     apps_link_delay = [a["delay"] for a in apps]
#     apps_users = [a["users"] for a in apps]
#
#     graphs = input.gen_net_graphs(nb_nodes, apps_link_delay)
#     net_delay = [path.calc_net_delay(g) for g in graphs]
#     nodes = input.gen_nodes_capacity(nb_nodes)
#     resources = nodes[0].keys()
#     users = input.gen_rand_users(nb_nodes, apps_users)
#
#     greedy_solution = greedy.solve_sp(nodes, apps, users, resources, net_delay, apps_demand)
#     print("greedy", greedy_solution[0])
#     genetic_solution = genetic.solve_sp(nodes, apps, users, resources, net_delay, apps_demand)
#     print("genetic", genetic_solution[0])
#     print("greedy", greedy_solution[0])
#
#     # print("Objective value: e = %.3f" % (solution[0]))
#     # print("\nApps Location:\nplace app a at nodes in list[a]")
#     # print(solution[1])
#     # print("\nRequests Distribution:\n(app, src, dest): value")
#     # print(solution[2])


def main():
    random.seed()
    np.random.seed()

    nb_nodes = 21
    r_nodes = [9, 21, 39]
    r_apps = range(10, 51, 10)
    r_users = range(1000, 10001, 3000)
    nb_runs = 30
    solutions = {"greedy": greedy.solve_sp, "genetic": genetic.solve_sp}

    results = []
    with open("output/result.csv", "w") as csv_file:
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
    main()
