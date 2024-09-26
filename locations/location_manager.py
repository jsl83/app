import arcade
import arcade.gui
import yaml
from util import *
from locations.location import Location
import astar

class LocationManager():
    def __init__(self):

        self.locations = {}

        try:
            with open('locations/locations.yaml') as stream:
                locations = yaml.safe_load(stream)
                for name in locations.keys():
                    self.locations[name] = Location(locations[name])
        except:
            self.locations = {}

    def get_closest_location(self, point, zoom, map_location):
        for key in self.locations.keys():
            location = self.locations[key]
            scaled_location = (location.x, location.y) if zoom == 1 else (location.x * 2 + map_location[0], (location.y + 200) * 2 + map_location[1])
            if get_distance(scaled_location, point) < (25 if location.size == 'small' else 50):
                return key
        return None
    
    def find_path(self, start, goal):
        neighbors = lambda name: self.locations[name].get_route_names()
        return astar.find_path(start, goal, neighbors)