import yaml
from util import *
import astar
from monsters.monster import Monster

class LocationManager():
    def __init__(self):

        self.locations = {}
        self.clue_count = 0
        self.gate_count = {
            'red': 0,
            'blue': 0,
            'green': 0
        }

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
    
    def spawn_monster(self, name, location):
        self.locations[location]['monsters'].append(Monster(name))

    def add_gate(self, name):
        self.gate_count[self.locations[name]['gate_color']] += 1

    def get_location_coord(self, key):
        loc = self.locations[key]
        return (loc['x'], loc['y'])
    
    def get_zoom_pos(self, key, map_location):
        location = self.locations[key]
        return (location['x'] * 2 + map_location[0], (location['y'] + 200) * 2 + map_location[1])
    
    def move_investigator(self, name, destination):
        key = next((loc for loc in self.locations if name in self.locations[loc]['investigators']))
        self.locations[key]['investigators'].remove(name)
        self.locations[destination]['investigators'].append(name)
        return key
    
    def get_encounters(self, location):
        encounters = ['generic']
        if hasattr(self.locations[location], 'color'):
            encounters.append(self.locations[location].color)
        for kind in ['gate', 'eldritch', 'rumor', 'expedition', 'clue']:
            if self.locations[location][kind]:
                encounters.append(kind)
        return encounters