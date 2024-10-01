import arcade, arcade.gui
from arcade import Texture

class ActionButton(arcade.gui.UITextureButton):
    def __init__(self,
                 x: float = 0,
                 y: float = 0,
                 width: float = None,
                 height: float = None,
                 texture: Texture = None,
                 texture_hovered: Texture = None,
                 texture_pressed: Texture = None,
                 text: str = "",
                 scale: float = None,
                 size_hint=None,
                 size_hint_min=None,
                 size_hint_max=None,
                 style=None,
                 text_position: tuple = (0,0),
                 font: str = "",
                 action=lambda: None,
                 enabled: bool=True,
                 action_args=None,
                 name: str = "",
                 **kwargs):
        
        super().__init__(x, y, width, height, texture, texture_hovered, texture_pressed, text, scale,
                         size_hint, size_hint_min, size_hint_max, style, text_position, font)
        
        self.action = action
        self.enabled = enabled
        self.action_args = action_args
        self.initial_x = x
        self.initial_y = y
        self.name = name

    def reset_position(self):
        self.move(self.initial_x - self.x, self.initial_y - self.y)