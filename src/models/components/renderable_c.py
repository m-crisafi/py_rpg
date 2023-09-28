import json

import pygame as py

from src import utils
from src.models.components.component import Component

RENDER_COMPONENT_KEY = "render_c"
DIRECTION_SOUTH = 0
DIRECTION_WEST = 1
DIRECTION_EAST = 2
DIRECTION_NORTH = 3


class Animation:

    def __init__(self, filepath: str, idx_start: (int, int), width: int, height: int, cell_w: int, scaled_w: int):
        self.filepath = filepath
        self.idx_start = idx_start
        self.width = width
        self.height = height
        self.frames = utils.sprite_from_sheet("resources/sprites/" + self.filepath, self.idx_start, self.width, self.height, cell_w, scaled_w)
        self.curr_idx = 0

    def next_frame(self, direction: int) -> py.Surface:
        frame = self.frames[direction][self.curr_idx]
        self.curr_idx += 1
        if self.curr_idx == len(self.frames[0]):
            self.curr_idx = 0
        return frame

    def to_json(self) -> {}:
        return {
            "filepath:": self.filepath,
            "idx_start:": self.idx_start,
            "width:": self.width,
            "height:": self.height,
            "curr_idx:": self.curr_idx,
        }


class RenderableComponent(Component):

    def __init__(self, id: int, surface: py.Surface, direction: int, animation: Animation = None):
        Component.__init__(self, id, RENDER_COMPONENT_KEY)
        self.surface: py.Surface = surface
        self.direction = direction
        self.animation = animation
        if animation:
            self.surface = self.animation.next_frame(direction)

    def to_json(self):
        result = Component.to_json(self)
        result["direction:"] = self.direction
        if self.animation:
            result['animation'] = self.animation
        return result

    def next_frame(self):
        if self.animation:
            self.surface = self.animation.next_frame(self.direction)

    def get_renderable(self) -> py.Surface:
        return self.surface
