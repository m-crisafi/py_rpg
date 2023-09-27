import json
import pygame as py


def flattened_to_xy(idx: int, width: int) -> (int, int):
    return int(idx % width), int(idx / width)


def load_json(filepath: str):
    with open(filepath, "r") as file:
        return json.load(file)


def sprite_from_sheet(filepath: str, p: (int, int), width: int, height: int, cell_size: int, scaled_size: int):
    result = []
    im = py.image.load(filepath)
    for y in range(p[1], p[1] + height):
        line = []
        for x in range(p[0], p[0] + width):
            rect = py.Rect(x * cell_size, y * cell_size, cell_size, cell_size)
            surf = im.subsurface(rect)
            scaled = py.transform.scale(surf, (scaled_size, scaled_size))
            line.append(scaled)
        result.append(line)
    return result
