from src.models.components.component import Component
from src.models.object import Object


class Entity(Object):

    def __init__(self, id: int, key: str, pos: [int, int], pathable: bool):
        Object.__init__(self, id, key)
        self.pos = pos
        self.pathable = pathable
        self.components: [Component] = []

    def add_component(self, component: Component):
        self.components.append(component)

    def get_component_by_key(self, key: str) -> Component or None:
        for c in self.components:
            if c.key == key:
                return c
        return None

    def has_component(self, key: str) -> bool:
        for c in self.components:
            if c.key == key:
                return True
        return False

    def collides(self, pos: (int, int)):
        return self.pos[0] == pos[0] and self.pos[1] == pos[1]

    def xy(self) -> (int, int):
        return self.pos[0], self.pos[1]

    def to_json(self) -> {}:
        result = Object.to_json(self)
        result["id"] = self.id
        result["pos"] = self.pos
        result["pathable"] = self.pathable
        result["components"] = [c.to_json() for c in self.components]
        return result
