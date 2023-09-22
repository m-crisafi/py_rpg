from datetime import date

import pygame as py

from teditor.copy_buffer import CopyBuffer
from tilemap import Tilemap
from tileset import *

PADDING = 20
SCREEN_H_MAX = 800 + PADDING * 2
SCREEN_WIDTH = 1500
SCREEN_HEIGHT = SCREEN_H_MAX
MAP_HEIGHT = SCREEN_H_MAX - PADDING * 2
MAG_VALUES = [160, 100, 80, 50, 40, 32, 25, 20, 16, 10, 8, 5]
MAG_START_IDX = 7

TILEMAPS_FILEPATH = "../resources/maps/tm/"
TILESETS_FILEPATH = "../resources/maps/ts/"
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SELECTED_COLOR = (0, 255, 0)
GRID_COLOR = (140, 140, 140)
MAP_COLOR = (190, 190, 190)
BG_COLOR = WHITE

TILESET_START = (20, 20)

LEFT_CLICK = 0
MIDDLE_CLICK = 1
RIGHT_CLICK = 2


class Controller:

    def __init__(self):
        self.screen = py.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.tileset = Tileset(TILESETS_FILEPATH + "castle.png", 20, TILESET_START)
        pos = (self.tileset.rect.x + self.tileset.rect.width + PADDING, TILESET_START[1])

        self.map_rect = py.Rect(
            pos[0],
            pos[1],
            MAP_HEIGHT,
            MAP_HEIGHT)

        self.mid_map = self.map_rect.midtop[0], self.map_rect.midleft[1]
        self.tilemap = Tilemap(pos, TILEMAPS_FILEPATH + "start.json")

        self.last_clicked_cell: (int, int) or None = None
        self.copy_buffer: CopyBuffer or None = None
        self.running = True
        self.dragging = False
        self.selecting = False
        self.show_grid = False
        self.selected_magnification = 7
        self.editing_passable = False

        self.cam_pos = [0, 0]
        self.map_size = int(MAP_HEIGHT / self.get_selected_magnification())
        self.tilemap.resize(self.get_selected_magnification())

    def loop(self):
        while self.running:
            self.render()
            self.handle_input()

    def draw_tileset(self):
        # draw tileset
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

    def render(self):
        self.screen.fill(BG_COLOR)
        pos = py.mouse.get_pos()

        self.draw_tileset()

        # draw map background
        py.draw.rect(self.screen, MAP_COLOR, self.map_rect)
        py.draw.rect(self.screen, BLACK, self.map_rect, width=1)

        # draw whole world
        for y in range(self.map_size):
            for x in range(self.map_size):
                nx, ny = self.abs_to_camera_pos((x, y))
                if self.tilemap.point_on_map(nx, ny):
                    rect = py.Rect(
                        x * self.tilemap.cell_size + self.tilemap.rect.x,
                        y * self.tilemap.cell_size + self.tilemap.rect.y,
                        self.tilemap.cell_size,
                        self.tilemap.cell_size)
                    idx = self.tilemap.tiles[ny][nx]
                    xy = self.flattened_to_xy(idx, self.tileset.width)
                    surf = self.tileset.tiles[xy[1]][xy[0]]
                    surf = py.transform.scale(surf, (self.tilemap.cell_size, self.tilemap.cell_size))
                    self.screen.blit(surf, rect)

        # draw grids if true
        if self.show_grid:
            self.draw_grid(self.map_rect, self.tilemap.cell_size, GRID_COLOR)

        # draw tile hover on map
        if self.mouse_collides_with_tilemap(pos) and self.tileset.selected_tile is not None:
            abs = self.mouse_to_xy(pos)
            rect = py.Rect(abs[0] * self.tilemap.cell_size + self.tilemap.rect.x,
                           abs[1] * self.tilemap.cell_size + self.tilemap.rect.y,
                           self.tilemap.cell_size,
                           self.tilemap.cell_size)
            surf = py.transform.scale(self.get_selected_tile(), (self.tilemap.cell_size, self.tilemap.cell_size))
            self.screen.blit(surf, rect)

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
                        rect = py.Rect(
                            self.tilemap.rect.x + (xy[0] * self.tilemap.cell_size) + (x * self.tilemap.cell_size),
                            self.tilemap.rect.y + (xy[1] * self.tilemap.cell_size) + (y * self.tilemap.cell_size),
                            self.tilemap.cell_size,
                            self.tilemap.cell_size)
                        idx = self.copy_buffer[y][x]
                        surf = self.tileset.tile_by_flattened_idx(idx)
                        surf = py.transform.scale(surf, (self.tilemap.cell_size, self.tilemap.cell_size))
                        self.screen.blit(surf, rect)
                rect = py.Rect(
                    self.tilemap.rect.x + xy[0] * self.tilemap.cell_size,
                    self.tilemap.rect.y + xy[1] * self.tilemap.cell_size,
                    len(self.copy_buffer[0]) * self.tilemap.cell_size,
                    len(self.copy_buffer) * self.tilemap.cell_size
                )
                self.draw_grid(rect, self.tilemap.cell_size, (255, 255, 255))

        py.display.flip()

    def draw_grid(self, rect: py.Rect, cell_size: int, color):
        py.draw.rect(self.screen, color, rect, width=1)
        for y in range(int(rect.height / cell_size)):
            start_y = y * cell_size + rect.y
            end_x = rect.x + rect.width
            self.draw_dashed_line(color, (rect.x, start_y), (end_x, start_y), dash_length=2)

        for x in range(int(rect.width / cell_size)):
            start_x = x * cell_size + rect.x
            end_y = rect.y + rect.height
            self.draw_dashed_line(color, (start_x, rect.y), (start_x, end_y), dash_length=2)

    def handle_input(self):
        for event in py.event.get():
            pos = py.mouse.get_pos()

            # event quit
            if event.type == py.QUIT:
                self.running = False

            if event.type == py.KEYDOWN:

                # quit on q
                if event.key == py.K_q:
                    self.running = False
                    return

                if event.key == py.K_n:
                    self.tilemap = Tilemap(pos, TILEMAPS_FILEPATH + "%s.json" % str(date.today()), width=50, height=50)
                    self.tilemap.resize(self.get_selected_magnification())

                if event.key == py.K_w:
                    # if self.cam_pos[1] > 0:
                    self.cam_pos[1] -= 1
                if event.key == py.K_s:
                    # if self.cam_pos[1] < self.map_size - 1:
                    self.cam_pos[1] += 1
                if event.key == py.K_a:
                    # if self.cam_pos[0] > 0:
                    self.cam_pos[0] -= 1
                if event.key == py.K_d:
                    # if self.cam_pos[0] < self.map_size - 1:
                    self.cam_pos[0] += 1

                if event.key == py.K_MINUS:
                    if self.selected_magnification < len(MAG_VALUES) - 1:
                        self.selected_magnification += 1
                        self.tilemap.resize(self.get_selected_magnification())
                        self.map_size = int(MAP_HEIGHT / self.get_selected_magnification())
                if event.key == py.K_EQUALS:
                    if self.selected_magnification > 0:
                        self.selected_magnification -= 1
                        self.tilemap.resize(self.get_selected_magnification())
                        self.map_size = int(MAP_HEIGHT / self.get_selected_magnification())

                # grow grid on D
                if event.key == py.K_g:
                    self.show_grid = not self.show_grid

                # save map on F
                if event.key == py.K_f:
                    self.tilemap.save(self.tileset.filename)
                    print("Map saved [%s]" % self.tileset.filename)

                # copy tile on left shift
                if event.key == py.K_LSHIFT:
                    if self.mouse_collides_with_rect(pos, self.tilemap.rect):
                        xy = self.tilemap.mouse_to_xy(pos)
                        tile_idx = self.tilemap.tiles[xy[1]][xy[0]]
                        self.tileset.selected_tile = Controller.flattened_to_xy(tile_idx, self.tileset.width)
                        self.tilemap.selector_start = None
                        self.tilemap.selected_end = None
                        self.dragging = False

                # undo on z
                if event.key == py.K_z:
                    self.tilemap.pop_prev()

                # copy selected on c
                if event.key == py.K_c:
                    if self.tilemap.selected_start is not None and self.tilemap.selected_end is not None:
                        self.load_copy_buffer()
                        self.selecting = False
                        self.tilemap.selected_start = None
                        self.tilemap.selected_end = None

                # enable passable on p
                if event.key == py.K_p:
                    self.editing_passable = not self.editing_passable
                    self.tileset.selected_tile = None
                    self.tilemap.deselect()

                if self.tileset.selected_tile is not None:
                    if event.key == py.K_UP:
                        if self.tileset.selected_tile[1] - 1 >= 0:
                            self.tileset.selected_tile = self.tileset.selected_tile[0], self.tileset.selected_tile[1] - 1
                    if event.key == py.K_DOWN:
                        if self.tileset.selected_tile[1] + 1 < self.tileset.height:
                            self.tileset.selected_tile = self.tileset.selected_tile[0], self.tileset.selected_tile[1] + 1
                    if event.key == py.K_LEFT:
                        if self.tileset.selected_tile[0] - 1 >= 0:
                            self.tileset.selected_tile = self.tileset.selected_tile[0] - 1, self.tileset.selected_tile[1]
                    if event.key == py.K_RIGHT:
                        if self.tileset.selected_tile[0] + 1 < self.tileset.width:
                            self.tileset.selected_tile = self.tileset.selected_tile[0] + 1, self.tileset.selected_tile[1]

            if self.dragging:
                if self.mouse_collides_with_tilemap(pos):
                    xy = self.mouse_to_xy(pos)
                    abs = self.abs_to_camera_pos(xy)
                    # if a tile is selected, draw a preview
                    if self.tileset.selected_tile is not None:
                        self.tilemap.push_prev()
                        self.tilemap.set_point(abs, self.tileset.selected_to_absolute())
                    elif not self.selecting:
                        self.tilemap.selected_start = abs
                        self.tilemap.selected_end = abs
                        self.selecting = True
                    elif self.selecting:
                        self.tilemap.selected_end = (abs[0] + 1, abs[1] + 1)

            if event.type == py.MOUSEBUTTONDOWN:

                self.dragging = True
                state = py.mouse.get_pressed()

                # if right mouse clicked is pressed, cancel all selections
                if state[RIGHT_CLICK]:
                    self.dragging = False
                    self.tileset.selected_tile = None
                    self.tilemap.deselect()
                    self.selecting = False
                    self.copy_buffer = None
                    return

                if state[LEFT_CLICK]:

                    # if copying
                    if self.copy_buffer is not None:
                        if self.mouse_collides_with_tilemap(pos):
                            x_len = len(self.copy_buffer.width)
                            y_len = len(self.copy_buffer.height)
                            xy = self.mouse_to_xy(pos)
                            cam = self.abs_to_camera_pos(xy)
                            self.tilemap.push_prev()
                            for y in range(y_len):
                                for x in range(x_len):
                                    if 0 <= (x + cam[0]) < self.tilemap.width and 0 <= (y + cam[1]) < self.tilemap.height:
                                        self.tilemap.set(x + cam[0], y + cam[1], self.copy_buffer.tileset_ids[y][x])
                        return

                    # if no tile is selected and dragging, set tilemap selector start
                    if self.tileset.selected_tile is None and self.tilemap.selected_start is None:
                        if self.mouse_collides_with_rect(pos, self.tilemap.rect):
                            self.tilemap.selector_start = self.tilemap.mouse_to_xy(pos)
                            self.tilemap.selector_end = \
                                self.tilemap.selector_start[0] + 1, \
                                self.tilemap.selector_start[1] + 1

                    # if mouse is over tileset, select a tile
                    if self.mouse_collides_with_rect(pos, self.tileset.rect):
                        self.tileset.selected_tile = self.tileset.mouse_to_xy(pos)

                    # if mouse is over tilemap
                    if self.mouse_collides_with_rect(pos, self.tilemap.rect):
                        xy = self.tilemap.mouse_to_xy(pos)
                        # if a tile is selected, draw a preview
                        if self.tileset.selected_tile is not None:
                            self.tilemap.push_prev()
                            self.tilemap.set_point(self.abs_to_camera_pos(xy), self.tileset.selected_to_absolute())

            if event.type == py.MOUSEBUTTONUP:
                # handle passable layer
                if self.editing_passable:
                    if self.mouse_collides_with_tilemap(pos):
                        if self.selecting:
                            pos = self.tilemap.selected_to_pos()
                            x_len = pos[1][0] - pos[0][0]
                            y_len = pos[1][1] - pos[0][1]
                            if x_len == 0 and y_len == 0:
                                self.tilemap.passable_layer[pos[0][1]][pos[0][0]] = not self.tilemap.passable_layer[pos[0][1]][pos[0][0]]
                            for y in range(pos[0][1], pos[0][1] + y_len):
                                for x in range(pos[0][0], pos[0][0] + x_len):
                                    if 0 <= x < self.tilemap.width and 0 <= y < self.tilemap.height:
                                        self.tilemap.invert_passable(self.abs_to_camera_pos((x, y)))
                        else:
                            xy = self.tilemap.mouse_to_xy(pos)
                            self.tilemap.invert_passable(self.abs_to_camera_pos(xy))
                    self.tilemap.deselect()

                self.dragging = False
                self.selecting = False

    def load_copy_buffer(self):
        pos = self.tilemap.selected_to_pos()
        width = pos[1][0] - pos[0][0] + 1
        height = pos[1][1] - pos[0][1] + 1
        self.copy_buffer = CopyBuffer(width, height)
        pos = pos[0][0] + self.cam_pos[0], pos[0][1] + self.cam_pos[1]
        sub_tiles = self.tilemap.get_sub_tiles(pos, width, height)
        for y in range(height):
            imgs = []
            ids = []
            for x in range(width):
                surf = py.transform.scale(sub_tiles[y][x], (self.tilemap.cell_size, self.tilemap.cell_size))
                imgs.append(surf)
                ids.append(sub_tiles[y][x])
            self.copy_buffer.scaled_buffer.append(imgs)
            self.copy_buffer.tileset_ids(ids)

    def abs_to_camera_pos(self, pos: (int, int)):
        return pos[0] + self.cam_pos[0], pos[1] + self.cam_pos[1]

    def get_selected_magnification(self):
        return MAG_VALUES[self.selected_magnification]

    def get_selected_tile(self) -> py.Surface:
        return self.tileset.tiles[self.tileset.selected_tile[1]][self.tileset.selected_tile[0]]

    def mouse_collides_with_tilemap(self, pos: (int, int)) -> bool:
        if self.mouse_collides_with_map(pos):
            rect = py.Rect(self.map_rect.x - (self.cam_pos[0] * self.tilemap.cell_size),
                           self.map_rect.y - (self.cam_pos[1] * self.tilemap.cell_size),
                           self.tilemap.rect.width,
                           self.tilemap.rect.height)
            return Controller.mouse_collides_with_rect(pos, rect)
        else:
            return False

    def mouse_collides_with_map(self, pos: (int, int)) -> bool:
        return Controller.mouse_collides_with_rect(pos, self.map_rect)

    def mouse_to_xy(self, pos: (int, int)):
        x = int((pos[0] - self.map_rect.x) / self.get_selected_magnification())
        y = int((pos[1] - self.map_rect.y) / self.get_selected_magnification())
        return x, y

    @staticmethod
    def mouse_collides_with_rect(pos: tuple[int, int], rect: py.Rect) -> bool:
        return rect.x <= pos[0] < rect.x + rect.width and \
               rect.y <= pos[1] < rect.y + rect.height

    @staticmethod
    def flattened_to_xy(flat, width):
        return int(flat % width), int(flat / width)

    def draw_dashed_line(self, color, start_pos, end_pos, width=1, dash_length=10):
        x1, y1 = start_pos
        x2, y2 = end_pos
        dl = dash_length

        if x1 == x2:
            ycoords = [y for y in range(y1, y2, dl if y1 < y2 else -dl)]
            xcoords = [x1] * len(ycoords)
        elif y1 == y2:
            xcoords = [x for x in range(x1, x2, dl if x1 < x2 else -dl)]
            ycoords = [y1] * len(xcoords)
        else:
            a = abs(x2 - x1)
            b = abs(y2 - y1)
            c = round(math.sqrt(a ** 2 + b ** 2))
            dx = dl * a / c
            dy = dl * b / c

            xcoords = [x for x in numpy.arange(x1, x2, dx if x1 < x2 else -dx)]
            ycoords = [y for y in numpy.arange(y1, y2, dy if y1 < y2 else -dy)]

        next_coords = list(zip(xcoords[1::2], ycoords[1::2]))
        last_coords = list(zip(xcoords[0::2], ycoords[0::2]))
        for (x1, y1), (x2, y2) in zip(next_coords, last_coords):
            start = (round(x1), round(y1))
            end = (round(x2), round(y2))
            py.draw.line(self.screen, color, start, end, width)
