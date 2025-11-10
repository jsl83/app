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
            IMAGE_PATH_ROOT + 'gui/ao_pane.png'))
        self.details = arcade.gui.UILayout(x=1000, width=280, height=350)
        self.layout.add(arcade.gui.UITextureButton(x=1000, width=280, y=515, text=human_readable(ancient.name), texture=self.blank, font="UglyQua", style={'font_size': 20, 'font_color': arcade.color.BLACK}))
        self.mystery_count = arcade.gui.UITextureButton(x=1000, y=570, texture=arcade.load_texture(IMAGE_PATH_ROOT +'ancient_ones/' + ancient.name + '_square.png')) 
        self.layout.add(self.mystery_count)
        self.layout.add(arcade.gui.UITextureButton(x=1000,y=562, texture=arcade.load_texture(IMAGE_PATH_ROOT + 'ancient_ones/ao_border.png')))
        self.toggle_attributes = ActionButton(1000, y=475, width=140, height=30, action=self.toggle_details, action_args={'flag': False}, texture_pressed='/gui/ao_selector.png')
        self.toggle_skills = ActionButton(1137, y=475, width=142, height=30, action=self.toggle_details, action_args={'flag': True}, texture_pressed='/gui/ao_selector.png')
        self.toggle_attributes.select(True)
        self.layout.add(self.toggle_attributes)
        self.layout.add(self.toggle_skills)
        self.mystery_title = arcade.gui.UITextureButton(x=1020, y=355, width=240, height=70, style={'font_size': 14, 'font_color': arcade.color.BLACK},
            text='', texture=self.blank, align='center', bold=True, font='UglyQua')
        self.mystery_counter = arcade.gui.UITextureButton(x=1020, y=350, width=240, height=20, style={'font_size': 12, 'font_color': arcade.color.BLACK},
            text='', texture=self.blank, align='center', font='UglyQua', bold=True)
        self.mystery = ActionButton(x=1020, y=0, width=240, height=350, style={'font_size': 12, 'font_color': arcade.color.BLACK},
            text='', texture=self.blank, align='center', multiline=True)
        self.stats = arcade.gui.UITextureButton(x=1020, y=25, width=240, height=400, style={'font_size': 14, 'font_color': arcade.color.BLACK},
            text=str(ancient.text), texture=self.blank, align='center', multiline=True, font='Typical Writer')
        self.details.add(self.stats)
        self.layout.add(self.details)

    def toggle_details(self, flag):
        self.details.clear()
        if flag:
            self.details.add(self.mystery)
            self.details.add(self.mystery_counter)
            self.details.add(self.mystery_title)
            self.toggle_skills.select(True)
            self.toggle_attributes.select(False)
        else:
            self.toggle_skills.select(False)
            self.toggle_attributes.select(True)
            self.details.add(self.stats)

    def on_show(self):
        self.toggle_details(False)