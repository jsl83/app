import arcade
import arcade.csscolor
import arcade.gui
import math
import random
import yaml
from util import *
from ancient_ones.ancient_one import AncientOne
from screens.ancient_pane import AncientOnePane
from investigators.investigator import Investigator
from screens.investigator_pane import InvestigatorPane
from screens.possessions_pane import PossessionsPane
from screens.reserve_pane import ReservePane
from screens.location_pane import LocationPane
from encounters.encounter_pane import EncounterPane
from locations.location_manager import LocationManager
from locations.map import Map
from screens.action_button import ActionButton

IMAGE_PATH_ROOT = ":resources:eldritch/images/"

with open('small_cards/assets.yaml') as stream:
    ASSET_DICTIONARY = yaml.safe_load(stream)

class HubScreen(arcade.View):
    
    def __init__(self, networker, investigator, ancient_one):
        super().__init__()
        self.background = None
        self.networker = networker
        self.networker.external_message_processor = self.set_listener

        self.investigator = Investigator(investigator)
        self.ancient_one = AncientOne(ancient_one)

        self.doom = 0
        self.omen = 0
        self.remaining_actions = 0
        
        self.item_actions = {}
        self.investigator_token = None
        self.original_investigator_location = ''
        self.server_message = ''

        for item in self.investigator.initial_items:
            request = item.split(':')
            #self.request_card(request[0], request[1])

        self.initial_click = (0,0)
        self.zoom = 1
        self.click_time = 0
        self.holding = None
        self.slow_move = (0, 0)
        self.slow_move_count = 0
        self.gui_enabled = True
        self.overlay_showing = False
        
        self.info_manager = arcade.gui.UIManager()
        self.ui_manager = arcade.gui.UIManager()
        self.choice_manager = arcade.gui.UIManager()
        self.choice_layout = arcade.gui.UILayout()
        self.doom_counter = arcade.gui.UITextureButton(x=10, y=760, scale=0.18, texture=arcade.load_texture(IMAGE_PATH_ROOT + 'maps/doom.png'))
        self.omen_counter = arcade.gui.UITextureButton(x=950, y=760, scale=0.35, texture=arcade.load_texture(IMAGE_PATH_ROOT + 'maps/omen.png'))
        ui_layout = arcade.gui.UILayout(x=0, y=0, width=1000, height=142).with_background(arcade.load_texture(IMAGE_PATH_ROOT + 'gui/ui_pane.png'))
        ui_layout.add(arcade.gui.UITextureButton(texture=arcade.load_texture(IMAGE_PATH_ROOT + 'gui/map_overlay.png'), y=-200, scale=0.5))
        ui_layout.add(self.doom_counter)
        ui_layout.add(self.omen_counter)
        self.overlay_toggle = ActionButton(x=10, y=142, width=336, height=87, action=self.toggle_overlay, texture='blank.png', style={'font_color': arcade.color.BLACK})
        index = 0
        for text in ['investigator', 'possessions', 'reserve', 'location', 'ancient_one']:
            ui_layout.add(ActionButton(index * 190 + 50, y=21, width=140, height=100, texture='buttons/placeholder.png', text=human_readable(text),
                                       action=self.switch_info_pane, action_args={'key': text}, texture_pressed='/buttons/pressed_placeholder.png'))
            index += 1

        self.maps = {
            'world': Map('world', (0, -200), 0.5)
        }
        self.location_manager = LocationManager()

        self.info_panes = {
            'investigator': InvestigatorPane(self.investigator, self),
            'possessions': PossessionsPane(self.investigator),
            'reserve': ReservePane(self),
            'location': LocationPane(self.location_manager),
            'ancient_one': AncientOnePane(self.ancient_one)
        }

        self.encounter_pane = EncounterPane(self)

        self.actions_taken = {
            'focus': {'taken': False, 'buttons': [self.info_panes['investigator'].focus_button]},
            'move': {'taken': False, 'buttons': []},
            'ticket': {'taken': False, 'buttons': [self.info_panes['investigator'].rail_button, self.info_panes['investigator'].ship_button]},
            'shop': {'taken': False, 'buttons': [self.info_panes['reserve'].acquire_button]},
            'personal': {'taken': False, 'buttons': [self.info_panes['investigator'].skill_button]},
            'rest': {'taken': False, 'buttons': [self.info_panes['investigator'].health_button]},
            'trade': {'taken': False, 'buttons': list(self.info_panes['location'].investigators.values())},
        }

        self.map = self.maps['world']
        self.info_pane = self.info_panes['investigator']
        self.info_panes['location'].location_select(self.investigator.location)

        self.info_manager.add(self.info_pane.layout)
        self.ui_manager.add(ui_layout)
        self.ui_manager.add(self.overlay_toggle)
        self.ui_manager.add(ActionButton(x=920, y=142, width=70, height=70, action=self.undo, texture='buttons/undo.png'))
        self.info_manager.enable()
        self.ui_manager.enable()
        self.choice_manager.enable()
        self.select_ui_button(0)
        self.set_doom(self.ancient_one.doom)
        self.set_omen(0, False)

        self.undo_action = {
            'action': None,
            'args': {}
        }

        self.networker.publish_payload({'message': 'ready'}, 'login')
        
    def on_draw(self):
        self.clear()
        self.map.draw()
        self.info_manager.draw()
        self.ui_manager.draw()
        self.choice_manager.draw()
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
        if self.holding == 'investigator':
            map_loc = self.map.get_location()
            location = self.location_manager.get_closest_location((x,y), self.zoom, map_loc, 50)
            if location == None:
                self.move_investigator(self.investigator.name, self.original_investigator_location)
            elif location[2] in self.in_movement_range().keys():
                tickets = self.in_movement_range()[location[2]]
                if len(tickets) > 1:
                    choices = []
                    for combo in tickets:
                        choices.append(ActionButton(texture='buttons/placeholder.png', action=self.ticket_move, text='Rail: ' + str(combo[0]) + '\nShip: ' + str(combo[1]),
                                                    width=200, height=100, action_args={'name': self.investigator.name, 'location': location[2], 'overlay': True,
                                                    'rail': combo[0], 'ship': combo[1], 'original': self.original_investigator_location}))
                    self.choice_layout = (create_choices(choices=choices, title='Choose Tickets'))
                    self.show_overlay()
                else:
                    self.ticket_move(self.investigator.name, location[2], tickets[0][0], tickets[0][1], self.original_investigator_location)
            else:
                self.move_investigator(self.investigator.name, self.original_investigator_location)
        elif x < 1000 and y > 142 and self.click_time <= 10 and self.gui_enabled:
            location = self.location_manager.get_closest_location((x,y), self.zoom, self.map.get_location())
            if location != None:
                if self.zoom == 2:
                    self.slow_move = ((500 - location[0]) / 10, (471 - location[1]) / 10)
                self.info_panes['location'].location_select(location[2])
                self.switch_info_pane('location')
                self.select_ui_button(3)
            buttons = list(self.ui_manager.get_widgets_at((x,y)))
            if len(buttons) > 0 and type(buttons[0]) == ActionButton:
                button = buttons[0]
                button.action()
        else:
            ui_buttons = list(self.info_manager.get_widgets_at((x,y))) + list(self.ui_manager.get_widgets_at((x,y))) + list(self.choice_manager.get_widgets_at((x,y)))
            if len(ui_buttons) > 0:
                for button in ui_buttons:
                    if type(button) == ActionButton and button.enabled:
                        key = next((key for key in self.actions_taken.keys() if button in self.actions_taken[key]['buttons']), None)
                        if key == None or (not self.actions_taken[key]['taken'] and self.remaining_actions > 0):
                            button.click_action()
                            buttons = self.get_ui_buttons()
                            if button in buttons:
                                for x in buttons:
                                    x.select(False)
                                button.select(True)
        self.holding = None

    def on_mouse_press(self, x, y, button, modifiers):
        if x < 1000 and y > 142 and not self.overlay_showing:
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
            if self.remaining_actions > 0 and not self.actions_taken['move']['taken']:
                location = self.location_manager.get_closest_location((x, y), self.zoom, self.map.get_location(), 40)
                if location != None:
                    key = location[2]
                    investigators = self.location_manager.locations[key]['investigators']
                    if len(investigators) > 0 and self.investigator.name in investigators:
                        self.holding = 'investigator'
                        tokens = self.map.get_tokens('investigator', key, self.investigator.name)
                        self.investigator_token = tokens[0] if self.zoom == 2 else tokens[1]
                        self.original_investigator_location = key
                    
        elif (self.info_pane == self.info_panes['possessions'] or (self.info_pane == self.info_panes['reserve'] and self.info_panes['reserve'].discard_view)) and x > 1000:
            self.holding = 'items'
            self.click_time = 0

    def on_mouse_motion(self, x, y, dx, dy):
        if self.holding == 'map':
            self.map.move(dx, dy)
            self.check_map_boundaries()
        elif self.holding == 'items':
            self.info_pane.move(dy)
        elif self.holding == 'investigator':
            self.investigator_token.move(dx, dy)

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
        if self.info_pane != self.info_panes[key] and self.gui_enabled:
            self.info_manager.children = {0:[]}
            self.info_pane = self.info_panes[key]
            self.info_manager.add(self.info_pane.layout)
            if key == 'possessions':
                self.info_pane.reset()
            elif key == 'reserve':
                self.info_pane.reset_discard()

    def show_encounter_pane(self):
        self.info_manager.children = {0:[]}
        self.info_pane = self.encounter_pane
        self.info_manager.add(self.info_pane.layout)
        self.gui_set(False)

    def toggle_overlay(self):
        if len(self.choice_layout.children) > 0:
            if self.overlay_showing:
                self.choice_manager.clear()
                button = next((button for button in self.choice_layout.children if hasattr(button, 'title')), None)
                title = 'SHOW OVERLAY' if button == None else button.title
                self.overlay_toggle.text = title
                self.overlay_showing = False
            else:
                self.choice_manager.add(self.choice_layout)
                self.overlay_toggle.text = 'HIDE OVERLAY'
                self.overlay_showing = True
            self.ui_manager.trigger_render()

    def set_listener(self, topic, payload):
        match payload['message']:
            case 'spawn':
                name = '' if payload['value'] not in ['monster', 'investigator'] else payload['name']
                self.maps[payload['map']].spawn(payload['value'], self.location_manager, payload['location'], name)
                if payload['value'] == 'investigator':
                    self.info_panes['location'].add_investigator(payload['name'])
                elif payload['value'] == 'monster':
                    self.location_manager.spawn_monster(name, payload['location'])
                if payload['location'] == self.info_panes['location'].selected:
                    self.info_panes['location'].update_all()
            case 'spells':
                spell = payload['value'].split(':')
                self.item_received('spells', spell[0], spell[1])
            case 'restock':
                self.info_panes['reserve'].restock(payload['removed'].split(':'), payload['value'].split(':'))
            case 'conditions':
                card = payload['value'].split(':')
                if next((condition for condition in self.investigator.possessions['conditions'] if condition.name == card[0]), None) is not None:
                    self.networker.publish_payload({'message': 'discard', 'value': payload['value']}, self.investigator.name)
                else:
                    self.item_received('conditions', card[0], card[1])
                    if card[0] == 'debt':
                        self.info_panes['reserve'].debt_button.disable()
            case 'asset':
                self.item_received('assets', payload['value'])
            case 'discard':
                self.info_panes['reserve'].discard_item(payload['value'])
            case 'investigator_moved':
                self.move_investigator(payload['value'], payload['destination'])
            case 'choose_lead':
                portraits = []
                for name in self.info_panes['location'].investigators:
                    portraits.append(ActionButton(texture='investigators/' + name + '_portrait.png', scale=0.4, action=self.networker.publish_payload,
                                                  action_args={'payload': {'message': 'lead_selected', 'value': name},'topic': self.investigator.name}))
                self.choice_layout = create_choices(choices=portraits, title="Choose Lead Investigator")
                self.show_overlay()
            case 'lead_selected':
                self.clear_overlay()
            case 'player_turn':
                if payload['value'] == 'action':
                    self.remaining_actions = 2
                elif payload['value'] == 'encounter':
                    self.encounter_pane.encounter_phase(self.investigator.location)
            case 'encounter_choice':
                self.clear_overlay()
                self.encounter_pane.start_encounter(payload['value'])
                self.show_encounter_pane()

    def draw_point_meters(self, max, current, pos, color):
        degrees = 360 / max
        for x in range(max - current, max):
            x = max - x - 1
            arcade.draw_arc_outline(
                pos, 577, 110, 110, color, x * degrees + 93, (x + 1) * degrees + 87, 18)
        angle = (max - current) * degrees * math.pi / 180
        x = 55 * math.sin(angle) + pos
        y = 55 * math.cos(angle) + 577
        arcade.draw_circle_filled(x, y, 15, color)
        arcade.draw_text(current, x, y+2, width=20, anchor_x='center', anchor_y='center', bold=True, font_size=17, font_name="calibri")

    def run_test(self, skill, mod=0, pane=None):
        choices = []
        rolls = []
        options = []
        titles = ['Lore', 'Influence', 'Observation', 'Strength', 'Will']
        for x in range(self.investigator.skills[skill] + mod):
            roll = random.randint(1, 6)
            rolls.append(roll)
            choices.append(arcade.gui.UITextureButton(texture = arcade.load_texture(IMAGE_PATH_ROOT + 'icons/die_' + str(roll) + '.png')))
        fail = next((roll for roll in rolls if roll < self.investigator.success), None)
        if fail != None:
            def reroll(kind, option_index):
                fail = next((roll for roll in rolls if roll < self.investigator.success), None)
                if fail != None:
                    index = rolls.index(fail)
                    new_roll = random.randint(1, 6)
                    choices[index].texture = arcade.load_texture(IMAGE_PATH_ROOT + 'icons/die_' + str(new_roll) + '.png')
                    if pane != None:
                        pane.reroll(new_roll, fail)
                    if kind == 'focus':
                        self.investigator.focus -= 1
                        if self.investigator.focus == 0:
                            options[option_index].disable()
                    elif kind == 'clue' and self.investigator.clues > 0:
                        self.investigator.clues -= 1
                        if self.investigator.clues == 0:
                            options[option_index].disable()
                    elif not self.investigator.reroll_items[skill][kind].action_used:
                        self.investigator.reroll_items[skill][kind].action_used = True
                        options[option_index].disable()
                else:
                    for x in options:
                        x.disable()
            option_index = 0
            if self.investigator.focus > 0:
                focus_button = ActionButton(action=reroll, action_args={'kind': 'focus', 'option_index': 0}, texture='icons/focus.png', text='Use', text_position=(20,-2))
                options.append(focus_button)
                option_index += 1
            if self.investigator.clues > 0:
                clue_button = ActionButton(action=reroll, action_args={'kind': 'focus', 'option_index': option_index}, texture='icons/clue.png', text='Use', text_position=(20,-2))
                options.append(clue_button)
                option_index += 1
            items = self.investigator.reroll_items[skill].keys()
            if len(items) > 0:
                for x in items:
                    item_button = ActionButton(action=reroll, action_args={'kind': x, 'option_index': option_index}, texture='buttons/placeholder.png', text=human_readable(x))
                    options.append(item_button)
                    option_index += 1
        self.choice_layout = create_choices(choices = choices, title=titles[skill] + ' Test', options=options, offset=(0,150))
        self.show_overlay()
        return rolls
    
    def gui_set(self, able=True):
        self.gui_enabled = able
        for x in self.get_ui_buttons():
            if able:
                x.enable()
            else:
                x.disable()

    def get_ui_buttons(self):
        buttons = self.ui_manager.children[0][0].children
        return buttons[len(buttons) - 5: len(buttons)]
    
    def select_ui_button(self, index):
        buttons = self.get_ui_buttons()
        for button in buttons:
            button.select(False)
        buttons[index].select(True)

    def get_item_info(self, name):
        return ASSET_DICTIONARY[name]
    
    def request_card(self, kind, name, command='get:'):
        self.networker.publish_payload({'message': kind, 'value': command + name}, self.investigator.name)

    def discard_card(self, kind, name):
        self.networker.publish_payload({'message': kind, 'value': 'discard:' + name}, self.investigator.name)

    def clear_overlay(self):
        self.choice_layout.clear()
        self.choice_manager.clear()
        self.overlay_toggle.text = self.server_message
        self.overlay_showing = False
        self.ui_manager.trigger_render()
        self.choice_manager.trigger_render()

    def show_overlay(self):
        self.choice_manager.add(self.choice_layout)
        self.overlay_showing = True
        self.overlay_toggle.text = 'HIDE OVERLAY'        

    def item_received(self, kind, name, variant=None):
        self.investigator.get_item(kind, name, variant)
        self.info_panes['possessions'].setup()

    def request_spawn(self, kind, name='', location='', number='1'):
        self.networker.publish_payload({'message': 'spawn', 'value': kind, 'location': location, 'name': name, 'number': number}, self.investigator.name)

    def set_doom(self, number):
        if number <= self.ancient_one.doom and number >= 0:
            self.doom_counter.move(10 + (20 - number) * 42.3 - self.doom_counter.x, 0)
            self.doom = number
            if number == 0:
                self.ancient_one.awaken()

    def increment_doom(self, interval):
        doom = self.doom + interval
        doom = 20 if doom > 20 else 0 if doom < 0 else doom
        self.set_doom(doom)

    def set_omen(self, index, trigger_gates=True):
        positions = [(921, 757), (956, 737), (937, 703), (904, 724)]
        colors = ['green', 'blue', 'red', 'blue']
        self.omen_counter.move(positions[index][0] - self.omen_counter.x, positions[index][1] - self.omen_counter.y)
        if trigger_gates:
            self.increment_doom(-self.location_manager.gate_count[colors[index]])

    def increment_omen(self, trigger_gates=True):
        self.omen += 1
        if self.omen == 4:
            self.omen = 0
        self.set_omen(self.omen, trigger_gates)

    def undo_move(self, loc, rail, ship):
        self.networker.publish_payload({'message': 'move_investigator', 'value': self.investigator.name, 'destination': loc}, self.investigator.name)
        self.investigator.rail_tickets += rail
        self.investigator.ship_tickets += ship
        self.info_panes['investigator'].set_ticket_counts()
        self.undo_action = None
        self.actions_taken['move']['taken'] = False
        self.remaining_actions += 1

    def move_investigator(self, name, location):
        destination = self.location_manager.get_location_coord(location)
        zoom_destination = self.location_manager.get_zoom_pos(location, self.map.get_location())
        key = self.location_manager.move_investigator(name, location)
        if name == self.investigator.name:
            self.investigator.location = location
        self.map.move_tokens('investigator', key, destination, zoom_destination, location, name)

    def in_movement_range(self):
        locations = self.location_manager.locations
        rails = self.investigator.rail_tickets
        ships = self.investigator.ship_tickets
        start_loc = next((start for start in locations if self.investigator.name in locations[start]['investigators']))
        move_dict = {}
        tickets = {'rail': 0, 'ship': 0}
        for route in locations[start_loc]['routes'].keys():
            move_dict[route] = [[0,0]]
            for move_one in locations[route]['routes'].keys():
                tickets = {'rail': 0, 'ship': 0}
                if move_one != start_loc and locations[route]['routes'][move_one] != 'uncharted':
                    tickets[locations[route]['routes'][move_one]] += 1
                    if tickets['rail'] <= rails and tickets['ship'] <= ships:
                        if move_one not in move_dict.keys():
                            move_dict[move_one] = []
                        if [tickets['rail'], tickets['ship']] not in move_dict[move_one] and [0,0] not in move_dict[move_one]:
                            rail_add = tickets['rail'] + 1
                            ship_add = tickets['ship'] + 1
                            move_dict[move_one].append([tickets['rail'], tickets['ship']])
                            for combo in [[rail_add, tickets['ship']], [tickets['rail'], ship_add]]:
                                if combo in move_dict[move_one]:
                                    move_dict[move_one].remove(combo)
                        for move_two in locations[move_one]['routes'].keys():
                            if move_two != start_loc and locations[move_one]['routes'][move_two] != 'uncharted':
                                tickets[locations[move_one]['routes'][move_two]] += 1
                                if tickets['rail'] <= rails and tickets['ship'] <= ships:
                                    if move_two not in move_dict.keys():
                                        move_dict[move_two] = []
                                    tix = [tickets['rail'], tickets['ship']]
                                    rail_check = tickets['rail'] - 1
                                    ship_check = tickets['ship'] - 1
                                    omit = False
                                    for combo in [tix, [0,0], [rail_check, tickets['ship']], [tickets['rail'], ship_check]]:
                                        if combo in move_dict[move_two]:
                                            omit = True
                                    if not omit:
                                        move_dict[move_two].append([tickets['rail'], tickets['ship']])
                                tickets[locations[move_one]['routes'][move_two]] -= 1
                    tickets[locations[route]['routes'][move_one]] -= 1
                tickets = {'rail': 0, 'ship': 0}
        return move_dict
    
    def ticket_move(self, name, location, rail, ship, original, overlay=False):
        self.undo_action = {
            'action': self.undo_move,
            'args': {'loc': original, 'rail': rail, 'ship': ship}
        }
        self.investigator.rail_tickets -= rail
        self.investigator.ship_tickets -= ship
        self.info_panes['investigator'].set_ticket_counts()
        self.networker.publish_payload({'message': 'move_investigator', 'value': name, 'destination': location}, self.investigator.name)
        if overlay:
            self.clear_overlay()
        self.action_taken('move')
    
    def undo(self):
        if self.undo_action != None:
            self.undo_action['action'](**self.undo_action['args'])

    def action_taken(self, action):
        self.actions_taken[action]['taken'] = True
        self.remaining_actions -= 1
        if self.remaining_actions == 0:
            self.undo_action = None
            self.networker.publish_payload({'message': 'turn_finished', 'value': None}, self.investigator.name)
            for action in self.actions_taken:
                self.actions_taken[action]['taken'] = False