import pygame as py

from src.models.components.component import Component

RENDER_COMPONENT_KEY = "r_component"
DIRECTION_NORTH = 0
DIRECTION_SOUTH = 1
DIRECTION_EAST = 2
DIRECTION_WEST = 3


class RenderComponent(Component):

    def __init__(self, id: int, surface: py.Surface, x: int, y: int, direction: int):
        Component.__init__(self, id, RENDER_COMPONENT_KEY)
        self.x: int = x
        self.y: int = y
        self.surface: py.Surface = surface
        self.direction = direction
