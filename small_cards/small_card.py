import yaml
import arcade

CARDS = {
    'assets': {},
    'spells': {},
    'conditions': {},
    'artifacts': {},
    'unique_assets': {}
}

def get_asset(name):
    card = CARDS['assets'][name]
    card['name'] = name
    card['texture'] = arcade.load_texture(":resources:eldritch/images/assets/" + name.replace('.','') + '.png')
    return card

for kind in ['assets', 'spells', 'conditions', 'artifacts']:
    with open('small_cards/' + kind + '.yaml') as stream:
        CARDS[kind] = yaml.safe_load(stream)

class SmallCard():
    def __init__(self, name, investigator):
        self.name = name
        self.action_used = False
        self.texture = None
        self.investigator = investigator

    def setup(self, kind):
        self.texture = arcade.load_texture(":resources:eldritch/images/" + kind + '/' + self.name.replace('.','') + '.png')
        for key in CARDS[kind][self.name]:
            setattr(self, key, CARDS[kind][self.name][key])

class Asset(SmallCard):
    def __init__(self, name, investigator):
        SmallCard.__init__(self, name, investigator)
        self.setup('assets')

class Spell(SmallCard):
    def __init__(self, name, investigator):
        self.variant = name[-1]
        SmallCard.__init__(self, name[0:-1], investigator)
        self.setup('spells')

class Condition(SmallCard):
    def __init__(self, name, investigator):
        self.variant = name[-1]
        SmallCard.__init__(self, name[0:-1], investigator)
        self.setup('conditions')

class Artifact(SmallCard):
    def __init__(self, name, investigator):
        SmallCard.__init__(self, name, investigator)
        self.setup('artifacts')