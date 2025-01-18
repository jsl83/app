import arcade, arcade.csscolor, arcade.gui
import math, random, copy
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

class HubScreen(arcade.View):
    
    def __init__(self, networker, investigator, ancient_one, all_investigators):
        super().__init__()
        self.background = None
        self.networker = networker
        self.networker.external_message_processor = self.set_listener

        self.ancient_one = AncientOne(ancient_one)

        self.doom = 0
        self.omen = 0
        self.remaining_actions = 0
        self.triggers = {
            'monster_kill': []
        }
        
        self.item_actions = {}
        self.investigator_token = None
        self.original_investigator_location = ''
        self.server_message = ''
        self.lead_investigator = None

        self.initial_click = (0,0)
        self.zoom = 1
        self.click_time = 0
        self.holding = None
        self.slow_move = (0, 0)
        self.slow_move_count = 0
        self.gui_enabled = True
        self.overlay_showing = False
        self.my_turn = False
        
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

        self.actions_taken = {
            'focus': False,
            'move': False,
            'ticket': False,
            'shop': False,
            'personal': False,
            'rest': False,
            'trade': False,
        }

        self.map = self.maps['world']
        self.location_manager = LocationManager(len(all_investigators))
        for name in all_investigators:
            self.location_manager.spawn_investigator(name)
            self.maps['world'].spawn('investigators', self.location_manager, self.location_manager.all_investigators[name].location, name)

        self.investigator = self.location_manager.all_investigators[investigator]
        self.encounter_pane = EncounterPane(self)

        self.info_panes = {
            'investigator': InvestigatorPane(self.investigator, self),
            'possessions': PossessionsPane(self.investigator),
            'reserve': ReservePane(self),
            'location': LocationPane(self.location_manager, self),
            'ancient_one': AncientOnePane(self.ancient_one)
        }
        self.info_pane = self.info_panes['investigator']
        #self.info_panes['location'].location_select(self.investigator.location)

        self.info_manager.add(self.info_pane.layout)
        self.ui_manager.add(ui_layout)
        self.ui_manager.add(self.overlay_toggle)
        self.ui_manager.add(ActionButton(x=920, y=142, width=70, height=70, action=self.undo, texture='buttons/undo.png'))
        self.info_manager.enable()
        self.ui_manager.enable()
        self.choice_manager.enable()
        self.select_ui_button(0)
        self.set_doom(self.ancient_one.doom)
        self.set_omen(0)

        self.undo_action = {
            'action': None,
            'args': {}
        }

        self.networker.publish_payload({'message': 'ready'}, 'login')

        '''
        #FOR TESTING
        self.request_card('assets', 'arcane_tome')
        self.request_card('assets', 'axe')
        self.request_card('assets', 'arcane_scholar')
        #self.request_card('conditions', 'amnesia')
        self.investigator.sanity -= 3
        self.investigator.clues.append('world:arkham')
        self.info_panes['investigator'].clue_button.text = 'x ' + str(len(self.investigator.clues))
        self.is_first = True
        self.location_manager.player_count = 1
        #self.request_card('conditions', 'blessed')
        #END TESTING
        '''
        #self.investigator.clues.append('world:arkham')

    def load_investigator(self, name):
        self.investigator = Investigator(name)
        self.info_panes['investigator'] = InvestigatorPane(self.investigator, self)
        self.info_panes['possessions'] = PossessionsPane(self.investigator)
        self.info_panes['possessions'].setup()
        for item in self.investigator.initial_items:
            request = item.split(':')
            self.request_card(request[0], request[1])
        self.networker.publish_payload({'message': 'update_hpsan', 'hp': self.investigator.health, 'san': self.investigator.sanity}, self.investigator.name)
        self.gui_set(True)
        self.encounter_pane.finish(True)
        self.encounter_pane.investigator = self.investigator
        self.info_panes['location'].possession_screen.investigator = self.investigator

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
        if self.holding == 'investigator' and self.click_time >= 10:
            map_loc = self.map.get_location()
            location = self.location_manager.get_closest_location((x,y), self.zoom, map_loc, 50)
            if self.encounter_pane.move_action != None:
                if location[2] in self.encounter_pane.allowed_locs:
                    self.move_unit(self.investigator.name, location[2])
                    self.original_investigator_location = location[2]
                    self.encounter_pane.move_action()
                else:
                    self.move_unit(self.investigator.name, self.original_investigator_location)
            else:
                if location == None:
                    self.move_unit(self.investigator.name, self.original_investigator_location)
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
                    self.move_unit(self.investigator.name, self.original_investigator_location)
        elif x < 1000 and y > 142 and self.click_time <= 10 and (self.gui_enabled or self.encounter_pane.click_action != None):
            location = self.location_manager.get_closest_location((x,y), self.zoom, self.map.get_location())
            if location != None:
                if self.encounter_pane.click_action != None:
                    self.encounter_pane.click_action(location[2])
                else:
                    if self.zoom == 2:
                        self.slow_move = ((500 - location[0]) / 10, (471 - location[1]) / 10)
                    self.info_panes['location'].location_select(location[2])
                    self.switch_info_pane('location')
                    self.select_ui_button(3)
                    self.info_manager.trigger_render()
            buttons = list(self.ui_manager.get_widgets_at((x,y)))
            if len(buttons) > 0 and type(buttons[0]) == ActionButton:
                buttons[0].action()
        else:
            ui_buttons = list(self.info_manager.get_widgets_at((x,y))) + list(self.ui_manager.get_widgets_at((x,y))) + list(self.choice_manager.get_widgets_at((x,y)))
            if len(ui_buttons) > 0:
                for button in ui_buttons:
                    if type(button) == ActionButton and button.enabled:
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
            if (self.remaining_actions > 0 and not self.actions_taken['move']) or self.encounter_pane.move_action != None:
                location = self.location_manager.get_closest_location((x, y), self.zoom, self.map.get_location(), 40)
                if location != None:
                    key = location[2]
                    if self.investigator.location == key:
                        self.holding = 'investigator'
                        tokens = self.map.get_tokens('investigators', key, self.investigator.name)
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
            self.info_pane.on_show()

    def show_encounter_pane(self):
        self.info_manager.children = {0:[]}
        self.info_pane = self.encounter_pane
        self.info_manager.add(self.info_pane.layout)
        self.info_manager.trigger_render()
        self.gui_set(False)

    def toggle_overlay(self):
        if len(self.choice_layout.children) > 0:
            if self.overlay_showing:
                self.choice_manager.clear()
                title = 'Show Overlay'
                self.overlay_toggle.text = title
                self.overlay_showing = False
            else:
                self.choice_manager.add(self.choice_layout)
                self.overlay_toggle.text = 'Hide Overlay'
                self.overlay_showing = True
            self.ui_manager.trigger_render()

    def set_listener(self, topic, payload):
        if topic == self.investigator.name + '_player':
            match payload['message']:
                case 'action_done':
                    if self.encounter_pane.player_wait_step != None:
                        action = self.encounter_pane.action_dict[self.encounter_pane.player_wait_step]
                        args = self.encounter_pane.player_wait_args
                        self.encounter_pane.player_wait_step = None
                        if args != None:
                            action(**args)
                        else:
                            action()
                case 'combat':
                    monster = next((monster for monster in self.location_manager.all_monsters if monster.monster_id == payload['value']))
                    self.encounter_pane.combat_will(monster, payload['sender'])
        else:
            match payload['message']:
                case 'spawn':
                    no_token = False
                    name = payload.get('name', '')
                    monster_id = None
                    if payload['value'] == 'investigators':
                        investigator = self.location_manager.spawn_investigator(name)
                        payload['location'] = investigator.location
                    elif payload['value'] == 'monsters':
                        monster = self.location_manager.spawn_monster(name, payload['location'], payload['map'], int(payload['monster_id']))
                        monster_id = str(monster.monster_id)
                    elif payload['value'] == 'rumor':
                        if payload['location'] == 'no_spawn':
                            no_token = True
                        self.location_manager.rumors[payload['name']] = self.encounter_pane.get_rumor(payload['name'])
                        self.location_manager.rumors[payload['name']]['location'] = payload.get('location', '')
                    elif payload['value'] == 'expedition':
                        loc = next((loc for loc in self.location_manager.locations.keys() if self.location_manager.locations[loc]['expedition']), None)
                        if loc != None:
                            self.location_manager.locations[loc]['expedition'] = False
                            self.map.remove_tokens('expedition', loc, 'expedition')
                    if payload['location'] == self.info_panes['location'].selected:
                        self.info_panes['location'].update_all()
                    if not no_token:
                        self.maps[payload['map']].spawn(payload['value'], self.location_manager, payload['location'], name, monster_id)
                case 'card_received':
                    investigator = self.location_manager.all_investigators[payload['owner']]
                    if payload['value'] != None:
                        investigator.get_item(payload['kind'], payload['value'])
                        if payload['owner'] == self.investigator.name:
                            if payload['value'][0:-1] == 'debt':
                                self.info_panes['reserve'].debt_button.disable()
                            self.info_panes['possessions'].setup()
                case 'restock':
                    removed = [] if payload['removed'] == '' or payload['removed'] == None else payload['removed'].split(':')
                    added = [] if payload['value'] == '' or payload['value'] == None else payload['value'].split(':')
                    self.info_panes['reserve'].restock(removed, added)
                case 'receive_clue':
                    self.location_manager.all_investigators[payload['owner']].clues.append(payload['value'])
                    self.info_panes['investigator'].clue_button.text = 'x ' + str(len(self.investigator.clues))
                case 'discard':
                    self.info_panes['reserve'].discard_item(payload['value'])
                case 'unit_moved':
                    self.move_unit(payload['value'], payload['destination'], payload['kind'])
                case 'choose_lead':
                    self.encounter_pane.finish(True)
                    portraits = []
                    for name in self.location_manager.all_investigators.keys():
                        portraits.append(ActionButton(texture='investigators/' + name + '_portrait.png', scale=0.4, action=self.networker.publish_payload,
                                                    action_args={'payload': {'message': 'lead_selected', 'value': name},'topic': self.investigator.name}))
                    self.choice_layout = create_choices(choices=portraits, title="Choose Lead Investigator")
                    self.show_overlay()
                    #FOR TESTING
                    #self.networker.publish_payload({'message': 'lead_selected', 'value': 'akachi_onyele'}, self.investigator.name)
                    #END TESTING
                case 'lead_selected':
                    self.lead_investigator = payload['value']
                    if not payload.get('dead_trigger', None) != None:
                        self.clear_overlay()
                case 'player_turn':
                    self.my_turn = True
                    if payload['value'] in ['action', 'encounter', 'reckoning'] and self.investigator.is_dead:
                        self.networker.publish_payload({'message': 'turn_finished', 'value': None}, self.investigator.name)
                    else:
                        match payload['value']:
                            case 'action':
                                if self.investigator.delayed:
                                    self.investigator.delayed = False
                                    self.networker.publish_payload({'message': 'turn_finished'}, self.investigator.name)
                                else:
                                    self.remaining_actions = 2
                                    #'''
                                    #FOR TESTING
                                    self.remaining_actions = 3
                                    #if self.is_first:
                                    #location = next((key for key in self.location_manager.locations.keys() if self.location_manager.locations[key]['expedition']))
                                    self.ticket_move(self.investigator.name, 'space_17', 0, 0, self.investigator.location)
                                    #else:
                                        #self.ticket_move('akachi_onyele', 'arkham', 0, 0, 'space_16')
                                    self.investigator.focus = 0
                                    self.info_panes['investigator'].focus_action()
                                    #END TESTING
                                    #'''
                            case 'encounter':
                                #FOR TESTING
                                self.networker.publish_payload({'message': 'turn_finished', 'value': None}, self.investigator.name)
                                #END TESTING
                                #self.show_encounter_pane()
                                #self.encounter_pane.encounter_phase()
                            case 'reckoning':
                                self.encounter_pane.reckoning()
                                #self.networker.publish_payload({'message': 'turn_finished', 'value': None}, self.investigator.name)
                            case 'mythos':
                                #FOR TESTING
                                #if self.is_first:
                                self.clear_overlay()
                                self.show_encounter_pane()
                                self.encounter_pane.activate_mythos()
                                self.is_first = False
                                #else:
                                #    self.networker.publish_payload({'message': 'turn_finished', 'value': None}, self.investigator.name)
                                #END TESTING
                case 'encounter_choice':
                    self.clear_overlay()
                    self.show_encounter_pane()
                    self.encounter_pane.start_encounter(payload['value'])
                case 'mythos':
                    #FOR TESTING
                    #if self.is_first:
                    self.clear_overlay()
                    self.show_encounter_pane()
                    self.encounter_pane.load_mythos(payload['value'])
                    #END TESTING
                case 'mythos_switch':
                    self.encounter_pane.mythos_switch = True
                case 'omen':
                    self.set_omen(int(payload['value']))
                case 'doom':
                    self.set_doom(int(payload['value']))
                case 'token_removed':
                    kind = payload['kind']
                    loc = payload['value']
                    loc = loc.split(':')
                    map_name = loc[0]
                    location = loc[1]
                    self.location_manager.locations[location][kind] = False
                    self.maps[map_name].remove_tokens(kind, location)
                    self.map.token_manager.trigger_render()
                case 'monster_damaged':
                    monster_id = int(payload['value'])
                    damage = int(payload['damage'])
                    def damage_monster(monster, damage):
                        dead = monster.on_damage(damage)
                        if dead:
                            if hasattr(monster, 'death'):
                                if hasattr(monster, 'dargs'):
                                    self.encounter_pane.action_dict[monster.death](**monster.dargs)
                                else:
                                    self.encounter_pane.action_dict[monster.death]()
                            self.location_manager.locations[monster.location]['monsters'].remove(monster)
                            self.location_manager.all_monsters.remove(monster)
                            if not hasattr(monster, 'epic'):
                                self.location_manager.monster_deck.append(monster.name)
                            self.map.remove_tokens('monsters', monster.location, str(payload['value']))
                            self.map.token_manager.trigger_render()
                    if monster_id < 0:
                        for monster in self.location_manager.all_monsters:
                            damage_monster(monster, damage)
                    else:
                        monster = next((monster for monster in self.location_manager.all_monsters if monster.monster_id == int(payload['value'])))
                        damage_monster(monster, damage)
                case 'rumor_solved':
                    rumor = self.location_manager.rumors[payload['value']]
                    if rumor['location'] != 'no_spawn':
                        self.location_manager.locations[rumor['location']]['rumor'] = False
                        self.maps['world'].remove_tokens('rumor', rumor['location'], payload['value'])
                    if not payload['solved'] and rumor.get('unsolve_encounter', None) != None:
                        text = ('Unsolved Rumor - ' if rumor['location'] != 'no_spawn' else '') + human_readable(payload['value']) + '\n\n' + rumor.get('unsolved')
                        self.encounter_pane.mythos_reckonings.append((rumor['unsolve_encounter'], text))
                    del self.location_manager.rumors[payload['value']]
                case 'update_rumor':
                    if self.location_manager.rumors.get(payload['name'], None) != None:
                        is_solve = self.location_manager.rumors[payload['name']].get('is_solve', False)
                        self.location_manager.rumors[payload['name']]['eldritch'] = payload['value'] if not is_solve else payload.get('solve', self.location_manager.rumors[payload['name']]['eldritch'])
                case 'group_pay_update':
                    self.encounter_pane.total_payment = payload['total']
                    self.encounter_pane.payment_needed = payload['needed']
                case 'mystery_count':
                    self.info_panes['ancient_one'].mystery_count.text = str(int(self.ancient_one.mysteries) - int(payload['value']))
                case 'exile_from_discard':
                    for item in payload['value'].split(':'):
                        self.info_panes['reserve'].discard_item(item, True)
                case 'investigator_died':
                    dead = self.location_manager.all_investigators[payload['value']]
                    dead.hp_death = payload['kind']
                    self.location_manager.dead_investigators[payload['value']] = dead
                    del self.location_manager.all_investigators[payload['value']]
                    world = self.location_manager.get_world(dead.location)
                    self.maps[world].remove_tokens('investigators', dead.location, payload['value'])
                    self.maps[world].token_manager.trigger_render()
                    if payload['value'] == self.investigator.name:
                        self.gui_set(False)
                        self.show_encounter_pane()
                case 'trade':
                    del payload['message']
                    names = list(payload.keys())
                    self.info_panes['location'].possession_screen.swap_items(payload[names[0]], payload[names[1]], names[0], names[1])
                case 'choose_new':
                    if self.investigator.is_dead:
                        self.networker.show_select(payload['names'])
                case 'body_recovered':
                    dead = self.location_manager.dead_investigators[payload['value']]
                    recover = self.location_manager.dead_investigators[payload['owner']]
                    for ticket in ['rail_tickets', 'ship_tickets']:
                        setattr(recover, ticket, getattr(recover, ticket) + getattr(dead, ticket))
                    for kind in ['assets', 'unique_assets', 'artifacts', 'spells']:
                        for item in dead.possessions[kind]:
                            recover.possessions[kind].append(item)
                    del self.location_manager.dead_investigators[payload['value']]
                    self.hub.info_panes['possessions'].setup()
                    self.hub.info_panes['investigator'].set_ticket_counts()
                case 'become_delayed':
                    self.investigator.delayed = True
                case 'player_mythos_reckoning':
                    self.encounter_pane.mythos_reckonings.append((payload['value'], payload['text']))
                case 'possession_lost':
                    if payload['kind'] == 'clue':
                        self.location_manager.all_investigators[payload['owner']].clues.remove(payload['value'])
                    else:
                        card = next((card for card in self.location_manager.all_investigators[payload['owner']].possessions[payload['kind']] if card.name == payload['value']))
                        self.location_manager.all_investigators[payload['owner']].possessions[payload['kind']].remove(card)
                case 'player_update':
                    investigator = self.location_manager.all_investigators[payload['owner']]
                    for key in ['health', 'sanity', 'ship_tickets', 'rail_tickets']:
                        setattr(self.location_manager.all_investigators[payload['owner']], key, payload[key])

            if self.encounter_pane.wait_step != None:
                self.encounter_pane.set_buttons(self.encounter_pane.wait_step)

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

    def run_test(self, skill, mod=0, pane=None, options=[], subtitle='', allow_clues=True):
        self.clear_overlay()
        choices = []
        rolls = []
        titles = ['Lore', 'Influence', 'Observation', 'Strength', 'Will']
        subtitle = subtitle if subtitle != '' else '' if mod == 0 else 'Mod: ' + str(mod)
        dice = self.investigator.skills[3 if skill == 5 else skill] + mod + self.investigator.skill_tokens[skill]
        for x in range(dice if dice > 1 else 1):
            roll = random.randint(1, 6) - self.investigator.encounter_impairment
            roll = 1 if roll < 1 else roll
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
                    elif kind == 'clue' and len(self.investigator.clues) > 0:
                        clue = random.choice(self.investigator.clues)
                        self.investigator.clues.remove(clue)
                        self.networker.publish_payload({'message': 'card_discarded', 'kind': 'clues', 'value': clue}, self.investigator.name)
                        if len(self.investigator.clues) == 0:
                            options[option_index].disable()
                    elif not self.investigator.reroll_items[skill][kind].action_used:
                        self.investigator.reroll_items[skill][kind].action_used = True
                        options[option_index].disable()
                else:
                    for x in options:
                        x.disable()
            option_index = len(options)
            if self.investigator.focus > 0:
                focus_button = ActionButton(action=reroll, action_args={'kind': 'focus', 'option_index': option_index}, texture='icons/focus.png', text='Use', text_position=(20,-2))
                options.append(focus_button)
                option_index += 1
            if len(self.investigator.clues) > 0 and allow_clues:
                clue_button = ActionButton(action=reroll, action_args={'kind': 'clue', 'option_index': option_index}, texture='icons/clue.png', text='Use', text_position=(20,-2))
                options.append(clue_button)
                option_index += 1
            items = self.investigator.reroll_items[skill].keys()
            if len(items) > 0:
                for x in items:
                    item_button = ActionButton(action=reroll, action_args={'kind': x, 'option_index': option_index}, texture='buttons/placeholder.png', text=human_readable(x))
                    options.append(item_button)
                    option_index += 1
        #FOR TESTING
        def autofail():
            self.encounter_pane.rolls = [1]
        def succeed():
            self.encounter_pane.rolls = [6,6,6,6,6]
        options.append(ActionButton(action=succeed, texture='buttons/placeholder.png', text='succeed'))
        options.append(ActionButton(action=autofail, texture='buttons/placeholder.png', text='fail'))
        #END TESTING
        self.choice_layout = create_choices(choices = choices, title=titles[3 if skill == 5 else skill] + ' Test', options=options, offset=(0,150), subtitle=subtitle)
        self.show_overlay()
        return rolls
    
    def single_roll(self, pane, options, title='', subtitle=''):
        roll = random.randint(1, 6)
        #FOR TESTING
        def autofail():
            self.encounter_pane.rolls = [1]
        def succeed():
            self.encounter_pane.rolls = [6]
        options.append(ActionButton(action=succeed, texture='buttons/placeholder.png', text='succeed'))
        options.append(ActionButton(action=autofail, texture='buttons/placeholder.png', text='fail'))
        #END TESTING
        self.choice_layout = create_choices(options=options,
            choices=[arcade.gui.UITextureButton(texture = arcade.load_texture(IMAGE_PATH_ROOT + 'icons/die_' + str(roll) + '.png'))])
        self.show_overlay()
        return [roll]
    
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
    
    def request_card(self, kind, name='', command='get', tag=''):
        owned = ''
        if kind == 'spells' or kind == 'conditions':
            if next((item for item in self.investigator.possessions[kind] if item.name == name), None) != None:
                return False
            for card in self.investigator.possessions[kind]:
                owned += card.name
        self.networker.publish_payload({'message': kind, 'value': name, 'tag': tag, 'command': command, 'owned': owned}, self.investigator.name)
        return True

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

    def request_spawn(self, kind, name='', location='', number='1'):
        self.networker.publish_payload({'message': 'spawn', 'value': kind, 'location': location, 'name': name, 'number': number}, self.investigator.name)

    def set_doom(self, number):
        number = 0 if number < 0 else number
        self.doom_counter.move(10 + (20 - number) * 42.3 - self.doom_counter.x, 0)
        self.doom = number
        if number == 0:
            self.ancient_one.awaken()

    def set_omen(self, index):
        positions = [(921, 757), (956, 737), (937, 703), (904, 724)]
        self.omen_counter.move(positions[index][0] - self.omen_counter.x, positions[index][1] - self.omen_counter.y)

    def undo_move(self, loc, rail, ship):
        self.networker.publish_payload({'message': 'move_investigator', 'value': self.investigator.name, 'destination': loc}, self.investigator.name)
        self.investigator.rail_tickets += rail
        self.investigator.ship_tickets += ship
        self.networker.publish_payload({'message': 'update_tickets', 'ship': self.investigator.ship_tickets, 'rail': self.investigator.rail_tickets}, self.investigator.name)
        self.info_panes['investigator'].set_ticket_counts()
        self.undo_action = None
        self.actions_taken['move'] = False
        self.remaining_actions += 1

    def move_unit(self, unit, location, kind='investigators'):
        destination = self.location_manager.get_location_coord(location)
        zoom_destination = self.location_manager.get_zoom_pos(location, self.map.get_location())
        key = self.location_manager.move_unit(unit, kind, location)
        self.map.move_tokens(kind, key, destination, zoom_destination, location, unit)

    def get_locations_within(self, distance, investigator=None, same_loc=True):
        locations = self.location_manager.locations
        investigator = investigator if investigator != None else self.investigator
        start_loc = investigator.location
        locs = {start_loc}
        temp = set()
        for x in range(distance):
            for loc in locs:
                for route in locations[loc]['routes'].keys():
                    temp.add(route)
            locs.update(temp)
            temp = {}
        if not same_loc:
            locs.remove(start_loc)
        return locs

    def in_movement_range(self):
        locations = self.location_manager.locations
        rails = self.investigator.rail_tickets
        ships = self.investigator.ship_tickets
        start_loc = self.investigator.location
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
        if rail != 0 or ship != 0:
            self.networker.publish_payload({'message': 'update_tickets', 'ship': self.investigator.ship_tickets, 'rail': self.investigator.rail_tickets}, self.investigator.name)
        self.info_panes['investigator'].set_ticket_counts()
        self.networker.publish_payload({'message': 'move_investigator', 'value': name, 'destination': location}, self.investigator.name)
        if overlay:
            self.clear_overlay()
        self.action_taken('move')
    
    def undo(self):
        if self.undo_action != None:
            self.undo_action['action'](**self.undo_action['args'])

    def action_taken(self, action):
        self.actions_taken[action] = True
        self.remaining_actions -= 1
        if self.remaining_actions == 0:
            self.undo_action = None
            self.my_turn = False
            self.networker.publish_payload({'message': 'turn_finished', 'value': None}, self.investigator.name)
            for action in self.actions_taken:
                self.actions_taken[action] = False

    def damage_monster(self, monster, damage, is_ambush=False):
        choices = []
        if monster.damage + damage >= monster.toughness:
            for trigger in self.triggers['monster_kill']:
                passes = True
                if trigger.get('location', None) != None and self.investigator.location != trigger.get('location'):
                    passes = False
                if trigger.get('spend_clue', False) and len(self.investigator.clues) == 0:
                    passes = False
                def result_action():
                    match trigger['result']:
                        case 'rumor_add':
                            self.networker.publish_payload({'message': 'update_rumor_solve', 'value': monster.toughness, 'name': trigger['name']}, self.investigator.name)
                if passes:
                    if trigger.get('spend_clue', False):
                        def clue_spend():
                            self.encounter_pane.spend_clue('nothing')
                            result_action()
                        choices.append(ActionButton(texture='buttons/placeholder.png', text='Spend 1 Clue ' + trigger['clue_text'], action=clue_spend, style={'font_size': 10}))
                    else:
                        result_action()
            if hasattr(monster, 'death_trigger'):
                pass
        if not is_ambush:
            self.networker.publish_payload({'message': 'damage_monster', 'value': monster.monster_id, 'damage': damage}, self.investigator.name)
        return choices