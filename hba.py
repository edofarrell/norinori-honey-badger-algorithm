from copy import copy
import numpy as np
from q_learning import Q_Learning


class HBA:
    def __init__(self, preprocessed_cells, parameters, objective_function):
        self.preprocessed = preprocessed_cells
        self.C = parameters['hba']['C']
        self.beta = parameters['hba']['beta']
        self.N = parameters['hba']['N']
        self.D = parameters['hba']['D']
        self.lb = parameters['hba']['lb']
        self.ub = parameters['hba']['ub']
        self.t_max = parameters['hba']['t_max']
        self.k = parameters['hba']['k']
        self.count = parameters['hba']['count']
        self.objective_function = objective_function
        self._q_learning = Q_Learning(2, 2, parameters['q_learning'])

    def solve(self):
        X = self.initialize_population()  # Position of all honey badgers
        fitness = []
        for i in range(self.N):
            fitness.append(self.objective_function(X[i]))

        f_prey = np.min(fitness)
        x_prey = X[np.argmin(fitness)]
        k_counter = 0

        for t in range(1, self.t_max + 1):
            if f_prey == 0:
                break

            x_new = np.zeros((self.N, self.D))
            alpha = self.C * np.exp(-t / self.t_max)
            I = self.calc_intensity(X, x_prey)

            self._q_learning.choose_action()
            mode = self._q_learning.next_state
            found_better = False

            # For each honey badgers
            for i in range(self.N):
                # For each decision variable
                for j in range(self.D):
                    r = np.random.rand()
                    if r <= 0.5:
                        F = 1
                    else:
                        F = -1

                    if self.preprocessed[j] is None:
                        di = (x_prey[j] - X[i][j])
                        # Digging mode
                        if mode == 0:
                            r1, r2, r3 = np.random.rand(), np.random.rand(), np.random.rand()
                            x_new[i][j] = x_prey[j] + F * self.beta * I[i] * x_prey[j] + F * r1 * alpha * di * abs(
                                np.cos(2 * np.pi * r2) * (1 - np.cos(2 * np.pi * r3)))
                        # Honey mode
                        else:
                            r4 = np.random.rand()
                            x_new[i][j] = x_prey[j] + F * r4 * alpha * di

                        # If any values exceed the lower and upper bounds, change it to the respective bounds
                        x_new[i][j] = min(x_new[i][j], self.ub)
                        x_new[i][j] = max(x_new[i][j], self.lb)
                    else:
                        x_new[i][j] = self.preprocessed[j]

                # Calculate fitness of x_new and replace if it is better
                fitness_new = self.objective_function(x_new[i])
                if fitness_new < fitness[i]:
                    fitness[i] = fitness_new
                    X[i] = x_new[i]
                if fitness_new < f_prey:
                    f_prey = fitness_new
                    x_prey = x_new[i]
                    found_better = True
                    k_counter = 0

            if not found_better:
                k_counter += 1
            self._q_learning.update(found_better)

            if k_counter == self.k:
                X, fitness = self.convert_opposite(X, fitness)
                f_prey = np.min(fitness)
                x_prey = X[np.argmin(fitness), :]
                k_counter = 0

        return x_prey, f_prey, t

    def calc_intensity(self, X, x_prey):
        I = np.zeros(self.N)

        # To avoid division by 0
        eps = np.finfo(float).eps

        # Calculate intensity for the 1st to the (n-1)th honey badger
        for i in range(self.N - 1):
            r = np.random.rand()
            S = np.linalg.norm(X[i] - X[i + 1] + eps) ** 2
            di = np.linalg.norm(X[i] - x_prey + eps) ** 2
            I[i] = r * S / (4 * np.pi * di)

        # Calculate intensity for the nth honey badger
        r = np.random.rand()
        S = np.linalg.norm(X[self.N - 1] - X[0] + eps) ** 2
        di = np.linalg.norm(X[self.N - 1] - x_prey + eps) ** 2
        I[self.N - 1] = r * S / (4 * np.pi * di)

        return I

    def initialize_population(self):
        X = np.zeros((self.N, self.D))
        for i in range(self.N):
            for j in range(self.D):
                if self.preprocessed[j] is None:
                    X[i][j] = self.lb + np.random.rand() * (self.ub - self.lb)
                else:
                    X[i][j] = self.preprocessed[j]
        return X

    ''' Change position of bad individuals '''
    def convert_opposite(self, X, fitness, ratio=3):
        fitness_copy = copy(fitness)
        for i in range(self.count):
            worst_index = np.argmax(fitness_copy)
            for j in range(self.D):
                if self.preprocessed[j] is None:
                    r = 0
                    while r == 0:
                        r = np.random.rand() * ratio * 2 - ratio
                    X[worst_index][j] = (self.lb + self.ub) / 2 + (self.lb + self.ub) / (2 * r) - X[worst_index][j] / r
                    X[worst_index][j] = min(X[worst_index][j], self.ub)
                    X[worst_index][j] = max(X[worst_index][j], self.lb)
            fitness[worst_index] = self.objective_function(X[worst_index])
            fitness_copy[worst_index] = -1
        return X, fitness
