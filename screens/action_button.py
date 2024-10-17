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
                 multiline: bool = False,
                 name: str = "",
                 anchor_y: str = "center",
                 is_action: bool = False,
                 undo=None,
                 **kwargs):
        
        super().__init__(x, y, width, height, texture, texture_hovered, texture_pressed, text, scale,
                         size_hint, size_hint_min, size_hint_max, style, text_position, font, multiline=multiline, anchor_y=anchor_y)
        
        self.click_action = action
        self.enabled = enabled
        self.action_args = action_args
        self.initial_x = x
        self.initial_y = y
        self.name = name
        self.original_texture = texture
        self.is_action = is_action
        self.undo = undo

    def reset_position(self):
        self.move(self.initial_x - self.x, self.initial_y - self.y)

    def disable(self):
        self.enabled = False
        self.style = {'font_color': arcade.color.ASH_GREY}
    
    def enable(self):
        self.enabled = True
        self.style = {'font_color': arcade.color.WHITE}

    def select(self, selected: bool = False):
        self._tex = self.texture_pressed if selected else self.original_texture
        self.trigger_render()

    def action_available(self, toggle: bool = False):
        if toggle:
            self.texture = self.texture_hovered
        else:
            self.texture = self.original_texture

    def action(self):
        if self.action_args != None:
            self.click_action(**self.action_args)
        else:
            self.click_action()
        if self.is_action:
            self.action_available(False)