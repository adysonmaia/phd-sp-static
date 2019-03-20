import csv
import random
import numpy as np
import sys
import pprint
import time
from util import input
import algo


def exp_1(args=[]):
    random.seed()
    np.random.seed()

    r_nodes = [9, 21]
    r_apps = range(10, 51, 10)
    r_users = range(1000, 10001, 3000)
    nb_runs = 30
    solutions = {"cloud": algo.greedy.solve_sp, "greedy": algo.greedy.solve_sp,
                 "genetic": algo.genetic.solve_sp, "minlp": algo.minlp.solve_sp}

    results = []
    with open("output/result_exp_4.csv", "w") as csv_file:
        field_names = ["nodes", "apps", "users", "run", "solution", "value"]
        writer = csv.DictWriter(csv_file, fieldnames=field_names)
        writer.writeheader()

        config = input.Input("input.json")

        for nb_nodes in r_nodes:
            for nb_apps in r_apps:
                for nb_users in r_users:
                    for run in range(nb_runs):
                        config.gen_rand_data(nb_nodes, nb_apps, nb_users)

                        for title, funct in solutions.iteritems():
                            output = funct(config)
                            row = {"nodes": nb_nodes,
                                   "apps": nb_apps,
                                   "users": nb_users,
                                   "run": run,
                                   "solution": title,
                                   "value": output.get_qos_violation()}
                            writer.writerow(row)
                            results.append(row)
                            print(row)


def exp_2(args=[]):
    random.seed(1)
    np.random.seed(1)

    nb_nodes = 21
    nb_apps = 10
    nb_users = 1000
    if len(args) >= 3:
        nb_nodes, nb_apps, nb_users = map(lambda i: int(i), args)

    config = input.Input("input.json")
    config.gen_rand_data(nb_nodes, nb_apps, nb_users)

    start_time = time.time()
    solution = algo.cloud.solve_sp(config)
    elapsed_time = round(time.time() - start_time, 2)
    print("{} - {} - {}s".format("cloud", solution.get_qos_violation(), elapsed_time))

    # start_time = time.time()
    # solution = algo.greedy.solve_sp(config)
    # elapsed_time = round(time.time() - start_time, 2)
    # print("{} - {} - {}s".format("greedy", solution.get_qos_violation(), elapsed_time))

    start_time = time.time()
    solution = algo.greedy_2.solve_sp(config)
    elapsed_time = round(time.time() - start_time, 2)
    print("{} - {} - {}s".format("greedy 2", solution.get_qos_violation(), elapsed_time))

    # start_time = time.time()
    # solution = algo.greedy_2_2.solve_sp(config)
    # elapsed_time = round(time.time() - start_time, 2)
    # print("{} - {} - {}s".format("greedy 2.2", solution.get_qos_violation(), elapsed_time))

    start_time = time.time()
    solution = algo.cluster.solve_sp(config)
    elapsed_time = round(time.time() - start_time, 2)
    print("{} - {} - {}s".format("cluster", solution.get_qos_violation(), elapsed_time))

    start_time = time.time()
    solution = algo.cluster_2.solve_sp(config)
    elapsed_time = round(time.time() - start_time, 2)
    print("{} - {} - {}s".format("cluster 2", solution.get_qos_violation(), elapsed_time))

    # start_time = time.time()
    # solution = algo.genetic.solve_sp(config)
    # elapsed_time = round(time.time() - start_time, 2)
    # print("{} - {} - {}s".format("genetic", solution.get_qos_violation(), elapsed_time))

    start_time = time.time()
    solution = algo.genetic_2.solve_sp(config)
    elapsed_time = round(time.time() - start_time, 2)
    print("{} - {} - {}s".format("genetic 2", solution.get_qos_violation(), elapsed_time))

    # start_time = time.time()
    # solution = algo.genetic_mo.solve_sp(config)
    # elapsed_time = round(time.time() - start_time, 2)
    # print("{} - {} - {}s".format("nsga-ii", solution.get_qos_violation(), elapsed_time))

    start_time = time.time()
    solution = algo.minlp.solve_sp(config)
    elapsed_time = round(time.time() - start_time, 2)
    print("{} - {} - {}s".format("minlp", solution.get_qos_violation(), elapsed_time))
    print("{} - {} - {}s".format("minlp relaxed", solution.e_relaxed, elapsed_time))

    # start_time = time.time()
    # solution = algo.minlp_2.solve_sp(config)
    # elapsed_time = round(time.time() - start_time, 2)
    # print("{} - {} - {}s".format("minlp 2", solution.get_qos_violation(), elapsed_time))
    # print("{} - {} - {}s".format("minlp relaxed 2", solution.e_relaxed, elapsed_time))

    # start_time = time.time()
    # solution = algo.lp.solve_sp(config)
    # elapsed_time = round(time.time() - start_time, 2)
    # print("{} - {} - {}s".format("lp", solution.get_qos_violation(), elapsed_time))

    # pp = pprint.PrettyPrinter(indent=4)
    # pp.pprint(solution[1])
    # pp.pprint(solution[2])


def exp_3(args=[]):
    from algo.util.kmedoids import KMedoids
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score
    random.seed(1)
    np.random.seed(1)

    nb_nodes = 21
    nb_apps = 10
    nb_users = 1000
    if len(args) >= 3:
        nb_nodes, nb_apps, nb_users = map(lambda i: int(i), args)

    config = input.Input("input.json")
    config.gen_rand_data(nb_nodes, nb_apps, nb_users)

    start_time = time.time()
    for a in range(nb_apps):
        data = [h for h in range(nb_nodes) if config.users[a][h] > 0]
        distances = config.net_delay[a]

        # pp = pprint.PrettyPrinter(indent=4)
        # pp.pprint(distances)
        # print(" ")

        nb_clusters = min(10, len(data), config.apps[a]["max_instances"])

        kmetoid = KMedoids()
        for k in range(1, nb_clusters + 1):
            clusters = kmetoid.fit(k, data, distances)
            score = kmetoid.silhouette_score(clusters, distances)

            # print(a, k)
            # pp = pprint.PrettyPrinter(indent=4)
            # pp.pprint(clusters)
            # print("silhouette score", score)
            # print(" ")
    elapsed_time = round(time.time() - start_time, 2)
    print("KMetoid {}s".format(elapsed_time))

    # start_time = time.time()
    # for a in range(nb_apps):
    #     bs = list(filter(lambda h: config.users[a][h] > 0, range(nb_nodes)))
    #     data = []
    #     for b in bs:
    #         point = config.bs_map[b].to_pixel()
    #         data.append([point.x, point.y])
    #
    #     for k in range(2, nb_clusters + 1):
    #         kmeans = KMeans(n_clusters=k)
    #         kmeans.fit(data)
    #         score = silhouette_score(data, kmeans.labels_)
    #
    # elapsed_time = round(time.time() - start_time, 2)
    # print("KMeans {}s".format(elapsed_time))


if __name__ == '__main__':
    args = sys.argv[1:]
    experiment = args[0] if args else 'exp_2'
    if experiment in locals():
        exp_func = locals()[experiment]
        exp_func(args[1:])
