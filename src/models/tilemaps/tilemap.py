import pygame as py

from src import utils


class Tile:

    def __init__(self, surface: py.Surface, pathable: bool):
        self.surface = surface
        self.pathable = pathable


class Tilemap:

    def __init__(self, filepath: str, cs: int):
        obj = utils.load_json(filepath)
        self.cs = cs
        self.width = obj["width"]
        self.height = obj["height"]
        self.tiles = obj["tiles"]
        self.tileset = self.load_tiles(obj["tileset_filename"])

    def tile_at(self, p: (int, int)) -> Tile:
        idx = self.tiles[p[1]][p[0]]
        return self.tileset[idx]

    def is_in_bounds(self, p: (int, int)):
        return 0 <= p[0] < self.width and 0 <= p[1] < self.height

    def load_tiles(self, tileset_filepath: str) -> list[Tile]:
        result = []
        obj = utils.load_json("resources/maps/ts/" + tileset_filepath)
        im = py.image.load("resources/maps/images/" + obj['png_name'])
        width, height = obj['width'], obj['height']
        size = im.get_width() / width

        for i in range(width * height):
            x, y = int(i % width), int(i / width)
            rect = py.Rect(x * size, y * size, size, size)
            surf = im.subsurface(rect)
            scaled = py.transform.scale(surf, (self.cs, self.cs))
            t = Tile(scaled, obj['pathable'][y][x])
            result.append(t)

        return result
