import copy

import pygame as py
import json


class Tilemap:

    def __init__(self, pos: (int, int), filename: str, width: int = -1, height: int = -1, cell_size: int = -1):
        self.filename = filename
        self.tiles = []
        self.prev_states = []
        self.passable_layer = []
        self.selected_start = None
        self.selected_end = None

        if width != -1:
            self.width = width
            self.height = height
            self.tiles = [[0 for x in range(self.width)] for y in range(self.height)]
            self.passable_layer = [[True for x in range(self.width)] for y in range(self.height)]
            self.cell_size = cell_size
        else:
            f = open(self.filename)
            j = json.load(f)
            f.close()
            self.tiles = j["tiles"]
            self.passable_layer = j["passable_layer"]
            self.width = j["width"]
            self.height = j["height"]
            self.cell_size = j["cell_size"]

        self.rect = py.Rect(pos[0], pos[1], self.cell_size * self.width, self.cell_size * self.height)

    def save(self, tileset_filename: str):
        to_write = {
            "filename": self.filename,
            "tileset_filename": tileset_filename,
            "width": self.width,
            "height": self.height,
            "cell_size": self.cell_size,
            "tiles": self.tiles,
            "passable_layer": self.passable_layer
        }
        f = open(self.filename, 'w')
        json.dump(to_write, f)
        f.close()

    def set(self, x: int, y: int, value: int):
        self.tiles[y][x] = value

    def mouse_to_xy(self, pos: (int, int)) -> (int, int):
        x = int((pos[0] - self.rect.x) / self.cell_size)
        y = int((pos[1] - self.rect.y) / self.cell_size)
        return x, y

    def pop_prev(self):
        if len(self.prev_states) > 0:
            idx = len(self.prev_states) - 1
            self.tiles = self.prev_states.pop(idx)

    def push_prev(self):
        self.prev_states.append(copy.deepcopy(self.tiles))

    def get_sub_tiles(self, pos: (int, int), width: int, height: int) -> [[py.Surface]]:
        result = []
        for j in range(pos[1], pos[1] + height):
            line = []
            for i in range(pos[0], pos[0] + width):
                line.append(self.tiles[j][i])
            result.append(line)
        return result

    def set_rect_centered_on(self, pos: (int, int)):
        self.rect.x = pos[0] - self.rect.width / 2
        self.rect.y = pos[1] - self.rect.height / 2

    def selected_pos(self) -> (int, int, int, int):
        return self.selected_start[0], \
               self.selected_start[1], \
               self.selected_end[0], \
               self.selected_end[1]

    def selected_to_pos(self) -> ((int, int), (int, int)):
        lx, ly, rx, ry = self.selected_pos()

        if lx <= rx and ly <= ry:
            return (lx, ly), (rx, ry)
        elif lx <= rx and ly > ry:
            return (lx, ry), (rx, ly)
        elif lx > rx and ly <= ry:
            return (rx, ly), (lx, ry)
        else:
            return (rx, ry), (lx, ly)

    def selected_to_rect(self) -> py.Rect:
        pos = self.selected_pos()
        lx, ly, rx, ry = \
                pos[0] * self.cell_size + self.rect.x, \
                pos[1] * self.cell_size + self.rect.y, \
                pos[2] * self.cell_size + self.rect.x, \
                pos[3] * self.cell_size + self.rect.y, \

        if lx <= rx and ly <= ry:
            return py.Rect(lx, ly, rx - lx, ry - ly)
        elif lx <= rx and ly > ry:
            return py.Rect(lx, ry, rx - lx, ly - ry)
        elif lx > rx and ly <= ry:
            return py.Rect(rx, ly, lx - rx, ry - ly)
        else:
            return py.Rect(rx, ry, lx - rx, ly - ry)