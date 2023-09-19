import xml.dom.minidom as xml


class Tilemap:

    def __init__(self, filename: str):
        self.xml = xml.parse(filename)
        self.impassable: list[tuple(int, int)] = None
    
