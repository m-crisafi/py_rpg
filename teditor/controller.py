import math
from datetime import date

import numpy as numpy
import pygame as py

from tilemap import Tilemap
from tileset import *

PADDING = 20
SCREEN_H_MAX = 800 + PADDING * 2
SCREEN_WIDTH = 1900
SCREEN_HEIGHT = SCREEN_H_MAX
MAP_HEIGHT = SCREEN_H_MAX - PADDING * 2
MAG_VALUES = [160, 100, 80, 50, 40, 32, 25, 20, 16, 10, 8, 5]
MAG_START_IDX = 7

WHITE = (255, 255, 255, 255)
BLACK = (0, 0, 0, 255)
SELECTED_COLOR = (0, 255, 0, 255)
GRID_COLOR = (140, 140, 140, 255)
MAP_COLOR = (190, 190, 190, 255)
ALPHA = 200
BG_COLOR = WHITE

TILESET_START = (20, 20)

LEFT_CLICK = 0
MIDDLE_CLICK = 1
RIGHT_CLICK = 2


class CopyBuffer:

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.scaled_buffer = [[None for x in range(width)] for y in range(height)]
        self.tileset_ids = [[-1 for x in range(width)] for y in range(height)]


class Controller:

    def __init__(self):
        self.screen = py.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.tileset = Tileset(30, TILESET_START)
        self.tileset.new("overworld.json", "overworld.png", 30, 16)
        # self.tileset.load("town.json")
        pos = (self.tileset.rect.x + self.tileset.rect.width + PADDING, TILESET_START[1])

        self.map_rect = py.Rect(
            pos[0],
            pos[1],
            MAP_HEIGHT,
            MAP_HEIGHT)

        self.selected_magnification = 7
        self.mid_map = self.map_rect.midtop[0], self.map_rect.midleft[1]
        self.tilemap = Tilemap("new.json", self.get_selected_magnification(), 50, 50, "overworld.json")

        self.last_clicked_cell: (int, int) or None = None
        self.last_clicked_abs: (int, int) or None = None
        self.copy_buffer: CopyBuffer or None = None
        self.running = True
        self.selecting = False
        self.show_grid = False
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
                self.screen.blit(self.tileset.tiles[y][x].scaled, rect)

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
        pos = py.mouse.get_pos()

        self.screen.fill(BG_COLOR)
        self.draw_tileset()

        # draw map background
        py.draw.rect(self.screen, MAP_COLOR, self.map_rect)
        py.draw.rect(self.screen, BLACK, self.map_rect, width=1)

        # draw whole world
        for y in range(self.map_size):
            for x in range(self.map_size):
                nx, ny = self.xy_to_camera_pos((x, y))
                if self.tilemap.point_on_map(nx, ny):
                    rect = self.get_map_rect_from_xy((x, y))
                    idx = self.tilemap.tiles[ny][nx]
                    xy = Controller.flattened_to_xy(idx, self.tileset.width)
                    surf = self.tileset.tiles[xy[1]][xy[0]].surf
                    surf = py.transform.scale(surf, (self.tilemap.cell_size, self.tilemap.cell_size))
                    self.screen.blit(surf, rect)

                    if self.editing_passable and not self.tilemap.pathable[ny][nx]:
                        alpha_surf = py.Surface((self.tilemap.cell_size, self.tilemap.cell_size), py.SRCALPHA)
                        py.draw.rect(alpha_surf, (150, 150, 150, ALPHA), (0, 0, self.tilemap.cell_size, self.tilemap.cell_size))
                        py.draw.rect(alpha_surf, (255, 0, 0, 255), (0, 0, self.tilemap.cell_size, self.tilemap.cell_size), width=1)
                        self.screen.blit(alpha_surf, rect)

        if self.editing_passable:
            for y in range(self.tileset.height):
                for x in range(self.tileset.width):
                    if not self.tileset.tile_at((x, y)).pathable:
                        rect = py.Rect(self.tileset.rect.x + x * self.tileset.cell_size,
                                       self.tileset.rect.y + y * self.tileset.cell_size,
                                       self.tileset.cell_size,
                                       self.tileset.cell_size)
                        alpha_surf = py.Surface((self.tileset.cell_size, self.tileset.cell_size), py.SRCALPHA)
                        py.draw.rect(alpha_surf, (150, 150, 150, ALPHA), (0, 0, self.tileset.cell_size, self.tileset.cell_size))
                        py.draw.rect(alpha_surf, (255, 0, 0, 255), (0, 0, self.tileset.cell_size, self.tileset.cell_size), width=1)
                        self.screen.blit(alpha_surf, rect)

        # draw grids if true
        if self.show_grid:
            self.draw_grid(self.map_rect, self.tilemap.cell_size, GRID_COLOR)

        if self.mouse_collides_with_tilemap(pos):

            # draw tile hover on map
            if self.tileset.selected_tile is not None:
                abs = self.mouse_to_xy(pos)
                rect = self.get_map_rect_from_xy(abs)
                surf = py.transform.scale(
                    self.tileset.get_selected_tile().surf,
                    (self.tilemap.cell_size, self.tilemap.cell_size)
                )
                self.screen.blit(surf, rect)

            # draw selected tileset tiles
            if self.selecting:
                p = self.tilemap.selected_to_pos()
                cam = p[0][0] - self.cam_pos[0], p[0][1] - self.cam_pos[1]
                width = p[1][0] - p[0][0] + 1
                height = p[1][1] - p[0][1] + 1

                if self.tileset.selected_tile is not None:
                    surf = py.transform.scale(
                        self.tileset.get_selected_tile().surf,
                        (self.tilemap.cell_size, self.tilemap.cell_size)
                    )
                    for y in range(height):
                        for x in range(width):
                            new_p = cam[0] + x, cam[1] + y
                            rect = self.get_map_rect_from_xy(new_p)
                            self.screen.blit(surf, rect)

                rect = self.get_map_rect_from_xy(cam, width, height)
                self.draw_grid(rect, self.tilemap.cell_size, (255, 255, 255))

            # draw copy buffer if it exists
            if self.copy_buffer is not None:
                xy = self.mouse_to_xy(pos)
                p = self.mouse_to_camera_pos(pos)

                for y in range(self.copy_buffer.height):
                    for x in range(self.copy_buffer.width):
                        if self.tilemap.point_on_map(p[0] + x, p[1] + y):
                            rect = self.get_map_rect_from_xy((xy[0] + x, xy[1] + y))
                            surf = self.copy_buffer.scaled_buffer[y][x]
                            self.screen.blit(surf, rect)
                rect = self.get_map_rect_from_xy(xy, self.copy_buffer.width, self.copy_buffer.height)
                self.draw_grid(rect, self.tilemap.cell_size, (255, 255, 255))

            # draw hover
            if not self.selecting and self.tileset.selected_tile is None and self.copy_buffer is None:
                abs = self.mouse_to_xy(pos)
                rect = self.get_map_rect_from_xy(abs)
                py.draw.rect(self.screen, (160, 160, 160), rect, 1)

        py.display.flip()

    def handle_input(self):

        for event in py.event.get():
            pos = py.mouse.get_pos()
            xy = self.mouse_to_xy(pos)
            abs = self.xy_to_camera_pos(xy)
            state = py.mouse.get_pressed()

            # event quit
            if event.type == py.QUIT:
                self.running = False

            """
            KEY PRESS HANDLING
            (q) Quit
            (n) New
            (wasd) Move camera
            (-) Zoom out
            (+) Zoom in
            (g) Show grid
            (f) Save map
            (z) Undo
            (p) Passable layer
            (lshift) Copy hovered tile
            (c) Copy selected
            (arrows) Move selected tile
            """
            if event.type == py.KEYDOWN:

                # quit on q
                if event.key == py.K_q:
                    self.running = False
                    return

                # new map on n
                if event.key == py.K_n:
                    self.tilemap = Tilemap(
                        "%s.json" % str(date.today()),
                        width=50,
                        height=50,
                        tileset_filename="forest.png")
                    self.tilemap.resize(self.get_selected_magnification())
                    self.cam_pos = [0, 0]

                # move cam on wasd
                if event.key == py.K_w:
                    self.cam_pos[1] -= 1
                if event.key == py.K_s:
                    self.cam_pos[1] += 1
                if event.key == py.K_a:
                    self.cam_pos[0] -= 1
                if event.key == py.K_d:
                    self.cam_pos[0] += 1

                # zoom out on minus
                if event.key == py.K_MINUS:
                    if self.selected_magnification < len(MAG_VALUES) - 1:
                        self.selected_magnification += 1
                        self.tilemap.resize(self.get_selected_magnification())
                        self.map_size = int(MAP_HEIGHT / self.get_selected_magnification())

                # zoom in on plus
                if event.key == py.K_EQUALS:
                    if self.selected_magnification > 0:
                        self.selected_magnification -= 1
                        self.tilemap.resize(self.get_selected_magnification())
                        self.map_size = int(MAP_HEIGHT / self.get_selected_magnification())

                # grow grid on G
                if event.key == py.K_g:
                    self.show_grid = not self.show_grid

                # save map on F
                if event.key == py.K_f:
                    self.tilemap.save()
                    self.tileset.save()
                    print("Map saved [%s]" % self.tileset.filename)

                # copy tile on left shift
                if event.key == py.K_LSHIFT:
                    if self.mouse_collides_with_tilemap(pos):
                        tile_idx = self.tilemap.tiles[abs[1]][abs[0]]
                        self.tileset.select_tile_by_flattened_index(tile_idx)
                        self.deselect()

                # undo on z
                if event.key == py.K_z:
                    self.tilemap.pop_prev()

                # copy selected on c
                if event.key == py.K_c:
                    if self.selecting:
                        self.load_copy_buffer()
                        self.deselect()

                # enable passable on p
                if event.key == py.K_p:
                    self.editing_passable = not self.editing_passable
                    self.tileset.selected_tile = None
                    self.deselect()

                # handle UP/DOWN/LEFT/RIGHT
                if self.tileset.selected_tile is not None:
                    x, y = self.tileset.selected_tile
                    if event.key == py.K_UP and y - 1 >= 0:
                        self.tileset.selected_tile = x, y - 1
                    if event.key == py.K_DOWN and y + 1 < self.tileset.height:
                        self.tileset.selected_tile = x, y + 1
                    if event.key == py.K_LEFT and x - 1 >= 0:
                        self.tileset.selected_tile = x - 1, y
                    if event.key == py.K_RIGHT and x + 1 < self.tileset.width:
                        self.tileset.selected_tile = x + 1, y

            """
            If mouse is dragging            
            """
            if self.selecting and self.mouse_collides_with_tilemap(pos) and self.last_clicked_cell != abs:
                if state[LEFT_CLICK]:
                    self.tilemap.selected_end = abs
                    self.last_clicked_cell = abs

            if event.type == py.MOUSEBUTTONDOWN:

                # if right mouse clicked is pressed, cancel all selections
                if state[RIGHT_CLICK]:

                    if self.tileset.selected_tile is not None or self.copy_buffer is not None or self.selecting:
                        self.tileset.selected_tile = None
                        self.deselect()
                        self.copy_buffer = None
                        return

                # if left click was pressed
                if state[LEFT_CLICK]:

                    # if copying
                    if self.copy_buffer is not None:
                        if self.mouse_collides_with_tilemap(pos):
                            self.tilemap.push_prev()
                            for y in range(self.copy_buffer.height):
                                for x in range(self.copy_buffer.width):
                                    nx, ny = abs
                                    p = (nx + x, ny + y)
                                    if self.tilemap.point_on_map(p[0], p[1]) and self.map_point_visible(p):
                                        id = self.copy_buffer.tileset_ids[y][x]
                                        self.tilemap.set_point(p, id)
                                        self.tilemap.set_pathable(p, self.tileset.tile_by_flattened_idx(id).pathable)
                            self.tilemap.deselect()
                        return

                    # if no tile is selected and dragging, set tilemap selector start
                    if not self.selecting:
                        if self.mouse_collides_with_map(pos):
                            self.tilemap.selected_start = abs
                            self.tilemap.selected_end = abs
                            self.last_clicked_cell = abs
                            self.selecting = True
                            return

                    # if mouse is over tileset, select a tile
                    if self.mouse_collides_with_rect(pos, self.tileset.rect):
                        cam = self.tileset.mouse_to_xy(pos)
                        if self.editing_passable:
                            self.tileset.flip_pathable(cam)
                        else:
                            self.tileset.selected_tile = self.tileset.mouse_to_xy(pos)
                        return

            if event.type == py.MOUSEBUTTONUP:

                if self.selecting and self.mouse_collides_with_tilemap(pos):
                    p = self.tilemap.selected_to_pos()
                    x_len = p[1][0] - p[0][0] + 1
                    y_len = p[1][1] - p[0][1] + 1

                    if self.tileset.selected_tile is not None:
                        self.tilemap.push_prev()

                    for y in range(p[0][1], p[0][1] + y_len):
                        for x in range(p[0][0], p[0][0] + x_len):
                            if self.tilemap.point_on_map(x, y):
                                if self.editing_passable:
                                    self.tilemap.invert_pathable((x, y))
                                elif self.tileset.selected_tile is not None:
                                    self.tilemap.set_point((x, y), self.tileset.selected_to_flattened())
                                    pathable = self.tileset.get_selected_tile().pathable
                                    self.tilemap.pathable[y][x] = pathable
                    if self.tileset.selected_tile is not None or self.editing_passable:
                        self.deselect()

            if state[RIGHT_CLICK]:
                if self.last_clicked_abs is None:
                    self.last_clicked_abs = xy
                elif xy != self.last_clicked_abs:
                    if xy[0] < self.last_clicked_abs[0]:
                        self.cam_pos[0] += 1
                    elif xy[0] > self.last_clicked_abs[0]:
                        self.cam_pos[0] -= 1
                    elif xy[1] < self.last_clicked_abs[1]:
                        self.cam_pos[1] += 1
                    elif xy[1] > self.last_clicked_abs[1]:
                        self.cam_pos[1] -= 1
                    self.last_clicked_abs = xy
                    return

    def map_point_visible(self, point: (int, int)) -> bool:
        width = self.map_rect.width / self.tilemap.cell_size
        height = self.map_rect.height / self.tilemap.cell_size
        return self.cam_pos[0] <= point[0] < width + self.cam_pos[1] and \
               self.cam_pos[1] <= point[1] < height + self.cam_pos[1]

    def get_map_rect_from_xy(self, pos: (int, int), width: int = 1, height: int = 1) -> py.Rect:
        return py.Rect(
            (pos[0] * self.tilemap.cell_size) + self.map_rect.x,
            (pos[1] * self.tilemap.cell_size) + self.map_rect.y,
            width * self.tilemap.cell_size,
            height * self.tilemap.cell_size,
        )

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

    def load_copy_buffer(self):
        pos = self.tilemap.selected_to_pos()
        width = pos[1][0] - pos[0][0] + 1
        height = pos[1][1] - pos[0][1] + 1
        self.copy_buffer = CopyBuffer(width, height)
        sub_tiles = self.tilemap.get_sub_tiles(pos[0], width, height)
        for y in range(height):
            for x in range(width):
                tile_idx = sub_tiles[y][x]
                surf = py.transform.scale(self.tileset.tile_by_flattened_idx(tile_idx).surf,
                                          (self.tilemap.cell_size, self.tilemap.cell_size))
                self.copy_buffer.scaled_buffer[y][x] = surf
                self.copy_buffer.tileset_ids[y][x] = tile_idx

    def deselect(self):
        self.tilemap.deselect()
        self.selecting = False

    def get_selected_magnification(self):
        return MAG_VALUES[self.selected_magnification]

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

    def mouse_to_camera_pos(self, pos: (int, int)):
        return self.xy_to_camera_pos(self.mouse_to_xy(pos))

    def xy_to_camera_pos(self, pos: (int, int)):
        return pos[0] + self.cam_pos[0], pos[1] + self.cam_pos[1]

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

    @staticmethod
    def pos_in_range(pos: (int, int), width: int, height: int):
        return 0 <= pos[0] < width and 0 <= pos[1] < height

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
