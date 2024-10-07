import arcade, arcade.gui
from screens.action_button import ActionButton

IMAGE_PATH_ROOT = ":resources:eldritch/images/"

class LocationPane():
    def __init__(self, location_manager):
        self.location_manager = location_manager
        self.blank = arcade.load_texture(IMAGE_PATH_ROOT + 'blank.png')

        self.layout = arcade.gui.UILayout(x=1000, width=280, height=800).with_background(texture=arcade.load_texture(
            IMAGE_PATH_ROOT + 'buttons/placeholder.png'))
        self.title = arcade.gui.UITextureButton(x=1000, width=280, y=720, text='', texture=self.blank, style={'font_size': 20})
        self.subtitle = arcade.gui.UITextureButton(x=1000, width=280, y=685, text='', texture=self.blank, style={'font_size': 14})
        self.small_icon = arcade.gui.UITextureButton(x=1100, y=600, width=80, height=80, texture=self.blank)
        self.large_icon = arcade.gui.UITextureButton(x=1035, y=600, width=210, height=171, texture=self.blank)
        
        self.token_layout = arcade.gui.UILayout(x=1000, y=425, width=280, height=120)

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
        self.token_label = arcade.gui.UITextureButton(x=1000, y=555, width=280, height=20, text='TOKENS', texture=arcade.load_texture(
            IMAGE_PATH_ROOT + 'buttons/placeholder.png'))
        self.investigator_label = arcade.gui.UITextureButton(x=1000, y=380, width=280, height=20, text='INVESTIGATORS', texture=arcade.load_texture(
            IMAGE_PATH_ROOT + 'buttons/placeholder.png'))
        self.investigator_layout = arcade.gui.UILayout(x=1000, y=450, width=280, height=120)
        self.monster_label = arcade.gui.UITextureButton(x=1000, y=555, width=280, height=20, text='MONSTERS', texture=arcade.load_texture(
            IMAGE_PATH_ROOT + 'buttons/placeholder.png'))
        self.monster_layout = arcade.gui.UILayout(x=1000, y=450, width=280, height=120)

        self.selected = None

        self.investigators = {}

        self.boundary = 0

    def location_select(self, key):
        location = self.location_manager.locations[key]
        self.selected = key
        self.layout.clear()
        self.update_all()
        
        if location['size'] == 'small':
            self.small_icon.texture = arcade.load_texture(IMAGE_PATH_ROOT + 'maps/' + location['kind'] + '.png')
            self.title.text = location['name']
            self.subtitle.text = location['subtitle']
            for button in [self.small_icon, self.title, self.subtitle]:
                self.layout.add(button)
        else:
            self.large_icon.texture = arcade.load_texture(IMAGE_PATH_ROOT + 'maps/' + key + '.png')
            self.layout.add(self.large_icon)

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
            for name in self.location_manager.locations[self.selected][kind]:
                column = i % 4
                if kind == 'investigators':
                    button = self.investigators[name]
                else:
                    button = ActionButton(texture = arcade.load_texture(IMAGE_PATH_ROOT + 'monsters/' + name + '.png'), scale=0.25)
                layout.add(button)
                button.move(1000 + offset + column * 61 - button.x, y - button.y)
                if i % 4 == 3:
                    row += 1
                    y -= 60
                    row_num = number - row * 4
                    offset = (280 - (row_num * 49 + (row_num - 1) * 12)) / 2 if row_num < 4 else 24
                i += 1
    
    def add_investigator(self, name):
        self.investigators[name] = ActionButton(texture = arcade.load_texture(IMAGE_PATH_ROOT + 'investigators/' + name + '_portrait.png'), scale=0.2)

    def update_all(self):
        self.update_tokens()
        self.update_list('investigators')
        self.update_list('monsters')
        for layout in [self.token_layout, self.investigator_layout, self.monster_layout]:
            self.layout.add(layout)