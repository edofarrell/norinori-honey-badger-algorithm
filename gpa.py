from collections import Counter
from copy import copy
from queue import Queue
import numpy as np
from hba import HBA

DIRECTION = [
    [0, -1],  # Left
    [0, 1],   # Right
    [-1, 0],  # Top
    [1, 0]    # Bottom
]

class GPA:
    def __init__(self, puzzle, parameters):
        self.puzzle = puzzle
        self.parameters = parameters

    def solve(self):
        self._preprocess()
        preprocessed_cells = [cell for row in self.puzzle.get_solution() for cell in row]
        preprocessed_count = 0
        for cell in preprocessed_cells:
            if cell is not None:
                preprocessed_count += 1
        preprocessed_fitness = self.objective_function([0 if cell is None else cell for cell in preprocessed_cells])

        hba = HBA(preprocessed_cells, self.parameters, self.objective_function)
        x_prey, f_prey, t = hba.solve()

        return x_prey, f_prey, preprocessed_count, t, preprocessed_fitness

    '''
        @params input: 1-dimensional array of float
    '''
    def objective_function(self, input):
        input = np.array(input)
        input = self.transfer_function(input)
        self.puzzle.input_solution(input)

        f1 = f2 = f3 = f4 = f5 = 0
        for region in self.puzzle.regions:
            f1 += abs(2 - len(region.shaded_cells))
            if len(region.shaded_cells) < 2:
                f3 += len(region.cells) - len(region.shaded_cells) - len(region.available_cells)
            if region.is_invalid():
                f5 += len(self.puzzle.get_adjacent_regions(region)) + len(region.cells) - len(
                    region.shaded_cells) - len(region.available_cells)

        for i in range(self.puzzle.size):
            for j in range(self.puzzle.size):
                cell = self.puzzle.cells[i][j]
                if cell.connected_shaded_squares is not None:
                    f2 += abs(2 - len(cell.connected_shaded_squares))
                if self.puzzle.is_cell_invalid(cell):
                    region = self.puzzle.regions[cell.region_id]
                    f4 += len(self.puzzle.get_adjacent_regions(region)) + len(region.cells) - len(
                        region.shaded_cells) - len(region.available_cells)

        weight = self.parameters["obj_function_weight"]
        return f1 * weight[0] + f2 * weight[1] + f3 * weight[2] + f4 * weight[3] + f5 * weight[4]

    '''
        @params input: 1-dimensional array of float
        @return input: 2-dimensional array of integer
    '''
    def transfer_function(self, input):
        return np.round(input).reshape((self.puzzle.size, self.puzzle.size)).astype(int)

    def _preprocess(self):
        queue = Queue()
        for region in self.puzzle.regions:
            if len(region.available_cells) <= 3:
                queue.put(region)

        while not queue.empty():
            region = queue.get()

            # Shade fixed cells (1st pattern)
            if len(region.available_cells) == 2 - len(region.shaded_cells):
                available_cells = copy(region.available_cells)
                for cell in available_cells:
                    self.puzzle.shade_cell(cell)
                    self.puzzle.update_connected_shaded_squares(cell)

            shaded_cells = copy(region.shaded_cells)
            for cell in shaded_cells:
                # Domino, put x's around it
                if len(cell.connected_shaded_squares) == 2:
                    self._cross_cells_around_domino(cell.connected_shaded_squares, queue)

                # Single shaded square
                elif len(cell.connected_shaded_squares) == 1:
                    available_adjacent_cells = self.puzzle.get_available_adjacent_cells(cell)

                    # Shading adjacent cell leads to invalid board (5th pattern)
                    for adj_cell in copy(available_adjacent_cells):
                        if adj_cell.is_shaded is None and len(self.puzzle.get_shaded_adjacent_cells(adj_cell)) > 1:
                            self.puzzle.cross_cell(adj_cell)
                            available_adjacent_cells.remove(adj_cell)
                            curr_region = self.puzzle.regions[adj_cell.region_id]
                            if curr_region not in list(queue.queue) and len(curr_region.shaded_cells) != 2 and len(curr_region.available_cells) <= 3:
                                queue.put(curr_region)

                    # Two available adjacent cells (2nd pattern)
                    if len(available_adjacent_cells) == 2:
                        self._cross_diagonal(cell, available_adjacent_cells, queue)

                    # One available adjacent cells (3rd pattern)
                    if len(available_adjacent_cells) == 1:
                        available_cell = available_adjacent_cells[0]
                        self.puzzle.shade_cell(available_cell)
                        self.puzzle.update_connected_shaded_squares(available_cell)
                        self._cross_cells_around_domino(available_cell.connected_shaded_squares, queue)

            # L-shaped region (4th pattern)
            if self._is_region_l(region):
                row_counts = Counter(cell.row for cell in region.available_cells)
                col_counts = Counter(cell.col for cell in region.available_cells)
                least_frequent_row = min(row_counts, key=row_counts.get)
                least_frequent_col = min(col_counts, key=col_counts.get)
                cell_to_cross = self.puzzle.cells[least_frequent_row][least_frequent_col]
                if cell_to_cross.is_shaded is None:
                    self.puzzle.cross_cell(cell_to_cross)
                    curr_region = self.puzzle.regions[cell_to_cross.region_id]
                    if curr_region not in list(queue.queue) and len(curr_region.shaded_cells) != 2 and len(curr_region.available_cells) <= 3:
                        queue.put(curr_region)

            if queue.empty():
                for region in self.puzzle.regions:
                    copy_available_cells = copy(region.available_cells)

                    # Invalid cells
                    for cell in copy_available_cells:
                        available_adjacent_cells = self.puzzle.get_available_adjacent_cells(cell)
                        if len(available_adjacent_cells) == 0:
                            self.puzzle.cross_cell(cell)
                            curr_region = self.puzzle.regions[cell.region_id]
                            if curr_region not in list(queue.queue) and len(curr_region.shaded_cells) != 2 and len(curr_region.available_cells) <= 3:
                                queue.put(curr_region)

                    # Completed region
                    if len(region.shaded_cells) == 2:
                        for cell in copy(region.available_cells):
                            self.puzzle.cross_cell(cell)
                            available_adjacent_cells = self.puzzle.get_available_adjacent_cells(cell)
                            for adj_cell in available_adjacent_cells:
                                adj_region = self.puzzle.regions[adj_cell.region_id]
                                if adj_region.id != cell.region_id and adj_region not in list(queue.queue) and len(
                                        adj_region.shaded_cells) != 2:
                                    queue.put(adj_region)

                    # Cells that can't cross regions for region with a single shaded square (6th pattern)
                    if len(region.shaded_cells) == 1:
                        available_cells = copy(region.available_cells)
                        for cell in available_cells:
                            adjacent_cells = self.puzzle.get_adjacent_cells(cell)
                            can_cross = False
                            for adj_cell in adjacent_cells:
                                if adj_cell.region_id != cell.region_id and adj_cell.is_shaded != False:
                                    can_cross = True
                            if not can_cross:
                                self.puzzle.cross_cell(cell)
                                curr_region = self.puzzle.regions[cell.region_id]
                                if curr_region not in list(queue.queue) and len(curr_region.shaded_cells) != 2 and len(curr_region.available_cells) <= 3:
                                    queue.put(curr_region)

                for region in self.puzzle.regions:
                    # Add region with fixed cells to be processed
                    if len(region.shaded_cells) < 2 and len(region.available_cells) == 2 - len(
                            region.shaded_cells) and region not in list(queue.queue):
                        queue.put(region)
                        continue
                    for cell in copy(region.shaded_cells):
                        available_adjacent_cells = self.puzzle.get_available_adjacent_cells(cell)
                        if len(cell.connected_shaded_squares) == 1:
                            # One available adjacent cells (3rd pattern)
                            if len(available_adjacent_cells) == 1 and region not in list(queue.queue):
                                queue.put(region)
                                continue
                            # Two available adjacent cells (2nd pattern)
                            elif len(available_adjacent_cells) == 2:
                                self._cross_diagonal(cell, available_adjacent_cells, queue)

    ''' 2nd pattern '''
    def _cross_diagonal(self, cell, available_adjacent_cells, queue):
        vertical = None
        horizontal = None
        for adj_cell in available_adjacent_cells:
            if adj_cell.row > cell.row:
                vertical = 1
            elif adj_cell.row < cell.row:
                vertical = -1

            if adj_cell.col > cell.col:
                horizontal = 1
            elif adj_cell.col < cell.col:
                horizontal = -1

        if vertical is not None and horizontal is not None:
            cell_to_cross = self.puzzle.cells[cell.row + vertical][cell.col + horizontal]
            if cell_to_cross.is_shaded is None:
                self.puzzle.cross_cell(cell_to_cross)
                curr_region = self.puzzle.regions[cell_to_cross.region_id]
                if curr_region not in list(queue.queue) and len(curr_region.shaded_cells) != 2 and len(
                        curr_region.available_cells) <= 3:
                    queue.put(curr_region)

    def _cross_cells_around_domino(self, domino, queue=None):
        for cell in domino:
            for direction in DIRECTION:
                row = cell.row + direction[0]
                col = cell.col + direction[1]
                cell_is_valid = row >= 0 and row < self.puzzle.size and col >= 0 and col < self.puzzle.size
                if cell_is_valid:
                    adjacent_cell = self.puzzle.cells[row][col]
                    if adjacent_cell not in domino and adjacent_cell.is_shaded is None:
                        self.puzzle.cross_cell(adjacent_cell)
                        curr_region = self.puzzle.regions[adjacent_cell.region_id]
                        if queue and curr_region.id != cell.region_id and curr_region not in list(queue.queue):
                            queue.put(curr_region)

    ''' 4th pattern, check for the middle cell '''
    def _is_region_l(self, region):
        if len(region.available_cells) == 3 and len(region.shaded_cells) == 0:
            for cell in region.available_cells:
                cells = copy(region.available_cells)
                cells.remove(cell)
                vertical = (cells[0].col == cell.col and abs(cells[0].row - cell.row) == 1) or (
                            cells[1].col == cell.col and abs(cells[1].row - cell.row) == 1)
                horizontal = (cells[0].row == cell.row and abs(cells[0].col - cell.col) == 1) or (
                            cells[1].row == cell.row and abs(cells[1].col - cell.col) == 1)
                if vertical and horizontal:
                    return True
        return False
