import pygame as py


class Tileset:

    def __init__(self, filename: str, cell_size: int, pos: (int, int)):
        self.filename = filename
        self.tiles = []
        self.cell_size = cell_size
        self.width = 0
        self.height = 0
        self.selected_tile = None
        self.load_tiles()
        self.rect = py.Rect(pos[0], pos[1], cell_size * self.width, cell_size * self.height)

    def tile_at(self, xy: tuple[int, int]) -> py.Surface:
        return self.tiles[xy[1]][xy[0]]

    def get_selected_tile(self) -> py.Surface:
        return self.tile_at(self.selected_tile)

    def select_tile(self, pos: tuple[int, int]):
        self.selected_tile = pos

    def deselect(self):
        self.selected_tile = None

    def tile_by_flattened_idx(self, idx: int) -> py.Surface:
        x, y = int(idx % self.width), int(idx / self.width)
        return self.tiles[y][x]

    def selected_to_absolute(self):
        return self.selected_tile[1] * self.width + self.selected_tile[0]

    def mouse_to_xy(self, pos: (int, int)) -> (int, int):
        x = int((pos[0] - self.rect.x) / self.cell_size)
        y = int((pos[1] - self.rect.y) / self.cell_size)
        return x, y

    def load_tiles(self):
        self.tiles = []
        im = py.image.load(self.filename)
        self.width = int(im.get_width() / self.cell_size)
        self.height = int(im.get_height() / self.cell_size)
        for y in range(self.height):
            line = []
            for x in range(self.width):
                rect = py.Rect(x * self.cell_size, y * self.cell_size, self.cell_size, self.cell_size)
                surface = im.subsurface(rect)
                line.append(surface)
            self.tiles.append(line)
