
class Object:

    def __init__(self, id: int, key: str):
        self.id: int = id
        self.key: str = key

    def to_json(self):
        return {
            "id": self.id,
            "key": self.key
        }