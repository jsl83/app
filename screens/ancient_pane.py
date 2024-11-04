import arcade, arcade.gui
from screens.action_button import ActionButton
from util import *

IMAGE_PATH_ROOT = ":resources:eldritch/images/"

class AncientOnePane():
    def __init__(self, ancient):
        self.ancient = ancient
        self.mystery = None
        self.blank = arcade.load_texture(IMAGE_PATH_ROOT + 'blank.png')

        self.layout = arcade.gui.UILayout(x=1000, width=280, height=800).with_background(texture=arcade.load_texture(
            IMAGE_PATH_ROOT + 'gui/info_pane.png'))
        self.details = arcade.gui.UILayout(x=1000, width=280, height=350)
        self.layout.add(arcade.gui.UITextureButton(x=1000, width=280, y=560, text=human_readable(ancient.name), texture=self.blank, font="Typical Writer", style={'font_size': 20}))
        self.layout.add(arcade.gui.UITextureButton(x=1062, y=505, texture=arcade.load_texture(
            IMAGE_PATH_ROOT +'ancient_ones/' + ancient.name + '_portrait.png'), text=ancient.mysteries, text_position=(50,-100)))
        self.toggle_attributes = ActionButton(1000, y=475, width=140, height=30, texture='buttons/placeholder.png', text='Details',
                                              action=self.toggle_details, action_args={'flag': False}, texture_pressed='/buttons/pressed_placeholder.png')
        self.toggle_skills = ActionButton(1140, y=475, width=140, height=30, texture='buttons/placeholder.png', text='Mystery',
                                          action=self.toggle_details, action_args={'flag': True}, texture_pressed='/buttons/pressed_placeholder.png')
        self.toggle_attributes.select(True)
        self.layout.add(self.toggle_attributes)
        self.layout.add(self.toggle_skills)
        self.mystery = arcade.gui.UITextureButton(x=1020, y=25, width=240, height=415, style={'font_size': 14},
            text='', texture=self.blank, align='center', multiline=True)
        self.stats = arcade.gui.UITextureButton(x=1020, y=25, width=240, height=415, style={'font_size': 14},
            text=str(ancient.text), texture=self.blank, align='center', multiline=True)
        self.details.add(self.stats)
        self.layout.add(self.details)

    def toggle_details(self, flag):
        self.details.clear()
        if flag:
            self.details.add(self.mystery)
            self.toggle_skills.select(True)
            self.toggle_attributes.select(False)
        else:
            self.toggle_skills.select(False)
            self.toggle_attributes.select(True)
            self.details.add(self.stats)

    def on_show(self):
        pass