import arcade, arcade.gui
from screens.action_button import ActionButton

IMAGE_PATH_ROOT = ":resources:eldritch/images/"
ICON_SIZES = {
    'lore': (38, 27),
    'influence': (35, 18),
    'observation': (33, 18),
    'strength': (37,22),
    'will': (24,28)
}

class LocationPane():
    def __init__(self, location_manager):
        self.location_manager = location_manager
        self.blank = arcade.load_texture(IMAGE_PATH_ROOT + 'blank.png')

        self.layout = arcade.gui.UILayout(x=1000, width=280, height=800).with_background(texture=arcade.load_texture(
            IMAGE_PATH_ROOT + 'gui/info_pane.png'))
        self.title = arcade.gui.UITextureButton(x=1000, width=280, y=720, text='', texture=self.blank, style={'font_size': 20})
        self.subtitle = arcade.gui.UITextureButton(x=1000, width=280, y=685, text='', texture=self.blank, style={'font_size': 14})
        self.small_icon = arcade.gui.UITextureButton(x=1100, y=600, width=80, height=80, texture=self.blank)
        self.large_icon = arcade.gui.UITextureButton(x=1035, y=600, width=210, height=171, texture=self.blank)
        
        self.token_layout = arcade.gui.UILayout(x=1000, y=425, width=280, height=120)
        self.location_layout = arcade.gui.UILayout(x=1000, y=425, width=280, height=120)

        self.tokens = {
            'expedition': arcade.gui.UITextureButton(x=1055, y=475, width=70, height=70, texture=arcade.load_texture(
                IMAGE_PATH_ROOT + 'maps/expedition.png')),
            'gate': arcade.gui.UITextureButton(x=1155, y=475, width=70, height=70, texture=arcade.load_texture(
                IMAGE_PATH_ROOT + 'maps/gate.png')),
            'clue': arcade.gui.UITextureButton(x=1050, y=425, width=40, height=40, texture=arcade.load_texture(
                IMAGE_PATH_ROOT + 'maps/clue.png')),
            'eldritch': arcade.gui.UITextureButton(x=1120, y=425, width=40, height=40, texture=arcade.load_texture(
                IMAGE_PATH_ROOT + 'maps/eldritch.png')),
            'rumor': arcade.gui.UITextureButton(x=1190, y=425, width=40, height=40, texture=arcade.load_texture(
                IMAGE_PATH_ROOT + 'maps/rumor.png'))
        }
        self.black = arcade.gui.UITextureButton(x=1000, y=425, width=280, height=120, texture=arcade.load_texture(
            IMAGE_PATH_ROOT + 'gui/overlay.png'))
        self.token_label = arcade.gui.UITextureButton(x=1000, y=555, width=280, height=20, text='TOKENS', texture=self.blank)
        self.investigator_label = arcade.gui.UITextureButton(x=1000, y=380, width=280, height=20, text='INVESTIGATORS', texture=self.blank)
        self.investigator_layout = arcade.gui.UILayout(x=1000, y=450, width=280, height=120)
        self.monster_label = arcade.gui.UITextureButton(x=1000, y=555, width=280, height=20, text='MONSTERS', texture=self.blank)
        self.monster_layout = arcade.gui.UILayout(x=1000, y=450, width=280, height=120)

        self.selected = None

        self.investigators = {}

        self.description_layout = arcade.gui.UILayout(x=1000, y=0, width=280, height=800)
        self.monster_close = ActionButton(x=1260, y=780, width=20, height=20, text='X', texture='buttons/placeholder.png', action=self.close_monster)
        self.monster_picture = arcade.gui.UITextureButton(x=1040, y=560, height=200, width=200, texture=self.blank)
        self.horror_test = arcade.gui.UITextureButton(x=1050, y=400, width=25, height=25, texture=self.blank)
        self.strength_test = arcade.gui.UITextureButton(x=1050, y=335, width=25, height=25, texture=self.blank)
        self.monster = {
            'name': arcade.gui.UITextureButton(x=1000, y=530, width=280, height=20, text='', texture=self.blank, multiline=True),
            'toughness': arcade.gui.UITextureButton(x=1000, y=465, width=140, height=20, text='', texture=self.blank, align='center', multiline=True),
            'horror': arcade.gui.UITextureButton(x=1040, y=400, width=100, height=20, text='', texture=self.blank, align='center', multiline=True),
            'sanity': arcade.gui.UITextureButton(x=1140, y=400, width=100, height=20, text='', texture=self.blank, align='center', multiline=True),
            'strength': arcade.gui.UITextureButton(x=1040, y=335, width=100, height=20, text='', texture=self.blank, align='center', multiline=True),
            'damage': arcade.gui.UITextureButton(x=1140, y=335, width=100, height=20, text='', texture=self.blank, align='center', multiline=True),
            'damage_taken': arcade.gui.UITextureButton(x=1140, y=465, width=140, height=20, text='', texture=self.blank, align='center', multiline=True),
            'text': arcade.gui.UITextureButton(x=1020, y=185, width=240, height=130, text='', texture=self.blank, align='center', multiline=True),
            'reckoning': arcade.gui.UITextureButton(x=1020, y=50, width=240, height=130, text='', texture=self.blank, align='center', multiline=True)
        }
        for key in self.monster:
            self.description_layout.add(self.monster[key])
        for button in [self.monster_picture, self.monster_close, self.horror_test, self.strength_test]:
            self.description_layout.add(button)
        self.icons = []
        for stat in ['lore', 'influence', 'observation', 'strength', 'will']:
            self.icons.append(arcade.load_texture(IMAGE_PATH_ROOT + 'icons/' + stat + '.png'))

    def location_select(self, key):
        location = self.location_manager.locations[key]
        self.selected = key
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
        self.layout.add(self.location_layout)

    def update_tokens(self):
        self.token_layout.clear()
        self.token_layout.add(self.token_label)
        location = self.location_manager.locations[self.selected]
        has = []
        has_not = []
        for key in ['gate', 'expedition', 'clue', 'eldritch', 'rumor']:
            if location[key]:
                has.append(key)
            else:
                has_not.append(key)
        
        for icon in has_not:
            self.token_layout.add(self.tokens[icon])
        self.token_layout.add(self.black)
        for icon in has:
            self.token_layout.add(self.tokens[icon])

    def update_list(self, kind):
        y_offset = 0
        if kind == 'monsters':
            layout = self.monster_layout
            label = self.monster_label
            inv_number = len(self.location_manager.locations[self.selected]['investigators'])
            y_offset = 0 if inv_number == 0 else 35 + (int((inv_number - 1) / 4) + 1) * 60
            label.move(0, 380 - y_offset - label.y)
        else:
            layout = self.investigator_layout
            label = self.investigator_label
        layout.clear()
        number = len(self.location_manager.locations[self.selected][kind])
        if number > 0:
            layout.add(label)
            i = 0
            row = 0
            y = 305 - y_offset + (19 if kind == 'monsters' else 0)
            row_num = number - row * 4
            offset = (280 - (row_num * 49 + (row_num - 1) * 12)) / 2 if row_num < 4 else 24
            for unit in self.location_manager.locations[self.selected][kind]:
                column = i % 4
                if kind == 'investigators':
                    button = self.investigators[unit]
                else:
                    name = unit.name
                    texture = 'monsters/' + name + '.png'
                    button = ActionButton(texture=texture, scale=0.25, action=self.show_monster, action_args={'unit':unit, 'texture': texture})
                layout.add(button)
                button.move(1000 + offset + column * 61 - button.x, y - button.y)
                if i % 4 == 3:
                    row += 1
                    y -= 60
                    row_num = number - row * 4
                    offset = (280 - (row_num * 49 + (row_num - 1) * 12)) / 2 if row_num < 4 else 24
                i += 1
    
    def add_investigator(self, name):
        self.investigators[name] = ActionButton(texture='investigators/' + name + '_portrait.png', scale=0.2)

    def update_all(self):
        self.update_tokens()
        self.update_list('investigators')
        self.update_list('monsters')
        for layout in [self.token_layout, self.investigator_layout, self.monster_layout]:
            self.location_layout.add(layout)

    def show_monster(self, unit, texture):
        self.layout.clear()
        stats = unit.description_dictionary()
        for stat in self.monster:
            self.monster[stat].text = str(stats[stat])
        self.monster_picture.texture = arcade.load_texture(":resources:eldritch/images/" + texture)
        self.horror_test = self.display_skill(stats['horror_check'], 1070, 400)
        self.strength_test = self.display_skill(stats['strength_check'], 1070, 335)
        self.description_layout.add(self.horror_test)
        self.description_layout.add(self.strength_test)
        self.layout.add(self.description_layout)

    def display_skill(self, index, x_pos, y_pos):
        skills = ['lore', 'influence', 'observation', 'strength', 'will']
        key = skills[index]
        return arcade.gui.UITextureButton(
            x=x_pos - ICON_SIZES[key][0], y=3 + y_pos - (ICON_SIZES[key][1] - 20) / 2, width=ICON_SIZES[key][0], height=ICON_SIZES[key][1], texture=self.icons[index])

    def close_monster(self):
        self.location_select(self.selected)