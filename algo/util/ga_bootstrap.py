from algo.util.kmedoids import KMedoids

INF = float("inf")


def create_individual_cloud(chromosome):
    """Create an individual that prioritizes the cloud node
    """
    return [0] * chromosome.nb_genes


def create_individual_avg_delay(chromosome):
    """Create an individual that prioritizes nodes having
    shorter avg. delays to other nodes
    and requests with strict deadlines
    """
    nb_apps = len(chromosome.apps)
    r_apps = range(nb_apps)
    nb_nodes = len(chromosome.nodes)
    r_nodes = range(nb_nodes)

    indiv = [0] * chromosome.nb_genes
    max_deadline = 1.0

    for a in r_apps:
        indiv[a] = 1.0

        deadline = chromosome.apps[a].deadline
        if deadline > max_deadline:
            max_deadline = deadline

        nodes_delay = []
        max_delay = 1.0

        for h in r_nodes:
            avg_delay = 0.0
            count = 0
            for b in r_nodes:
                if chromosome.get_nb_users(a, b) > 0:
                    avg_delay += chromosome.get_net_delay(a, b, h)
                    count += 1
            if count > 0:
                avg_delay = avg_delay / float(count)
            nodes_delay.append(avg_delay)
            if avg_delay > max_delay:
                max_delay = avg_delay

        for h in r_nodes:
            key = nb_apps + a * nb_nodes + h
            value = 1.0 - nodes_delay[h] / float(max_delay)
            indiv[key] = value

    # for (req_index, req) in enumerate(chromosome.requests):
    #     a, b = req
    #     key = nb_apps * (nb_nodes + 1) + req_index
    #     value = 1.0 - chromosome.apps[a].deadline / float(max_deadline)
    #     indiv[key] = value

    return indiv


def create_individual_cluster(chromosome):
    """Create an individual based on k-medoids clustering
    The idea is the users of an application are grouped
    and central nodes of each group are prioritized.
    It also prioritizes requests with strict deadlines
    """
    nb_apps = len(chromosome.apps)
    r_apps = range(nb_apps)
    nb_nodes = len(chromosome.nodes)
    r_nodes = range(nb_nodes)
    kmedoids = KMedoids()

    indiv = [0] * chromosome.nb_genes
    max_deadline = 1.0

    for a in r_apps:
        indiv[a] = 1.0
        app = chromosome.apps[a]
        deadline = app.deadline
        if deadline > max_deadline:
            max_deadline = deadline

        distances = [[app.get_net_delay(i, j)
                      for j in chromosome.nodes]
                     for i in chromosome.nodes]
        features = list(filter(lambda h: app.get_nb_users(chromosome.nodes[h]) > 0, r_nodes))
        max_nb_clusters = min(len(features), app.max_instances)

        clusters = [list(r_nodes)]
        max_score = -1
        if max_nb_clusters > 1:
            for k in range(1, max_nb_clusters + 1):
                k_clusters = kmedoids.fit(k, features, distances)
                k_score = kmedoids.silhouette_score(k_clusters, distances)
                if k_score > max_score:
                    max_score = k_score
                    clusters = k_clusters

        nb_instances = min(nb_nodes, app.max_instances)
        cluster_nb_instances = nb_instances // len(clusters)
        for cluster in clusters:
            priority = {i: sum([distances[i][j] for j in cluster])
                        for i in cluster}
            cluster.sort(key=lambda i: priority[i])
            for (index, h) in enumerate(cluster):
                key = nb_apps + a * nb_nodes + h
                value = 0
                if index < cluster_nb_instances:
                    value = 1.0 - index / float(cluster_nb_instances)
                indiv[key] = value

    # for (req_index, req) in enumerate(chromosome.requests):
    #     a, b = req
    #     key = nb_apps * (nb_nodes + 1) + req_index
    #     value = 1.0 - chromosome.apps[a].deadline / float(max_deadline)
    #     indiv[key] = value

    return indiv


def create_individual_cluster_2(chromosome):
    """Create an individual based on k-medoids clustering
    The idea is the users of an application are grouped
    and central nodes of each group are prioritized.
    It also prioritizes requests with strict deadlines
    """
    nb_apps = len(chromosome.apps)
    r_apps = range(nb_apps)
    nb_nodes = len(chromosome.nodes)
    r_nodes = range(nb_nodes)
    kmedoids = KMedoids()

    indiv = [0] * chromosome.nb_genes
    max_deadline = 1.0

    for a in r_apps:
        indiv[a] = 1.0
        app = chromosome.apps[a]
        deadline = app.deadline
        if deadline > max_deadline:
            max_deadline = deadline

        distances = [[app.get_net_delay(i, j)
                      for j in chromosome.nodes]
                     for i in chromosome.nodes]
        features = list(filter(lambda h: app.get_nb_users(chromosome.nodes[h]) > 0, r_nodes))

        nb_clusters = min(len(features), app.max_instances)
        kmedoids.fit(nb_clusters, features, distances)
        metoids = kmedoids.get_last_metoids()
        for h in metoids:
            key = nb_apps + a * nb_nodes + h
            value = 1.0
            indiv[key] = value

    # for (req_index, req) in enumerate(chromosome.requests):
    #     a, b = req
    #     key = nb_apps * (nb_nodes + 1) + req_index
    #     value = 1.0 - chromosome.apps[a].deadline / float(max_deadline)
    #     indiv[key] = value

    return indiv


