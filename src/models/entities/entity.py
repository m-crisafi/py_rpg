from src.models.components.component import Component
from src.models.object import Object


class Entity(Object):

    def __init__(self, id: int, key: str):
        Object.__init__(self, id, key)
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
