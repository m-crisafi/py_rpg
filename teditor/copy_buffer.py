
class CopyBuffer:

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.scaled_buffer = [[None for x in range(width)] for y in range(height)]
        self.tileset_ids = [[-1 for x in range(width)] for y in range(height)]
