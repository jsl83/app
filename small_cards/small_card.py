import arcade

IMAGE_PATH_ROOT = ":resources:eldritch/images/"

TYPE_DICT = {
    'assets': {
        'scale': 1
    },
    'spells': {
        'scale': 0.8
    },
    'conditions': {
        'scale': 1
    },
    'artifacts': {
        'scale': 1
    },
    'unique_assets': {
        'scale': 1
    }
}

class SmallCard():
    def __init__(self, name, kind):

        self.name = name
        self.kind = kind
        self.scale = TYPE_DICT[kind]['scale']
        self.texture = arcade.load_texture(IMAGE_PATH_ROOT + kind + '/' + name.replace('.', '') + '.png')