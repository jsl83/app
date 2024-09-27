import arcade
import yaml
from util import *

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
        self.skill_mods = [0,0,0,0,0]
        self.small_cards = {
            'assets': [],
            'uniques': [],
            'artifacts': [],
            'conditions': []
        }
        self.clues = 0
        self.focus = 0
        self.ship_tickets = 0
        self.rail_tickets = 0
        self.location = INVESTIGATORS[name]['location']

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