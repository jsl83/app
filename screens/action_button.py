import arcade, arcade.gui
from arcade import Texture

class ActionButton(arcade.gui.UITextureButton):
    def __init__(self,
                 x: float = 0,
                 y: float = 0,
                 width: float = None,
                 height: float = None,
                 texture: str | Texture = None,
                 texture_hovered: Texture = None,
                 texture_pressed: str = None,
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
                 **kwargs):
        
        arcade_texture = None if texture == None else arcade.load_texture(":resources:eldritch/images/" + texture) if type(texture) == str else texture
        arcade_pressed = None if texture_pressed == None else arcade.load_texture(":resources:eldritch/images/" + texture_pressed)
        
        super().__init__(x, y, width, height, arcade_texture, texture_hovered, arcade_pressed, text, scale,
                         size_hint, size_hint_min, size_hint_max, style, text_position, font, multiline=multiline, anchor_y=anchor_y)
        
        self.action = action
        self.enabled = enabled
        self.action_args = action_args
        self.initial_x = x
        self.initial_y = y
        self.name = name
        self.original_texture = arcade_texture
        self.is_action = is_action

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

    def click_action(self):
        if self.action_args != None:
            self.action(**self.action_args)
        else:
            self.action()
        if self.is_action:
            self.action_available(False)