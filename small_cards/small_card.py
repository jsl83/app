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
        self.action_used = False