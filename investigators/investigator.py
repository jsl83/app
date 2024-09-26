import arcade
import yaml
from util import *

IMAGE_PATH_ROOT = ":resources:eldritch/images/investigators/"
INVESTIGATORS = None

with open('investigators/investigators.yaml') as stream:
    try:
        INVESTIGATORS = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        INVESTIGATORS = []

class Investigator():

    def __init__(self, name):
        self.front = None
        self.back = None
        self.portrait = None
        self.name = None
        self.label = ''
        self.skills = [0,0,0,0,0]
        self.assets = []
        self.unique_assets = []
        self.conditions = []
        self.artifacts = []
        self.clues = []
        self.focus = 0
        self.ship_tickets = 0
        self.rail_tickets = 0
        self.location = None

    def char_selected(self, name):
        self.front = arcade.load_texture(IMAGE_PATH_ROOT + name + '_front.png')
        self.back = arcade.load_texture(IMAGE_PATH_ROOT + name + '_back.png')
        self.portrait = arcade.load_texture(IMAGE_PATH_ROOT + name + '_portrait.png')
        self.label = human_readable(name)
        self.name = name