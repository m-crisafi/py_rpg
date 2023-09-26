from src.models.entities.entity import Entity


class Player(Entity):

    def __init__(self, id: str, key: str):
        Entity.__init__(self, id, key)