def create_individual_user(chromosome):
    """Create an individual that priorizes nodes
    with large number of users
    """
    nb_apps = len(chromosome.apps)
    r_apps = range(nb_apps)
    nb_nodes = len(chromosome.nodes)
    r_nodes = range(nb_nodes)

    indiv = [0] * chromosome.nb_genes
    max_deadline = 1.0
    max_nb_users = 1.0

    for a in r_apps:
        indiv[a] = 1.0
        app = chromosome.apps[a]
        deadline = app.deadline
        if deadline > max_deadline:
            max_deadline = deadline

        total_nb_users = app.nb_users
        for h in r_nodes:
            key = nb_apps + a * nb_nodes + h
            nb_users = chromosome.get_nb_users(a, h)
            value = nb_users / total_nb_users
            indiv[key] = value
            if nb_users > max_nb_users:
                max_nb_users = nb_users

    for (req_index, req) in enumerate(chromosome.requests):
        a, b = req
        key = nb_apps * (nb_nodes + 1) + req_index
        # value_1 = 1.0 - chromosome.apps[a].deadline / float(max_deadline)
        # value_2 = chromosome.get_nb_users(a, b) / float(max_nb_users)
        # value = 0.5 * value_1 + 0.5 * value_2
        value = chromosome.get_nb_users(a, b) / float(max_nb_users)
        indiv[key] = value

    return indiv


def create_individual_capacity(chromosome):
    """Create an individual that priorizes nodes
    with high capacity of resources
    """
    nb_apps = len(chromosome.apps)
    r_apps = range(nb_apps)
    nb_nodes = len(chromosome.nodes)
    r_nodes = range(nb_nodes)
    nb_resources = len(chromosome.resources)

    indiv = [0] * chromosome.nb_genes

    max_capacity = {r: 1.0 for r in chromosome.resources}
    for node in chromosome.nodes:
        for r in chromosome.resources:
            capacity = node.get_capacity(r)
            if capacity > max_capacity[r] and capacity != INF:
                max_capacity[r] = float(capacity)

    node_priority = [0 for _ in r_nodes]
    for h in r_nodes:
        value = 0.0
        for r in chromosome.resources:
            capacity = chromosome.nodes[h].get_capacity(r)
            if capacity == INF:
                value += 1
            else:
                value += capacity / max_capacity[r]
        value = value / float(nb_resources)
        node_priority[h] = value

    max_deadline = 1.0
    for a in r_apps:
        indiv[a] = 1.0
        deadline = chromosome.apps[a].deadline
        if deadline > max_deadline:
            max_deadline = deadline

        for h in r_nodes:
            key = nb_apps + a * nb_nodes + h
            indiv[key] = node_priority[h]

    # for (req_index, req) in enumerate(chromosome.requests):
    #     a, b = req
    #     key = nb_apps * (nb_nodes + 1) + req_index
    #     value = 1.0 - chromosome.apps[a].deadline / float(max_deadline)
    #     indiv[key] = value

    return indiv


def create_individual_deadline(chromosome):
    """Create an individual that priorizes request
    with strict response deadline
    """
    nb_apps = len(chromosome.apps)
    r_apps = range(nb_apps)
    nb_nodes = len(chromosome.nodes)

    indiv = [0] * chromosome.nb_genes
    max_deadline = 1.0

    for a in r_apps:
        indiv[a] = 1.0
        app = chromosome.apps[a]
        deadline = app.deadline
        if deadline > max_deadline:
            max_deadline = deadline

    for (req_index, req) in enumerate(chromosome.requests):
        a, b = req
        key = nb_apps * (nb_nodes + 1) + req_index
        value = 1.0 - chromosome.apps[a].deadline / float(max_deadline)
        indiv[key] = value

    return indiv


def merge_individual(chromosome, func_1, func_2, weight_1=0.5):
    """Create an individual by merging the results of two creation function
    """
    indiv_1 = func_1(chromosome)
    w_1 = weight_1
    indiv_2 = func_2(chromosome)
    w_2 = 1.0 - w_1
    result_indiv = list(map(lambda i, j: w_1 * i + w_2 * j, indiv_1, indiv_2))
    return result_indiv
