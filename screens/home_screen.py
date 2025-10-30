import arcade
import arcade.gui
from util import *

IMAGE_PATH_ROOT = ":resources:eldritch/images/"

class HomeScreen(arcade.View):
    def __init__(self, host_action, join_action, window):
        super().__init__()

        self.window = window
        self.manager = arcade.gui.UIManager()
        self.manager.enable()
        self.layout = arcade.gui.UILayout(width=1280, height=800)
        self.manager.add(self.layout)
        cover = arcade.gui.UITextureButton(texture=arcade.load_texture(IMAGE_PATH_ROOT + 'home.png'))
        self.host_button = arcade.gui.UITextureButton(text='Host Game', width=200, height=50, x=944, y=600, texture=arcade.load_texture(IMAGE_PATH_ROOT + '/buttons/placeholder.png'))
        self.join_button = arcade.gui.UITextureButton(text='Join Game', width=200, height=50, x=944, y=450, texture=arcade.load_texture(IMAGE_PATH_ROOT + '/buttons/placeholder.png'))
        self.ip_button = arcade.gui.UIInputText(width=200, height=50, x=944, y=390).with_background(arcade.load_texture(IMAGE_PATH_ROOT + '/buttons/pressed_placeholder.png'))
        self.click_time = 0
        for buttons in [cover, self.host_button, self.join_button, self.ip_button]:
            self.layout.add(buttons)
        self.host_action = host_action
        self.join_action = join_action

        self.host_action(self.window)
    
    def on_draw(self):
        self.clear()        
        self.manager.draw()
        self.click_time += 1

    def on_mouse_press(self, x, y, button, modifiers):
        self.click_time = 0

    def on_mouse_release(self, x, y, button, modifiers):
        self.holding = False
        if (self.click_time <= 10):
            buttons = list(self.manager.get_widgets_at((x,y)))
            if len(buttons) > 0:
                if buttons[0] == self.host_button:
                    self.host_action(self.window)
                elif buttons[0] == self.join_button and self.ip_button.children[0].text != '':
                    self.join_action(self.ip_button.children[0].text, self.window)