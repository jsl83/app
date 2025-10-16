import arcade
import math, random
from util import *
from ancient_ones.ancient_one import AncientOne
from screens.ancient_pane import AncientOnePane
from screens.investigator_pane import InvestigatorPane
from screens.possessions_pane import PossessionsPane
from screens.reserve_pane import ReservePane
from screens.location_pane import LocationPane
from encounters.encounter_pane import EncounterPane, SmallCardPane
from locations.location_manager import LocationManager
from locations.map import Map
from screens.action_button import ActionButton
from small_cards.small_card import get_asset

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
            'monster_kill': [],
            'investigator_location': [],
            'gate_close': [],
            'gate_test': [],
            'spells_test': [],
            'hp_san_loss': [],
            'precombat': [],
            'turn_end': [],
            'spend_clue': [],
            'combat_strength_test': [],
            'combat_will_test': [],
            'lore_test': [],
            'influence_test': [],
            'observation_test': [],
            'strength_test': [],
            'will_test': [],
            'rest_actions': [],
            'acquire_assets_test': [],
            'combat_damage_reduction': [],
            'combat_san_reduction': [],
            'rest_san_bonus': [],
            'rest_hp_bonus': [],
            'all_test': [],
            'preencounter': [],
            'special_encounters': [],
            'in_combat_test': []
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
        self.charlie_action = False
        self.hold_item = None
        
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
        self.location_manager = LocationManager(len(all_investigators), self)
        self.all_investigators = all_investigators
        for name in all_investigators:
            self.location_manager.spawn_investigator(name, investigator)
            self.maps['world'].spawn('investigators', self.location_manager, self.location_manager.all_investigators[name].location, name)

        self.investigator = self.location_manager.all_investigators[investigator]
        self.encounter_pane = EncounterPane(self)
        self.click_pane = self.encounter_pane

        self.info_panes = {
            'investigator': InvestigatorPane(self.investigator, self),
            'possessions': PossessionsPane(self.investigator, self),
            'reserve': ReservePane(self),
            'location': LocationPane(self.location_manager, self),
            'ancient_one': AncientOnePane(self.ancient_one)
        }
        self.info_panes['investigator'].skill_reqs['leo_anderson'] = lambda *args: len([card for card in self.info_panes['reserve'].reserve if 'ally' in card['tags']] + [card for card in self.info_panes['reserve'].discard if 'ally' in self.info_panes['reserve'].retrieve_card(card)['tags']]) > 0
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
        self.waiting_panes = []

        self.undo_action = {
            'action': None,
            'args': {}
        }

        self.small_card_pane = SmallCardPane(self)
        if self.investigator.name == 'lola_hayes':
            self.gui_set(False)
            def lola_ready(encounter):
                self.networker.publish_payload({'message': 'ready'}, 'login')
            self.small_card_pane.finish_action = lola_ready
            self.small_card_pane.set_return_gui(self.info_pane)
            self.small_card_pane.improve_skill('01234')
        else:
            self.networker.publish_payload({'message': 'ready'}, 'login')
        self.respawn_name = ''

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
        elif getattr(self.holding, 'name', None) == 'charlie_send':
            inv_buttons = [button for button in self.info_pane.choice_layout.children if getattr(button, 'name', None) in list(self.location_manager.all_investigators.keys()) and self.holding.check_overlap(button)]
            if len(inv_buttons) > 0:
                self.holding.action(self.holding.action_args['item'], self.location_manager.all_investigators[inv_buttons[0].name])
            else:
                self.holding.reset_position()
            self.holding = None
        elif x < 1000 and y > 142 and self.click_time <= 10 and (self.gui_enabled or self.click_pane.click_action != None):
            location = self.location_manager.get_closest_location((x,y), self.zoom, self.map.get_location())
            if location != None:
                click_action = getattr(self.click_pane, 'click_action', False)
                if click_action:
                    click_action(location[2])
                else:
                    if self.zoom == 2:
                        self.slow_move = ((500 - location[0]) / 10, (471 - location[1]) / 10)
                    self.info_panes['location'].location_select(location[2])
                    self.switch_info_pane('location')
                    self.select_ui_button(3)
                    self.info_manager.trigger_render()
            elif getattr(self.click_pane, 'no_loc_click', False):
                self.click_pane.no_loc_click()
            buttons = list(self.ui_manager.get_widgets_at((x,y))) + list(self.info_manager.get_widgets_at((x,y)))
            if len(buttons) > 0:
                button = next((button for button in buttons if type(button) == ActionButton and button.enabled), False)
                if button:
                    button.click_action()
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
            if self.remaining_actions > 0 and not self.actions_taken['move']:
                location = self.location_manager.get_closest_location((x, y), self.zoom, self.map.get_location(), 40)
                if location != None:
                    key = location[2]
                    if self.investigator.location == key:
                        self.holding = 'investigator'
                        tokens = self.map.get_tokens('investigators', key, self.investigator.name)
                        self.investigator_token = tokens[0] if self.zoom == 2 else tokens[1]
                        self.original_investigator_location = key
                    
        elif (self.info_pane == self.info_panes['possessions'] or (self.info_pane == self.info_panes['reserve'] and self.info_panes['reserve'].discard_view) or (self.info_pane == self.info_panes['location'] and self.info_panes['location'].is_trading)) and x > 1000:
            self.holding = 'items'
            self.click_time = 0
        elif getattr(self.info_pane, 'charlie_send', False):
            item_buttons = [item for item in list(self.info_manager.get_widgets_at((x,y))) if getattr(item, 'name', None) == 'charlie_send']
            if len(item_buttons) > 0:
                self.holding = item_buttons[0]

    def on_mouse_motion(self, x, y, dx, dy):
        if self.holding == 'map':
            self.map.move(dx, dy)
            self.check_map_boundaries()
        elif self.holding == 'items':
            self.info_pane.move(dy)
        elif self.holding == 'investigator':
            self.investigator_token.move(dx, dy)
        elif self.holding != None:
            self.holding.move(dx, dy)

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
                    if self.waiting_panes[-1].player_wait_step != None:
                        action = self.waiting_panes[-1].action_dict[self.waiting_panes[-1].player_wait_step]
                        args = self.waiting_panes[-1].player_wait_args
                        self.waiting_panes[-1].player_wait_step = None
                        self.info_manager.children = {0:[]}
                        self.info_manager.add(self.waiting_panes[-1].layout)
                        self.info_pane = self.waiting_panes[-1]
                        self.waiting_panes = self.waiting_panes[:-1]
                        if payload.get('return_value', None) != None and args != None:
                            args['return_value'] = payload['return_value']
                        if args != None:
                            action(**args)
                        else:
                            action()
                case 'combat':
                    monster = next((monster for monster in self.location_manager.all_monsters if monster.monster_id == payload['value']))
                    self.small_card_pane.set_return_gui(self.info_pane)
                    self.small_card_pane.combat_will(monster, payload['sender'])
                case 'group_pay_reckoning':
                    del payload['message']
                    self.encounter_pane.group_pay(**payload)
                case 'player_encounter':
                    small_card = SmallCardPane(self)
                    small_card.request_player = payload['requestor']
                    small_card.setup([payload['value']], self.info_pane, force_select=True)
                    small_card.gui_enabled = self.gui_enabled
                    self.gui_set(False)
                    self.info_pane = small_card
                case 'charlie_kane':
                    self.remaining_actions = 1
                    self.charlie_action = True
                case 'services':
                    self.gui_set(False)
                    service = get_asset(payload['service'])
                    service['title'] = human_readable(service['name'])
                    self.networker.publish_payload({'message': 'card_discarded', 'value': service['name'], 'kind': 'assets'}, self.investigator.name)
                    def service_finish(name):
                        self.gui_set(True)
                        self.networker.publish_payload({'message': 'action_done'}, payload['sender'] + '_player')
                    self.small_card_pane.setup([service], parent=self.info_pane, single_pick=False, finish_action=service_finish, force_select=True)
                case 'jacqueline_check':
                    if self.investigator.name == 'jacqueline_fine':
                        small_card = SmallCardPane(self)
                        small_card.parent = self.info_pane
                        small_card.gui_enabled = self.gui_enabled
                        small_card.jacqueline_check(payload['value'], payload['owner'])
                        self.gui_set(False)
                        self.info_pane = small_card
                        self.info_manager.children = {0:[]}
                        self.info_manager.add(self.info_pane.layout)
                        self.info_manager.trigger_render()
                case 'recover_hp_san':
                    self.investigator.health = min(self.investigator.health + payload['hp'], self.investigator.max_health)
                    self.investigator.sanity = min(self.investigator.sanity + payload['san'], self.investigator.max_sanity)
                    self.networker.publish_payload({'message': 'update_hpsan', 'hp': self.investigator.health, 'san': self.investigator.sanity})
        else:
            match payload['message']:
                case 'spawn':
                    no_token = False
                    name = payload.get('name', '')
                    monster_id = None
                    if payload['value'] == 'investigators':
                        investigator = self.location_manager.spawn_investigator(name, self.respawn_name)
                        payload['location'] = investigator.location
                        self.all_investigators = [inv_name.replace(payload['replace'], name) for inv_name in self.all_investigators]
                        if investigator.name == self.respawn_name:
                            self.investigator = investigator
                            self.encounter_pane.finish(True)
                            self.info_panes['investigator'] = InvestigatorPane(self.investigator, self)
                            self.info_panes['possessions'] = PossessionsPane(self.investigator, self)
                            self.info_panes['possessions'].setup()
                            self.encounter_pane.investigator = self.investigator
                            self.small_card_pane.investigator = self.investigator
                            self.info_panes['location'].possession_screen.investigator = self.investigator
                    elif payload['value'] == 'monsters':
                        monster = self.location_manager.spawn_monster(name, payload['location'], payload['map'], int(payload['monster_id']))
                        monster_id = str(monster.monster_id)
                        if hasattr(monster, 'on_spawn') and (not monster.on_spawn.get('lead_only', False) or self.investigator.name == self.lead_investigator):
                            if monster.on_spawn.get('action', False):
                                self.encounter_pane.monster_spawns.append(monster.on_spawn['action'])
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
                    if payload['owner'] == 'mark_harrigan' and self.investigator.name == 'mark_harrigan' and 'detained' in payload.get('value', '') and not payload.get('bypass_mark', False):
                        small_card = SmallCardPane(self)
                        small_card.parent = self.info_pane
                        small_card.gui_enabled = self.gui_enabled
                        small_card.mark_harrigan()
                        self.gui_set(False)
                        self.info_pane = small_card
                        self.info_manager.children = {0:[]}
                        self.info_manager.add(self.info_pane.layout)
                        self.info_manager.trigger_render()                    
                    elif payload['value'] != None and payload['value'] != '':
                        card = investigator.get_item(payload['kind'], payload['value'])
                        card.back_seen = payload.get('revealed', False)
                        self.info_panes['possessions'].on_get(card, payload['owner'])
                        if card.name == 'debt' or card.name == 'detained':
                            card.action['pargs'][0]['investigator'] = payload['owner']
                        if payload['owner'] == self.investigator.name:
                            if payload['value'][0:-1] == 'debt':
                                self.info_panes['reserve'].debt_button.disable()
                            self.info_panes['possessions'].setup()
                        if payload.get('from_discard', False):
                            self.info_panes['reserve'].discard_item(payload['value'])
                case 'restock':
                    removed = [] if payload['removed'] == '' or payload['removed'] == None else payload['removed'].split(':')
                    added = [] if payload['value'] == '' or payload['value'] == None else payload['value'].split(':')
                    self.info_panes['reserve'].restock(removed, added)
                case 'receive_clue':
                    clues_to_add = payload['value'].split(';')
                    for clue in clues_to_add:
                        self.location_manager.all_investigators[payload['owner']].clues.append(clue)
                    self.info_panes['investigator'].clue_button.text = 'x ' + str(len(self.investigator.clues))
                    self.info_manager.trigger_render()
                case 'discard':
                    self.info_panes['reserve'].discard_item(payload['value'])
                case 'unit_moved':
                    self.move_unit(payload['value'], payload['destination'], payload['kind'])
                case 'choose_lead':
                    self.gui_set(False)
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
                    self.gui_set(True)
                    self.lead_investigator = payload['value']
                    if not payload.get('dead_trigger', None) != None:
                        self.clear_overlay()
                    for action in self.actions_taken:
                        self.actions_taken[action] = False
                        self.info_panes['reserve'].acquire_button.enable()
                        if hasattr(self.investigator, 'passive_used'):
                            self.investigator.passive_used = False
                    if hasattr(self.investigator, 'passive_used'):
                        self.investigator.passive_used = False
                case 'player_turn':
                    self.my_turn = True
                    if self.investigator.is_dead:
                        self.networker.publish_payload({'message': 'turn_finished', 'value': None}, self.investigator.name)
                        self.my_turn = False
                    else:
                        match payload['value']:
                            case 'action':
                                if self.investigator.delayed:
                                    self.investigator.delayed = False
                                    self.networker.publish_payload({'message': 'delay_status', 'value': False, 'investigator': self.investigator.name}, 'server_update')
                                    self.networker.publish_payload({'message': 'turn_finished'}, self.investigator.name)
                                else:
                                    self.remaining_actions = 2 if not next((card for card in self.investigator.possessions['conditions'] if card.name == 'detained'), False) else 0
                                    self.info_panes['investigator'].skill_check()
                                    for items in self.investigator.possessions.values():
                                        for item in items:
                                            item.action_used = False
                                    for triggers in self.triggers.values():
                                        for trigger in triggers:
                                            trigger['used'] = False
                                    #'''
                                    #FOR TESTING
                                    #self.remaining_actions = 3
                                    #if self.is_first:
                                    #location = next((key for key in self.location_manager.locations.keys() if self.location_manager.locations[key]['expedition']))
                                    #if self.investigator.name == 'akachi_onyele':
                                    #self.ticket_move(self.investigator.name, 'arkham', 0, 0, self.investigator.location)
                                    #else:
                                        #self.ticket_move('akachi_onyele', 'arkham', 0, 0, 'space_16')
                                    #self.investigator.focus = 0
                                    #self.info_panes['investigator'].focus_action()
                                    #END TESTING
                                    #'''
                            case 'encounter':
                                    #FOR TESTING
                                #self.networker.publish_payload({'message': 'turn_finished', 'value': None}, self.investigator.name)
                                    #END TESTING
                                self.show_encounter_pane()
                                self.encounter_pane.encounter_phase()
                            case 'reckoning':
                                self.encounter_pane.reckoning(first=True)
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
                    loc = payload['value'].split(':')
                    self.location_manager.locations[loc[1]][kind] = False
                    self.maps[loc[0]].remove_tokens(kind, loc[1])
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
                        rumor['unsolve_encounter']['title'] = human_readable(payload['value']) + ' - Reckoning'
                        self.encounter_pane.mythos_reckonings.append(rumor['unsolve_encounter'])
                    elif payload['solved'] and rumor.get('trigger', False):
                        self.triggers[rumor['trigger']] = [trig for trig in self.triggers[rumor['trigger']] if trig['name'] != payload['value']]
                    del self.location_manager.rumors[payload['value']]
                case 'update_rumor':
                    if self.location_manager.rumors.get(payload['name'], False):
                        is_solve = self.location_manager.rumors[payload['name']].get('is_solve', False)
                        self.location_manager.rumors[payload['name']]['eldritch'] = payload['value'] if not is_solve else payload.get('solve', self.location_manager.rumors[payload['name']]['eldritch'])
                case 'group_pay_update':
                    self.encounter_pane.group_payments[payload['name']] = {'group_total': payload['total'], 'needed': payload['needed'], 'my_payment': 0}
                case 'mystery_count':
                    self.info_panes['ancient_one'].mystery_count.text = str(int(self.ancient_one.mysteries) - int(payload['value']))
                case 'exile_from_discard':
                    for item in payload['value'].split(':'):
                        self.info_panes['reserve'].discard_item(item, True)
                case 'investigator_died':
                    dead = self.location_manager.all_investigators[payload['value']]
                    if hasattr(dead, 'triggers'):
                        for trigger in dead.triggers:
                            if not trigger.get('self_only', False) or dead.name == self.investigator.name:
                                self.triggers[trigger['kind']].remove(trigger)
                    if not payload['devoured']:
                        dead.hp_death = payload['kind']
                        self.location_manager.dead_investigators[payload['value']] = dead
                    world = self.location_manager.get_map_name(dead.location)
                    del self.location_manager.all_investigators[payload['value']]
                    self.maps[world].remove_tokens('investigators', dead.location, payload['value'])
                    self.maps[world].token_manager.trigger_render()
                    if payload['value'] == self.investigator.name:
                        self.encounter_pane.death_screen()
                        self.show_encounter_pane()
                    for key in self.triggers.keys():
                        self.triggers[key] = [trigger for trigger in self.triggers[key] if trigger.get('investigator', '') != payload['value']]
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
                            self.info_pane['possessions'].on_get(item, self.investigator.name)
                    del self.location_manager.dead_investigators[payload['value']]
                    self.hub.info_panes['possessions'].setup()
                    self.hub.info_panes['investigator'].set_ticket_counts()
                case 'become_delayed':
                    self.show_encounter_pane()
                    self.encounter_pane.delay('nothing')
                case 'player_mythos_reckoning':
                    self.encounter_pane.mythos_reckonings.append(payload['value'])
                case 'possession_lost':
                    if payload['kind'] == 'clues':
                        clues = payload['value'].split(';')
                        for clue in clues:
                            self.location_manager.all_investigators[payload['owner']].clues.remove(clue)
                        self.info_panes['investigator'].clue_button.text = 'x ' + str(len(self.investigator.clues))
                    else:
                        items = self.location_manager.all_investigators[payload['owner']].possessions[payload['kind']]
                        item = next((item for item in items if item.get_server_name() == payload['value']))
                        self.location_manager.all_investigators[payload['owner']].possessions[payload['kind']].remove(item)
                        self.info_panes['possessions'].on_discard(item, payload['owner'] == self.investigator.name)
                case 'player_update':
                    investigator = self.location_manager.all_investigators[payload['owner']]
                    for key in ['health', 'sanity', 'ship_tickets', 'rail_tickets']:
                        setattr(self.location_manager.all_investigators[payload['owner']], key, payload[key])
                case 'investigator_skill':
                    self.waiting_panes[-1].server_value = payload['value']
                case 'delay_status':
                    self.location_manager.all_investigators[payload['investigator']].delayed = payload['value']
            if len(self.waiting_panes) > 0 and self.waiting_panes[-1].wait_step != None:
                if self.waiting_panes[-1].last_value == None or self.waiting_panes[-1].last_value == payload.get('message', None):
                    pane = self.waiting_panes[-1]
                    self.waiting_panes = self.waiting_panes[:-1]
                    pane.set_buttons(pane.wait_step)
            if payload['message'] == 'trigger_used':
                ident = payload['value'].split(':')
                used_trigger = next((trigger for trigger in self.triggers[payload['kind']] if trigger['investigator'] == ident[0] and trigger['name'] == ident[1]), False)
                if used_trigger:
                    used_trigger['used'] = True

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

    def run_test(self, skill, pane, mod=0, options=[], subtitle='', allow_clues=True):
        self.clear_overlay()
        choices = []
        rolls = []
        titles = ['Lore', 'Influence', 'Observation', 'Strength', 'Will']
        subtitle = subtitle if subtitle != '' else '' if mod == 0 else 'Mod: ' + str(mod)
        self.investigator.skill_bonuses[skill] = [bonus for bonus in self.investigator.skill_bonuses[skill] if bonus.get('condition', 'dummy') in pane.encounter_type]
        double_six = False
        triggers = []
        for kind in pane.encounter_type + ['all'] + (['in_combat'] if getattr(pane, 'in_combat', False) else []):
            triggers += [add for add in self.triggers.get(kind + '_test', []) if not add.get('reroll', False) and not add.get('add', False)]
        triggers += self.triggers[titles[skill].lower() + '_test']
        additional_die = 0
        for trigger in triggers:
            if self.trigger_check(trigger, pane.encounter_type + [titles[skill].lower() + '_test']):
                if trigger.get('double_six', None) != None:
                    double_six = True
                elif trigger.get('additional_die', False):
                    additional_die += 1
        dice = max(1, self.investigator.skills[skill] + mod + self.investigator.skill_tokens[skill] + self.investigator.calc_max_bonus(skill, pane.encounter_type) + additional_die)
        self.investigator.skill_bonuses[skill] = [bonus for bonus in self.investigator.skill_bonuses[skill] if bonus.get('temp', 'remove') == 'remove']
        for x in range(dice):
            roll = random.randint(1, 6) + self.investigator.encounter_impairment
            roll = max(1, roll)
            rolls.append(roll)
            choices.append(arcade.gui.UITextureButton(texture = arcade.load_texture(IMAGE_PATH_ROOT + 'icons/die_' + str(roll) + '.png')))
        if not (len(set(rolls)) == 1 and 6 in rolls):
            norman_trigger = next((trigger for trigger in self.triggers['all_test'] if trigger.get('action', {}).get('title') == 'Norman Withers - Passive' and not getattr(self.investigator, 'passive_used', True)), False)
            small_card = SmallCardPane(self)
            small_card.dice_number = dice
            small_card.double_six = double_six
            reroll_triggers = []
            def reroll(dice_rolls, root_pane, root_choices, is_reroll_all=False, spend_clue=False):
                lowest = min(dice_rolls)
                sixes = []
                if (dice_rolls[x] == lowest and not is_reroll_all) or (is_reroll_all and dice_rolls[x] < self.investigator.success):
                    new_roll = random.randint(1, 6)
                    dice_rolls[x] = new_roll
                    root_pane.rolls[x] = new_roll
                    if new_roll == 6 and double_six:
                        sixes.append(6)
                    root_choices[x].texture = arcade.load_texture(IMAGE_PATH_ROOT + 'icons/die_' + str(new_roll) + '.png')
                root_pane.rolls += sixes
                if spend_clue:
                    if len(self.investigator.clues) == 1 or (len(set(dice_rolls)) == 1 and 6 in dice_rolls):
                        clue_button = next((button for button in root_pane.choice_layout.children if getattr(button, 'name', '') == 'clue'))
                        root_pane.choice_layout.children.remove(clue_button)
                        self.info_manager.trigger_render()
                    self.encounter_pane.spend_clue('nothing')
            def finish_action(name):
                roll_button = next((button for button in pane.choice_layout.children if getattr(button, 'name', '') == name.split(':')[1]))
                is_reroll = False
                reroll_all = False
                if name == 'focus:focus':
                    self.investigator.focus -= 1
                    self.info_panes['investigator'].focus_button.text = 'x ' + str(self.investigator.focus)
                    is_reroll = True
                    if self.investigator.focus == 0:
                        pane.choice_layout.children.remove(roll_button)
                elif name == 'clue:clue':
                    self.encounter_pane.spend_clue('nothing')
                    is_reroll = True
                    if self.encounter_pane.spend_clue(is_check=True) > len(self.investigator.clues):
                        pane.choice_layout.children.remove(roll_button)
                elif name == 'norman_withers_test:norman_withers_test':
                    if len(self.investigator.clues) == 0:
                        pane.choice_layout.children.remove(roll_button)
                    else:
                        roll_button.action = reroll
                        roll_button.action_args = {'dice_rolls': rolls, 'root_pane': pane, 'root_choices': choices, 'spend_clue': True}
                        roll_button.name = 'clue'
                    is_reroll = True
                    norman_trigger['used'] = True
                else:
                    kind = small_card.encounter_name.split(':')[0]
                    roll_trigger = next((trig for trig in self.triggers[kind] if trig['name'] == small_card.encounter_name.split(':')[1]), {})
                    if small_card.item_used:
                        pane.choice_layout.children.remove(roll_button)
                        if roll_trigger.get('temp', False):
                            self.triggers[kind].remove(roll_trigger)
                        else:
                            roll_trigger['used'] = True
                        is_reroll = roll_trigger['mod_die'] != 'add_to'
                        reroll_all = roll_trigger['mod_die'] == 'all'
                    else:
                        small_card.encounters.append(roll_trigger['action'])
                if 'combat_strength' in pane.encounter_type or 'combat_will' in pane.encounter_type:
                    subtitle_button = next((button for button in pane.choice_layout.children if getattr(button, 'identifier', '') == 'overlay_subtitle'))
                    subtitle_button.text = 'Health: ' + str(self.investigator.health) + '   Sanity: ' + str(self.investigator.sanity)
                if small_card.item_used:
                    if is_reroll:
                        for x in range(dice):
                            reroll(rolls, pane, choices, reroll_all)
                        if name == 'norman_withers_test:norman_withers_test' and (len(set(rolls)) == 1 and 6 in rolls):
                            pane.choice_layout.children.remove(roll_button)
                    else:
                        fails = [roll for roll in rolls if roll < self.investigator.success]
                        die = max(fails) if len(fails) > 0 else min(rolls)
                        if double_six and self.investigator.success - die > 1 and 5 in rolls:
                            die = 5
                        index = rolls.index(die)
                        new_roll = die + 1
                        choices[index].texture = arcade.load_texture(IMAGE_PATH_ROOT + 'icons/die_' + str(new_roll) + '.png')
                        rolls[index] = new_roll
                        pane.rolls[index] = new_roll
                        if new_roll == 6 and double_six:
                            pane.rolls.append(6)
                self.info_manager.trigger_render()
            small_card.finish_action = finish_action
            if self.investigator.focus > 0:
                options.append(ActionButton(action=finish_action, action_args={'name': 'focus:focus'}, texture='icons/focus.png', name='focus'))
            if self.encounter_pane.spend_clue(is_check=True) <= len(self.investigator.clues) and allow_clues and not norman_trigger:
                options.append(ActionButton(action=finish_action, action_args={'name':'clue:clue'}, texture='icons/clue_small.png', name='clue'))
            for kind in pane.encounter_type + [titles[skill].lower()] + ['all']:
                reroll_triggers += [reroll for reroll in self.triggers.get(kind + '_test', []) if reroll.get('mod_die', False) and (not reroll.get('used', False) or not reroll.get('single_use', False))]
            if len(reroll_triggers) > 0:
                for trigger in reroll_triggers:
                    trigger_button = ActionButton(width=100, height=50, action=small_card.setup, action_args={'encounters': [trigger['action']], 'parent': pane, 'finish_action': finish_action, 'force_select': True}, texture=trigger.get('texture', 'buttons/placeholder.png'), text=human_readable(trigger.get('name', '')), name=trigger.get('name', trigger.get('id', '')), scale=trigger.get('scale', 1))
                    if trigger.get('used', False) and trigger.get('single_use', False):
                        trigger_button.disable()
                    options.append(trigger_button)
            lola_trigger = next((trigger for trigger in self.triggers['all_test'] if trigger.get('same_space', False) == 'lola_hayes'), False)
            if lola_trigger and not lola_trigger['used'] and self.investigator.location == self.location_manager.all_investigators['lola_hayes'].location:
                def lola_hayes(choices, title, options, subtitle, pane, trigger, button, double):
                    self.networker.publish_payload({'value': 'lola_hayes:lola_hayes', 'kind': 'all_test', 'message': 'trigger_used'}, 'server_update')
                    roll = random.randint(1, 6) + self.investigator.encounter_impairment
                    roll = max(1, roll)
                    pane.rolls.append(roll)
                    if double and roll == 6:
                        pane.rolls.append(6)
                    if button in options:
                        options.remove(button)
                    choices.append(arcade.gui.UITextureButton(texture = arcade.load_texture(IMAGE_PATH_ROOT + 'icons/die_' + str(roll) + '.png')))
                    pane.clear_overlay()
                    for x in choices + options:
                        x.move(-x.x, -x.y)
                    pane.choice_layout = create_choices(title, subtitle, choices, options=options, offset=(0,150))
                    pane.layout.add(pane.choice_layout)
                    trigger['used'] = True
                lola_button = ActionButton(texture='investigators/lola_hayes_portrait.png', text='Add die', text_position=(0,-50), scale=0.25, action=lola_hayes, action_args={})
                lola_button.action_args = {'choices': choices, 'title':titles[skill] + ' Test', 'options': options, 'subtitle':subtitle, 'pane': pane, 'trigger':lola_trigger, 'button': lola_button, 'double': double_six}
                options.append(lola_button)
        #FOR TESTING
        def autofail():
            pane.rolls = [1]
        def succeed():
            pane.rolls = [6,6,6,6,6]
        options.append(ActionButton(action=succeed, texture='buttons/placeholder.png', text='succeed'))
        options.append(ActionButton(action=autofail, texture='buttons/placeholder.png', text='fail'))
        #END TESTING
        if double_six:
            rolls += [roll for roll in rolls if roll == 6]
        return rolls, create_choices(choices = choices, title=titles[skill] + ' Test', options=options, offset=(0,150), subtitle=subtitle)
    
    def trigger_check(self, trigger, encounter_types):
        pass_condition = True
        if trigger.get('owner', False) and (self.investigator.location != next((inv.location for inv in self.location_manager.all_investigators.values() if trigger['name'] in [item.get_server_name() for item in inv.possessions[trigger['owner']]]))):
            pass_condition = False
        if trigger.get('space_type', False) and not self.location_manager.locations[self.investigator.location]['kind'] == trigger['space_type']:
            pass_condition = False
        if trigger.get('encounter', False) and trigger['encounter'] not in encounter_types:
            pass_condition = False
        if trigger.get('location', False) and trigger['location'] != self.investigator.location:
            pass_condition = False
        if trigger.get('spend_clue', False) and self.encounter_pane.spend_clue(is_check=True) > len(self.investigator.clues):
            pass_condition = False
        if trigger.get('not_encounter', False) and trigger['not_encounter'] in encounter_types:
            pass_condition = False
        if trigger.get('exists', False) and not next((loc for loc in self.location_manager.locations.values() if loc[trigger['exists']]), False):
            pass_condition = False
        if trigger.get('monsters_exist', False) and len(self.location_manager.all_monsters) <= 0:
            pass_condition = False
        if trigger.get('same_space', False) and self.investigator.location != self.location_manager.all_investigators[trigger['same_space']].location:
            pass_condition = False
        return pass_condition
    
    def gui_set(self, able=True):
        self.gui_enabled = able
        for x in self.get_ui_buttons():
            if able:
                x.enable()
            else:
                x.disable()
        self.ui_manager.trigger_render()

    def get_ui_buttons(self):
        buttons = self.ui_manager.children[0][0].children
        return buttons[len(buttons) - 5: len(buttons)]
    
    def select_ui_button(self, index):
        buttons = self.get_ui_buttons()
        for button in buttons:
            button.select(False)
        buttons[index].select(True)
    
    def request_card(self, kind, name='', command='get', tag='', investigator=None):
        requestor = self.investigator if investigator == None else investigator
        if kind == 'spells' or kind == 'conditions':
            if next((item for item in requestor.possessions[kind] if item.name == name), None) != None:
                return False
        self.networker.publish_payload({'message': kind, 'value': name, 'tag': tag, 'command': command}, requestor.name)
        return True

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
        self.omen = index

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

    def get_locations_within(self, distance, start_loc, same_loc=True, kind=None):
        locations = self.location_manager.locations
        locs = {start_loc} if kind == None or locations[start_loc]['kind'] == kind else {}
        temp = set()
        for x in range(distance):
            for loc in locs:
                for route in locations[loc]['routes'].keys():
                    if kind == None or locations[route]['kind'] == kind:
                        temp.add(route)
            locs.update(temp)
            temp = set()
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

    def end_turn(self):
        self.clear_overlay()
        self.undo_action = None
        self.my_turn = False
        self.networker.publish_payload({'message': 'turn_finished', 'value': None}, self.investigator.name)

    def action_taken(self, action, action_point=1):
        if self.charlie_action:
            self.networker.publish_payload({'message': 'action_done'}, 'charlie_kane_player')
            self.charlie_action = False
            self.actions_taken[action] = True
        else:
            def ruby():
                self.clear_overlay()
                self.remaining_actions += 1 if next((card for card in self.investigator.possessions['conditions'] if card.name == 'detained'), False) else 0
                next((trigger for trigger in self.triggers['turn_end'] if trigger['name'] == 'ruby_of_r\'lyeh'))['used'] = True
                self.encounter_pane.take_damage(0, -1, self.clear_overlay, {})
            trigger_dict = {'ruby_of_r\'lyeh': ruby}
            if action != None:
                self.actions_taken[action] = True
            self.remaining_actions -= action_point
            if self.remaining_actions == 0:
                if len([trigger for trigger in self.triggers['turn_end'] if not trigger['used']]) > 0:
                    choices = [ActionButton(width=100, height=50, text=human_readable(trigger['name']), action=trigger_dict[trigger['name']], texture='buttons/placeholder.png') for trigger in self.triggers['turn_end']]
                    choices.append(ActionButton(width=100, height=50, text='End Turn', action=self.end_turn, texture='buttons/placeholder.png'))
                    self.choice_layout = create_choices('End of Turn Actions', choices=choices)
                    self.show_overlay()
                else:
                    self.end_turn()

    def damage_monster(self, monster, damage, is_ambush=False, is_combat=False):
        choices = []
        if damage != 99 and monster.damage + damage >= monster.toughness:
            for trigger in self.triggers['monster_kill'] + [getattr(monster, 'death_trigger', {})]:
                if self.trigger_check(trigger, ['combat'] if is_combat else []):
                    if trigger.get('action', False):
                        encounter = trigger['action']
                        if trigger.get('set_monster', False):
                            encounter[trigger['set_monster']['key']][0][trigger['set_monster']['arg']] = getattr(monster, trigger['set_monster']['attr'])
                        choices.append(encounter)
                    if trigger.get('recover_san', False):
                        self.investigator.sanity = min(self.investigator.max_sanity, self.investigator.sanity + trigger['recover_san'])
                        self.hub.networker.publish_payload({'message': 'update_hpsan', 'hp': self.investigator.health, 'san': self.investigator.sanity}, self.investigator.name)
                    if trigger.get('receive_clue', False):
                        self.encounter_pane.gain_clue('nothing')
                    if trigger.get('no_encounter', False):
                        self.encounter_pane.no_encounter = True
            if hasattr(monster, 'death_trigger') and monster.death_trigger.get('special_encounter', False):
                self.triggers['special_encounters'].append(monster.death_trigger['special_encounter'])
        if not is_ambush and not is_combat:
            self.networker.publish_payload({'message': 'damage_monster', 'value': monster.monster_id, 'damage': damage}, self.investigator.name)
        return choices