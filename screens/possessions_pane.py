import arcade, arcade.gui
from screens.action_button import ActionButton
from util import *

IMAGE_PATH_ROOT = ":resources:eldritch/images/"

class PossessionsPane():
    def __init__(self, investigator):
        self.investigator = investigator
        self.layout = arcade.gui.UILayout(x=1000)
        self.button_layout = arcade.gui.UILayout(x=1000, y=0, width=280, height=800)
        self.position = 0
        self.boundary = 0
        self.setup()

    def setup(self):
        self.button_layout.children = []
        self.layout.children = []
        
        y_pos = 800
        for card_type in ['assets', 'unique_assets', 'artifacts', 'spells', 'conditions']:
            item_list = self.investigator.possessions[card_type]
            if len(item_list) > 0:
                y_pos -= 45
                self.button_layout.add(ActionButton(x=1000, y=y_pos, width=280, height=25, text=human_readable(card_type)))
                if len(item_list) > 1:
                    number = 0
                    for item in item_list:
                        if number == 0:
                            y_pos -= 190
                        self.button_layout.add(ActionButton(1015 + number * 130, y_pos, texture=item.texture, scale=0.6 * item.scale))
                        number += 1
                        if number == 2:
                            number = 0
                else:
                    y_pos -= 190
                    self.button_layout.add(ActionButton(1080, y_pos, texture=item_list[0].texture, scale=0.6 * item_list[0].scale))
        self.boundary = -y_pos + 20 if y_pos < 0 else 0
        self.layout.add(arcade.gui.UITexturePane(self.button_layout, arcade.load_texture(IMAGE_PATH_ROOT + 'gui/info_pane.png')))

    def reset(self):
        for item in self.button_layout.children:
            item.reset_position()
        self.position = 0

    def move(self, y):
        if self.position + y < 0:
            y = self.position
        elif self.position + y > self.boundary:
            y = self.boundary - self.position
        self.position += y
        if y != 0:
            for item in self.button_layout.children:
                item.move(0, y)