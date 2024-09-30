import arcade, arcade.gui
from screens.action_button import ActionButton

IMAGE_PATH_ROOT = ":resources:eldritch/images/"

TOKEN_DICT = {
    'clue': {
        'size': 36,
        'scale': 0.75
    },
    'gate': {
        'size': 284,
        'scale': 0.4
    }
}

class Map():
    def __init__(self, name, offset, zoom):
        self.manager = arcade.gui.UIManager()
        self.manager.enable()
        self.token_manager = arcade.gui.UIManager()
        self.token_manager.enable()
        self.layout = arcade.gui.UILayout(width=1280, height=800)
        map_texture = arcade.load_texture(":resources:eldritch/images/maps/" + name + ".png")
        self.map = arcade.gui.UITextureButton(texture=map_texture, x=offset[0], y=offset[1], scale=zoom, width=10)
        self.layout.add(self.map)

        self.layouts = {
            'gate': arcade.gui.UILayout(width=1280, height=800),
            'clue': arcade.gui.UILayout(width=1280, height=800)
        }
        self.zoom_layout = arcade.gui.UILayout(width=1280, height=800)

        self.manager.add(self.layout)
        self.token_manager.add(self.zoom_layout)
        
    def move(self, x, y):
        self.map.move(x, y)
        for item in self.layouts['gate'].children + self.layouts['clue'].children:
            item.move(x, y)

    def get_location(self):
        return (self.map.x, self.map.y)
    
    def zoom(self, factor, x=0, y=0):
        self.map.scale(factor)
        self.token_manager.children = {0:[]}
        if factor == 2:
            for item in self.layouts['gate'].children + self.layouts['clue'].children:
                item.reset_position()
                item.move(x, y)
            self.token_manager.add(self.layouts['gate'], index=2)
            self.token_manager.add(self.layouts['clue'], index=1)
        else:
            self.token_manager.add(self.zoom_layout)
        self.map.move(x, y)

    def draw(self):
        self.manager.draw()
        self.token_manager.draw()

    def spawn(self, kind, location, location_name):
        if kind == 'monster':
            pass
        else:
            location[kind] = True
            path = IMAGE_PATH_ROOT + ('icons/clue.png' if kind == 'clue' else 'maps/' + location_name + '_gate.png')
            item = TOKEN_DICT[kind]
            button = ActionButton(
                location['x'] * 2 - item['size'] * item['scale'] / 2, location['y'] * 2 - item['size'] * item['scale'] / 2, texture=arcade.load_texture(path), scale=item['scale'])
            button.kind = kind
            button.location = location_name
            self.layouts[kind].add(button)