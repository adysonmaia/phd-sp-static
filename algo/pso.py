import random
import math
from algo import sp

X_MIN = -1.0
X_MAX = 1.0


class Particle:
    def __init__(self,
                 x0,
                 cost_func,
                 weight=0.5,
                 cognative_const=1,
                 social_const=2,
                 bounds=None):
        self.position = []          # particle position
        self.velocity = []          # particle velocity
        self.pos_best = []          # best position coding
        self.cost_best = -1         # best error coding
        self.cost = -1              # error coding
        self.w = weight             # constant inertia weight (how much to weigh the previous velocity)
        self.c1 = cognative_const   # cognative constant
        self.c2 = social_const      # social constant
        self.bounds = bounds
        self.cost_func = cost_func
        self.nb_dimensions = len(x0)

        for i in range(self.nb_dimensions):
            self.velocity.append(random.uniform(-1, 1))
            self.position.append(x0[i])

    # evaluate current fitness
    def evaluate(self):
        self.cost = self.cost_func(self.position)

        # check to see if the current position is an coding best
        if self.cost < self.cost_best or self.cost_best < 0:
            self.pos_best = self.position
            self.cost_best = self.cost

    # update new particle velocity
    def update_velocity(self, pos_best_g):
        for i in range(self.nb_dimensions):
            r1 = random.random()
            r2 = random.random()

            vel_cognitive = r1 * self.c1 * (self.pos_best[i] - self.position[i])
            vel_social = r2 * self.c2 * (pos_best_g[i] - self.position[i])
            self.velocity[i] = self.w * self.velocity[i] + vel_cognitive + vel_social

    # update the particle position based off new velocity updates
    def update_position(self):
        for i in range(self.nb_dimensions):
            self.position[i] = self.position[i] + self.velocity[i]

            if self.bounds:
                # adjust maximum position if necessary
                if self.position[i] > self.bounds[i][1]:
                    self.position[i] = self.bounds[i][1]

                # adjust minimum position if neseccary
                if self.position[i] < self.bounds[i][0]:
                    self.position[i] = self.bounds[i][0]


class PSO():
    def __init__(self,
                 cost_func,
                 nb_dimensions,
                 nb_particles,
                 max_iteration,
                 stopping_func=None,
                 bounds=None):

        self.cost_func = cost_func
        self.nb_dimensions = nb_dimensions
        self.nb_particles = nb_particles
        self.max_iteration = max_iteration
        self.stopping_criteria = stopping_func
        self.bounds = bounds

        if not self.bounds:
            self.bounds = [(X_MIN, X_MAX)] * self.nb_dimensions

    def solve(self):
        cost_best_g = -1                  # best cost for group
        pos_best_g = []                   # best position for group

        # establish the swarm
        swarm = []
        for i in range(self.nb_particles):
            x0 = [random.uniform(*self.bounds[d]) for d in range(self.nb_dimensions)]
            swarm.append(Particle(x0, self.cost_func, bounds=self.bounds))

        # begin optimization loop
        # try:
        for i in range(self.max_iteration):
            for particle in swarm:
                particle.evaluate()

                # determine if current particle is the best (globally)
                if particle.cost < cost_best_g or cost_best_g < 0:
                    pos_best_g = list(particle.position)
                    cost_best_g = float(particle.cost)

            # cycle through swarm and update velocities and position
            for particle in swarm:
                particle.update_velocity(pos_best_g)
                particle.update_position()

            if self.stopping_criteria and self.stopping_criteria(pos_best_g, cost_best_g):
                break

        # except KeyboardInterrupt:
        #     raise
        # finally:
        #     return pos_best_g, cost_best_g
        return pos_best_g, cost_best_g


class PSO_Decoder(sp.Decoder):
    def __init__(self, input):

        sp.Decoder.__init__(self, input)

        nb_apps = len(self.apps)
        r_apps = range(nb_apps)
        nb_nodes = len(self.nodes)
        r_nodes = range(nb_nodes)

        self.requests = []
        for a in r_apps:
            for b in r_nodes:
                nb_requests = int(math.ceil(self.users[a][b] * self.apps[a][sp.REQUEST_RATE]))
                self.requests += ([(a, b)] * nb_requests)

        self.nb_dimensions = len(self.apps) * len(self.requests)

    def stopping_criteria(self, best_coding, best_cost):
        print("best: {}".format(best_cost))
        return best_cost == 0.0

    def fitness(self, coding):
        data_decoded = self.decode(coding)
        return self.calc_qos_violation(*data_decoded)

    def decode(self, coding):
        nb_apps = len(self.apps)
        r_apps = range(nb_apps)
        nb_nodes = len(self.nodes)
        r_nodes = range(nb_nodes)
        nb_requests = len(self.requests)
        r_requests = range(nb_requests)
        cloud = nb_nodes - 1

        place = {(a, h): 0
                 for h in r_nodes
                 for a in r_apps}
        load = {(a, b, h): 0
                for h in r_nodes
                for b in r_nodes
                for a in r_apps}

        selected_nodes = []
        for a in r_apps:
            start = a * nb_nodes
            end = start + nb_nodes + 1
            priority = coding[start:end]
            nodes = sorted(r_nodes, key=lambda v: priority[v], reverse=True)
            max_nodes = min(nb_nodes, self.apps[a][sp.MAX_INSTANCES])
            selected_nodes.append(nodes[:max_nodes])

        capacity = {(h, r): 0 for h in r_nodes for r in self.resources}

        start = nb_apps * nb_nodes
        end = start + nb_requests + 1
        priority = coding[start:end]

        s_requests = sorted(r_requests, key=lambda v: priority[v], reverse=True)
        for req in s_requests:
            a, b = self.requests[req]
            nodes = list(selected_nodes[a])
            nodes.sort(key=lambda h: self._decode_node_priority(coding, a, b, h, place, load))
            nodes.append(cloud)
            for h in nodes:
                fit = True
                resources = {}
                for r in self.resources:
                    value = (capacity[h, r]
                             + self.demand[a][r][sp.K1]
                             + (1 - place[a, h]) * self.demand[a][r][sp.K2])
                    resources[r] = value
                    fit = fit and (value <= self.nodes[h][r])

                if fit:
                    load[a, b, h] += 1
                    place[a, h] = 1
                    for r in self.resources:
                        capacity[h, r] = resources[r]
                    break

        return self._decode_local_search(place, load)

    def _decode_node_priority(self, coding, a, b, h, place, load):
        nb_nodes = len(self.nodes)
        r_nodes = range(nb_nodes)

        cloud_delay = self.net_delay[a][b][nb_nodes - 1]
        node_delay = self.net_delay[a][b][h]
        delay = (cloud_delay - node_delay) / cloud_delay

        max_load = sum([load[a, b, v] for v in r_nodes])
        max_load = float(max_load) if max_load > 0 else 1.0

        return delay + load[a, b, h] / max_load


def solve_sp(input, nb_particles=100, max_iteration=100):
    decoder = PSO_Decoder(input)
    pso = PSO(decoder.fitness, decoder.nb_dimensions, nb_particles, max_iteration,
              decoder.stopping_criteria)
    position, cost = pso.solve()

    data_decoded = decoder.decode(position)
    e = decoder.calc_qos_violation(*data_decoded)
    place = decoder.get_places(*data_decoded)
    distribution = decoder.get_distributions(*data_decoded)

    return e, place, distribution
