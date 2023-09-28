import pygame as py

from models.tilemaps.tilemap import Tilemap
from src.models.components.renderable_c import *
from src.models.components.trigger_c import *
from src.models.entities.entity import Entity
from src.models.entities.player import Player

MAP_SIZE = 21
CELL_SIZE = 40
DIMS = MAP_SIZE * CELL_SIZE, MAP_SIZE * CELL_SIZE

COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)


class Game:

    def __init__(self):
        self.screen: py.Surface = py.display.set_mode(DIMS)
        self.running: bool = True
        self.cam: [int, int] = [0, 0]
        self.tm: Tilemap = Tilemap("resources/maps/tm/start.json", CELL_SIZE)
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
        for y in range(MAP_SIZE):
            for x in range(MAP_SIZE):
                p = self.map_to_cam_pos((x, y))
                rect = self.rect_from_pos((x, y))
                if self.tm.is_in_bounds(p):
                    surface = self.tm.surface_at(p)
                    self.screen.blit(surface, rect)
                else:
                    self.screen.blit(self.tm.fill_surf, rect)

    def render(self):
        self.screen.fill(COLOR_WHITE)
        self.render_map()
        r = self.player.get_component_by_key(RENDER_COMPONENT_KEY)
        xy = self.player.xy()[0] - self.cam[0], self.player.xy()[1] - self.cam[1]
        # xy = self.map_to_cam_pos(r.xy())
        rect = py.Rect(abs(xy[0] * CELL_SIZE), abs(xy[1] * CELL_SIZE), CELL_SIZE, CELL_SIZE)
        self.screen.blit(r.get_renderable(), rect)
        py.display.flip()

    def handle_input(self):
        for event in py.event.get():
            if event.type == py.QUIT:
                self.running = False
            if event.type == py.KEYDOWN:
                x, y = self.player.xy()
                if event.key == py.K_s:
                    if self.tm.pathable_at((x, y + 1)):
                        self.player.pos[1] += 1
                    r.direction = DIRECTION_SOUTH
                    r.next_frame()
                elif event.key == py.K_a:
                    if self.tm.pathable_at((x - 1, y)):
                        self.player.pos[0] -= 1
                    r.direction = DIRECTION_WEST
                    r.next_frame()
                elif event.key == py.K_d:
                    if self.tm.pathable_at((x + 1, y)):
                        self.player.pos[0] += 1
                    r.direction = DIRECTION_EAST
                    r.next_frame()
                elif event.key == py.K_w:
                    if self.tm.pathable_at((x, y - 1)):
                        self.player.pos[1] -= 1
                    r.direction = DIRECTION_NORTH
                    r.next_frame()

                self.center_on_pos(self.player.pos)

    def try_move_player(self, pos: (int, int), direction: int):
        r: RenderableComponent = self.player.get_component_by_key(RENDER_COMPONENT_KEY)
        entity = self.entity_at(pos)
        if entity:
            trigger = entity.get_componenet_by_key(TRIGGER_COMPONENT_KEY)
            if trigger and trigger.type == TRIGGER_MOVE_TILEMAPS:
                self.move_tilemap(trigger.payload)
                return
        if self.tm.pathable_at(pos):
            self.player.pos = list(pos)
        r.direction = direction
        r.next_frame()

    def move_tilemap(self, payload: {}):
        self.tm = Tilemap(payload["target_map"])
        self.player.pos = payload["pos"]

    def entity_at(self, pos: (int, int)) -> Entity or None:
        for e in self.entities:
            if e.collides(pos):
                return e
        return None

    def center_on_pos(self, p: (int, int)):
        self.cam[0] = p[0] - int(MAP_SIZE / 2)
        self.cam[1] = p[1] - int(MAP_SIZE / 2)

    def rect_from_pos(self, p: (int, int)) -> py.Rect:
        return py.Rect(p[0] * self.tm.cs, p[1] * self.tm.cs, self.tm.cs, self.tm.cs)

    def map_to_cam_pos(self, p: (int, int)):
        return p[0] + self.cam[0], p[1] + self.cam[1]

    def generate_test(self):
        # make test player
        self.player = Player(0, "player", [7, 7], False)
        a = Animation("characters.png", (0, 0), 3, 4, 32, CELL_SIZE)
        r = RenderableComponent(1, None, DIRECTION_NORTH, a)
        self.player.add_component(r)
        self.center_on_pos(self.player.xy())

        # make test stair
        ent = Entity(4, "move_tilemaps", [11, 9], True)
        t = TriggerComponent(2, TRIGGER_MOVE_TILEMAPS, {"target_map": "new.json", "pos": [10, 10]})
        r = RenderableComponent(3, None, DIRECTION_NORTH, a)
        ent.add_component(t)
        ent.add_component(r)
        self.entities.append(ent)
