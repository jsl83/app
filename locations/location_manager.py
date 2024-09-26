import arcade
import arcade.gui
import yaml
from util import *
from locations.location import Location

class LocationManager():
    def __init__(self):

        self.locations = []

        try:
            with open('locations/locations.yaml') as stream:
                locations = yaml.safe_load(stream)
                for location in locations:
                    self.locations.append(Location(locations[location]))
        except:
            self.locations = []

    def get_closest_location(self, point, zoom, map_location):
        for location in self.locations:
            scaled_location = (location.x, location.y) if zoom == 1 else (location.x * 2 + map_location[0], (location.y + 200) * 2 + map_location[1])
            if get_distance(scaled_location, point) < (25 if location.size == 'small' else 50):
                return location
        return None