import yaml
from util import *
from small_cards.small_card import Spell, Asset, Condition, Artifact

IMAGE_PATH_ROOT = ":resources:eldritch/images/investigators/"
INVESTIGATORS = None

with open('investigators/investigators.yaml') as stream:
    #try:
    INVESTIGATORS = yaml.safe_load(stream)
    #except yaml.YAMLError as exc:
    #    INVESTIGATORS = []

class Investigator():

    def __init__(self, name, hub):
        self.name = name
        self.hub = hub
        self.label = human_readable(name)
        self.subtitle = INVESTIGATORS[name]['subtitle']
        # lore, diplomacy, observation, strength, will
        self.skills = INVESTIGATORS[name]['skills']
        self.max_health = INVESTIGATORS[name]['health']
        self.max_sanity = 12 - self.max_health
        self.health = self.max_health
        self.sanity = self.max_sanity
        self.skill_tokens = [0,0,0,0,0]
        self.skill_bonuses = [[],[],[],[],[]]
        self.possessions = {
            'assets': [],
            'unique_assets': [],
            'artifacts': [],
            'conditions': [],
            'spells': []
        }
        self.clues = []
        self.focus = 0
        self.ship_tickets = 0
        self.rail_tickets = 0
        self.location = INVESTIGATORS[name]['location']
        self.map = 'world'
        self.initial_items = INVESTIGATORS[name]['possessions']
        self.success = 5
        self.passive = INVESTIGATORS[name]['passive']
        self.active = INVESTIGATORS[name]['active']
        self.delayed = False

        self.reroll_items = [[],[],[],[],[]]
        self.max_bonus = [0,0,0,0,0]

        self.san_damage = 0
        self.hp_damage = 0

        self.encounter_impairment = 0
        self.is_dead = False

        self.recover_restrictions = []
        self.health_recover_restrictions = []
        self.sanity_recover_restrictions = []

        self.rest_triggers = []

    def calc_max_bonus(self, index, conditions=[]):
        return max([0] + [bonus['value'] for bonus in self.skill_bonuses[index] if not bonus.get('condition', False) or bonus.get('condition') in conditions])

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

    def get_item(self, cardtype, name):
        card = None
        match cardtype:
            case 'assets':
                card = Asset(name, self)
            case 'spells':
                card = Spell(name, self)
            case 'conditions':
                card = Condition(name, self)
            case 'artifacts':
                card = Artifact(name, self)
        self.possessions[cardtype].append(card)
        return card

    def calculate_skill(self, index):
        return self.skill[3 if index == 5 else index] + self.skill_tokens[3 if index == 5 else index] + self.skill_bonuses[index]

    def improve_skill(self, skill, amt):
        self.skill_tokens[skill] += amt
        self.skill_tokens[skill] = 2 if self.skill_tokens[skill] > 2 else -2 if self.skill_tokens[skill] < -2 else self.skill_tokens[skill]

    def get_number(self, kind, tag=None):
        if kind == 'clues':
            return len(self.clues)
        elif kind == 'hp':
            return self.health
        elif kind =='san':
            return self.sanity
        else:
            return len([card for card in self.possessions[kind] if tag == None or tag in card['tags']])
        
    def rest(self):
        if not ((self.health == self.max_health and self.sanity == self.max_sanity and len(self.rest_triggers) == 0) or len(self.recover_restrictions) != 0):
            if len(self.sanity_recover_restrictions) == 0:
                self.sanity += (1 + len([trigger for trigger in self.hub.triggers['rest_san_bonus'] if self.hub.trigger_check(trigger, [])]))
            if len(self.health_recover_restrictions) == 0:
                self.health += (1 + len([trigger for trigger in self.hub.triggers['rest_hp_bonus'] if self.hub.trigger_check(trigger, [])]))
            return True
        else:
            return False