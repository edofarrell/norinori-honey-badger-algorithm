import numpy as np
from experiment_manager import ExperimentManager
from gpa import GPA
from puzzle import Puzzle
from web_interactor import WebInteractor

SIZE_URL = {
    6: {"normal": "?size=0", "hard": "?size=1"},
    8: {"normal": "?size=2", "hard": "?size=3"},
    10: {"normal": "?size=4", "hard": "?size=5"},
    15: {"normal": "?size=6", "hard": "?size=7"},
    20: {"normal": "?size=8", "hard": "?size=9"},
    30: "?size=10",
    40: "?size=11",
    50: "?size=12"
}

URL = {
    "base_url": "https://www.puzzle-norinori.com/",
    "specific_url": "specific.php",
    "size_url": SIZE_URL
}

CREDENTIALS = {
    "email": "email",
    "password": "password"
}

class Main:
    def run(self):
        try:
            print("Please choose an action:")
            print("1. Play Norinori")
            print("2. Collect data")
            print("3. Start an experiment")
            command = int(input(f"Choice: "))
            if command == 1:
                self.play()
            elif command == 2:
                self.collect_data()
            elif command == 3:
                self.experiment()
            else:
                raise Exception()
        except:
            print("Invalid input")

    def play(self):
        size, difficulty = self.get_puzzle_info()
        id = None
        id_input = input(f"Enter puzzle ID (Optional, input -1 to skip): ")
        if id_input != "-1":
            id = id_input

        print("Do you want to use GPA? (Y/N)")
        use_gpa = input(f"Choice: ")
        if use_gpa == "Y":
            use_gpa = 1
        elif use_gpa == "N":
            use_gpa = 0
        else:
            raise Exception()

        if use_gpa:
            parameters = self.get_parameters(size)

        web_interactor = WebInteractor(URL, CREDENTIALS)
        id, borders = web_interactor.open_puzzle(size, difficulty, id)
        # Convert borders from flattened bitstring to 2-dimensional array of integer
        borders["horizontal"] = [[int(borders["horizontal"][i + j]) for j in range(size)] for i in range(0, len(borders["horizontal"]), size)]
        borders["vertical"] = [[int(borders["vertical"][i + j]) for j in range(size - 1)] for i in range(0, len(borders["vertical"]), size - 1)]

        if use_gpa:
            puzzle = Puzzle(size, borders)
            gpa = GPA(puzzle, parameters)
            gpa.solve()
            web_interactor.input_answer(puzzle.get_solution())

    def collect_data(self):
        size, difficulty = self.get_puzzle_info()
        amount = None
        ids = None
        if size <= 20:
            id = input(f"Enter puzzle IDs (Optional, input -1 to skip or when done): ")
            if id != "-1":
                ids = [id]
                while True:
                    id = input()
                    if id == "-1":
                        break
                    ids.append(id)
            if ids is None:
                amount = int(input(f"Amount: "))
                if amount <= 0:
                    raise Exception()
        else:
            ids = []
            print(f"For puzzle with size {size}, ids needed to be specified")
            print(f"Enter ids (input -1 when done):")
            while True:
                id = input()
                if id == "-1":
                    break
                ids.append(id)

        if size <= 20:
            web_interactor = WebInteractor(URL)
        else:
            web_interactor = WebInteractor(URL, CREDENTIALS)
        web_interactor.scrape_puzzle(size, difficulty, amount, ids)
        web_interactor.close()

    def experiment(self):
        print("-----Configure experiment-----")
        size, difficulty = self.get_puzzle_info()
        amount = int(input(f"Amount: "))
        if amount <= 0:
            raise Exception()
        save_file_name = input(f"Save file name: ")  # Without extension
        parameters = self.get_parameters(size)

        experiment_manager = ExperimentManager()
        experiment_manager.run_experiment(amount, parameters, save_file_name, size, difficulty)

    def get_puzzle_info(self):
        print(f"Available size: {list(SIZE_URL.keys())}")
        size = int(input(f"Choice: "))
        if size not in SIZE_URL.keys():
            raise KeyError()

        difficulty = None
        if size <= 20:
            print(f"Available difficulty: {list(SIZE_URL[size].keys())}")
            difficulty = input(f"Choice: ")
            if difficulty not in SIZE_URL[size].keys():
                raise KeyError()

        return size, difficulty

    def get_parameters(self, size):
        default_parameters = {
            "hba": {
                "C": 2,
                "beta": 6,
                "N": 50,
                "D": size ** 2,
                "lb": 0,
                "ub": 1,
                "t_max": 1000,
                "count": 67,  # Percentage of N
                "k": 0.2  # Percentage of t_max
            },
            "q_learning": {
                "reward": [-1, 1],
                "alpha": 0.1,
                "gamma": 0.6,
                "eps": 0.6,
                "chi": 0.2
            },
            "obj_function_weight": [0.5, 0.5, 0, 0, 0]
        }

        print("---Configure parameters for GPA---")
        print("Each parameter's default value is showed in this format: <parameter>(<default value>)")
        N = int(input(f"{'N':5}({default_parameters['hba']['N']:4}), {'value range: 1-infinity(integer)':35} | Choice: "))
        t_max = int(input(f"{'t_max':5}({default_parameters['hba']['t_max']:4}), {'value range: 1-infinity(integer)':35} | Choice: "))
        count = int(input(f"{'count':5}({default_parameters['hba']['count']:4}), {'value range: 0-100(float)':35} | Choice: "))
        k = float(input(f"{'k':5}({default_parameters['hba']['k']:4}), {'value range: 0-100(float)':35} | Choice: "))
        alpha = float(input(f"{'alpha':5}({default_parameters['q_learning']['alpha']:4}), {'value range: 0-1(float)':35} | Choice: "))
        gamma = float(input(f"{'gamma':5}({default_parameters['q_learning']['gamma']:4}), {'value range: 0-1(float)':35} | Choice: "))
        eps = float(input(f"{'eps':5}({default_parameters['q_learning']['eps']:4}), {'value range: 0-1(float)':35} | Choice: "))
        chi = float(input(f"{'chi':5}({default_parameters['q_learning']['chi']:4}), {'value range: 0-1(float), eps+chi<=1':35} | Choice: "))
        obj_func_weight = []
        for i in range(len(default_parameters['obj_function_weight'])):
            weight = input(f"objective function weight f{i + 1}({default_parameters['obj_function_weight'][i]:3}), value range: 0-1(float) | Choice: ")
            obj_func_weight.append(float(weight))

        parameters = {
            "hba": {
                "C": 2,
                "beta": 6,
                "N": N,
                "D": size ** 2,
                "lb": 0,
                "ub": 1,
                "t_max": t_max,
                "count": np.floor(N * count / 100).astype(int),
                "k": np.floor(t_max * k / 100).astype(int)
            },
            "q_learning": {
                "reward": [-1, 1],
                "alpha": alpha,
                "gamma": gamma,
                "eps": eps,
                "chi": chi
            },
            "obj_function_weight": obj_func_weight
        }
        return parameters


main = Main()
main.run()
