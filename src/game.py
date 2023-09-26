import pygame as py

from models.tilemaps.tilemap import Tilemap
from src.models.components.renderable_c import *
from src.models.entities.player import Player

MAP_SIZE = 31
CELL_SIZE = 32
DIMS = MAP_SIZE * CELL_SIZE, MAP_SIZE * CELL_SIZE

COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)


class Game:

    def __init__(self):
        self.screen: py.Surface = py.display.set_mode(DIMS)
        self.running: bool = True
        self.cam: [int, int] = [0, 0]
        self.tm: Tilemap = Tilemap("resources/maps/tm/start.json", 32)
        self.entities = []
        self.player: Player = None
        self.center_on_pos((10, 10))
        self.generate_test()
        self.loop()

    def loop(self):
        while self.running:
            self.render()
            self.handle_input()

    def render_map(self):
        for i in range(MAP_SIZE * MAP_SIZE):
            x, y = int(i % MAP_SIZE), int(i / MAP_SIZE)
            p = self.map_to_cam_pos((x, y))
            rect = self.rect_from_pos((x, y))
            if self.tm.is_in_bounds(p):
                t = self.tm.tile_at(p)
                self.screen.blit(t.surface, rect)
            else:
                self.screen.blit(self.tm.fill_surf, rect)

    def render(self):
        self.screen.fill(COLOR_WHITE)
        self.render_map()
        r = self.player.get_component_by_key(RENDER_COMPONENT_KEY)
        self.screen.blit(r.getRenderable(), py.Rect(self.map_to_cam_pos((r.x, r.y)), CELL_SIZE, CELL_SIZE))
        py.display.flip()

    def handle_input(self):
        for event in py.event.get():
            if event.type == py.QUIT:
                self.running = False

    def center_on_pos(self, p: (int, int)):
        self.cam[0] = p[0] - int(MAP_SIZE / 2)
        self.cam[1] = p[1] - int(MAP_SIZE / 2)

    def rect_from_pos(self, p: (int, int)) -> py.Rect:
        return py.Rect(p[0] * self.tm.cs, p[1] * self.tm.cs, self.tm.cs, self.tm.cs)

    def map_to_cam_pos(self, p: (int, int)):
        return p[0] + self.cam[0], p[1] + self.cam[1]

    def generate_test(self):
        self.player = Player(0, "player")
        a = Animation("characters.png", 0, 3, 4)
        r = RenderableComponent(1, None, 10, 10, DIRECTION_WEST, a)
        self.player.add_component(r)
        self.center_on_pos((r.x, r.y))
