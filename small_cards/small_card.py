import yaml
import arcade

CARDS = {
    'assets': {},
    'spells': {},
    'conditions': {},
    'artifacts': {},
    'unique_assets': {}
}

for kind in ['assets', 'spells', 'conditions']:
    with open('small_cards/' + kind + '.yaml') as stream:
        CARDS[kind] = yaml.safe_load(stream)

class SmallCard():
    def __init__(self, name):
        self.name = name
        self.action_used = False
        self.texture = None

    def setup(self, kind):
        self.texture = arcade.load_texture(":resources:eldritch/images/" + kind + '/' + self.name.replace('.','') + '.png')
        for key in CARDS[kind][self.name]:
            setattr(self, key, CARDS[kind][self.name][key])

class Asset(SmallCard):
    def __init__(self, name):
        SmallCard.__init__(self, name)
        self.setup('assets')

class Spell(SmallCard):
    def __init__(self, name):
        self.variant = name[-1]
        SmallCard.__init__(self, name[0:-1])
        self.setup('spells')

class Condition(SmallCard):
    def __init__(self, name):
        self.variant = name[-1]
        SmallCard.__init__(self, name[0:-1])
        self.setup('conditions')