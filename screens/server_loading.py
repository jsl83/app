import arcade, arcade.gui
from util import *

IMAGE_PATH = ":resources:eldritch/images/"

class ServerLoadingScreen(arcade.View):
    def __init__(self, networker):
        super().__init__()
        self.status = ''
        self.investigators = []
        self.manager = arcade.gui.UIManager()
        self.ancient_one = None

        self.manager.add(arcade.gui.UILabel(y=650, text="Ancient One", align='center', width=500))
        self.manager.add(arcade.gui.UILabel(y=650, text="Investigators", align='center', width=700, x=580))
        self.start_button = arcade.gui.UITextureButton(texture=arcade.load_texture(IMAGE_PATH + 'buttons/placeholder.png'), y=150, x=855, width=150, text='Start Game', align='center')
        self.start_button.enabled = False
        self.manager.add(self.start_button)
        self.click_time = 0
        self.networker = networker

    def select_ao(self, name):
        self.ancient_one = name
        texture = arcade.load_texture(IMAGE_PATH + 'ancient_ones/' + name + '_front.png')
        scale = 400 / texture.width
        self.manager.add(arcade.gui.UITextureButton(x=50, y=(700 - (texture.height * scale)) / 2, texture=texture, scale=scale))
        if len(self.investigators) > 0:
            self.start_button.enabled = True

    def investigator_selected(self, name):
        if name not in self.investigators:
            texture = arcade.load_texture(IMAGE_PATH + 'investigators/' + name + '_portrait.png')
            scale = 100 / texture.width
            self.investigators.append(name)
            x_pos = 680 + ((len(self.investigators) % 4) - 1) * 133
            x_pos = x_pos if len(self.investigators) % 4 != 0 else x_pos - 33
            self.manager.add(arcade.gui.UITextureButton(
                x=x_pos, y=475 if len(self.investigators) < 4 else 375, scale=scale, texture=texture, text=human_readable(name), text_position=(0, -55)))
        if self.ancient_one:
            self.start_button.enabled = True

    def on_draw(self):
        self.clear()        
        self.manager.draw()
        self.click_time += 1

    def on_mouse_release(self, x, y, button, modifiers):
        if (self.click_time <= 15):
            buttons = list(self.manager.get_widgets_at((x,y)))
            if len(buttons) > 0 and type(buttons[0]) is arcade.gui.UITextureButton and getattr(buttons[0], 'enabled', False):
                self.networker.publish_payload({'message': 'start_game'}, 'login')
    
    def on_mouse_press(self, x, y, button, modifiers):
        self.click_time = 0