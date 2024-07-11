class ExperimentResult:
    def __init__(self, ids, fitness, runtime, optimal_iteration, result, preprocessed_count, preprocessed_fitness):
        self.ids = ids
        self.fitness = fitness
        self.runtime = runtime
        self.optimal_iteration = optimal_iteration
        self.result = result
        self.preprocessed_count = preprocessed_count
