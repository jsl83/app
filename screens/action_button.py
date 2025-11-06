import arcade, arcade.gui
from arcade import Texture
from arcade.gui.surface import Surface

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
                 style={'font_color': arcade.color.WHITE, 'font_size': 15},
                 text_position: tuple = (0,0),
                 font: str = "",
                 action=lambda **args: None,
                 enabled: bool=True,
                 action_args=None,
                 multiline: bool = False,
                 name: str = "",
                 anchor_y: str = "center",
                 is_action: bool = False,
                 bold=False,
                 **kwargs):
        
        arcade_texture = None if texture == None else arcade.load_texture(":resources:eldritch/images/" + texture) if type(texture) == str else texture
        arcade_pressed = None if texture_pressed == None else arcade.load_texture(":resources:eldritch/images/" + texture_pressed)
        
        super().__init__(x, y, width, height, arcade_texture, texture_hovered, arcade_pressed, text, scale,
                         size_hint, size_hint_min, size_hint_max, style=style, font=font, multiline=multiline, anchor_y=anchor_y, text_position=text_position, bold=bold)
        
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
    
    def enable(self):
        self.enabled = True

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

    def unset(self):
        self.action = lambda: None
        self.action_args = None
        self.text = ''
        self.enable()

    def check_overlap(self, button):
        return self.rect.x < button.rect.x + button.rect.width and self.rect.x + self.rect.width > button.rect.x and self.rect.y + self.rect.height > button.rect.y and self.rect.y < button.rect.y + button.rect.height

    def set_style(self, color=None, size=None):
        self._style['font_color'] = color or self._style.get('font_color', arcade.color.WHITE)
        self._style['font_size'] = size or self._style.get('font_size', 15)
