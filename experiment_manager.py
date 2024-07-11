import csv
import math
import os
import time
import numpy as np
from experiment_result import ExperimentResult
from gpa import GPA
from puzzle import Puzzle

PATH_DATA = "./Data"
PATH_RESULT = "./Result"

class ExperimentManager:
    def load_data(self, path):
        file = open(path, "r")
        id = file.readline().rstrip()
        size = file.readline().rstrip()
        difficulty = None
        if not size.isnumeric():
            size, difficulty = size.split()
        horizontal_lines = file.readline().rstrip()
        vertical_lines = file.readline().rstrip()
        file.close()

        size = int(size)
        # Convert borders from flattened bitstring to 2-dimensional array of integer
        horizontal_lines = [[int(horizontal_lines[i + j]) for j in range(size)] for i in range(0, len(horizontal_lines), size)]
        vertical_lines = [[int(vertical_lines[i + j]) for j in range(size - 1)] for i in range(0, len(vertical_lines), size - 1)]
        borders = {"horizontal": horizontal_lines, "vertical": vertical_lines}

        return id, size, difficulty, borders

    def save_result(self, path, size, difficulty, parameters, seed, experiment_results):
        ids = experiment_results.ids
        fitness = experiment_results.fitness
        runtime = experiment_results.runtime
        optimal_iteration = experiment_results.optimal_iteration
        result = experiment_results.result
        preprocessed_count = experiment_results.preprocessed_count
        amount = len(fitness)

        max_f1 = size ** 2 - 2
        max_f2 = size ** 4 - 2 * size ** 2
        max_f3 = size ** 2
        max_f4 = (1 / 8) * size ** 4
        max_f5 = (1 / 8) * size ** 4 + (1 / 2) * size ** 2
        weight = parameters["obj_function_weight"]
        max_fitness = max(
            weight[0] * max_f1 + weight[1] * max_f2,
            weight[0] * ((1 / 2) * (size ** 2)) + weight[2] * max_f3 + weight[4] * max_f5,
            weight[0] * max_f1 + weight[2] * max_f3 + weight[3] * max_f4 + weight[4] * max_f5
        )

        csv_file = open(f"{path}.csv", "w", newline='')
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(["Number", "ID", "Fitness", "Runtime", "Preprocessed", "Result"])

        txt_file = open(f"{path}.txt", "w")
        avg_fitness = 0
        max_value = -1
        min_value = max_fitness
        optimal = 0
        for value in fitness:
            avg_fitness += value
            max_value = max(max_value, value)
            min_value = min(min_value, value)
            if value == 0.0:
                optimal += 1
        avg_fitness = avg_fitness / amount

        optimal_preprocess = 0
        avg_preprocess = 0
        for value in preprocessed_count:
            avg_preprocess += 100 * value / (size ** 2)
            if value == size ** 2:
                optimal_preprocess += 1
        avg_preprocess = avg_preprocess / amount

        avg_runtime = 0
        for value in runtime:
            avg_runtime += value
        avg_runtime = avg_runtime / amount

        std_dev = 0
        for value in fitness:
            std_dev += (value - avg_fitness) ** 2
        std_dev = std_dev / amount
        std_dev = math.sqrt(std_dev)

        txt_file.write(f"Puzzle: {size} {difficulty if difficulty else ''}\n")
        txt_file.write(f"Amount: {amount}\n")
        txt_file.write(f"Result details: {path}.csv\n")
        txt_file.write(f"Maximum Fitness: {max_fitness}\n\n")

        txt_file.write(f"-----Parameters-----\n")
        txt_file.write(f"Objective Function Weight = {weight}\n")
        txt_file.write(f"C = {parameters['hba']['C']}\n")
        txt_file.write(f"beta = {parameters['hba']['beta']}\n")
        txt_file.write(f"N = {parameters['hba']['N']}\n")
        txt_file.write(f"D = {parameters['hba']['D']}\n")
        txt_file.write(f"lb = {parameters['hba']['lb']}\n")
        txt_file.write(f"ub = {parameters['hba']['ub']}\n")
        txt_file.write(f"t_max = {parameters['hba']['t_max']}\n")
        txt_file.write(f"count = {parameters['hba']['count']}\n")
        txt_file.write(f"k = {parameters['hba']['k']}\n")
        txt_file.write(f"reward = {parameters['q_learning']['reward']}\n")
        txt_file.write(f"alpha = {parameters['q_learning']['alpha']}\n")
        txt_file.write(f"gamma = {parameters['q_learning']['gamma']}\n")
        txt_file.write(f"eps = {parameters['q_learning']['eps']}\n")
        txt_file.write(f"chi = {parameters['q_learning']['chi']}\n\n")

        txt_file.write(f"-----Results-----\n")
        txt_file.write(f"Fitness:\n")
        txt_file.write(f"\tMinimal = {min_value}\n")
        txt_file.write(f"\tMaximal = {max_value}\n")
        txt_file.write(f"\tAverage = {avg_fitness}\n")
        txt_file.write(f"\tStandard Deviation = {std_dev}\n")

        txt_file.write(f"Runtime:\n")
        txt_file.write(f"\tAverage = {avg_runtime}\n")
        txt_file.write(f"\tTotal = {avg_runtime * amount}\n")

        txt_file.write(f"Optimal = {optimal}/{amount} ({100 * optimal / amount}%)\n")
        txt_file.write(
            f"Optimal by Preprocessing = {optimal_preprocess}/{amount} ({100 * optimal_preprocess / amount}%)\n")
        txt_file.write(f"Average Preprocessing = {avg_preprocess}%\n\n")

        txt_file.write(f"-----Details-----\n")
        for i in range(len(ids)):
            txt_file.write(
                "{0:d}.{1:>{2}s} ID = {3:<10}, Fitness = {4:<9.4f} (Iteration: {5:>4d}), Runtime = {6:<7.4f}, Preprocessed = {7:<{8}d}/{9:d} ({10:>6.2f}%)\n"
                .format(
                    i + 1,
                    '',
                    3 - len(str(i + 1)),
                    ids[i],
                    fitness[i],
                    optimal_iteration[i],
                    runtime[i],
                    preprocessed_count[i],
                    len(str(size ** 2)),
                    size ** 2,
                    100 * preprocessed_count[i] / (size ** 2)
                )
            )

            csv_writer.writerow([
                i + 1,
                ids[i],
                "{0:.6f}".format(fitness[i]),
                "{0:.6f}".format(runtime[i]),
                "{0:d}/{1:d} ({2:.2f}%)".format(preprocessed_count[i], size ** 2, 100 * preprocessed_count[i] / (size ** 2)),
                result[i]
            ])

        txt_file.write(f"\nSeed =\n{seed}\n")
        txt_file.close()
        csv_file.close()

    def run_experiment(self, amount, parameters, save_file_name, size, difficulty=None):
        processed = 0
        optimal = 0
        optimal_preprocessed = 0
        ids = []
        runtime = []
        fitness = []
        preprocessed_count = []
        preprocessed_fitness = []
        result = []
        optimal_iteration = []
        seed = np.random.get_state()

        for file_name in os.listdir(f"./Data/{size}{difficulty if difficulty else ''}"):
            if processed == amount:
                break

            path = f"{PATH_DATA}/{size}{difficulty if difficulty is not None else ''}/{file_name}"
            if os.path.isfile(path):
                id, size, difficulty, borders = self.load_data(path)
                puzzle = Puzzle(size, borders)
                gpa = GPA(puzzle, parameters)

                print("Processing {0}{1}: {2:<{3}d}/{4:d}, ID = {5:<10}"
                    .format(
                        size,
                        difficulty if difficulty else '',
                        processed + 1,
                        len(str(amount)),
                        amount,
                        id)
                        , end="\r")

                start_time = time.time()
                curr_result, curr_fitness, curr_preprocessed_count, curr_iteration, curr_preprocessed_fitness = gpa.solve()
                end_time = time.time()

                curr_runtime = end_time - start_time
                ids.append(id)
                fitness.append(curr_fitness)
                runtime.append(curr_runtime)
                preprocessed_count.append(curr_preprocessed_count)
                preprocessed_fitness.append(curr_preprocessed_fitness)
                result.append(curr_result)
                optimal_iteration.append(curr_iteration)

                if curr_fitness == 0:
                    optimal += 1
                if preprocessed_count == size ** 2:
                    optimal_preprocessed += 1
                processed += 1

        save_file_path = f"{PATH_RESULT}/{save_file_name}"
        experiment_results = ExperimentResult(ids, fitness, runtime, optimal_iteration, result, preprocessed_count,
                                              preprocessed_fitness)
        self.save_result(save_file_path, size, difficulty, parameters, seed, experiment_results)
