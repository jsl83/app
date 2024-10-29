import arcade, arcade.gui
from screens.action_button import ActionButton

IMAGE_PATH_ROOT = ":resources:eldritch/images/"

TOKEN_DICT = {
    'clue': {
        'size': 36,
        'scale': 1.1,
        'zoom_scale': 0.5
    },
    'gate': {
        'size': 284,
        'scale': 0.4,
        'zoom_scale': 0.2
    },
    'investigator': {
        'size': 247,
        'scale': 0.4,
        'zoom_scale': 0.2
    },
    'monster': {
        'size': 200,
        'scale': 0.3,
        'zoom_scale': 0.15
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
            'clue': arcade.gui.UILayout(width=1280, height=800),
            'investigator': arcade.gui.UILayout(width=1280, height=800),
            'monster': arcade.gui.UILayout(width=1280, height=800)
        }
        self.zoom_layout = arcade.gui.UILayout(width=1280, height=800)

        self.manager.add(self.layout)
        self.token_manager.add(self.zoom_layout)
        
    def move(self, x, y):
        self.map.move(x, y)
        for item in self.layouts['gate'].children + self.layouts['clue'].children + self.layouts['investigator'].children + self.layouts['monster'].children:
            item.move(x, y)

    def get_location(self):
        return (self.map.x, self.map.y)
    
    def zoom(self, factor, x=0, y=0):
        self.map.scale(factor)
        self.token_manager.children = {0:[]}
        if factor == 2:
            for layout in [self.layouts['gate'], self.layouts['monster'], self.layouts['investigator'], self.layouts['clue']]:
                for item in layout.children:
                    item.reset_position()
                    item.move(x, y)
                self.token_manager.add(layout)
        else:
            self.token_manager.add(self.zoom_layout)
        self.map.move(x, y)

    def draw(self):
        self.manager.draw()
        self.token_manager.draw()

    def spawn(self, kind, manager, location_name, name=None):
        location = manager.locations[location_name]
        path = None
        offset = 0
        match kind:
            case 'investigator':
                location['investigators'].append(name)
                path = 'investigators/' + name + '_portrait.png'
                offset = 1
            case 'clue':
                path = 'icons/clue.png'
                location['clue'] = True
            case 'gate':
                path = 'maps/' + location_name + '_gate.png'
                location['gate'] = True
            case 'monster':
                path = 'monsters/' + name + '.png'
        item = TOKEN_DICT[kind]
        button = ActionButton(location['x'] * 2 - item['size'] * item['scale'] / 2, location['y'] * 2 - item['size'] * item['scale'] / 2 - offset * 45,
                                texture=path, scale=item['scale'], name=location_name)
        button.kind = kind
        button.item_name = name
        self.layouts[kind].add(button)
        zoom_button = ActionButton(location['x'] - item['size'] * item['zoom_scale'] / 2, location['y'] - item['size'] * item['zoom_scale'] / 2 - offset * 25,
                                    texture=path, scale=item['zoom_scale'], name=location_name)
        zoom_button.kind = kind
        zoom_button.item_name = name
        self.zoom_layout.add(zoom_button)

    def move_tokens(self, kind, location, destination, zoom_destination, dest_name, name=None):
        buttons = self.get_tokens(kind, location, name)
        zoom_in = buttons[0]
        zoom_out = buttons[1]
        offset = 1 if kind == 'investigator' else 0
        item = TOKEN_DICT[kind]
        zoom_in.name = dest_name
        zoom_out.name = dest_name

        zoom_in.initial_x = destination[0] * 2 - item['size'] * item['scale'] / 2
        zoom_in.initial_y = destination[1] * 2 - item['size'] * item['scale'] / 2 - offset * 45
        zoom_in.move(zoom_destination[0] - item['size'] * item['scale'] / 2 - zoom_in.x, zoom_destination[1] - item['size'] * item['scale'] / 2 - offset * 45 - zoom_in.y)

        zoom_out.initial_x = destination[0] - item['size'] * item['zoom_scale'] / 2
        zoom_out.initial_y = destination[1] - item['size'] * item['zoom_scale'] / 2 - offset * 25
        zoom_out.move(zoom_out.initial_x - zoom_out.x, zoom_out.initial_y - zoom_out.y)

    def get_tokens(self, kind, location, name):
        zoom_in = next((button for button in self.layouts[kind].children if button.name == location and (True if name == None else button.item_name == name)), None)
        zoom_out = next((button for button in self.zoom_layout.children if button.name == location and (True if name == None else button.item_name == name)), None)

        return (zoom_in, zoom_out)
