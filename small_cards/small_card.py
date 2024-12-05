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
        self.kind = None

    def setup(self):
        self.texture = arcade.load_texture(":resources:eldritch/images/" + self.kind + '/' + self.name.replace('.','') + '.png')
        for key in CARDS[self.kind][self.name]:
            setattr(self, key, CARDS[self.kind][self.name][key])

    def discard(self):
        self.investigator.possessions[self.kind].remove(self)

    def get_server_name(self):
        return self.name

class Asset(SmallCard):
    def __init__(self, name, investigator):
        SmallCard.__init__(self, name, investigator)
        self.kind = 'assets'
        self.setup()

class Spell(SmallCard):
    def __init__(self, name, investigator):
        self.variant = int(name[-1])
        SmallCard.__init__(self, name[0:-1], investigator)
        self.kind = 'spells'
        self.setup()

    def get_server_name(self):
        return self.name + ':' + str(self.variant)

class Condition(SmallCard):
    def __init__(self, name, investigator):
        self.variant = int(name[-1])
        SmallCard.__init__(self, name[0:-1], investigator)
        self.kind = 'conditions'
        self.card_back = CARDS['conditions'][self.name][str(self.variant)]['back']
        self.setup()

    def get_server_name(self):
        return self.name + ':' + str(self.variant)

class Artifact(SmallCard):
    def __init__(self, name, investigator):
        SmallCard.__init__(self, name, investigator)
        self.kind = 'artifacts'
        self.setup()