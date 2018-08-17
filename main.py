import input
import path
import random
import numpy as np
import genetic
import greedy


INF = float("inf")


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
    # random.seed(1)
    # np.random.seed(1)

    nb_nodes = 21
    r_apps = range(10, 51, 10)
    r_users = range(1000, 10001, 3000)
    nb_runs = 1

    for nb_apps in r_apps:
        for nb_users in r_users:
            e_greedy = []
            e_genetic = []
            for r in range(nb_runs):
                apps = input.gen_rand_apps(nb_apps, nb_nodes, nb_users)
                apps_demand = [a["demand"] for a in apps]
                apps_link_delay = [a["delay"] for a in apps]
                apps_users = [a["users"] for a in apps]

                graphs = input.gen_net_graphs(nb_nodes, apps_link_delay)
                net_delay = [path.calc_net_delay(g) for g in graphs]
                nodes = input.gen_nodes_capacity(nb_nodes)
                resources = nodes[0].keys()
                users = input.gen_rand_users(nb_nodes, apps_users)

                result = greedy.solve_sp(nodes, apps, users, resources, net_delay, apps_demand)
                e_greedy.append(result[0])

                result = genetic.solve_sp(nodes, apps, users, resources, net_delay, apps_demand)
                e_genetic.append(result[0])

            avg_e_greedy = round(sum(e_greedy) / float(nb_runs), 3)
            avg_e_genetic = round(sum(e_genetic) / float(nb_runs), 3)
            print(nb_apps, nb_users, "greedy", avg_e_greedy)
            print(nb_apps, nb_users, "genetic", avg_e_genetic)


if __name__ == '__main__':
    main()
