import arcade
import arcade.csscolor
import arcade.gui
import math
from util import *
from investigators.investigator import Investigator
from investigators.investigator_pane import InvestigatorPane
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
        self.holding = False
        self.slow_move = (0, 0)
        self.slow_move_count = 0
        
        self.map_manager = arcade.gui.UIManager()
        self.info_manager = arcade.gui.UIManager()
        self.ui_manager = arcade.gui.UIManager()
        self.map_token_manager = arcade.gui.UIManager()
        ui_layout = arcade.gui.UILayout(x=0, y=0, width=1000, height=142)

        index = 0
        for text in ['investigator', 'possessions', 'reserve', 'location', 'ancient_one']:
            ui_layout.add(ActionButton(index * 190 + 50, y=21, width=140, height=100, texture=arcade.load_texture(
                IMAGE_PATH_ROOT + 'buttons/placeholder.png'), text=human_readable(text), action=self.switch_info_pane, action_args={'key': text}))
            index += 1

        self.maps = {
            'world': {
                'map': Map('world', (0, -200), 0.5),
                'tokens': arcade.gui.UILayout(x=0, y=142, width=1000, height=658)
            }
        }
        self.info_panes = {
            'investigator': InvestigatorPane(self.investigator)
        }

        self.map = self.maps['world']['map']
        self.info_pane = self.info_panes['investigator']

        self.map_manager.add(self.map.layout)
        self.info_manager.add(self.info_pane.layout)
        self.ui_manager.add(ui_layout)
        self.map_token_manager.add(self.maps['world']['tokens'])
        self.map_manager.enable()
        self.info_manager.enable()
        self.ui_manager.enable()
        self.map_token_manager.enable()

        self.location_manager = LocationManager()

        self.networker.publish_payload({'message': 'ready'}, 'login')

    def on_draw(self):
        self.clear()
        self.map_manager.draw()
        self.info_manager.draw()
        self.ui_manager.draw()
        self.map_token_manager.draw()
        self.click_time += 1
        if self.slow_move[0] != 0 or self.slow_move[1] != 0:
            self.map.move(self.slow_move[0], self.slow_move[1])
            self.check_map_boundaries()
            self.slow_move_count += 1
            if self.slow_move_count == 10:
                self.slow_move = (0,0)
                self.slow_move_count = 0
        self.draw_point_meters(self.investigator.max_health, self.investigator.health, 1075, (204,43,40))
        self.draw_point_meters(self.investigator.max_sanity, self.investigator.sanity, 1202, (84, 117, 184))
    
    def on_mouse_release(self, x, y, button, modifiers):
        self.holding = False
        if x < 1000 and y > 200:
            location = self.location_manager.get_closest_location((x,y), self.zoom, self.map.get_location())
            if location != None and self.zoom == 2:
                self.slow_move = ((500 - x) / 10, (471 - y) / 10)
        else:
            ui_buttons = list(self.info_manager.get_widgets_at((x,y))) + list(self.ui_manager.get_widgets_at((x,y)))
            if len(ui_buttons) > 0 and type(ui_buttons[0]) == ActionButton and ui_buttons[0].enabled:
                ui_buttons[0].action() if ui_buttons[0].action_args == None else ui_buttons[0].action(**ui_buttons[0].action_args)

    def on_mouse_press(self, x, y, button, modifiers):
        map = list(self.map_manager.get_widgets_at((x,y)))
        ui_buttons = list(self.info_manager.get_widgets_at((x,y)))
        if x < 1000 and y > 200:
            if self.click_time < 25 and get_distance((x,y), self.initial_click) < 50:
                if self.zoom == 1:
                    self.map.zoom(2)
                    self.zoom = 2
                    self.map.move(500 - (x * 2), 471 - (y * 2))
                else:
                    self.map.zoom(0.5)
                    self.zoom = 1
                self.check_map_boundaries()
            self.holding = True
            self.click_time = 0
            self.initial_click = (x, y)

    def on_mouse_motion(self, x, y, dx, dy):
        if self.holding:
            self.map.move(dx, dy)
            self.check_map_boundaries()

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
        self.map_manager.children = {0:[]}
        self.map_manager.add(self.map.layout)

    def switch_info_pane(self, key):
        self.info_pane = self.info_panes[key]
        self.info_manager.children = {0:[]}
        self.info_manager.add(self.info_pane)

    def set_listener(self, topic, payload):
        match payload['message']:
            case 'spawn':
                location = self.location_manager.locations[payload['location']]
                kind = payload['value']
                if kind == 'monster':
                    pass
                else:
                    location[kind] = True
                    if kind == 'clue':
                        button = arcade.gui.UITextureButton(location['x'], location['y'],
                            texture=arcade.load_texture(IMAGE_PATH_ROOT + 'icons/clue.png'), scale=0.75)
                        button.kind = kind
                        button.location = payload['location']
                        self.maps[payload['map']]['tokens'].add(button)

            case 'spells':
                self.investigator.get_item('spells', payload['value'])

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
