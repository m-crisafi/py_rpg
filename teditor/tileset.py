import json

import pygame as py

from src import utils


class Tile:

    def __init__(self, id: int, pathable: bool, surf: py.Surface, scaled: py.Surface):
        self.id = id
        self.pathable = pathable
        self.surf = surf
        self.scaled = scaled


class Tileset:

    def __init__(self, filename: str, cell_size: int, pos: (int, int)):
        self.filename = filename
        obj = utils.load_json("../resources/maps/ts/" + self.filename)
        self.png_name = obj['png_name']
        self.width = obj['width']
        self.height = obj['height']
        self.tiles: [Tile] = []
        self.base_size = 0
        self.cell_size = cell_size
        self.selected_tile = None
        self.load_tiles(obj['pathable'])
        self.rect = py.Rect(pos[0], pos[1], cell_size * self.width, cell_size * self.height)

    def save(self):
        to_write = {
            "png_name": self.png_name,
            "width": self.width,
            "height": self.height,
            "pathable": [[self.tiles[y][x].pathable for x in range(self.width)] for y in range(self.height)]
        }
        f = open("../resources/maps/ts/" + self.filename, 'w')
        json.dump(to_write, f)
        f.close()

    def flip_pathable(self, p: (int, int)):
        self.tile_at(p).pathable = not self.tile_at(p).pathable

    def set_pathable(self, p: (int, int), value: bool):
        self.tile_at(p).pathable = value

    def tile_at(self, xy: (int, int)) -> Tile:
        return self.tiles[xy[1]][xy[0]]

    def tile_by_flattened_idx(self, idx: int) -> Tile:
        x, y = int(idx % self.width), int(idx / self.width)
        return self.tiles[y][x]

    def get_selected_tile(self) -> Tile:
        return self.tile_at(self.selected_tile)

    def select_tile(self, p: (int, int)):
        self.selected_tile = p

    def select_tile_by_flattened_index(self, idx: int):
        self.selected_tile = int(idx % self.width), int(idx / self.width)

    def deselect(self):
        self.selected_tile = None

    def selected_to_flattened(self):
        return self.selected_tile[1] * self.width + self.selected_tile[0]

    def mouse_to_xy(self, p: (int, int)) -> (int, int):
        x = int((p[0] - self.rect.x) / self.cell_size)
        y = int((p[1] - self.rect.y) / self.cell_size)
        return x, y

    def load_tiles(self, pathable: [[bool]]):
        im = py.image.load("../resources/maps/images/" + self.png_name)
        self.base_size = im.get_width() / self.width
        for y in range(self.height):
            line = []
            for x in range(self.width):
                rect = py.Rect(x * self.base_size, y * self.base_size, self.base_size, self.base_size)
                surf = im.subsurface(rect)
                scaled = py.transform.scale(surf, (self.cell_size, self.cell_size))
                t = Tile(y * self.width + x, pathable[y][x], surf, scaled)
                line.append(t)
            self.tiles.append(line)
