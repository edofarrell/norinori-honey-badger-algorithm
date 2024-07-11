class Cell:
    def __init__(self, row, col):
        self.row = row
        self.col = col
        self.region_id = None
        self.is_shaded = None
        self.connected_shaded_squares = None
