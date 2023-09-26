import json

import pygame as py

from src import utils
from src.models.components.component import Component

RENDER_COMPONENT_KEY = "r_component"
DIRECTION_SOUTH = 0
DIRECTION_WEST = 1
DIRECTION_EAST = 2
DIRECTION_NORTH = 3


class Animation:

    def __init__(self, filepath: str, idx_start: (int, int), width: int, height: int):
        self.filepath = filepath
        self.idx_start = idx_start
        self.width = width
        self.height = height
        self.frames = utils.sprite_from_sheet(self.filepath, self.idx_start, self.width, self.height, s)
        self.curr_idx = 0

    def next_frame(self, direction: int) -> py.Surface:
        frame = self.frames[direction][self.curr_idx]
        self.curr_idx += 1
        if self.curr_idx > len(self.frames[0]):
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

    def __init__(self, id: int, surface: py.Surface, x: int, y: int, direction: int, animation: Animation = None):
        Component.__init__(self, id, RENDER_COMPONENT_KEY)
        self.x: int = x
        self.y: int = y
        self.surface: py.Surface = surface
        self.direction = direction
        self.animation = animation

    def to_json(self):
        result = {
            "x:": self.x,
            "y:": self.y,
            "direction:": self.direction,
            }
        if self.animation:
            result['animation'] = self.animation
        return result

    def get_renderable(self) -> py.Surface:
        if self.animation is not None:
            self.surface = self.animation.next_frame(self.direction)
        return self.surface
