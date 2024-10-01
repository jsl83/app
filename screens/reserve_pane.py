import arcade, arcade.gui
from screens.action_button import ActionButton
from util import *

IMAGE_PATH_ROOT = ":resources:eldritch/images/"

class ReservePane():
    def __init__(self):
        self.layout = arcade.gui.UILayout(x=1000)
        self.button_layout = arcade.gui.UILayout(x=1000, y=0, width=280, height=800)
        self.reserve = []
        y_pos = 760
        number = 0
        for i in range(4):
            if number == 0:
                y_pos -= 190
            self.button_layout.add(ActionButton(1013 + number * 134, y_pos, width=120, height=185, texture=arcade.load_texture(
                IMAGE_PATH_ROOT + 'buttons/placeholder.png')))
            number += 1
            if number == 2:
                number = 0
        self.layout.add(arcade.gui.UITexturePane(self.button_layout, arcade.load_texture(IMAGE_PATH_ROOT + 'gui/info_pane.png')))
        self.layout.add(ActionButton(x=1000, y=760, width=280, height=25, text='RESERVE'))

    def restock(self, removed, added):
        if removed != '':
            for item in removed:
                item = item.replace('.', '')
                option = next((button for button in self.button_layout.children if button.name == item), None)
                option.name = added[0].replace('.', '')
                option.texture = arcade.load_texture(IMAGE_PATH_ROOT + 'assets/' + added[0] + '.png')
                added.remove(added[0])
            for item in added:
                item = item.replace('.', '')
                option = next((button for button in self.button_layout.children if button.name == None or button.name == ''), None)
                option.name = item
                option.texture = arcade.load_texture(IMAGE_PATH_ROOT + 'assets/' + item + '.png')