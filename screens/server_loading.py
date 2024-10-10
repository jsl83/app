import arcade, arcade.gui
from util import *

IMAGE_PATH = ":resources:eldritch/images/"

class ServerLoadingScreen(arcade.View):
    def __init__(self):
        super().__init__()
        self.status = ''
        self.investigators = []
        self.manager = arcade.gui.UIManager()

        self.manager.add(arcade.gui.UILabel(y=650, text="Ancient One", align='center', width=500))
        self.manager.add(arcade.gui.UILabel(y=650, text="Investigators", align='center', width=700, x=580))

    def select_ao(self, name):
        texture = arcade.load_texture(IMAGE_PATH + 'ancient_ones/' + name + '_front.png')
        scale = 400 / texture.width
        self.manager.add(arcade.gui.UITextureButton(x=50, y=(675 - (texture.height * scale)) / 2, texture=texture, scale=scale))

    def add_investigator(self, name):
        texture = arcade.load_texture(IMAGE_PATH + 'investigators/' + name + '_portrait.png')
        scale = 100 / texture.width
        self.investigators.append(name)
        x_pos = 680 + ((len(self.investigators) % 4) - 1) * 133
        x_pos = x_pos if len(self.investigators) % 4 != 0 else x_pos - 33
        self.manager.add(arcade.gui.UITextureButton(
            x=x_pos, y=450 if len(self.investigators) < 4 else 350, scale=scale, texture=texture, text=human_readable(name), text_position=(0, -55)))

    def on_draw(self):
        self.clear()        
        self.manager.draw()