import yaml
from util import *

with open('monsters/monsters.yaml') as stream:
    MONSTERS = yaml.safe_load(stream)

class Monster():
    def __init__(self, name, monster_id, inv_number):
        self.name = name
        self.epic = False
        for key in MONSTERS[name]:
            setattr(self, key, MONSTERS[name][key])

        if not hasattr(self, 'horror'):
            self.horror = {
                'index': 4,
                'san': '-',
                'mod': '-'
            }
            self.no_horror = True
        if not hasattr(self, 'strength'):
            self.strength = {
                'index': 3,
                'san': '-',
                'mod': '-'
            }
            self.no_strength = True

        if '+' in str(self.toughness):
            self.toughness = int(inv_number + len(self.toughness))

        self.reckoning = self.set_reckoning(self.reckoning) if hasattr(self, 'reckoning') else None
        self.spawn = self.set_spawn(self.spawn) if hasattr(self, 'spawn') else None
        self.damage = 0
        self.monster_id = monster_id

    def set_reckoning(self, actions):
        pass
    
    def set_spawn(self, action):
        pass

    def description_dictionary(self):
        return {
            'name': human_readable(self.name),
            'toughness': self.toughness,
            'horror': self.horror['mod'],
            'horror_check': self.horror['index'],
            'sanity': self.horror['san'],
            'strength': self.strength['mod'],
            'strength_check': self.strength['index'],
            'damage': self.strength['str'],
            'damage_taken': self.damage,
            'text': self.text,
            'reckoning': self.reckoning_text
        }
    
    def heal(self, amt=1):
        self.damage -= amt
        self.damage = 0 if self.damage < 0 else self.damage

    def on_damage(self, amt, investigator=None):
        self.damage += amt
        self.damage = 0 if self.damage < 0 else self.damage
        return self.damage >= self.toughness