import yaml, random, math
from util import *
import astar
from monsters.monster import Monster
from investigators.investigator import Investigator

class LocationManager():
    def __init__(self):

        self.locations = {}
        self.all_investigators = {}
        self.all_monsters = []
        self.dead_investigators = {}
        try:
            with open('locations/locations.yaml') as stream:
                self.locations = yaml.safe_load(stream)
                for name in self.locations.keys():
                    self.locations[name]['gate'] = False
                    self.locations[name]['clue'] = False
                    self.locations[name]['monsters'] = []
                    self.locations[name]['investigators'] = []
                    self.locations[name]['expedition'] = False
                    self.locations[name]['eldritch'] = False
                    self.locations[name]['rumor'] = False
                    self.locations[name]['dead'] = []
        except:
            self.locations = {}
        self.rumors = {}
        self.monster_deck = []
        monster_counts = {'cultist': 6, 'avian_thrall': 1}
        for key in monster_counts.keys():
            for x in range(monster_counts[key]):
                self.monster_deck.append(key)

    def get_closest_location(self, point, zoom, map_location, area=None):
        for key in self.locations.keys():
            location = self.locations[key]
            scaled_location = (location['x'], location['y']) if zoom == 1 else (location['x'] * 2 + map_location[0], (location['y'] + 200) * 2 + map_location[1])
            if get_distance(scaled_location, point) < (area if area != None else 15 if location['size'] == 'small' else 50):
                return (scaled_location[0], scaled_location[1], key)
        return None
    
    def find_path(self, start, goal):
        neighbors = lambda name: list(map(lambda route: list(route.keys())[0], self.locations[name]['routes']))
        return astar.find_path(start, goal, neighbors)
    
    def spawn_monster(self, name, location, world, monster_id):
        monster = Monster(name, monster_id, len(self.all_investigators))
        monster.location = location
        monster.map = world
        self.all_monsters.append(monster)
        self.locations[location]['monsters'].append(monster)
        if not hasattr(monster, 'epic'):
            self.monster_deck.remove(name)
        return monster

    def spawn_investigator(self, name, location):
        self.all_investigators[name] = {'assets': [], 'unique_assets': [], 'artifacts': [], 'spells': [], 'conditions': [], 'rail': 0, 'ship': 0}
        self.locations[location]['investigators'].append(name)

    def get_location_coord(self, key):
        loc = self.locations[key]
        return (loc['x'], loc['y'])
    
    def get_zoom_pos(self, key, map_location):
        location = self.locations[key]
        return (location['x'] * 2 + map_location[0], (location['y'] + 200) * 2 + map_location[1])
    
    def move_unit(self, unit, kind, destination):
        if kind == 'investigators':
            loc = next((loc for loc in self.locations.keys() if unit in self.locations[loc]['investigators']))
        else:
            loc = unit.location
        self.locations[loc][kind].remove(unit)
        self.locations[destination][kind].append(unit)
        return loc
    
    def get_encounters(self, location):
        encounters = ['generic']
        if self.locations[location].get('color', None) != None:
            encounters.append(self.locations[location].get('color'))
        for kind in ['gate', 'eldritch', 'rumor', 'expedition', 'clue']:
            if self.locations[location][kind]:
                encounters.append(kind)
            if kind == 'rumor':
                rumor = next((rumor for rumor in self.rumors if self.rumors[rumor]['location'] == location), None)
                if rumor != None and self.rumors[rumor]['not_encounter']:
                    encounters.remove(kind)
        for name in self.dead_investigators:
            if self.dead_investigators[name]['location'] == location:
                encounters.append(name)
        return encounters
    
    def get_all(self, kind, is_array=False):
        count = []
        for loc in self.locations:
            if not is_array and self.locations[loc][kind]:
                count.append(loc)
            elif is_array:
                count += self.locations[loc][kind]
        return count
    
    def get_map_name(self, loc):
        return 'world'
    
    def create_ambush_monster(self, name=None):
        name = name if name != None else random.choice(self.monster_deck)
        return Monster(name, -1)