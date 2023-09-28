from src.models.entities.entity import Entity


class Player(Entity):

    def __init__(self, id: id, key: str, pos: [int, int]):
        Entity.__init__(self, id, key, pos, False)

    def to_json(self):
        result = Entity.to_json(self)
        return result
