from src.models.object import Object


class Component(Object):

    def __init__(self, id: int, key: str):
        Object.__init__(self, id, key)

    def to_json(self) -> {}:
        return Object.to_json(self)
