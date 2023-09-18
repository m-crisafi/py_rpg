from models.components.component import Component

RENDER_COMPONENT_KEY = "r_component"


class RenderComponent(Component):

    def __init__(self, id: int, bmp: str, width: int, height: int):
        Component.__init__(self, id, RENDER_COMPONENT_KEY)
        self.bmp: str = bmp
        self.width: int = width
        self.height: int = height
