import pygame as py

from src import utils


class Tilemap:

    def __init__(self, filepath: str, cs: int):
        obj = utils.load_json(filepath)
        self.cs = cs
        self.width = obj["width"]
        self.height = obj["height"]
        self.tiles = obj["tiles"]
        self.pathable = obj["pathable"]
        self.tileset_filename = obj["tileset_filename"]
        self.tileset: [py.Surface] = self.load_tiles()
        self.fill_surf = self.tileset[self.tiles[0][0]]

    def surface_at(self, p: (int, int)) -> py.Surface:
        idx = self.tiles[p[1]][p[0]]
        return self.tileset[idx]

    def pathable_at(self, p: (int, int)):
        return self.pathable[p[1]][p[0]]

    def is_in_bounds(self, p: (int, int)):
        return 0 <= p[0] < self.width and 0 <= p[1] < self.height

    def load_tiles(self) -> list[py.Surface]:
        result = []
        obj = utils.load_json("resources/maps/ts/" + self.tileset_filename)
        im = py.image.load("resources/maps/images/" + obj['png_name'])
        width, height = obj['width'], obj['height']
        size = im.get_width() / width

        for i in range(width * height):
            x, y = int(i % width), int(i / width)
            rect = py.Rect(x * size, y * size, size, size)
            surf = im.subsurface(rect)
            scaled = py.transform.scale(surf, (self.cs, self.cs))
            result.append(scaled)

        return result
