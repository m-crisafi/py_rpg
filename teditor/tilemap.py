import copy
import os

import pygame as py
import json

from src import utils


class Tilemap:

    def __init__(self, filename: str, cell_size: int, width: int = -1, height: int = -1, tileset_filename: str = ""):
        self.filename = filename
        self.tiles = []
        self.pathable = []
        self.prev_states = []
        self.cell_size = cell_size
        self.selected_start = None
        self.selected_end = None

        if not os.path.exists("resources/maps/tm/" + self.filename):
            self.width = width
            self.height = height
            self.tileset_filename = tileset_filename
            self.tiles = [[0 for x in range(self.width)] for y in range(self.height)]
            self.pathable = [[True for x in range(self.width)] for y in range(self.height)]
        else:
            obj = utils.load_json("resources/maps/tm/" + self.filename)
            self.tiles = obj["tiles"]
            self.tileset_filename = obj["tileset_filename"]
            self.pathable = obj["pathable"]
            self.width = obj["width"]
            self.height = obj["height"]

        self.rect = py.Rect(0, 0, self.cell_size * self.width, self.cell_size * self.height)

    def save(self):
        to_write = {
            "tileset_filename": self.tileset_filename,
            "width": self.width,
            "height": self.height,
            "cell_size": self.cell_size,
            "tiles": self.tiles,
            "pathable": self.pathable
        }
        f = open("resources/maps/tm/" + self.filename, 'w')
        json.dump(to_write, f)
        f.close()

    def set_point(self, pos: (int, int), value: int):
        self.tiles[pos[1]][pos[0]] = value

    def set(self, x: int, y: int, value: int):
        self.tiles[y][x] = value

    def invert_pathable(self, pos: (int, int)):
        self.pathable[pos[1]][pos[0]] = not self.pathable[pos[1]][pos[0]]

    def set_pathable(self, pos: (int, int), value: bool):
        self.pathable[pos[1]][pos[0]] = value

    def deselect(self):
        self.selected_start = None
        self.selected_end = None

    def resize(self, cell_size: int):
        self.cell_size = cell_size
        self.rect.width = cell_size * self.width
        self.rect.height = cell_size * self.height

    def mouse_to_xy(self, pos: (int, int)) -> (int, int):
        x = int((pos[0] - self.rect.x) / self.cell_size)
        y = int((pos[1] - self.rect.y) / self.cell_size)
        return x, y

    def point_on_map(self, x: int, y: int):
        return 0 <= x < self.width and 0 <= y < self.height

    def pop_prev(self):
        if len(self.prev_states) > 0:
            idx = len(self.prev_states) - 1
            self.tiles = self.prev_states.pop(idx)

    def push_prev(self):
        if len(self.prev_states) > 0:
            if not self.compare_states(self.prev_states[-1], self.tiles):
                print("Pushing state")
                self.prev_states.append(copy.deepcopy(self.tiles))
            else:
                print("Ignoring state push")
        else:
            print("Pushing state")
            self.prev_states.append(copy.deepcopy(self.tiles))

    def compare_states(self, left, right) -> bool:
        for y in range(self.height):
            for x in range(self.width):
                if left[y][x] != right[y][x]:
                    return False
        return True

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
