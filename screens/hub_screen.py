import arcade
import arcade.csscolor
import arcade.gui
import math
from util import *
from investigators.investigator import Investigator
from screens.investigator_pane import InvestigatorPane
from screens.possessions_pane import PossessionsPane
from locations.location_manager import LocationManager
from locations.map import Map
from screens.action_button import ActionButton

IMAGE_PATH_ROOT = ":resources:eldritch/images/"

class HubScreen(arcade.View):
    
    def __init__(self, networker, investigator):
        super().__init__()
        self.background = None
        self.networker = networker
        self.networker.external_message_processor = self.set_listener

        investigator = 'akachi_onyele'

        self.investigator = Investigator(investigator)

        for item in self.investigator.initial_items:
            request = item.split(':')
            self.networker.publish_payload({'message': request[0], 'value': 'get:' + request[1]}, self.investigator.name)

        self.initial_click = (0,0)
        self.zoom = 1
        self.click_time = 0
        self.holding = None
        self.slow_move = (0, 0)
        self.slow_move_count = 0
        
        self.info_manager = arcade.gui.UIManager()
        self.ui_manager = arcade.gui.UIManager()
        ui_layout = arcade.gui.UILayout(x=0, y=0, width=1000, height=142).with_background(arcade.load_texture(IMAGE_PATH_ROOT + 'gui/ui_pane.png'))

        index = 0
        for text in ['investigator', 'possessions', 'reserve', 'location', 'ancient_one']:
            ui_layout.add(ActionButton(index * 190 + 50, y=21, width=140, height=100, texture=arcade.load_texture(
                IMAGE_PATH_ROOT + 'buttons/placeholder.png'), text=human_readable(text), action=self.switch_info_pane, action_args={'key': text}))
            index += 1

        self.maps = {
            'world': Map('world', (0, -200), 0.5)
        }
        self.info_panes = {
            'investigator': InvestigatorPane(self.investigator),
            'possessions': PossessionsPane(self.investigator)
        }

        self.map = self.maps['world']

        self.info_pane = self.info_panes['investigator']

        self.info_manager.add(self.info_pane.layout)
        self.ui_manager.add(ui_layout)
        self.info_manager.enable()
        self.ui_manager.enable()

        self.location_manager = LocationManager()

        self.networker.publish_payload({'message': 'ready'}, 'login')

    def on_draw(self):
        self.clear()
        self.map.draw()
        self.info_manager.draw()
        self.ui_manager.draw()
        self.click_time += 1
        if self.slow_move[0] != 0 or self.slow_move[1] != 0:
            self.map.move(self.slow_move[0], self.slow_move[1])
            self.check_map_boundaries()
            self.slow_move_count += 1
            if self.slow_move_count == 10:
                self.slow_move = (0,0)
                self.slow_move_count = 0

        if self.info_pane == self.info_panes['investigator']:
            self.draw_point_meters(self.investigator.max_health, self.investigator.health, 1075, (204,43,40))
            self.draw_point_meters(self.investigator.max_sanity, self.investigator.sanity, 1202, (84, 117, 184))
    
    def on_mouse_release(self, x, y, button, modifiers):
        self.holding = None
        if x < 1000 and y > 142 and self.click_time <= 5:
            location = self.location_manager.get_closest_location((x,y), self.zoom, self.map.get_location())
            if location != None and self.zoom == 2:
                self.slow_move = ((500 - location[0]) / 10, (471 - location[1]) / 10)
        else:
            ui_buttons = list(self.info_manager.get_widgets_at((x,y))) + list(self.ui_manager.get_widgets_at((x,y)))
            if len(ui_buttons) > 0 and type(ui_buttons[0]) == ActionButton and ui_buttons[0].enabled:
                ui_buttons[0].action() if ui_buttons[0].action_args == None else ui_buttons[0].action(**ui_buttons[0].action_args)

    def on_mouse_press(self, x, y, button, modifiers):
        if x < 1000 and y > 142:
            if self.click_time < 25 and get_distance((x,y), self.initial_click) < 50:
                if self.zoom == 1:
                    self.map.zoom(2, 500 - (x * 2), 471 - (y * 2))
                    self.zoom = 2
                else:
                    self.map.zoom(0.5)
                    self.zoom = 1
                self.check_map_boundaries()
            self.holding = 'map'
            self.initial_click = (x, y)
            self.click_time = 0
        elif self.info_pane == self.info_panes['possessions'] and x > 1000:
            self.holding = 'items'
            self.click_time = 0

    def on_mouse_motion(self, x, y, dx, dy):
        if self.holding == 'map':
            self.map.move(dx, dy)
            self.check_map_boundaries()
        elif self.holding == 'items':
            self.info_pane.move(dy) 

    def check_map_boundaries(self):
        x, y = self.map.get_location()[0], self.map.get_location()[1]
        dx, dy = 0, 0
        if x > 0:
            dx = -x
        elif  x < (-1000 if self.zoom == 2 else 0):
            dx = -x - (1000 if self.zoom == 2 else 0)
        if y > -542:
            dy = -y + (-542 if self.zoom == 2 else -200)
        elif y < 800 - (1000 * self.zoom):
            dy = -y + (-1200 if self.zoom == 2 else -200)
        self.map.move(dx, dy)

    def switch_map(self, key):
        self.map = self.maps[key]

    def switch_info_pane(self, key):
        if self.info_pane != self.info_panes[key]:
            self.info_manager.children = {0:[]}
            self.info_pane = self.info_panes[key]
            self.info_manager.add(self.info_pane.layout)
            if key == 'possessions':
                self.info_pane.reset()

    def set_listener(self, topic, payload):
        match payload['message']:
            case 'spawn':
                self.maps[payload['map']].spawn(payload['value'], self.location_manager.locations[payload['location']], payload['location'])
            case 'spells':
                spell = payload['value'].split(':')
                self.investigator.get_item('spells', spell[0], spell[1])
                self.info_panes['possessions'].setup()

    def draw_point_meters(self, max, current, pos, color):
        degrees = 360 / max
        for x in range(max - current, max):
            x = max - x - 1
            arcade.draw_arc_outline(
                pos, 597, 110, 110, color, x * degrees + 93, (x + 1) * degrees + 87, 18)
        angle = (max - current) * degrees * math.pi / 180
        x = 55 * math.sin(angle) + pos
        y = 55 * math.cos(angle) + 597
        arcade.draw_circle_filled(x, y, 15, color)
        arcade.draw_text(current, x, y+2, width=20, anchor_x='center', anchor_y='center', bold=True, font_size=17, font_name="calibri")
