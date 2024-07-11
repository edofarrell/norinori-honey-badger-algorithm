class Region:
    def __init__(self, id):
        self.id = id
        self.cells = []
        self.shaded_cells = []
        self.available_cells = []

    def add_cell(self, cell):
        self.cells.append(cell)
        self.available_cells.append(cell)

    def shade_cell(self, cell):
        if not cell.is_shaded:
            if cell.is_shaded is None:
                self.available_cells.remove(cell)
            cell.is_shaded = True
            self.shaded_cells.append(cell)

    def cross_cell(self, cell):
        if cell.is_shaded is None:
            self.available_cells.remove(cell)
        elif cell.is_shaded:
            self.shaded_cells.remove(cell)
        cell.is_shaded = False

    def empty_cell(self, cell):
        if cell.is_shaded is not None:
            if cell.is_shaded:
                self.shaded_cells.remove(cell)
            cell.is_shaded = None
            self.available_cells.append(cell)

    def is_invalid(self):
        if len(self.shaded_cells) < 2:
            cells_to_shade = 2 - len(self.shaded_cells)
            if len(self.available_cells) < cells_to_shade:
                return True
        return False
