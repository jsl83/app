import yaml
from util import *
import astar

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
        except:
            self.locations = {}

    def get_closest_location(self, point, zoom, map_location):
        for key in self.locations.keys():
            location = self.locations[key]
            scaled_location = (location['x'], location['y']) if zoom == 1 else (location['x'] * 2 + map_location[0], (location['y'] + 200) * 2 + map_location[1])
            if get_distance(scaled_location, point) < (25 if location['size'] == 'small' else 50):
                return key
        return None
    
    def find_path(self, start, goal):
        neighbors = lambda name: list(map(lambda route: list(route.keys())[0], self.locations[name]['routes']))
        return astar.find_path(start, goal, neighbors)