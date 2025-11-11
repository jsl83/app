import arcade
import arcade.gui
from util import *
from screens.action_button import ActionButton

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
        background = arcade.gui.UITextureButton(texture=arcade.load_texture(IMAGE_PATH_ROOT + 'gui/home.png'), x=808)
        blank = arcade.load_texture(IMAGE_PATH_ROOT + 'blank.png')
        self.host_button = ActionButton(text='Host Game', width=300, height=64, x=894, y=500, texture=blank, font='Typical Writer', style={'font_color': arcade.color.BLACK, 'font_size': 20}, bold=True)
        self.join_button = ActionButton(text='Join Game', width=300, height=64, x=894, y=350, texture=blank, font='Typical Writer', style={'font_color': arcade.color.BLACK, 'font_size': 20}, bold=True)
        self.ip_button = ActionButton(width=300, height=50, x=894, y=310, texture=blank, font='Poster Bodoni', style={'font_color': arcade.color.GRAY, 'font_size': 12}, text='Type host IP')
        self.click_time = 0
        for buttons in [cover, background, self.host_button, self.join_button, self.ip_button]:
            self.layout.add(buttons)
        self.host_action = host_action
        self.join_action = join_action

        #self.host_action(self.window)
    
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

    def on_key_press(self, symbol, modifiers):
        added_char = None
        if symbol == 65288 and len(self.ip_button.text) > 0:
            new = self.ip_button.text[:-1]
        elif symbol in list(range(65456, 65466)) + [65454]:
            symbol -= 65408
            added_char = chr(symbol)
        elif symbol in list(range(48, 58)) + [46]:
            added_char = chr(symbol)
        else:
            return
        if added_char:
            if self.ip_button.text == 'Type host IP':
                self.ip_button.text = ''
                self.ip_button.set_style(arcade.color.BLACK, 20)
            new = self.ip_button.text + added_char
        self.ip_button.text = ''
        self.manager.trigger_render()
        self.ip_button.text = new
        if self.ip_button.text == '':
            self.ip_button.text = 'Type host IP'
            self.ip_button.set_style(arcade.color.GRAY, 15)