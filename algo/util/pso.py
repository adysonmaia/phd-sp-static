import random

# Constants
X_MIN = -1.0
X_MAX = 1.0
INF = float("inf")


class PSO_Decoder:
    def __init__(self):
        self.nb_dimensions = 0

    def get_dimensions(self):
        return self.nb_dimensions

    def stopping_criteria(self,  best_coding, best_cost):
        return False

    def get_cost(self, coding):
        return 0.0


class Particle:
    def __init__(self,
                 x0,
                 decoder,
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
        self.decoder = decoder
        self.nb_dimensions = len(x0)

        for i in range(self.nb_dimensions):
            self.velocity.append(random.uniform(-1, 1))
            self.position.append(x0[i])

    # evaluate current fitness
    def evaluate(self):
        self.cost = self.decoder.get_cost(self.position)

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
                 decoder,
                 nb_particles,
                 max_iteration,
                 stopping_func=None,
                 bounds=None):

        self.decoder = decoder
        self.nb_dimensions = decoder.get_dimensions()
        self.nb_particles = nb_particles
        self.max_iteration = max_iteration
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
            swarm.append(Particle(x0, self.decoder, bounds=self.bounds))

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

            if self.decoder.stopping_criteria(pos_best_g, cost_best_g):
                break

        return pos_best_g, cost_best_g
