from algo.util.metric import Metric


class Output:
    def __init__(self, input, place=None, load=None):
        self.input = input
        self.place = place
        self.load = load
        self.metric = Metric(input)

    def set_solution(self, place, load):
        self.place = place
        self.load = load
        return self

    def get_qos_violation(self):
        return self.metric.get_qos_violation(self.place, self.load)

    def get_active_nodes(self):
        return self.metric.get_active_nodes(self.place, self.load)
