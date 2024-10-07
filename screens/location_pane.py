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
        
        self.token_layout = arcade.gui.UILayout(x=1000, y=450, width=280, height=120)

        self.tokens = {
            'expedition': arcade.gui.UITextureButton(x=1055, y=480, width=70, height=70, texture=arcade.load_texture(
                IMAGE_PATH_ROOT + 'maps/expedition.png')),
            'gate': arcade.gui.UITextureButton(x=1155, y=480, width=70, height=70, texture=arcade.load_texture(
                IMAGE_PATH_ROOT + 'maps/gate.png')),
            'clue': arcade.gui.UITextureButton(x=1050, y=430, width=40, height=40, texture=arcade.load_texture(
                IMAGE_PATH_ROOT + 'maps/clue.png')),
            'eldritch': arcade.gui.UITextureButton(x=1120, y=430, width=40, height=40, texture=arcade.load_texture(
                IMAGE_PATH_ROOT + 'maps/eldritch.png')),
            'rumor': arcade.gui.UITextureButton(x=1190, y=430, width=40, height=40, texture=arcade.load_texture(
                IMAGE_PATH_ROOT + 'maps/rumor.png'))
        }
        self.black = arcade.gui.UITextureButton(x=1000, y=430, width=280, height=120, texture=arcade.load_texture(
            IMAGE_PATH_ROOT + 'gui/overlay.png'))
        self.token_label = arcade.gui.UITextureButton(x=1000, y=555, width=280, height=20, text='TOKENS', texture=arcade.load_texture(
            IMAGE_PATH_ROOT + 'buttons/placeholder.png'))
        self.investigator_label = arcade.gui.UITextureButton(x=1000, y=555, width=280, height=20, text='TOKENS', texture=arcade.load_texture(
            IMAGE_PATH_ROOT + 'buttons/placeholder.png'))
        
        self.selected = None

    def location_select(self, key):
        self.layout.clear()
        self.token_layout.clear()
        self.layout.add(self.token_label)
        location = self.location_manager.locations[key]
        self.selected = key
        has = []
        has_not = []
        for kind in ['gate', 'expedition', 'clue', 'eldritch', 'rumor']:
            if location[kind]:
                has.append(kind)
            else:
                has_not.append(kind)
        
        for icon in has_not:
            self.token_layout.add(self.tokens[icon])
        self.token_layout.add(self.black)
        for icon in has:
            self.token_layout.add(self.tokens[icon])
        
        if location['size'] == 'small':
            self.small_icon.texture = arcade.load_texture(IMAGE_PATH_ROOT + 'maps/' + location['kind'] + '.png')
            self.title.text = location['name']
            self.subtitle.text = location['subtitle']
            for button in [self.small_icon, self.title, self.subtitle]:
                self.layout.add(button)
        else:
            self.large_icon.texture = arcade.load_texture(IMAGE_PATH_ROOT + 'maps/' + key + '.png')
            self.layout.add(self.large_icon)

        self.layout.add(self.token_layout)

    def update_tokens(self):
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