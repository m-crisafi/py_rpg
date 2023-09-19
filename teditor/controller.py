from PIL import Image
import pygame as py

from tilemap import Tilemap
from tileset import *

SCREEN_WIDTH = 1500
SCREEN_HEIGHT = 1000
CELL_SIZE = 20

TILEMAPS_FILEPATH = "tilemaps/"
TILESETS_FILEPATH = "tilesets/"
BG_COLOR = (255, 255, 255)
BLACK = (0, 0, 0)
SELECTED_COLOR = (0, 255, 0)
MAP_COLOR = (190, 190, 190)
PADDING = 20

TILESET_START = (20, 20)

LEFT_CLICK = 0
MIDDLE_CLICK = 1
RIGHT_CLICK = 2


class Controller:

    def __init__(self):
        self.screen = py.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.tileset = Tileset(TILESETS_FILEPATH + "castle.png", 20, TILESET_START)
        pos = (self.tileset.rect.x + self.tileset.rect.width + PADDING, TILESET_START[1])
        self.map_rect = py.Rect(pos[0], pos[1], self.screen.get_width() - pos[0] - PADDING, self.screen.get_height() - pos[1] - PADDING)
        self.tilemap = Tilemap(pos, TILEMAPS_FILEPATH + "start.json")
        self.tilemap.set_rect_centered_on((self.map_rect.x + self.map_rect.width / 2, self.map_rect.y + self.map_rect.height / 2))

        self.copy_buffer = None
        self.running = True
        self.dragging = False
        self.selecting = False
        self.show_grid = False
        self.editing_passable = False

    def loop(self):
        while self.running:
            self.render()
            self.handle_input()

    def render(self):
        self.screen.fill(BG_COLOR)
        pos = py.mouse.get_pos()

        # draw tiles
        for y in range(self.tileset.height):
            for x in range(self.tileset.width):
                rect = py.Rect(
                    x * self.tileset.cell_size + self.tileset.rect.x,
                    y * self.tileset.cell_size + self.tileset.rect.y,
                    self.tileset.cell_size,
                    self.tileset.cell_size)
                self.screen.blit(self.tileset.tiles[y][x], rect)

        # draw tileset grid
        self.draw_grid(self.tileset.rect, self.tileset.cell_size, BLACK)

        # draw selected tileset tile
        if self.tileset.selected_tile is not None:
            rect = py.Rect(self.tileset.selected_tile[0] * self.tileset.cell_size + self.tileset.rect.x,
                           self.tileset.selected_tile[1] * self.tileset.cell_size + self.tileset.rect.y,
                           self.tileset.cell_size,
                           self.tileset.cell_size)
            py.draw.rect(self.screen, SELECTED_COLOR, rect, width=1)

        # draw background
        py.draw.rect(self.screen, MAP_COLOR, self.map_rect)
        py.draw.rect(self.screen, BLACK, self.map_rect, width=1)

        # draw whole world
        for y in range(self.tilemap.height):
            for x in range(self.tilemap.height):
                rect = py.Rect(
                    x * self.tilemap.cell_size + self.tilemap.rect.x,
                    y * self.tilemap.cell_size + self.tilemap.rect.y,
                    self.tilemap.cell_size,
                    self.tilemap.cell_size)
                idx = self.tilemap.tiles[y][x]
                xy = self.flattened_to_xy(idx, self.tileset.width)
                surf = self.tileset.tiles[xy[1]][xy[0]]
                self.screen.blit(surf, rect)

        # draw grids if true
        if self.show_grid:
            self.draw_grid(self.tilemap.rect, self.tilemap.cell_size, (190, 190, 190))

        # draw tile hover on map
        if self.mouse_collides_with_rect(pos, self.tilemap.rect) and self.tileset.selected_tile is not None:
            xy = self.tilemap.mouse_to_xy(pos)
            rect = py.Rect(xy[0] * self.tilemap.cell_size + self.tilemap.rect.x,
                           xy[1] * self.tilemap.cell_size + self.tilemap.rect.y,
                           self.tilemap.cell_size,
                           self.tilemap.cell_size)
            self.screen.blit(self.get_selected_tile(), rect)

        # draw selected tileset tiles
        if self.tilemap.selected_start is not None and self.tilemap.selected_end is not None:
            if self.mouse_collides_with_rect(pos, self.tilemap.rect):
                rect = self.tilemap.selected_to_rect()
                self.draw_grid(rect, self.tilemap.cell_size, (255, 255, 255))

        # draw copy buffer if it exists
        if self.copy_buffer is not None:
            if self.mouse_collides_with_rect(pos, self.tilemap.rect):
                xy = self.tilemap.mouse_to_xy(pos)
                for y in range(len(self.copy_buffer)):
                    for x in range(len(self.copy_buffer[0])):
                        rect = py.Rect(self.tilemap.rect.x + (xy[0] * self.tilemap.cell_size) + (x * self.tilemap.cell_size),
                                       self.tilemap.rect.y + (xy[1] * self.tilemap.cell_size) + (y * self.tilemap.cell_size),
                                       self.tilemap.cell_size,
                                       self.tilemap.cell_size)
                        idx = self.copy_buffer[y][x]
                        surf = self.tileset.tile_by_flattened_idx(idx)
                        self.screen.blit(surf, rect)
                rect = py.Rect(
                    self.tilemap.rect.x + xy[0] * self.tilemap.cell_size,
                    self.tilemap.rect.y + xy[1] * self.tilemap.cell_size,
                    len(self.copy_buffer[0]) * self.tilemap.cell_size,
                    len(self.copy_buffer) * self.tilemap.cell_size
                )
                self.draw_grid(rect, self.tilemap.cell_size, (255, 255, 255))

        # if editing passable
        if self.editing_passable:
            for y in range(self.tilemap.height):
                for x in range(self.tilemap.width):
                    if not self.tilemap.passable_layer[y][x]:
                        rect = py.Rect(x * self.tilemap.cell_size + self.tilemap.rect.x,
                                       y * self.tilemap.cell_size + self.tilemap.rect.y,
                                       self.tilemap.cell_size,
                                       self.tilemap.cell_size)
                        py.draw.rect(self.screen, (150, 150, 150), rect)

        py.display.flip()

    def draw_grid(self, rect: py.Rect, cell_size: int, color):
        py.draw.rect(self.screen, color, rect, width=1)
        for y in range(int(rect.height / cell_size)):
            start_y = y * cell_size + rect.y
            end_x = rect.x + rect.width
            py.draw.line(self.screen, color, (rect.x, start_y), (end_x, start_y), width=1)

        for x in range(int(rect.width / cell_size)):
            start_x = x * cell_size + rect.x
            end_y = rect.y + rect.height
            py.draw.line(self.screen, color, (start_x, rect.y), (start_x, end_y), width=1)

    def handle_input(self):
        for event in py.event.get():
            pos = py.mouse.get_pos()

            # event quit
            if event.type == py.QUIT:
                self.running = False

            if event.type == py.KEYDOWN:
                # grow grid on D
                if event.key == py.K_g:
                    self.show_grid = not self.show_grid

                # save map on S
                if event.key == py.K_s:
                    self.tilemap.save(self.tileset.filename)
                    print("Map saved [%s]" % self.tileset.filename)

                if event.key == py.K_LSHIFT:
                    if self.mouse_collides_with_rect(pos, self.tilemap.rect):
                        xy = self.tilemap.mouse_to_xy(pos)
                        tile_idx = self.tilemap.tiles[xy[1]][xy[0]]
                        self.tileset.selected_tile = Controller.flattened_to_xy(tile_idx, self.tileset.width)
                        self.tilemap.selector_start = None
                        self.tilemap.selected_end = None
                        self.dragging = False

                if event.key == py.K_z:
                    self.tilemap.pop_prev()

                if event.key == py.K_c:
                    if self.tilemap.selected_start is not None and self.tilemap.selected_end is not None:
                        self.tilemap.push_prev()
                        pos = self.tilemap.selected_to_pos()
                        width = pos[1][0] - pos[0][0]
                        height = pos[1][1] - pos[0][1]
                        self.copy_buffer = self.tilemap.get_sub_tiles(pos[0], width, height)
                        self.selecting = False
                        self.tilemap.selected_start = None
                        self.tilemap.selected_end = None

                if event.key == py.K_p:
                    self.editing_passable = not self.editing_passable

            if event.type == py.MOUSEBUTTONDOWN or self.dragging:

                if self.editing_passable:
                    if self.mouse_collides_with_rect(pos, self.tilemap.rect):
                        xy = self.tilemap.mouse_to_xy(pos)
                        self.tilemap.passable_layer[xy[1]][xy[0]] = not self.tilemap.passable_layer[xy[1]][xy[0]]
                    return

                # if right mouse clicked is pressed, cancel all selections
                state = py.mouse.get_pressed()
                if state[RIGHT_CLICK]:
                    self.dragging = False
                    self.tileset.selected_tile = None
                    self.tilemap.selector_start = None
                    self.tilemap.selector_end = None
                    self.selecting = False
                    self.copy_buffer = None
                    return

                # if copying
                if self.copy_buffer is not None:
                    x_len = len(self.copy_buffer[0])
                    y_len = len(self.copy_buffer)
                    if self.mouse_collides_with_rect(pos, self.tilemap.rect):
                        xy = self.tilemap.mouse_to_xy(pos)
                        self.tilemap.push_prev()
                        for y in range(y_len):
                            for x in range(x_len):
                                if 0 <= (x + xy[0]) < self.tilemap.width and 0 <= (y + xy[1]) < self.tilemap.height:
                                    self.tilemap.set(x + xy[0], y + xy[1], self.copy_buffer[y][x])
                    return

                self.dragging = True

                # if no tile is selected and dragging, set tilemap selector start
                if self.tileset.selected_tile is None and self.tilemap.selected_start is None:
                    self.tilemap.selector_start = pos

                # if mouse is over tileset, select a tile
                if self.mouse_collides_with_rect(pos, self.tileset.rect):
                    self.tileset.selected_tile = self.tileset.mouse_to_xy(pos)

                # if mouse is over tilemap
                if self.mouse_collides_with_rect(pos, self.tilemap.rect):
                    xy = self.tilemap.mouse_to_xy(pos)
                    # if a tile is selected, draw a preview
                    if self.tileset.selected_tile is not None:
                        self.tilemap.push_prev()
                        self.tilemap.set(xy[0], xy[1],
                                         self.tileset.selected_tile[1] * self.tileset.width + self.tileset.selected_tile[0])
                    elif not self.selecting:
                        self.tilemap.selected_start = xy
                        self.tilemap.selected_end = xy
                        self.selecting = True
                    elif self.selecting:
                        self.tilemap.selected_end = (xy[0] + 1, xy[1] + 1)

            if event.type == py.MOUSEBUTTONUP:
                self.dragging = False
                self.selecting = False

    def get_selected_tile(self) -> py.Surface:
        return self.tileset.tiles[self.tileset.selected_tile[1]][self.tileset.selected_tile[0]]

    @staticmethod
    def mouse_collides_with_rect(pos: tuple[int, int], rect: py.Rect) -> bool:
        return rect.x <= pos[0] < rect.x + rect.width and \
               rect.y <= pos[1] < rect.y + rect.height

    @staticmethod
    def flattened_to_xy(flat, width):
        return int(flat % width), int(flat / width)