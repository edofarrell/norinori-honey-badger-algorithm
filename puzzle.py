from copy import copy
from queue import Queue
from cell import Cell
from region import Region

DIRECTION = [
    [0, -1],
    [0, 1],
    [-1, 0],
    [1, 0]
]

class Puzzle:
    def __init__(self, size, borders):
        self.size = size
        self.cells = []
        self.regions = []
        self.borders = borders

        for i in range(size):
            row = []
            for j in range(size):
                cell = Cell(i, j)
                row.append(cell)
            self.cells.append(row)

        for i in range(size):
            for j in range(size):
                if self.cells[i][j].region_id is None:
                    self._group_region(self.cells[i][j])

    def _group_region(self, init_cell):
        region = Region(len(self.regions))
        self.regions.append(region)

        region.add_cell(init_cell)
        init_cell.region_id = region.id
        queue = Queue()
        queue.put(init_cell)

        while not queue.empty():
            cell = queue.get()
            for direction in DIRECTION:
                row = cell.row + direction[0]
                col = cell.col + direction[1]
                cell_is_valid = row >= 0 and row < self.size and col >= 0 and col < self.size
                if cell_is_valid:
                    adjacent_cell = self.cells[row][col]
                    border_type = 'vertical' if direction[0] == 0 else 'horizontal'
                    border_row = row if -1 in direction or border_type == 'vertical' else row - 1
                    border_col = col if -1 in direction or border_type == 'horizontal' else col - 1
                    if not self.borders[border_type][border_row][border_col] and adjacent_cell.region_id is None:
                        region.add_cell(adjacent_cell)
                        adjacent_cell.region_id = region.id
                        queue.put(adjacent_cell)

    def get_solution(self):
        solution = []
        for i in range(self.size):
            temp = []
            for j in range(self.size):
                if self.cells[i][j].is_shaded:
                    temp.append(1)
                elif self.cells[i][j].is_shaded == False:
                    temp.append(0)
                else:
                    temp.append(None)
            solution.append(temp)
        return solution

    def input_solution(self, solution):
        for i in range(self.size):
            for j in range(self.size):
                self.cells[i][j].connected_shaded_squares = None
                if solution[i][j] == 1:
                    self.shade_cell(self.cells[i][j])
                elif solution[i][j] == 0:
                    self.cross_cell(self.cells[i][j])
                else:
                    self.empty_cell(self.cells[i][j])

        for i in range(self.size):
            for j in range(self.size):
                if self.cells[i][j].is_shaded and self.cells[i][j].connected_shaded_squares is None:
                    self.update_connected_shaded_squares(self.cells[i][j])

    def shade_cell(self, cell):
        self.regions[cell.region_id].shade_cell(cell)

    def cross_cell(self, cell):
        self.regions[cell.region_id].cross_cell(cell)

    def empty_cell(self, cell):
        self.regions[cell.region_id].empty_cell(cell)

    def is_cell_invalid(self, cell):
        adj_cells = self.get_available_adjacent_cells(cell)
        if cell.is_shaded and len(adj_cells) == 0:
            return True
        return False

    def get_adjacent_cells(self, cell):
        result = []
        for direction in DIRECTION:
            row = cell.row + direction[0]
            col = cell.col + direction[1]
            cell_is_valid = row >= 0 and row < self.size and col >= 0 and col < self.size
            if cell_is_valid:
                result.append(self.cells[row][col])
        return result

    def get_available_adjacent_cells(self, cell):
        result = self.get_adjacent_cells(cell)
        for adj_cell in copy(result):
            if adj_cell.is_shaded == False:
                result.remove(adj_cell)
        return result

    def get_shaded_adjacent_cells(self, cell):
        result = self.get_adjacent_cells(cell)
        for adj_cell in copy(result):
            if adj_cell.is_shaded != True:
                result.remove(adj_cell)
        return result

    def update_connected_shaded_squares(self, init_cell):
        init_cell.connected_shaded_squares = []
        init_cell.connected_shaded_squares.append(init_cell)
        queue = Queue()
        queue.put(init_cell)

        while not queue.empty():
            cell = queue.get()
            for direction in DIRECTION:
                row = cell.row + direction[0]
                col = cell.col + direction[1]
                cell_is_valid = row >= 0 and row < self.size and col >= 0 and col < self.size
                if cell_is_valid:
                    adjacent_cell = self.cells[row][col]
                    if adjacent_cell.is_shaded and adjacent_cell not in init_cell.connected_shaded_squares:
                        init_cell.connected_shaded_squares.append(adjacent_cell)
                        queue.put(adjacent_cell)

        for cell in init_cell.connected_shaded_squares:
            if cell != init_cell:
                cell.connected_shaded_squares = init_cell.connected_shaded_squares

    def get_adjacent_regions(self, region):
        result = []
        for cell in region.cells:
            adj_cells = self.get_adjacent_cells(cell)
            for adj_cell in adj_cells:
                if adj_cell.region_id != region.id and adj_cell.region_id not in [region.id for region in result]:
                    result.append(self.regions[adj_cell.region_id])
        return result
