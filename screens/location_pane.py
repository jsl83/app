import arcade, arcade.gui
from screens.action_button import ActionButton
from screens.possessions_pane import TradePane
from util import *

IMAGE_PATH_ROOT = ":resources:eldritch/images/"

class LocationPane():
    def __init__(self, location_manager, hub):
        self.hub = hub
        self.location_manager = location_manager
        self.blank = arcade.load_texture(IMAGE_PATH_ROOT + 'blank.png')

        self.layout = arcade.gui.UILayout(x=1000, width=280, height=800)

        self.top_pane = arcade.gui.UILayout(x=1000, width=280, height=375, y=425).with_background(texture=arcade.load_texture(
            IMAGE_PATH_ROOT + 'gui/location_top.png'))
        self.bottom_pane = arcade.gui.UILayout(x=1000, width=280, height=469, y=0).with_background(texture=arcade.load_texture(
            IMAGE_PATH_ROOT + 'gui/location_bottom.png'))
        self.title = ActionButton(x=1041, width=198, y=701, height=82, text='', font='Garamond Eldritch', text_position=(0,11), texture=arcade.load_texture(
                IMAGE_PATH_ROOT + 'gui/location_name.png'), style={'font_size': 20, 'font_color': arcade.color.BLACK}, bold=True)
        self.subtitle = ActionButton(x=1000, width=280, y=704, text='', texture=self.blank, style={'font_size': 12, 'font_color': arcade.color.BLACK}, font='Garamond Eldritch', )
        self.small_icon = arcade.gui.UITextureButton(x=1100, y=610, width=80, height=80, texture=self.blank)
        self.large_icon = arcade.gui.UITextureButton(x=1035, y=600, width=210, height=171, texture=self.blank)
        
        self.token_layout = arcade.gui.UILayout(x=1000, y=425, width=280, height=120)
        self.location_layout = arcade.gui.UILayout(x=1000, y=425, width=280, height=120)

        self.tokens = {
            'expedition': arcade.gui.UITextureButton(x=1104, y=438, width=71, height=74, texture=arcade.load_texture(
                IMAGE_PATH_ROOT + 'gui/circle_overlay.png')),
            'gate': arcade.gui.UITextureButton(x=1098, y=518, width=82, height=82, texture=arcade.load_texture(
                IMAGE_PATH_ROOT + 'gui/circle_overlay.png')),
            'clue': arcade.gui.UITextureButton(x=1064, y=496, width=37, height=37, texture=arcade.load_texture(
                IMAGE_PATH_ROOT + 'gui/circle_overlay.png')),
            'eldritch': arcade.gui.UITextureButton(x=1177, y=495, width=37, height=37, texture=arcade.load_texture(
                IMAGE_PATH_ROOT + 'gui/circle_overlay.png')),
            'mystery': arcade.gui.UITextureButton(x=1027, y=457, width=37, height=37, texture=arcade.load_texture(
                IMAGE_PATH_ROOT + 'gui/circle_overlay.png')),
            'rumor': arcade.gui.UITextureButton(x=1216, y=457, width=37, height=37, texture=arcade.load_texture(
                IMAGE_PATH_ROOT + 'gui/circle_overlay.png'))
        }
        self.investigator_label = ActionButton(x=1032, y=315, width=215, height=58, text='Investigators', font='Garamond Eldritch', bold=True, text_position=(0,4), style={'font_color': arcade.color.BLACK}, texture='gui/location_underline.png')
        self.investigator_layout = arcade.gui.UILayout(x=1000, y=405, width=280, height=120)
        self.monster_label = ActionButton(x=1032, y=470, width=215, height=58, text='Monsters', font='Garamond Eldritch', bold=True, text_position=(0,4), style={'font_color': arcade.color.BLACK}, texture='gui/location_underline.png')
        self.monster_layout = arcade.gui.UILayout(x=1000, y=405, width=280, height=120)
        self.toggle_layout = arcade.gui.UILayout(x=1000, y=0, height=425, width=280)

        self.selected = None
        self.description_layout = arcade.gui.UILayout(x=1000, y=0, width=280, height=800).with_background(texture=arcade.load_texture(IMAGE_PATH_ROOT + 'gui/monster_back.png'))
        self.monster_close = ActionButton(x=1031, y=0, width=217, height=46, text='Close Details', texture='buttons/button.png', action=self.close_monster, font='Garamond Eldritch', style={'font_color': arcade.color.BLACK}, text_position=(0,-2))
        self.monster_picture = arcade.gui.UITextureButton(x=1000, y=520, height=280, width=280, texture=self.blank)
        self.horror_test = arcade.gui.UITextureButton(x=1050, y=400, width=25, height=25, texture=self.blank)
        self.strength_test = arcade.gui.UITextureButton(x=1050, y=335, width=25, height=25, texture=self.blank)
        self.monster = {
            'toughness': arcade.gui.UITextureButton(x=1182, y=465, width=140, height=40, text='', texture=self.blank, align='center', multiline=True, font='Poster Bodoni', style={'font_color': arcade.color.WHITE, 'font_size': 32}, bold=True),
            'horror': arcade.gui.UITextureButton(x=1018, y=478, width=100, height=25, text='', texture=self.blank, align='center', multiline=True, style={'font_color': arcade.color.BLACK, 'font_size': 19}, font='Poster Bodoni'),
            'sanity': arcade.gui.UITextureButton(x=1090, y=478, width=100, height=25, text='', texture=self.blank, align='center', multiline=True, font='Poster Bodoni', style={'font_color': arcade.color.BLUE, 'font_size': 19}),
            'strength': arcade.gui.UITextureButton(x=1018, y=418, width=100, height=25, text='', texture=self.blank, align='center', multiline=True, style={'font_color': arcade.color.BLACK, 'font_size': 19}, font='Poster Bodoni'),
            'damage': arcade.gui.UITextureButton(x=1090, y=418, width=100, height=25, text='', texture=self.blank, align='center', multiline=True, font='Poster Bodoni', style={'font_color': arcade.color.DARK_RED, 'font_size': 19}),
            'damage_taken': arcade.gui.UITextureButton(x=1240, y=407, width=30, height=40, text='', texture=self.blank, align='center', multiline=True, font='Poster Bodoni', style={'font_color': arcade.color.WHITE, 'font_size': 19}),
            'text': arcade.gui.UITextureButton(x=1020, y=46, width=240, height=354, text='', texture=self.blank, align='center', multiline=True, font='Adobe Garamond Pro', style={'font_color': arcade.color.DARK_RED})
        }
        for key in self.monster:
            self.description_layout.add(self.monster[key])
        for button in [self.monster_picture, self.monster_close, self.horror_test, self.strength_test]:
            self.description_layout.add(button)
        self.icons = []
        for stat in ['lore', 'influence', 'observation', 'strength', 'will']:
            self.icons.append(arcade.load_texture(IMAGE_PATH_ROOT + 'icons/' + stat + '.png'))

        self.toggle_rumor = ActionButton(1140, y=380, width=140, height=35, text='Rumors', font='Garamond Eldritch', text_position=(0,-2), style={'font_color': arcade.color.BLACK}, action=self.toggle_details, action_args={'flag': False}, bold=True)
        self.toggle_info = ActionButton(1000, y=380, width=140, height=35, text='-= Details =-', font='Garamond Eldritch', text_position=(0,-2), style={'font_color': arcade.color.BLACK}, action=self.toggle_details, action_args={'flag': True}, bold=True)
        self.rumor_details = arcade.gui.UITextureButton(x=1000, y=0, height=390, width=280, texture=self.blank, font='Typical Writer', style={'font_color': arcade.color.BLACK})
        self.rumor = None
        self.possession_screen = TradePane(self.hub.investigator, self.hub)
        self.possession_screen.close_button.action = self.on_show
        self.is_trading = False
        
    def toggle_details(self, flag):
        if flag:
            self.toggle_info.text = '-= Details =-'
            self.toggle_rumor.text = 'Rumors'
        else:
            self.toggle_info.text = 'Details'
            self.toggle_rumor.text = '-= Rumors =-'
        self.toggle_layout.clear()
        if flag:
            for widget in [self.monster_layout, self.investigator_layout]:
                self.toggle_layout.add(widget)
        else:
            self.toggle_layout.add(self.rumor_details)

    def location_select(self, key):
        if key == None:
            key = self.hub.investigator.location
        self.selected = key
        location = self.location_manager.locations[key]
        self.rumor = next((rumor for rumor in self.location_manager.rumors.keys() if self.location_manager.rumors[rumor]['location'] == self.selected), None)
        if self.location_manager.rumors.get('secrets_of_the_past', None) != None and location['expedition']:
            self.rumor = 'secrets_of_the_past'
        self.tokens['rumor'].text = ''
        self.layout.clear()
        self.location_layout.clear()
        self.update_all()
        
        if location['size'] == 'small':
            self.small_icon.texture = arcade.load_texture(IMAGE_PATH_ROOT + 'maps/' + location['kind'] + '.png')
            self.title.text = location['name']
            self.subtitle.text = location['subtitle']
            for button in [self.small_icon, self.title, self.subtitle]:
                self.location_layout.add(button)
        else:
            self.large_icon.texture = arcade.load_texture(IMAGE_PATH_ROOT + 'maps/' + key + '.png')
            self.location_layout.add(self.large_icon)
        self.layout.add(self.top_pane)
        self.layout.add(self.bottom_pane)
        self.layout.add(self.location_layout)

    def on_show(self):
        self.is_trading = False
        self.location_select(self.selected)

    def update_tokens(self):
        self.token_layout.clear()
        location = self.location_manager.locations[self.selected]
        has = []
        has_not = []
        for key in ['gate', 'expedition', 'clue', 'eldritch', 'rumor', 'mystery']:
            if location[key]:
                has.append(key)
            else:
                has_not.append(key)
        
        for icon in has_not:
            self.token_layout.add(self.tokens[icon])
        if self.rumor != None:
            self.tokens['rumor'].text = str(self.location_manager.rumors[self.rumor].get('eldritch', ''))
            self.tokens['rumor'].style['font_color'] = arcade.color.PURPLE

    def update_list(self, kind):
        y_offset = 0
        investigators = [val for val in self.location_manager.all_investigators.values() if val.location == self.selected]
        dead = [] if kind != 'investigators' else [name for name in self.location_manager.dead_investigators.values() if name.location == self.selected]
        if kind == 'monsters':
            layout = self.monster_layout
            label = self.monster_label
            inv_number = len(investigators) + len(dead)
            y_offset = 0 if inv_number == 0 else 35 + (int((inv_number - 1) / 4) + 1) * 60
            label.move(0, 315 - y_offset - label.y)
            number = len(self.location_manager.locations[self.selected]['monsters'])
        else:
            layout = self.investigator_layout
            label = self.investigator_label
            number = len(investigators) + len(dead)
        layout.clear()
        if number > 0:
            layout.add(label)
            i = 0
            row = 0
            y = 240 - y_offset + (19 if kind == 'monsters' else 0)
            row_num = number - row * 4
            offset = (280 - (row_num * 49 + (row_num - 1) * 12)) / 2 if row_num < 4 else 24
            for unit_obj in [monster for monster in self.location_manager.locations[self.selected][kind]] if kind == 'monsters' else investigators + dead:
                unit = unit_obj.name
                column = i % 4
                texture = 'monsters/' + unit + '.png' if kind == 'monsters' else 'investigators/' + unit + '_portrait.png'
                button = ActionButton(texture=texture, action=self.show_monster if kind == 'monsters' else self.trade, action_args={'unit_obj':unit_obj}, scale=0.25 if kind == 'monsters' else 0.2)
                layout.add(button)
                if unit in dead:
                    dead_button = ActionButton(texture='investigators/dead.png', scale=0.2)
                    layout.add(dead_button)
                    dead_button.move(1000 + offset + column * 61, y)
                button.move(1000 + offset + column * 61, y)
                if i % 4 == 3:
                    row += 1
                    y -= 60
                    row_num = number - row * 4
                    offset = (280 - (row_num * 49 + (row_num - 1) * 12)) / 2 if row_num < 4 else 24
                i += 1

    def trade(self, unit_obj):
        unit = unit_obj.name
        if unit != self.hub.investigator.name:
            investigator = self.hub.location_manager.all_investigators.get(unit, self.hub.location_manager.dead_investigators.get(unit))
            trade = (investigator.location == self.hub.investigator.location
                 and not unit in self.location_manager.dead_investigators.keys() and self.hub.remaining_actions > 0 and not self.hub.actions_taken['trade'])
            self.layout.clear()
            self.possession_screen.investigator = investigator
            self.possession_screen.setup(trade)
            self.layout.add(self.possession_screen.layout)
            self.is_trading = True

    def update_all(self):
        self.update_tokens()
        self.update_list('investigators')
        self.update_list('monsters')
        for layout in [self.token_layout, self.toggle_layout]:
            self.location_layout.add(layout)
        self.location_layout.add(self.toggle_info)
        self.location_layout.add(self.toggle_rumor)
        self.toggle_rumor.enable()
        self.toggle_rumor.set_style(arcade.color.BLACK)
        if self.rumor == None:
            self.toggle_rumor.disable()
            self.toggle_rumor.set_style(arcade.color.GRAY)
        else:
            self.rumor_details.text = human_readable(self.rumor)
            for x in ['solve', 'unsolved', 'reckoning', 'effect']:
                if self.location_manager.rumors[self.rumor].get(x, None) != None:
                    self.rumor_details.text += '\n\n' + human_readable(x) + '\n' + self.location_manager.rumors[self.rumor].get(x)
            self.rumor_details.style = {'font_size': self.location_manager.rumors[self.rumor].get('font_size', 12)}
        self.toggle_details(True)

    def show_monster(self, unit_obj):
        self.layout.clear()
        stats = unit_obj.description_dictionary()
        for stat in self.monster:
            self.monster[stat].text = str(stats[stat])
        self.monster_picture.texture = arcade.load_texture(":resources:eldritch/images/monsters/" + unit_obj.name + '.png')
        self.horror_test = arcade.gui.UITextureButton(x=1014, y=474, texture=self.icons[stats['horror_check']])
        self.strength_test = arcade.gui.UITextureButton(x=1014, y=412, texture=self.icons[stats['strength_check']])
        self.description_layout.add(self.horror_test)
        self.description_layout.add(self.strength_test)
        self.layout.add(self.description_layout)

    def close_monster(self):
        self.location_select(self.selected)

    def move(self, dy):
        self.possession_screen.move(dy)