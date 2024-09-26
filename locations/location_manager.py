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

    def get_closest_location(self, point, distance=25):
        print(point)
        for location in self.locations:
            print(location.coordinates)
            if get_distance(location.coordinates, point) < (25 if location.size == 'small' else 80):
                return location
        return None