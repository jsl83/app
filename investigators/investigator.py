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
            'assets': [],
            'unique_assets': [],
            'artifacts': [],
            'conditions': [],
            'spells': []
        }
        self.clues = 0
        self.focus = 0
        self.ship_tickets = 0
        self.rail_tickets = 0
        self.location = INVESTIGATORS[name]['location']
        self.initial_items = INVESTIGATORS[name]['possessions']
        self.success = 5
        self.passive = INVESTIGATORS[name]['passive']
        self.active = INVESTIGATORS[name]['active']

        self.reroll_items = [{}, {}, {}, {}, {}, {}]

    def get_ticket(self, kind):
        rail = 0
        ship = 0
        match kind:
            case 'rail':
                self.rail_tickets += 1
                rail = -1
                if self.rail_tickets + self.ship_tickets > 2:
                    self.ship_tickets -= 1
                    ship = 1
            case 'ship':
                self.ship_tickets += 1
                ship = -1
                if self.rail_tickets + self.ship_tickets > 2:
                    self.rail_tickets -= 1
                    rail = 1
        return (rail, ship)

    def get_item(self, cardtype, name, variant=None):
        self.possessions[cardtype].append(SmallCard(name, cardtype))