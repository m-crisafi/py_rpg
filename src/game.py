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
        self.save_file = "one"
        self.current_tilemap = "start.json"
        self.tm: Tilemap = Tilemap("resources/maps/tm/" + self.current_tilemap, CELL_SIZE)
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
                    self.try_move_player((x, y + 1), DIRECTION_SOUTH)
                elif event.key == py.K_a:
                    self.try_move_player((x - 1, y), DIRECTION_WEST)
                elif event.key == py.K_d:
                    self.try_move_player((x + 1, y), DIRECTION_EAST)
                elif event.key == py.K_w:
                    self.try_move_player((x, y - 1), DIRECTION_NORTH)
                elif event.key == py.K_p:
                    self.save_player()

    def try_move_player(self, pos: (int, int), direction: int):
        can_move = True
        r: RenderableComponent = self.player.get_component_by_key(RENDER_COMPONENT_KEY)
        entity = self.entity_at(pos)
        if entity:
            if entity.pathable:
                trigger = entity.get_component_by_key(TRIGGER_COMPONENT_KEY)
                if trigger and trigger.type == TRIGGER_MOVE_TILEMAPS:
                    self.move_tilemap(trigger.payload)
                    return
            else:
                can_move = False
        if self.tm.pathable_at(pos) and can_move:
            self.player.pos = list(pos)
        r.direction = direction
        r.next_frame()
        self.center_on_player()

    def move_tilemap(self, payload: {}):
        self.save_tilemap()
        self.current_tilemap = payload["target_map"]
        self.tm = Tilemap("resources/maps/tm/" + self.current_tilemap, CELL_SIZE)
        self.player.pos = payload["pos"]
        self.entities = []
        self.center_on_pos(self.player.xy())

    def save_tilemap(self):
        j = {
            "entities": [e.to_json() for e in self.entities],
            "tilemap_filename": self.current_tilemap
        }
        with open("saves/%s/data/%s" % (self.save_file, self.current_tilemap), 'w') as f:
            json.dump(j, f)

    def save_player(self):
        j = {
            "current_tilemap": self.current_tilemap,
            "entity": self.player.to_json()
        }
        with open("saves/%s/player.json" % self.save_file, 'w') as f:
            json.dump(j, f)

    def entity_at(self, pos: (int, int)) -> Entity or None:
        for e in self.entities:
            if e.collides(pos):
                return e
        return None

    def center_on_player(self):
        return self.center_on_pos(self.player.xy())

    def center_on_pos(self, p: (int, int)):
        self.cam[0] = p[0] - int(MAP_SIZE / 2)
        self.cam[1] = p[1] - int(MAP_SIZE / 2)

    def rect_from_pos(self, p: (int, int)) -> py.Rect:
        return py.Rect(p[0] * self.tm.cs, p[1] * self.tm.cs, self.tm.cs, self.tm.cs)

    def map_to_cam_pos(self, p: (int, int)):
        return p[0] + self.cam[0], p[1] + self.cam[1]

    def generate_test(self):
        # make test player
        self.player = Player(0, "player", [7, 7])
        a = Animation("characters.png", (0, 0), 3, 4, 32, CELL_SIZE)
        r = RenderableComponent(1, None, DIRECTION_NORTH, a)
        self.player.add_component(r)
        self.center_on_pos(self.player.xy())
