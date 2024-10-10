import yaml
from util import *
from small_cards.small_card import SmallCard

IMAGE_PATH_ROOT = ":resources:eldritch/images/investigators/"
INVESTIGATORS = None

with open('investigators/investigators.yaml') as stream:
    #try:
    INVESTIGATORS = yaml.safe_load(stream)
    #except yaml.YAMLError as exc:
    #    INVESTIGATORS = []

class Investigator():

    def __init__(self, name):
        self.name = name
        self.label = human_readable(name)
        self.subtitle = INVESTIGATORS[name]['subtitle']
        # lore, diplomacy, observation, strength, will
        self.skills = INVESTIGATORS[name]['skills']
        self.max_health = INVESTIGATORS[name]['health']
        self.max_sanity = 12 - self.max_health
        self.health = self.max_health
        self.sanity = self.max_sanity
        self.skill_tokens = [0,0,0,0,0]
        self.skill_mods = [0,0,0,0,0]
        self.possessions = {
            'assets': [SmallCard('.18_derringer', 'assets'), SmallCard('.18_derringer', 'assets'), SmallCard('.18_derringer', 'assets'), SmallCard('.18_derringer', 'assets')],
            'unique_assets': [SmallCard('ace_of_swords', 'unique_assets')],
            'artifacts': [],
            'conditions': [SmallCard('agreement', 'conditions')],
            'spells': [SmallCard('mists_of_releh', 'spells')]
        }
        self.clues = 0
        self.focus = 0
        self.ship_tickets = 0
        self.rail_tickets = 0
        self.location = INVESTIGATORS[name]['location']
        #self.initial_items = INVESTIGATORS[name]['possessions']
        self.initial_items = []
        self.success = 5
        self.passive = INVESTIGATORS[name]['passive']
        self.active = INVESTIGATORS[name]['active']

    def get_token(self, kind, amt=1, swap=False):
        match kind:
            case 'focus':
                self.focus += amt
            case 'rail':
                self.rail_tickets += amt
                if self.rail_tickets + self.ship_tickets > 2:
                    self.ship_tickets -= 1
            case 'ship':
                self.ship_tickets += amt
                if self.rail_tickets + self.ship_tickets > 2:
                    self.rail_tickets -= 1

    def get_item(self, cardtype, name, variant=None):
        self.possessions[cardtype].append(SmallCard(name, cardtype))