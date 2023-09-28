from src.models.components.component import Component

TRIGGER_COMPONENT_KEY = "trigger_c"

TRIGGER_MOVE_TILEMAPS = 0


class TriggerComponent(Component):

    def __init__(self, id: int, type: int, payload: {}):
        Component.__init__(self, id, TRIGGER_COMPONENT_KEY)
        self.type = type
        self.payload = payload

    def to_json(self) -> {}:
        result = Component.to_json(self)
        result["type"] = self.type
        result["payload"] = self.payload
