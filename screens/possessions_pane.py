import arcade, arcade.gui
from screens.action_button import ActionButton
from util import *

IMAGE_PATH_ROOT = ":resources:eldritch/images/"

class PossessionsPane():
    def __init__(self, investigator):
        self.investigator = investigator
        self.blank = arcade.load_texture(IMAGE_PATH_ROOT + 'blank.png')
        self.layout = arcade.gui.UILayout(x=1000, width=280, height=800).with_background(texture=arcade.load_texture(
            IMAGE_PATH_ROOT + 'buttons/placeholder.png'))
        self.layouts = {
            'assets': arcade.gui.UILayout(),
            'spells': arcade.gui.UILayout(),
            'conditions': arcade.gui.UILayout()
        }
        self.layout_positions = [0,0,0]
        self.right_positions = [0,0,0]
        self.rows = []
        self.setup()

    def setup(self):
        self.layout.children = []
        index = 0
        for card_type in ['assets', 'spells', 'conditions']:
            items = self.investigator.possessions
            item_list = items[card_type] if card_type != 'assets' else items['assets'] + items['unique_assets'] + items['artifacts']
            if len(item_list) > 0:
                self.layout.add(arcade.gui.UITextureButton(x=1000, y=760 - index * 260, width=280, height=25, text=human_readable(card_type)))
                if len(item_list) > 1:
                    number = 0
                    for item in item_list:
                        self.layouts[card_type].add(ActionButton(1020 + number * 150, 540 - index * 260, texture=item.texture, scale=0.7 * item.scale))
                        number += 1
                else:
                    self.layouts[card_type].add(ActionButton(1070, 540 - index * 260, texture=item_list[0].texture, scale=0.7 * item_list[0].scale))
                self.rows.append(card_type)
                self.right_positions[index] = 0 if len(item_list) == 1 else 50 + 140 * (len(item_list) - 2)
            index += 1
            self.layout.add(self.layouts[card_type])

    def reset(self):
        for key in self.layouts.keys():
            for item in self.layouts[key].children:
                item.reset_position()
        self.layout_positions = [0,0,0]

    def move_row(self, index, x):
        if len(self.rows) >= index + 1:
            items = self.layouts[self.rows[index]].children
            if len(items) > 1:
                pos = self.layout_positions[index]
                if pos - x < 0:
                    x = -self.layout_positions[index]
                elif pos - x > self.right_positions[index]:
                    x = self.right_positions[index] - pos
                for item in self.layouts[self.rows[index]].children:
                    item.move(x, 0)
                self.layout_positions[index] -= x