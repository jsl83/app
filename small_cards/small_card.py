import yaml, arcade, copy

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
        self.back_seen = False
        self.texture = None
        self.investigator = investigator
        self.kind = None
        self.bonuses = []

    def setup(self):
        self.texture = arcade.load_texture(":resources:eldritch/images/" + self.kind + '/' + self.name.replace('.','') + '.png')
        for key in [attr for attr in CARDS[self.kind][self.name].keys() if attr != 'texture']:
            setattr(self, key, copy.deepcopy(CARDS[self.kind][self.name][key]))

    def discard(self, investigator):
        pass

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
        self.texture = arcade.load_texture(":resources:eldritch/images/spells/" + name[0:-1] + '.png')
        for attr in [attribute for attribute in ['triggers', 'reckoning', 'tags', 'action'] if CARDS['spells'][self.name].get(attribute, False)]:
            setattr(self, attr, copy.deepcopy(CARDS['spells'][self.name][attr]))
        self.back = copy.deepcopy(CARDS['spells'][self.name][str(self.variant)])

    def get_server_name(self):
        return self.name + str(self.variant)

class Condition(SmallCard):
    def __init__(self, name, investigator):
        self.variant = int(name[-1])
        SmallCard.__init__(self, name[0:-1], investigator)
        self.kind = 'conditions'
        self.texture = arcade.load_texture(":resources:eldritch/images/conditions/" + name[0:-1] + '.png')
        for attr in [attribute for attribute in ['triggers', 'reckoning', 'tags', 'action'] if CARDS['conditions'][self.name].get(attribute, False)]:
            setattr(self, attr, copy.deepcopy(CARDS['conditions'][self.name][attr]))
        self.back = copy.deepcopy(CARDS['conditions'][self.name][str(self.variant)])

    def get_server_name(self):
        return self.name + str(self.variant)

class Artifact(SmallCard):
    def __init__(self, name, investigator):
        SmallCard.__init__(self, name, investigator)
        self.kind = 'artifacts'
        self.setup()

class UniqueAsset(SmallCard):
    def __init__(self, name, investigator):
        SmallCard.__init__(self, name, investigator)
        self.kind = 'unique_assets'
        self.setup()
        self.variant = int(name[-1])
        self.card_back = CARDS['conditions'][self.name][str(self.variant)]['back']

    def get_server_name(self):
        return self.name + str(self.variant)
