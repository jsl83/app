import arcade, arcade.gui, yaml, random, math, copy
from screens.action_button import ActionButton
from util import *

ENCOUNTERS = {}
MYTHOS = {}
RUMORS = {}

for kind in ['generic', 'green', 'orange', 'purple', 'expeditions', 'gate', 'rumor', 'investigators']:
    with open('encounters/' + kind + '.yaml') as stream:
        ENCOUNTERS[kind] = yaml.safe_load(stream)
with open('encounters/mythos.yaml') as stream:
    MYTHOS = yaml.safe_load(stream)

class EncounterPane():
    def __init__(self, hub):
        self.layout = arcade.gui.UILayout(x=1000)
        self.choice_layout = arcade.gui.UILayout()
        self.hub = hub
        self.monsters = []
        self.encounters = []
        self.investigator = self.hub.investigator
        self.first_fight = True
        self.rolls = []
        self.rumor_not_gate = None
        self.gate_close = True
        self.phase_button = ActionButton(x=1020, width=240, y=725, height=50, texture='blank.png')
        self.text_button = ActionButton(x=1020, width=240, y=275, height=425, texture='blank.png')
        self.proceed_button = ActionButton(1020, 200, 240, 50, 'buttons/pressed_placeholder.png')
        self.option_button = ActionButton(1020, 125, 240, 50, 'buttons/placeholder.png')
        self.last_button = ActionButton(1020, 50, 240, 50, 'buttons/placeholder.png')
        self.action_dict = {
            'additional_action': self.additional_action,
            'adjust_triggers': self.adjust_triggers,
            'allow_gate_close': self.allow_gate_close,
            'allow_move': self.allow_move,
            'ambush': self.ambush,
            'attract_investigator': self.attract_investigator,
            'choose_investigator': self.choose_investigator,
            'choose_location': self.choose_location,
            'choose_monster': self.choose_monster,
            'close_gate': self.close_gate,
            'combat': self.encounter_phase,
            'combat_strength': self.combat_strength,
            'condition_check': self.condition_check,
            'damage_monsters': self.damage_monsters,
            'delayed': self.delay,
            'despawn_clues': self.despawn_clues,
            'disable_expeditions': self.disable_expeditions,
            'discard': self.discard,
            'end_mythos': self.end_mythos,
            'gain_asset': self.gain_asset,
            'gain_clue': self.gain_clue,
            'group_pay': self.group_pay,
            'group_pay_reckoning': self.group_pay_reckoning,
            'heal_monster': self.heal_monster,
            'hp_san': self.hp_san,
            'impair_encounter': self.impair_encounter,
            'improve_skill': self.improve_skill,
            'loss_per_condition': self.loss_per_condition,
            'monster_heal': self.monster_heal,
            'monster_reckoning': self.monster_reckoning,
            'move_investigator': self.move_investigator,
            'move_monster': self.move_monster,
            'mythos_reckoning': self.mythos_reckoning,
            'nearest_investigator': self.nearest_investigator,
            'recover': self.recover_investigator,
            'request_card': self.request_card,
            'resting_enabled': self.resting_enabled,
            'select_location': self.select_location,
            'send_encounter': self.send_encounter,
            'server_check': lambda: self.set_buttons('pass') if self.mythos_switch else self.set_buttons('fail'),
            'set_buttons': self.set_buttons,
            'set_doom': self.set_doom,
            'set_omen': self.set_omen,
            'shuffle_mystery': self.shuffle_mystery,
            'single_roll': self.single_roll,
            'skill': self.skill_test,
            'skip_combat': self.skip_combat,
            'small_card': self.small_card,
            'spawn_clue': self.spawn_clue,
            'spawn_gate': self.spawn_gate,
            'spawn_monster': self.spawn_monster,
            'spend_clue': self.spend_clue,
            'solve_rumor': self.solve_rumor,
            'trigger_encounter': self.trigger_encounter,
            'update_rumor': self.update_rumor
        }
        self.req_dict = {
            'damage_monsters': lambda *args: len(self.hub.location_manager.get_all('monsters', True)) > 0 and (args[0].get('location', None) == None or len(self.hub.location_manager.locations[args[0]['location'] if args[0]['location'] != 'self' else self.investigator.location]['monsters']) > 0),
            'request_card': lambda *args: not args[0].get('check', False) or next((item for item in self.investigator.possessions[args[0]['kind']] if item.name == args[0]['name']), None) == None,
            'spend_clue': lambda args: len(self.investigator.clues) >= self.spend_clue(is_check=True, **args),
            'discard': lambda *args: self.discard_check(args[0]['kind'], args[0].get('tag', 'any'), args[0].get('name', None), args[0].get('voluntary', True)),
            'solve_rumor': lambda *args: len(self.hub.location_manager.rumors) > 0,
            'gain_asset': lambda args: self.gain_asset(is_check=True, **args),
            'group_pay': lambda args: self.group_pay(is_check=True, **args),
            'group_pay_reckoning': lambda *args: self.group_pay(args[0]['kind'], args[0]['name'], is_check=True)
        }
        self.encounter = None
        self.layout.add(self.text_button)
        self.layout.add(self.proceed_button)
        self.layout.add(self.phase_button)
        self.click_action = None
        self.wait_step = None
        self.player_wait_step = None
        self.player_wait_args = None
        self.ambush_steps = None
        self.group_payments = {}
        self.set_button_set = set()
        self.mythos_switch = False
        self.reckonings = []
        self.mythos = None
        self.final_step = ''
        self.small_card_dict = None
        self.recover_name = ''
        self.reckonings = {
            'monster': [],
            'mythos': [],
            'item': [],
            'ancient_one': []
        }
        self.mythos_reckonings = []
        self.monster_spawns = []
        self.no_loc_click = None
        self.last_value = None
        self.player_index = 0
        self.encounter_type = []
        self.hp_damage = 0
        self.san_damage = 0
        self.current_key = ''
        self.combat_only = False
        self.chosen_investigator = ''
        self.chosen_location = ''
        self.chosen_monster = ''
        self.clue_location = None
        self.no_encounter = False

    def clear_overlay(self):
        if self.choice_layout in self.layout.children:
            self.choice_layout.clear()
            self.layout.children.remove(self.choice_layout)

    def clear_buttons(self, buttons=[]):
        self.layout.clear()
        self.layout.add(self.text_button)
        self.layout.add(self.phase_button)
        if len(self.choice_layout.children) > 0:
            self.layout.add(self.choice_layout)
        for button in buttons:
            self.layout.add(button)

    def death_screen(self):
        self.investigator.is_dead = True
        self.text_button.text = 'You have fallen to the forces of the night.\n\nSelect a new Investigator at the end of the turn.'
        self.clear_buttons()
        self.hub.gui_set(False)
        if self.hub.my_turn:
            self.hub.end_turn()

    def get_rumor(self, name):
        return MYTHOS[name]['manager_object']

    def discard_check(self, kind, tag='any', name=None, voluntary=True):
        if kind == 'all':
            items = self.investigator.possessions['assets'] + self.investigator.possessions['artifacts'] + self.investigator.possessions['unique_assets']
        else:
            items = self.investigator.possessions[kind]
        items = [item for item in items if tag in item.tags] if tag != 'any' else [item for item in items if name == item.name] if name != None else items
        return len(items) > 0 or not voluntary

    def encounter_phase(self, combat_only=False, step='finish'):
        self.combat_only = combat_only
        location = self.investigator.location
        monsters = self.hub.location_manager.locations[location]['monsters']
        self.monsters = [monster for monster in monsters] if self.first_fight else self.monsters
        self.encounters = self.hub.location_manager.get_encounters(location)
        self.phase_button.text = 'Combat Phase'
        choices = []
        if len(self.monsters) > 0:
            small_card = SmallCardPane(self.hub)
            def finish_action(name):
                used_trigger = next((utrig for utrig in self.hub.triggers['precombat'] if human_readable(utrig['name']) == name), False)
                if small_card.item_used:
                    button = next((button for button in self.choice_layout.children if getattr(button, 'name', '') == name), False)
                    if button:
                        self.choice_layout.children = [opt for opt in self.choice_layout.children if opt != button]
                    if used_trigger:
                        used_trigger['used'] = True
                else:
                    small_card.encounters.append(used_trigger['action'])
            for monster in self.monsters:
                choices.append(ActionButton(texture='monsters/' + monster.name + '.png', action=self.combat_will, action_args={'monster': monster}, scale=0.5))
            options = []
            for trigger in [trig for trig in self.hub.triggers['precombat'] if (not trig['used'] or not trig.get('single_use', False)) and (not trig.get('first_combat', False) or self.first_fight)]:
                trigger['action']['title'] = human_readable(trigger['name'])
                options.append(ActionButton(width=100, height=50, texture='buttons/placeholder.png', text=human_readable(trigger['name']), action=small_card.setup, action_args={'encounters':[trigger['action']], 'parent': self, 'finish_action': finish_action, 'force_select': True}, name=human_readable(trigger['name'])))
            self.choice_layout = create_choices('Choose Monster', choices=choices, options=options)
            self.layout.add(self.choice_layout)
        elif not self.combat_only and len(self.hub.location_manager.locations[location]['monsters']) == 0 and not self.no_encounter:
            self.combat_only = False
            self.choose_encounter()
        else:
            self.no_encounter = False
            if self.first_fight:
                self.proceed_button.text = 'Next'
                self.proceed_button.action = self.set_buttons
                self.proceed_button.action_args = {'key': step}
                self.clear_buttons([self.proceed_button])
            else:
                self.set_buttons(step)

    def choose_encounter(self, remote_clue=False):
        self.clear_overlay()
        choices = []
        options = []
        self.phase_button.text = 'Encounter Phase'
        detained = next((card for card in self.investigator.possessions['conditions'] if card.name == 'detained'), False)
        if detained:
            def begin_detained():
                self.encounter = detained.back
                self.set_buttons('action')
            choices.append(ActionButton(texture='conditions/detained.png', action=begin_detained, scale=0.5))
        else:
            for encounter in self.encounters:
                request = False
                args = {}
                for trigger in [trig for trig in self.hub.triggers['preencounter'] if self.hub.trigger_check(trig, self.encounter_type) and (not trig.get('single_use', False) or not trig['used'])]:
                    small_card = SmallCardPane(self.hub)
                    def finish_action(name):
                        trigger['used'] = small_card.item_used
                        if trigger['name'] == 'clairvoyance' and small_card.rolls != None:
                            self.choice_layout.children = [button for button in self.choice_layout.children if not getattr(button, 'text', '') == 'Clairvoyance']
                            if len([roll for roll in small_card.rolls if roll >= self.investigator.success]) > 0:
                                self.choose_encounter(small_card.chosen_location)
                    small_card.rolls = None
                    options.append(ActionButton(width=100, height=50, text=human_readable(trigger['name']), texture='buttons/placeholder.png', action=small_card.setup, action_args={'encounters': [trigger], 'parent': self, 'force_select': True, 'finish_action': finish_action}))
                if encounter in ['clue', 'expedition', 'gate', 'generic', 'green', 'orange', 'purple']:
                    path = 'encounters/' + encounter + '.png'
                    request = True
                    args = {'topic': self.investigator.name, 'payload':{'message': 'get_encounter', 'value': encounter if encounter != 'expedition' else self.investigator.location}}
                elif encounter[:-2] in self.hub.location_manager.dead_investigators.keys():
                    path = 'investigators/' + encounter[:-2] + '_portrait.png'
                    args = {'value': 'investigators:' + '0' if self.hub.location_manager.dead_investigators[encounter[:-2]].hp_death else '1', 'loc': encounter[:-2]}
                else:
                    path = 'encounters/rumor.png'
                    args = {'value': 'rumor:0', 'loc': encounter}
                button = ActionButton(texture=path, scale=0.3)
                button.action = self.hub.networker.publish_payload if request else self.start_encounter
                button.action_args = args           
                choices.append(button)
            for x in range(len(self.hub.triggers['special_encounters'])):
                button = ActionButton(texture=self.hub.triggers['special_encounters'][x]['texture'], width=75, height=75, action=self.start_encounter, action_args={'value': 'special:' + str(x)})
                choices.append(button)
        if remote_clue:
            choices.append(ActionButton(texture='encounters/clue.png', action=self.hub.networker.publish_payload, action_args={'topic': self.investigator.name, 'payload':{'message': 'get_encounter', 'value': 'clue', 'location': remote_clue}}, scale=0.3, text=human_readable(remote_clue)))
        self.choice_layout = create_choices('Choose Encounter', choices=choices, options=options)
        self.layout.add(self.choice_layout)
        self.layout.add(self.phase_button)

    def start_encounter(self, value, loc=None):
        choice = value.split(':')
        if choice[0] == 'special':
            self.encounter = self.hub.triggers['special_encounters'][int(choice[1])]
            self.set_buttons('action')
            self.hub.triggers['special_encounters'] = [trigger for trigger in self.hub.triggers['special_encounters'] if not trigger.get('temp', False)]
        else:
            if loc == None:
                location = self.investigator.location
                loc = 'gate' if choice[0] == 'gate' else location if (location.find('space') == -1 and choice[0] != 'generic') else self.hub.location_manager.locations[location]['kind']
            if choice[0] == 'clue':
                self.clue_location = loc if loc != None else self.investigator.location
                loc = self.hub.ancient_one.name
            self.encounter = ENCOUNTERS[choice[0]][loc][int(choice[1])]
            self.encounter_type.append(choice[0])
            if loc == 'gate':
                self.phase_button.text = self.encounter['world']
            elif choice[0] == 'investigators':
                self.recover_name = loc
            if self.encounter['test'] != 'None':
                self.set_buttons('test')
            else:
                self.set_buttons('pass')

    def combat_will(self, monster, player_request=None, first_trigger=True):
        self.layout.clear()
        self.encounter_type.append('combat')
        self.first_fight = False
        self.hub.info_manager.children = {0:[]}
        self.hub.info_panes['location'].show_monster(monster)
        if first_trigger:
            self.hub.info_panes['location'].description_layout.children.remove(self.hub.info_panes['location'].monster_close)
        self.layout.add(self.hub.info_panes['location'].layout)
        self.hub.info_manager.add(self.layout)
        self.clear_overlay()
        if monster.horror['mod'] == '-':
            self.combat_strength(monster, player_request)
        if first_trigger and hasattr(monster, 'before_will'):
            trigger_pane = SmallCardPane(self.hub)
            def finish_action(name):
                self.combat_will(monster, player_request, False)
            trigger_pane.setup([monster.before_will], self, finish_action=finish_action, force_select=True)
        else:
            def lose_san():
                self.clear_overlay()
                self.encounter_type.remove('combat_will')
                successes = len([roll for roll in self.rolls if roll >= self.investigator.success])
                if monster.name == 'riot':
                    if successes > 0:
                        self.rolls = [6,6,6,6]
                        self.resolve_combat(monster, player_request)
                    else:
                        self.combat_strength(monster, player_request)
                elif monster.name == 'witch' and successes == 0:
                    self.encounter = {'combat': ['combat_strength'], 'cargs':[{'monster': monster, 'player_request': player_request, 'skip': True}]}
                    self.request_card('conditions', 'combat', 'cursed')
                else:
                    horror = 1 if self.investigator.name == 'diana_stanley' else monster.horror['san']
                    dmg = successes - horror
                    dmg = min(dmg, 0)
                    self.take_damage(0, dmg, self.resolve_combat if (monster.horror.get('skip', False) and successes == 0) or monster.horror.get('damage', False) else self.combat_strength, {'monster': monster, 'player_request': player_request})
            next_button = ActionButton(width=100, height=30, texture='buttons/placeholder.png', text='Next', action=lose_san)
            self.encounter_type.append('combat_will')
            self.rolls, self.choice_layout = self.hub.run_test(monster.horror['index'],
                                        self,
                                        monster.horror['mod'],
                                        [next_button],
                                        'Health: ' + str(self.investigator.health) + '   Sanity: ' + str(self.investigator.sanity),
                                        allow_clues=not hasattr(monster, 'no_clues'))
            self.layout.add(self.choice_layout)
        
    def combat_strength(self, monster, player_request=None):
        self.clear_overlay()
        if monster.strength['mod'] == '-':
            self.resolve_combat(monster, player_request)
        elif monster.strength.get('single', False):
            def damage():
                self.rolls = [6]*25 if str(self.rolls[0]) in monster.strength['single'] else [0]
                self.resolve_combat(monster, player_request)
            self.single_roll({}, damage)
        else:
            def lose_hp():
                self.clear_overlay()
                self.encounter_type.remove('combat_strength')
                successes = len([roll for roll in self.rolls if roll >= self.investigator.success])
                dmg = successes - monster.strength['str']
                dmg = dmg if dmg < 0 else 0
                self.take_damage(dmg, 0, self.resolve_combat, {'monster': monster, 'player_request': player_request})
            next_button = ActionButton(width=100, height=30, texture='buttons/placeholder.png', text='Next', action=lose_hp)
            self.encounter_type.append('combat_strength')
            self.rolls, self.choice_layout = self.hub.run_test(monster.strength['index'],
                                        self,
                                        monster.strength['mod'],                                        
                                        [next_button],
                                        'Health: ' + str(self.investigator.health) + '   Sanity: ' + str(self.investigator.sanity),
                                        allow_clues=not hasattr(monster, 'no_clues'))
            self.layout.add(self.choice_layout)

    def resolve_combat(self, monster, player_request=None, first_trigger=True):
        trigger = getattr(monster, 'resolve_trigger', None)
        condition = True
        if trigger:
            if trigger.get('check'):
                condition = self.req_dict[trigger.get('check')]
            if trigger.get('cond'):
                if trigger['cond'] == 'hp_damage' and self.hp_damage >= 0:
                    condition = False
            if trigger.get('monster_damage'):
                self.rolls = [6]*trigger['monster_damage']
        if first_trigger and trigger and condition:
            trigger_pane = SmallCardPane(self.hub)
            def finish_action(name):
                self.resolve_combat(monster, player_request, False)
            trigger_pane.setup([trigger], self, finish_action=finish_action, force_select=True)
        else:
            self.hub.info_panes['location'].description_layout.add(self.hub.info_panes['location'].monster_close)
            self.encounter_type.remove('combat')
            successes = len([roll for roll in self.rolls if roll >= self.investigator.success])
            is_ambush = self.ambush_steps != None
            triggers = self.hub.damage_monster(monster, successes, is_ambush, True)
            def finish_combat(name=None):
                self.layout.remove(self.hub.info_panes['location'].layout)
                damage = successes - 2 if monster.name == 'vampire' and self.hp_damage < 0 and successes + monster.damage < 3 else successes
                if player_request == None:
                    self.hub.show_encounter_pane()
                    self.monsters.remove(monster)
                    self.hub.waiting_panes.append(self)
                    self.wait_step = 'combat'
                    self.encounter = {'combat': ['combat'], 'cargs': [{'skip': True}]}
                    self.last_value = 'monster_damaged'
                    self.hub.networker.publish_payload({'message': 'damage_monster', 'value': monster.monster_id, 'damage': damage}, self.investigator.name)
                else:
                    self.hub.networker.publish_payload({'message': 'damage_monster', 'value': monster.monster_id, 'damage': damage}, self.investigator.name)
                    if hasattr(self, 'parent'):
                        self.hub.info_manager.children = {0:[]}
                        self.clear_overlay()
                        self.hub.info_manager.add(self.parent.layout)
                        self.hub.info_manager.trigger_render()
                    self.hub.networker.publish_payload({'message': 'action_done'}, player_request + '_player')
            if len(triggers) > 0:
                small_card = SmallCardPane(self.hub)
                small_card.setup(triggers, self, False, human_readable(monster.name) + ' - Defeated', [trig.get('texture') for trig in triggers], finish_combat, len(triggers) == 1 and triggers[0]['is_required'])
            elif is_ambush:
                self.set_buttons(self.ambush_steps[0] if successes >= monster.toughness else self.ambush_steps[1])
                self.ambush_steps = None
            else:
                finish_combat()

    def reroll(self, new, old):
        self.rolls.remove(old)
        self.rolls += new

    def finish(self, skip=False):
        self.encounter_type = []
        self.layout.clear()
        for button in [self.phase_button, self.text_button, self.proceed_button, self.option_button, self.last_button]:
            button.unset()
        self.layout.add(self.text_button)
        self.layout.add(self.phase_button)
        self.monsters = []
        self.encounters = []
        self.first_fight = True
        self.rolls = []
        self.clear_overlay()
        self.hub.gui_set(True)
        self.hub.switch_info_pane('investigator')
        self.hub.select_ui_button(0)
        self.rumor_not_gate = None
        self.mythos_switch = False
        self.investigator.encounter_impairment = 0
        self.no_loc_click = None
        self.chosen_investigator = ''
        self.chosen_location = ''
        for x in range(5):
            self.investigator.skill_bonuses[x] = [bonus for bonus in self.investigator.skill_bonuses[x] if not bonus.get('temp', False)]
        if not skip:
            self.hub.my_turn = False
            self.hub.networker.publish_payload({'message': 'turn_finished', 'value': None}, self.investigator.name)

    def additional_action(self, amt=1, step='finish'):
        self.hub.remaining_actions += 1
        self.set_buttons(step)

    def adjust_triggers(self, kind, args, step='finish'):
        self.hub.triggers[kind].append(args)
        self.set_buttons(step)

    def allow_gate_close(self, allow=True, step='finish'):
        self.gate_close = allow
        self.set_buttons(step)

    def allow_move(self, distance, step='finish', same_loc=True, must_move=False, investigator='self', nightgaunt=None, loc_props=[], nearest=None):
        investigator_location = self.investigator.location if investigator == 'self' else self.hub.location_manager[self.chosen_investigator].location
        if nearest == None:
            allowed_locs = self.hub.get_locations_within(distance, investigator_location, same_loc=same_loc) if distance != 99 else []
            for prop in loc_props:
                for loc in list(self.hub.location_manager.locations.keys()):
                    if self.hub.location_manager.locations[loc][prop]:
                        allowed_locs.add(loc)
        else:
            for x in range(0,5):
                near_locs = self.hub.get_locations_within(x, self.investigator.location)
                allowed_locs = [loc for loc in near_locs if self.hub.location_manager.locations[loc]['kind'] == nearest]
                if len(allowed_locs) > 0:
                    break
        if len(allowed_locs) == 0 and distance != 99:
            self.set_buttons(step)
        elif len(allowed_locs) == 1 and must_move and allowed_locs[0] == investigator_location:
            self.proceed_button.text = 'Next'
            self.proceed_button.action = self.set_buttons
            self.proceed_button.action_args = {'key': step}
        else:
            def move(unit, location):
                self.hub.networker.publish_payload({'message': 'move_investigator', 'value': unit, 'destination': location}, self.investigator.name)
                if nightgaunt != None:
                    self.hub.networker.publish_payload({'message': 'move_monster', 'value': nightgaunt, 'location': location}, self.investigator.name)
                    self.delay()
                self.click_action = None
                self.no_loc_click = None
                self.set_buttons(step)
            self.proceed_button.action = move
            self.proceed_button.action_args = {'unit': self.investigator.name if investigator == 'self' else self.chosen_investigator, 'location': ''}
            self.option_button.text = 'Stay still'
            self.option_button.action = self.set_buttons
            self.option_button.action_args = {'key': step}
            self.hub.click_pane = self
            def no_click():
                self.proceed_button.text = 'Select location'
                self.proceed_button.disable()
                self.clear_buttons([self.proceed_button] + ([] if must_move else [self.option_button]))
            def loc_select(loc):
                if distance == 99 or loc in allowed_locs:
                    self.proceed_button.text = 'Move to ' + human_readable(loc)
                    self.proceed_button.action_args['location'] = loc
                    self.proceed_button.enable()
                    self.clear_buttons([self.proceed_button])
                else:
                    no_click()
            self.click_action = loc_select
            no_click()
            self.no_loc_click = no_click

    def ambush(self, name=None, step='finish', fail='finish'):
        self.ambush_steps = (step, fail)
        self.combat_will(self.hub.location_manager.create_ambush_monster(name))

    def attract_investigator(self, distance=1, location='', step='finish', monster=None):
        if monster != None:
            location = monster.location
        routes = {}
        for inv in self.hub.location_manager.all_investigators:
            routes[inv] = self.hub.location_manager.find_path(self.hub.location_manager.all_investigators[inv].location, location, distance)
        shortest = min([len(path[0]) for path in routes.values()])
        investigators = [name for name in routes.keys() if len(routes[name][0]) == shortest]
        def move_investigator(name):
            places = set()
            for route in routes[name]:
                places.add(route[min(distance, len(route) - 1)])
            if len(places) > 1:
                self.clear_overlay()
                def choose_path(loc):
                    self.hub.networker.publish_payload({'message': 'move_investigator', 'value': name, 'destination': loc}, self.investigator.name)
                    self.set_buttons(step)
                choices = []
                for destination in places:
                    choices.append(ActionButton(texture='buttons/placeholder.png', text=human_readable(destination), action=choose_path, action_args={'loc': destination}))
                self.clear_overlay()
                self.clear_buttons()
                self.choice_layout = create_choices(choices=choices, title='Select Location')
                self.layout.add(self.choice_layout)
            else:
                self.hub.networker.publish_payload({'message': 'move_investigator', 'value': name, 'destination': routes[name][0][distance]}, self.investigator.name)
                self.set_buttons(step)
        if len(investigators) == 1:
            move_investigator(investigators[0])
        else:
            inv_choices = []
            for inv in investigators:
                inv_choices.append(ActionButton(texture='investigators/' + inv + '_portrait.png', action=move_investigator, action_args={'name': inv}, scale=0.4))
            self.clear_overlay()
            self.choice_layout = create_choices('Select Investigator', choices=inv_choices)
            self.layout.add(self.choice_layout)

    def choose_investigator(self, action, no_self=False, on_location=False, step='finish', no_bless=False, has_curse=False, none_step=None, no_delayed=False):
        choices = []
        subtitle = ''
        if action == 'delay':
            def button_action(name):
                self.chosen_investigator = name
                self.hub.networker.publish_payload({'message': 'become_delayed'}, name + '_server')
                self.set_buttons(step)
            subtitle = 'to become Delayed'
        elif action == 'same_action':
            def button_action(name):
                self.chosen_investigator = name
                self.clear_overlay()
                self.encounter[self.current_key[0] + 'args'][0]['investigator'] = name
                self.encounter[self.current_key[0] + 'args'][0]['skip'] = True
                self.set_buttons(self.current_key)
        elif action == 'set_chosen':
            def button_action(name):
                self.chosen_investigator = name
                self.clear_overlay()
                self.set_buttons(step)
        investigators = list(self.hub.location_manager.all_investigators.values())
        if on_location:
            investigators = [inv.name for inv in investigators if inv.location == self.investigator.location]
        elif no_bless:
            investigators = [inv.name for inv in investigators if not next((card for card in inv.possessions['conditions'] if card.name == 'blessed'), False)]
        elif has_curse:
            investigators = [inv.name for inv in investigators if next((card for card in inv.possessions['conditions'] if card.name == 'cursed'), False)]
        elif no_delayed:
            investigators = [inv.name for inv in investigators if not inv.delayed]
        else:
            investigators = [inv.name for inv in investigators]
        if no_self and self.investigator.name in investigators:
            investigators.remove(self.investigator.name)
        if len(investigators) != 0:
            for names in investigators:
                choices.append(ActionButton(texture='investigators/' + names + '_portrait.png', action=button_action, action_args={'name': names}, scale=0.4))
            self.clear_overlay()
            self.choice_layout = create_choices('Choose Investigator', subtitle, choices)
            self.layout.add(self.choice_layout)
        elif none_step:
            self.set_buttons(none_step)
        return len(investigators)

    def choose_monster(self, step='finish', on_location=True, monster=None):
        if monster != None:
            self.chosen_monster = monster.monster_id
            self.set_buttons(step)
        else:
            monsters = [monster for monster in self.hub.location_manager.locations[self.investigator.location]['monsters']] if on_location else self.hub.location_manager.all_monsters
            def select(monster):
                self.chosen_monster = monster.monster_id
                self.set_buttons(step)
            choices = []
            options = []
            for monster in monsters:
                choices.append(ActionButton(
                    width=100, height=100, texture='monsters/' + monster.name + '.png', action=select, action_args={'monster': monster}))
                options.append(ActionButton(width=100, height=50, texture='buttons/placeholder.png', text=str(monster.toughness - monster.damage) + '/' + str(monster.toughness)))
            self.clear_overlay()
            self.choice_layout = create_choices(title='Select Monster', choices=choices, options=options)
            self.layout.add(self.choice_layout)

    def choose_location(self, action, has_token=None, step='finish'):
        def selected(loc):
            if action == 'set_chosen':
                self.chosen_location = loc
            self.set_buttons(step)
        def no_loc():
            self.proceed_button.disable()
            self.proceed_button.text = 'Select Location'
        def select_loc(loc):
            if has_token == None or self.hub.location_manager.locations[loc][has_token]:
                self.proceed_button.enable()
                self.proceed_button.text = 'Confirm: ' + human_readable(loc)
                self.proceed_button.action = selected
                self.proceed_button.action_args = {'loc': loc}
            else:
                no_loc()
        self.clear_buttons([self.proceed_button])
        self.clear_overlay()
        self.hub.click_pane = self
        self.click_action = select_loc
        self.no_loc_click = no_loc
        no_loc()

    def close_gate(self, step='finish', skip_triggers=False, is_otherworld=True):
        if self.gate_close:
            self.wait_step = step
            self.hub.waiting_panes.append(self)
            triggers = [trigger for trigger in self.hub.triggers['gate_close'] if self.hub.trigger_check(trigger, ['otherworld'])]
            def finish_close(name=None):
                if self.rumor_not_gate != None:
                    self.hub.networker.publish_payload({'message': 'solve_rumor', 'value': self.rumor_not_gate}, self.investigator.name)
                else:
                    map_name = self.hub.location_manager.get_map_name(self.investigator.location)
                    self.hub.networker.publish_payload({'message': 'remove_gate', 'value': map_name + ':' + self.investigator.location}, self.investigator.name)
            if len(triggers) > 0:
                trigger_pane = SmallCardPane(self.hub)
                trigger_pane.setup(triggers, self, False, textures=[trigger.get('texture', 'buttons/placeholder.png') for trigger in triggers], finish_action=finish_close, force_select=True)
            else:
                finish_close()
        else:
            self.set_buttons(step)
    
    def condition_check(self, space_type=None, item_type=None, tag=None, step='finish', fail='finish', on_location=None, radius=0):
        pass_check = True
        if space_type != None and self.hub.location_manager.locations[self.investigator.location]['kind'] != space_type:
            pass_check = False
        if item_type != None:
            items = []
            if item_type == 'all':
                for possession_type in ['assets', 'unique_assets', 'artifacts']:
                    items += [item for item in self.investigator.possessions[possession_type] if tag == None or tag in item.tags]
            else:
                items = [item for item in self.investigator.possessions[item_type] if tag == None or tag in item.tags]
            if len(items) == 0:
                pass_check = False
        if on_location != None:
            on_location = on_location if on_location != 'expedition' else self.hub.location_manager.active_expedition
            pass_check = self.investigator.location in self.hub.get_locations_within(radius, on_location)
        self.set_buttons(step if pass_check else fail)

    def damage_monsters(self, damage=1, step='finish', single=True, epic=True, lose_hp=False, location=None, chosen=False):
        if type(damage) == str and damage == 'success':
            damage = len([roll for roll in self.rolls if roll >= self.investigator.success])
        if chosen:
            monster = next((monster for monster in self.hub.location_manager.all_monsters if monster.monster_id == self.chosen_monster))
            self.hub.damage_monster(monster, damage)
            self.set_buttons(step)
        else:
            def damage_all(loc):
                triggers = []
                for monster in self.hub.location_manager.locations[loc]['monsters']:
                    triggers += self.hub.damage_monster(monster, damage)
                if len(triggers) > 0:
                    pass
                else:
                    self.set_buttons(step)
                    self.click_action = None
            if len(self.hub.location_manager.get_all('monsters', True)) == 0:
                self.proceed_button.text = 'The world is peaceful'
                self.proceed_button.action = self.set_buttons
                self.proceed_button.action_args = {'key': 'finish'}
            else:
                if location == 'self':
                    location = self.investigator.location
                    if not single:
                        damage_all(location)
                        return
                self.hub.gui_set(False)
                if self.encounter.get(step + '_text', None) != None:
                    self.text_button.text = self.encounter.get(step + '_text')
                self.layout.clear()
                self.proceed_button.disable()
                self.proceed_button.text = 'Select Monster'
                for button in [self.text_button, self.phase_button, self.proceed_button]:
                    self.layout.add(button)
                if not single:
                    self.proceed_button.action = damage_all
                    self.proceed_button.text = 'Select Location'
                def select(monster):
                    self.clear_overlay()
                    self.hub.waiting_panes.append(self)
                    if lose_hp:
                        self.encounter['1action'] = ['hp_san']
                        self.encounter['1args'] = [{'step': step, 'hp': -monster.toughness, 'skip': True}]
                        self.wait_step = '1action'
                        self.hp_san(step, -monster.toughness)
                    else:
                        self.wait_step = step
                    self.click_action = None
                    self.hub.damage_monster(monster, damage)
                def damage_loc(loc):
                    self.proceed_button.disable()
                    choices = []
                    options = []
                    monsters = [monster for monster in self.hub.location_manager.locations[loc]['monsters'] if epic or not monster.epic]
                    if len(monsters) > 0:
                        self.proceed_button.text = ''
                        self.proceed_button.action_args = {'loc': loc}
                        for monster in monsters:
                            choices.append(ActionButton(
                                width=100, height=100, texture='monsters/' + monster.name + '.png', action=select if single else lambda *args: None, action_args={'monster': monster}))
                            options.append(ActionButton(width=100, height=50, texture='buttons/placeholder.png', text=str(monster.toughness - monster.damage) + '/' + str(monster.toughness)))
                        self.clear_overlay()
                        self.choice_layout = create_choices(title='Select ' + ('' if single else 'all ') + 'Monster(s)', subtitle=('Damage: ' + str(damage)) if damage != 99 else 'Discard Monster', choices=choices, options=options)
                        self.clear_buttons([self.proceed_button, self.option_button])
                        self.layout.add(self.choice_layout)
                        if not single:
                            self.proceed_button.enable()
                            self.proceed_button.text = 'Confirm: ' + human_readable(loc)
                if location != None:
                    damage_loc(location)
                else:
                    self.hub.click_pane = self
                    self.click_action = damage_loc
                    self.proceed_button.disable()
                    self.option_button.text = 'Select Another Location'
                    def close():
                        self.clear_buttons([self.proceed_button])
                        self.proceed_button.text = 'Select Location'
                        self.clear_overlay()
                    self.option_button.action = close
                    self.option_button.action_args = None

    def delay(self, step='finish', bypass=False):
        def get_delayed():
            self.hub.networker.publish_payload({'message': 'delay_status', 'value': True, 'investigator': self.investigator.name}, 'server_update')
            self.investigator.delayed = True
            self.set_buttons(step)
        if next((item for item in self.investigator.possessions['assets'] if item.name == 'pocket_watch'), False) and not bypass:
            self.phase_button.text = 'Pocket Watch'
            self.text_button.text = 'You cannot become Delayed unless you choose to.'
            self.proceed_button.text = 'Do not become Delayed'
            self.proceed_button.action = self.set_buttons
            self.proceed_button.action_args = {'key': step}
            self.option_button.text = 'Become Delayed'
            self.option_button.action = get_delayed
            self.encounter[self.current_key].append('delayed')
        else:
            get_delayed()            

    def despawn_clues(self, location, player=False, lead_only=False, step='finish'):
        location = location if location != 'chosen' else self.chosen_location
        if player:
            for clue in self.investigator.clues:
                self.investigator.clues.remove(clue)
                self.hub.networker.publish_payload({'message': 'card_discarded', 'kind': 'clues', 'value': clue}, self.investigator.name)
        if not lead_only or self.investigator.name == self.hub.lead_investigator:
            if location == 'all':
                for loc in self.hub.location_manager.locations.keys():
                    stats = self.hub.location_manager.locations[loc]
                    if stats['clue']:
                        stats['clue'] = False
                        self.hub.networker.publish_payload({'message': 'card_discarded', 'kind': 'clues', 'value': stats['map'] + ':' + loc, 'from_map': True}, self.investigator.name)
            elif self.hub.location_manager.locations[location]['clue']:
                stats = self.hub.location_manager.locations[location]
                stats['clue'] = False
                self.hub.networker.publish_payload({'message': 'card_discarded', 'kind': 'clues', 'value': stats['map'] + ':' + location, 'from_map': True}, self.investigator.name)
        self.set_buttons(step)

    def disable_expeditions(self, enabled, step='finish'):
        self.hub.location_manager.expeditions_enabled = enabled
        self.set_buttons(step)

    def discard(self, kind, step='finish', tag='any', amt='one', name=None, get_owner=False, investigator=None, not_in_rolls=None, voluntary=True):
        player = self.investigator if investigator == None else self.hub.location_manager.all_investigators[self.chosen_investigator if investigator == 'chosen' else investigator]
        if get_owner:
            player = next((inv for inv in self.hub.location_manager.all_investigators.values() if name in [pos.name for pos in inv.possessions[kind]]))
        if name != None:
            card = next((item for item in player.possessions[kind] if item.name == name), None)
            if card != None and (not_in_rolls == None or not not_in_rolls in self.rolls):
                self.hub.networker.publish_payload({'message': 'card_discarded', 'value': card.get_server_name(), 'kind': kind}, player.name)
                self.hub.info_panes['possessions'].setup()
                self.wait_step = step
                self.hub.waiting_panes.append(self)
            else:
                self.set_buttons(step)
        else:
            items = []
            if kind == 'all':
                for possession_type in ['assets', 'unique_assets', 'artifacts']:
                    items += player.possessions[possession_type]
            else:
                items = player.possessions[kind]
            items = [item for item in items if tag in item.tags] if tag != 'any' else items
            if len(items) == 0:
                self.set_buttons(step)
            else:
                options = []
                selected = []
                def discard_card(card):
                    self.hub.networker.publish_payload({'message': 'card_discarded', 'value': card.get_server_name(), 'kind': card.kind}, player.name)
                    self.hub.info_panes['possessions'].setup()
                if amt == 'one':
                    def select(card, step):
                        discard_card(card)
                        if type(step) == str:
                            self.wait_step = step
                            self.hub.waiting_panes.append(self)
                        else:
                            step()
                else:
                    def submit():
                        if len(selected) == 0:
                            self.set_buttons(step)
                        else:
                            for x in range(len(selected)):
                                if x == len(selected) - 1:
                                    self.last_value = selected[x].get_server_name()
                                    self.wait_step = step
                                    self.hub.waiting_panes.append(self)
                                discard_card(selected[x])
                    button = ActionButton(width=150, height=50, text='Discard Selected', texture='buttons/placeholder.png', action=submit)
                    if (amt == 'keep_one' and len(items) != len(selected) + 1) or type(amt) == int:
                        button.disable()
                    def select(card, step):
                        if card in selected:
                            selected.remove(card)
                        else:
                            selected.append(card)
                        if amt == 'keep_one':
                            if len(items) != len(selected) + 1:
                                button.disable()
                            else:
                                button.enable()
                        if type(amt) == int:
                            if len(selected) == amt or (len(selected) == len(items) and len(items) < amt):
                                button.enable()
                            else:
                                button.disable()
                        button.trigger_render()
                    options = [button]
                title_text = 'Select ' + ((human_readable(tag) + ' ') if tag != 'any' else '') + (kind[:-1] if kind != 'all' else 'Possession') + ('' if amt == 'one' else 's') + ' to discard'
                choices = [ActionButton(texture=item.texture, width=120, height=185, action=select, action_args={'card': item, 'step': step}) for item in items]
                self.choice_layout = create_choices(choices = choices, options = options, title=title_text)
                self.layout.add(self.choice_layout)

    def end_mythos(self):
        self.hub.networker.publish_payload({'message': 'end_mythos'}, self.investigator.name)

    def gain_asset(self, tag='any', reserve=False, step='finish', name='', successes=False, is_check=False):
        cost = len([roll for roll in self.rolls if roll >= self.investigator.success]) if successes else 99
        if successes:
            card_back = next((card for card in self.investigator.possessions['spells'] if card.name == 'conjuration')).back
            if successes != 'multi':
                card_back[2]['cost'] = cost
        if reserve:
            items = self.hub.info_panes['reserve'].reserve
            pickable = []
            for tags in tag.split(','):
                pickable += items if tag == 'any' else [item for item in items if tags in item['tags'] and item['cost'] <= cost]
            if is_check:
                return len(pickable) > 0
            if len(pickable) > 0:
                selected = []
                options = []
                if successes == 'multi':
                    def confirm():
                        if len(selected) == 0:
                            self.set_buttons(step)
                        else:
                            for item in selected:
                                if selected.index(item) == len(selected) - 1:
                                    self.wait_step = step
                                    self.hub.waiting_panes.append(self)
                                self.hub.request_card('assets', item, 'acquire')
                    confirm_button = ActionButton(width=100, height=50, y=50, action=confirm, text='Confirm', texture='buttons/placeholder.png')
                    confirm_button.disable()
                    options.append(confirm_button)
                    def next_step(item, step):
                        #card_back = next((card for card in self.investigator.possessions['spells'] if card.name == 'conjuartion')).back
                        if item['name'] in selected:
                            selected.remove(item['name'])
                            card_back[2]['cost'] += item['cost']
                        else:
                            selected.append(item['name'])
                            card_back[2]['cost'] -= item['cost']
                        if card_back[2]['cost'] < 0:
                            confirm_button.disable()
                        else:
                            confirm_button.enable()
                        confirm_button.trigger_render()
                        self.choice_layout.children[2].text = 'Successes: ' + str(card_back[2]['cost'])
                        self.choice_layout.children[2].trigger_full_render()
                else:
                    def next_step(item, step):
                        self.wait_step = step
                        self.hub.waiting_panes.append(self)
                        if successes:
                            card_back[2]['cost'] -= item['cost']
                        self.hub.request_card('assets', item['name'], 'acquire')
                        self.clear_overlay()
                choices = [ActionButton(texture=item['texture'], width=120, height=185, action=next_step, action_args={'item': item, 'step': step}) for item in pickable]
                self.choice_layout = create_choices(choices = choices, options=options, title='Choose Asset', subtitle=('Successes: ' + str(card_back[2]['cost'])) if successes else '')
                self.layout.add(self.choice_layout)
            elif not successes:
                self.set_buttons(step)
        else:
            self.wait_step = step
            self.hub.waiting_panes.append(self)
            self.hub.request_card('assets', name, tag=tag)
            return True

    def gain_clue(self, step='finish', amt=1, rolls=False):
        if rolls:
            amt = len([roll for roll in self.rolls if roll >= self.investigator.success])
        if amt == 0:
            self.set_buttons(step)
        else:
            for x in range(amt):
                if x == amt - 1:
                    self.wait_step = step
                    self.hub.waiting_panes.append(self)
                self.hub.networker.publish_payload({'message': 'get_clue', 'value': amt}, self.investigator.name)

    def group_pay(self, kind, name, step='finish', player_request=None, is_check=False):
        total_payment = self.group_payments[name]['group_total']
        payment_needed = self.group_payments[name]['needed']
        qty = self.investigator.get_number(kind)
        max_pay = min(payment_needed, qty)
        remaining_total = total_payment - qty
        min_pay = max(payment_needed - remaining_total, 0)
        self.group_payments[name]['my_payment'] = min(min_pay, qty)
        if is_check:
            return qty >= min_pay
        step = step if player_request == None else player_request
        if self.hub.lead_investigator != self.investigator.name or payment_needed == 0:
            self.clear_buttons() 
        if payment_needed == 0:
            self.proceed_button.action = self.set_buttons
            self.proceed_button.action_args = {'key': step}
            self.proceed_button.text = 'Proceed: Payment met'
            self.layout.add(self.proceed_button)
        title = ''
        match kind:
            case 'clues':
                title = 'Clues'
            case 'hp':
                title = 'Health'
            case 'san':
                title = 'Sanity'
        payment_button = ActionButton(height=100, width=100, text=str(self.group_payments[name]['my_payment']), texture='buttons/placeholder.png')
        minus_button = ActionButton(height=50, width=50, text='-', texture='buttons/placeholder.png', action_args={'amt': -1})
        submit_button = ActionButton(height=50, width=100, text='Submit Payment', texture='buttons/placeholder.png')
        plus_button =  ActionButton(height=50, width=50, text='+', texture='buttons/placeholder.png', action_args={'amt': 1})
        options = [minus_button, submit_button, plus_button]
        def increment(amt):
            for button in options:
                button.enable()
            self.group_payments[name]['my_payment'] += amt
            payment_button.text = str(self.group_payments[name]['my_payment'])
            if self.group_payments[name]['my_payment'] < min_pay or self.group_payments[name]['my_payment'] > max_pay:
                submit_button.disable()
            if self.group_payments[name]['my_payment'] <= min_pay:
                minus_button.disable()
            if self.group_payments[name]['my_payment'] >= max_pay:
                plus_button.disable()
        def pay():
            self.hub.networker.publish_payload({
                'message': 'group_pay_update',
                'needed': payment_needed - self.group_payments[name]['my_payment'],
                'total': remaining_total,
                'name': name},
                'server_update')
            if kind == 'clues':
                self.spend_clue(step, self.group_payments[name]['my_payment'])
            elif kind == 'hp':
                self.hp_san(step, self.group_payments[name]['my_payment'])
            else:
                self.hp_san(step, 0, self.group_payments[name]['my_payment'])
        minus_button.action = increment
        plus_button.action = increment
        submit_button.action = pay
        minus_button.disable()
        if self.group_payments[name]['my_payment'] == max_pay:
            plus_button.disable()
        if self.group_payments[name]['my_payment'] < min_pay:
            submit_button.disable()
        subtitle = 'Minimum: ' + str(min_pay) + '  ' + 'Maximum: ' + str(max_pay)
        self.choice_layout = create_choices(choices=[payment_button], options=options, title='Spend ' + title, subtitle=subtitle)
        self.layout.add(self.choice_layout)

    def group_pay_reckoning(self, kind, name, first=False, step='reckoning', is_check=False):
        if first:
            self.encounter['1'] = ['group_pay_reckoning']
            self.encounter['1args'] = [{'kind': kind, 'name': name, 'step': step, 'skip': True}]
            self.player_index = self.hub.all_investigators.index(self.investigator.name)
            self.group_pay(kind, name, False, '1', None)
        else:
            if self.group_payments[name]['needed'] == 0:
                self.set_buttons(step)
            else:
                self.player_index += 1
                self.player_wait_step = 'group_pay_reckoning'
                self.hub.waiting_panes.append(self)
                self.player_wait_args = {'kind': kind, 'name': name, 'step': step}
                self.hub.networker.publish_payload({'message': 'group_pay_reckoning', 'kind': kind, 'name': name, 'player_request': self.investigator.name}, self.hub.all_investigators[self.player_index] + '_player')
                self.clear_buttons([self.proceed_button])
                self.proceed_button.disable()
                self.proceed_button.text = 'Waiting for other players'

    def heal_monster(self, monster, amt, step='finish'):
        self.hub.networker.publish_payload({'message': 'monster_damaged', 'value': monster.monster_id, 'damage': amt}, 'server_update')
        self.set_buttons(step)

    def hp_san(self, step='finish', hp=0, san=0, stat='health', kind=None, tag=None, no_damage_step=None, investigator='self'):
        if investigator == 'select':
            self.choose_investigator('same_action', True)
            self.clear_buttons()
        else:
            inv = next((player for player in self.hub.location_manager.all_investigators.values() if player.name == investigator), self.investigator)
            self.layout.clear()
            self.layout.add(self.text_button)
            self.layout.add(self.phase_button)
            if kind != None:
                if kind in ['assets', 'conditions', 'unique_assets', 'spells', 'artifacts']:
                    damage = len([item for item in inv.possessions[kind] if tag == None or tag in item.tags])
                elif kind == 'all':
                    all_items = inv.possessions['assets'] + inv.possessions['unique_assets'] + inv.possessions['artifacts']
                    damage = len([item for item in all_items if tag == None or tag in item.tags])
                elif kind == 'omen_gates':
                    color = ['green', 'blue', 'red', 'blue'][self.hub.omen]
                    damage = len([loc for loc in self.hub.location_manager.locations.values() if loc['gate'] and loc['gate_color'] == color])
                if stat == 'health':
                    hp = -damage
                else:
                    san = -damage
            if hp == 0 and san == 0:
                self.set_buttons(no_damage_step if no_damage_step != None else step)
            else:
                if (hp < 0 or san < 0) and hp != -999:
                    self.take_damage(hp, san, self.set_buttons, {'key': step})
                else:
                    inv.health = min(inv.health + hp, inv.max_health)
                    inv.sanity = min(inv.sanity + san, inv.max_sanity)
                    self.hub.networker.publish_payload({'message': 'update_hpsan', 'hp': inv.health, 'san': inv.sanity}, inv.name)
                    if (inv.health < 0 or inv.sanity < 0) and inv == self.investigator:
                        self.death_screen()
                    else:
                        self.set_buttons(step)

    def impair_encounter(self, amt, step='finish'):
        self.investigator.encounter_impairment += amt
        self.set_buttons(step)

    def improve_skill(self, skill, step='finish', amt=1, option=None):
        if len(str(skill)) == 1:
            self.investigator.improve_skill(skill, amt)
            self.hub.info_panes['investigator'].calc_skill(skill)
            self.set_buttons(step)
        else:
            choices = []
            skills = ['lore', 'influence', 'observation', 'strength', 'will']
            def improve(stat):
                self.investigator.improve_skill(stat, amt)
                self.hub.info_panes['investigator'].calc_skill(stat)
                self.set_buttons(step)
            for char in str(skill):
                if self.investigator.skill_tokens[int(char)] < 2:
                    choices.append(ActionButton(width=80, height=80, texture='icons/' + skills[int(char)] + '.png', action=improve, action_args={'stat': int(char)}))
            options = []
            if option != None:
                options = [ActionButton(height=50, texture='buttons/placeholder.png', text='Skip', action=self.set_buttons, action_args={'key': option})]
            self.choice_layout = create_choices(choices=choices, title='Improve a Skill', options=options)
            self.layout.add(self.choice_layout)

    def loss_per_condition(self, lose, per, step='finish'):
        amt = self.discard_check('conditions', per)
        if lose == 'clues':
            amt = amt if amt <= len(self.investigator.clues) else len(self.investigator.clues)
            self.spend_clue(step, amt)
        else:
            self.hp_san(step, -amt if lose == 'health' else 0, -amt if lose == 'sanity' else 0)

    def monster_heal(self, amt, step='finish'):
        for location in self.hub.location_manager.locations:
            for monster in self.hub.location_manager.locations[location]['monsters']:
                monster.heal(amt)
        self.set_buttons(step)

    def move_investigator(self, investigator=None, location=None, step='finish', swap=None):
        investigator = self.investigator.name if investigator == None else investigator
        old_loc = self.hub.location_manager.all_investigators[investigator].location
        location = location if swap == None else self.hub.location_manager.all_investigators[swap].location
        if location == None:
            pass
        else:
            self.hub.networker.publish_payload({'message': 'move_investigator', 'value': investigator, 'destination': location}, self.investigator.name)
            if swap != None:
                self.hub.networker.publish_payload({'message': 'move_investigator', 'value': swap, 'destination': old_loc}, swap)
        self.set_buttons(step)

    def move_monster(self, step='finish', encounter=True, move_to='self', optional=False, monster_name=None):
        if len(self.hub.location_manager.get_all('monsters', True)) == 0:
            self.set_buttons(step)
        else:
            def move(monster, encounter, loc):
                self.hub.networker.publish_payload({'message': 'move_monster', 'value': monster.monster_id, 'location': loc}, self.investigator.name)
                if encounter:
                    self.combat_will(monster)
                    self.ambush_steps = (step, step)
                else:
                    self.set_buttons(step)
                self.click_action = None
            def move_any(monster, encounter):
                self.proceed_button.text += 'Selected: ' + human_readable(monster.name)
                if move_to == 'self':
                    move(monster, encounter, self.investigator.location)
                else:
                    self.hub.click_pane = self
                    self.click_action = lambda locat: move(monster, encounter, locat)
                    self.clear_overlay()
                
            def select(loc):
                choices = []
                options = []
                monsters = self.hub.location_manager.locations[loc]['monsters']
                if len(monsters) > 0:
                    for monster in monsters:
                        choices.append(ActionButton(
                            width=100, height=100, texture='monsters/' + monster.name + '.png', action=move_any, action_args={'monster': monster, 'encounter': encounter}))
                        options.append(ActionButton(width=100, height=50, texture='buttons/placeholder.png', text=str(monster.toughness - monster.damage) + '/' + str(monster.toughness)))
                    self.clear_overlay()
                    self.choice_layout = create_choices(title='Move Monster(s)', choices=choices, options=options)
                    self.layout.add(self.choice_layout)
            if monster_name != None:
                monsters = [monster for monster in self.hub.location_manager.locations[self.investigator.location]['monsters'] if monster.name == monster_name]
                if len(monsters) > 0:
                    self.clear_overlay()
                    self.hub.click_pane = self
                    self.click_action = lambda locat: move(monsters[0], encounter, locat)
                else:
                    self.set_buttons(step)
            else:
                self.hub.click_pane = self
                self.click_action = select
                if optional:
                    self.layout.add(self.option_button)
                    self.option_button.text = 'Pass'
                    self.option_button.action = self.set_buttons
                    self.option_button.action_args = {'key': step}

    def mythos_reckoning(self, number=1, step='finish'):
        self.hub.networker.publish_payload({'message': 'mythos_reckoning', 'value': number}, self.investigator.name)
        self.set_buttons(step)

    def monster_reckoning(self, step='finish', none_step='finish'):
        self.load_reckoning_effects(True)
        if len(self.reckonings['monster']) == 0:
            self.set_buttons(none_step)
        else:
            self.reckoning(step=step)

    def nearest_investigator(self, monster=None, step='finish'):
        location = self.investigator.location
        if monster:
            location = monster.location
        shortest = 99
        investigators = []
        for investigator in self.hub.location_manager.all_investigators:
            path = self.hub.location_manager.find_path(location, self.hub.location_manager.all_investigators[investigator].location, 99)
            if len(path[0]) < shortest:
                investigators = []
                shortest = len(path[0])
            if len(path[0]) == shortest:
                investigators.append(investigator)
        def set_chosen(name):
            self.clear_overlay()
            self.chosen_investigator = name
            self.set_buttons(step)
        if len(investigators) == 1:
            set_chosen(investigators[0])
        else:
            choices = []
            for name in investigators:
                choices.append(ActionButton(texture='investigators/' + name + '_portrait.png', action=set_chosen, action_args={'name': name}, scale=0.4))
            self.clear_overlay()
            self.choice_layout = create_choices('Select Investigator', choices=choices)
            
    def recover_investigator(self, step='finish'):
        self.hub.networker.publish_payload({'message': 'recover_body', 'body': self.recover_name}, self.investigator.name)
        self.wait_step = step
        self.hub.waiting_panes.append(self)

    def request_card(self, kind, step='finish', name='', tag='', trigger=False, investigator=None):
        if investigator in ['select', 'on_location']:
            choices = self.choose_investigator('same_action', on_location=investigator == 'on_location')
            if choices == 0:
                self.set_buttons(step)
        else:
            if investigator == None:
                requestor = self.investigator
            elif investigator == 'chosen':
                requestor = self.hub.location_manager.all_investigators[self.chosen_investigator]
            else:
                requestor = next((inv for inv in self.hub.location_manager.all_investigators.values() if inv.name == investigator))
            card = next((card for card in requestor.possessions[kind] if card.name == name), False)
            if trigger and card:
                self.small_card([card])
            else:
                if name in ['blessed', 'cursed'] and requestor == self.investigator:
                    if card:
                        self.small_card([card], attribute='back', step=step)
                        return
                    else:
                        other = next((card for card in self.investigator.possessions['conditions'] if card.name in ['blessed', 'cursed']), False)
                        if other:
                            self.hub.networker.publish_payload({'message': 'card_discarded', 'value': other.get_server_name(), 'kind': 'conditions'}, self.investigator.name)
                            self.set_buttons(step)
                            return
                self.wait_step = step
                self.hub.waiting_panes.append(self)
                message_sent = self.hub.request_card(kind, name, tag=tag, investigator=requestor)
                if not message_sent:
                    self.wait_step = None
                    self.set_buttons(step)

    def resting_enabled(self, enabled, origin, step='finish'):
        if enabled and origin in self.investigator.recover_restrictions:
            self.investigator.recover_restrictions.remove(origin)
        else:
            self.investigator.recover_restrictions.append(origin)
        self.set_buttons(step)

    def select_location(self, mythos='', step='finish'):
        self.clear_buttons()
        self.no_loc_click = self.clear_buttons
        if mythos == 'that_which_consumes' and len([gate for gate in self.hub.location_manager.locations.values() if gate['gate']]) == 0:
            self.set_buttons(step)
            return
        def doom_end(loc, doom):
            map_name = self.hub.location_manager.get_map_name(loc)
            self.hub.networker.publish_payload({'message': 'remove_gate', 'value': map_name + ':' + loc}, self.investigator.name)
            if doom:
                self.hub.networker.publish_payload({'message': 'doom_change', 'value': -1}, self.investigator.name)
            self.hub.networker.publish_payload({'message': 'end_mythos'}, self.investigator.name)
        def select_loc(location):
            if mythos == 'that_which_consumes'and self.hub.location_manager.locations[location]['gate']:
                on_omen = self.hub.location_manager.locations[location]['color'] == ['green', 'blue', 'red', 'blue'][self.hub.omen]
                self.clear_buttons()
                self.proceed_button.action = doom_end
                self.proceed_button.action_args = {'loc': location, 'doom': not on_omen}
                self.proceed_button.text = 'Discard Gate' + ('' if on_omen else '; Advance Doom by 1')
                self.option_button.text = human_readable(location)
                self.option_button.disable()
                self.layout.add(self.proceed_button)
                self.layout.add(self.option_button)
        self.hub.click_pane = self
        self.click_action = select_loc

    def send_encounter(self, investigator, encounter, last_step=None, step='finish'):
        player = investigator
        if investigator == 'self':
            player = self.investigator.name
        elif investigator == 'chosen':
            player = self.chosen_investigator
        elif investigator == 'trigger':
            player = self.investigator.name if not hasattr(self, 'encounter_name') else self.encounter_name.split(':')[1]
        elif investigator == 'request_player':
            player = self.investigator.name if not hasattr(self, 'request_player') else self.request_player
        if last_step != None:
            for arg in encounter[last_step[0] + 'args']:
                if arg.get('key', False):
                    arg['key'] = self.investigator.name
                else:
                    arg['step'] = self.investigator.name
        self.hub.waiting_panes.append(self)
        self.player_wait_step = self.encounter[step][0]
        self.player_wait_args = self.encounter[step[0] + 'args'][0]
        self.text_button.text = self.text_button.text + '\n\nWaiting for other player'
        self.clear_buttons()
        self.hub.networker.publish_payload({'message': 'player_encounter', 'value': encounter, 'requestor': self.investigator.name}, player + '_player')

    def set_buttons(self, key, return_value=None):
        self.wait_step = None
        self.last_value = None
        self.current_key = key
        if key == 'nothing':
            return
        elif key == 'finish':
            self.finish()
        elif key == 'reckoning':
            self.reckoning()
        elif key in self.hub.all_investigators:
            self.request_player = None
            payload = {'message': 'action_done'}
            if return_value == 'success':
                payload['return_value'] = len([roll for roll in self.rolls if roll >= self.investigator.success]) > 0
            elif return_value == 'success_num':
                payload['return_value'] = len([roll for roll in self.rolls if roll >= self.investigator.success])
            self.finish(True)
            self.hub.networker.publish_payload(payload, key + '_player')
            self.hub.gui_set(getattr(self, 'gui_enabled', True))
        else:
            self.clear_overlay()
            self.set_button_set = set()
            if key == 'no_effect':
                self.proceed_button.enable()
                self.proceed_button.text = 'Onward...'
                self.text_button.text = 'The long night continues...'
                if self.proceed_button not in self.layout.children:
                    self.layout.add(self.proceed_button)
                self.proceed_button.action = self.set_buttons
                self.proceed_button.action_args = {'key': 'finish'}
            else:
                buttons = [self.proceed_button, self.option_button, self.last_button]
                actions = self.encounter[key]
                has_text = self.encounter.get(key + '_flavor', False) or self.encounter.get(key + '_text', False)
                self.text_button.text = (self.encounter.get(key + '_flavor', '') + ('\n\n' if self.encounter.get(key + '_flavor', False) else '') + self.encounter.get(key + '_text', '')) if has_text else self.text_button.text
                for x in range(len(actions)):
                    args = self.encounter[key[0] + 'args'][x]
                    buttons[x].text = args.get('text', '')
                    buttons[x].enable()
                    omit_args = {}
                    for keys in [key for key in args.keys() if key not in ['text', 'check', 'skip', 'owner_only', 'on_trade']]:
                        omit_args[keys] = args[keys]
                    if actions[x] in self.req_dict and not self.req_dict[actions[x]](omit_args) and len(actions) > 0:
                        buttons[x].disable()
                    if actions[x] == 'skill' or args.get('skip', None) != None:
                        buttons[x].action = lambda: None
                        buttons[x].action_args = None
                        self.action_dict[actions[x]](**omit_args)
                    else:
                        buttons[x].action = self.action_dict[actions[x]]
                        buttons[x].action_args = omit_args
                        if actions[x] == 'spend_clue':
                            clues = self.spend_clue(is_check=True, **omit_args)
                            buttons[x].text = buttons[x].text.replace('Spend Clues', 'Spend ' + str(clues) + ' Clue' + ('s' if clues == 1 else ''))
                            rumor_count = 0
                            for map in self.hub.maps.values():
                                rumor_count += len(map.layouts['rumor'].children)
                            if args.get('condition') == 'the_storm' and rumor_count == 0:
                                buttons[x].text = 'Spawn a Rumor'
                                buttons[x].action = self.hub.networker.publish_payload
                                buttons[x].action_args = {'payload': {'message': 'spawn_rumor'}, 'topic': self.investigator.name}
                    self.set_button_set.add(buttons[x])
                self.layout.clear()
                self.layout.add(self.text_button)
                self.layout.add(self.phase_button)
                for x in range(len(self.encounter.get(key, actions))):
                    self.layout.add(buttons[x])
                if len(self.choice_layout.children) > 0:
                    self.layout.add(self.choice_layout)
                if 'combat_strength' in self.encounter.get(key, []):
                    self.layout.add(self.hub.info_panes['location'].layout)
            #self.hub.info_manager.trigger_render()

    def set_doom(self, increment=1, step='finish'):
        self.hub.networker.publish_payload({'message': 'doom_change', 'value': increment}, self.investigator.name)
        self.set_buttons(step)

    def set_omen(self, advance_doom=False, choice=True, increment=1, step='finish'):
        if choice:
            colors = ['green', 'blue', 'red', 'blue']
            choices = []
            def choose_omen(color):
                self.hub.networker.publish_payload({'message': 'set_omen', 'pos': color, 'trigger': advance_doom}, self.investigator.name)
                self.clear_overlay()
                self.set_buttons(step)
            for x in range(4):
                choices.append(ActionButton(height=150, width=150, texture='icons/' + colors[x] + '_omen.png', action=choose_omen, action_args={'color': x}, scale=0.5))
            self.choice_layout = create_choices('Set Omen', choices=choices)
            self.layout.add(self.choice_layout)
        else:
            omen = (self.hub.omen + increment) % 4
            self.hub.networker.publish_payload({'message': 'set_omen', 'pos': omen}, self.investigator.name)
            self.set_buttons(step)

    def shuffle_mystery(self, step='finish'):
        self.hub.networker.publish_payload({'message': 'shuffle_mystery'}, self.investigator.name)
        self.set_buttons(step)

    def single_roll(self, effects, other_action=None):
        def trigger_effects():
            self.clear_overlay()
            for key in effects.keys():
                if str(self.rolls[0]) in str(key):
                    self.set_buttons(effects[key])
        roll = random.randint(1, 6) + self.investigator.encounter_impairment
        roll = 1 if roll < 1 else roll
        options = [ActionButton(width=100, height=30, texture='buttons/placeholder.png', text='Next', action=trigger_effects if other_action == None else other_action)]
        #FOR TESTING
        def autofail():
            self.rolls = [1]
        def succeed():
            self.rolls = [6]
        options.append(ActionButton(action=succeed, texture='buttons/placeholder.png', text='succeed'))
        options.append(ActionButton(action=autofail, texture='buttons/placeholder.png', text='fail'))
        #END TESTING
        self.choice_layout = create_choices(options=options,
            choices=[arcade.gui.UITextureButton(texture = arcade.load_texture(IMAGE_PATH_ROOT + 'icons/die_' + str(roll) + '.png'))])
        self.layout.add(self.choice_layout)
        self.rolls = [roll]

    def skill_test(self, stat, mod=0, step='pass', fail='fail', clue_mod=False, needed=1):
        self.clear_overlay()
        self.clear_buttons()
        mod = mod if not clue_mod else mod + len(self.investigator.clues)
        def confirm_test():
            if len([roll for roll in self.rolls if roll >= self.investigator.success]) >= needed:
                self.set_buttons(step)
            else:
                self.set_buttons(fail)
        next_button = ActionButton(width=100, height=30, texture='buttons/placeholder.png', text='Next', action=confirm_test)
        self.rolls, self.choice_layout = self.hub.run_test(stat, self, mod, [next_button])
        self.layout.add(self.choice_layout)

    def skip_combat(self, step=None):
        self.parent.monsters = []
        self.parent.first_fight = False
        self.parent.clear_overlay()
        self.parent.clear_buttons()
        self.parent.choose_encounter()
        if step != None:
            self.set_buttons(step)

    def small_card(self, cards=None, categories=[], single_card=True, attribute='reckoning', step='finish'):
        if cards == None:
            cards = []
            for cat in categories:
                cards += self.investigator.possessions[cat]
        if len(cards) == 0:
            self.clear_buttons([self.proceed_button])
            self.proceed_button.action = self.set_buttons
            self.proceed_button.action_args = {'key': step if step != 'finish' else 'no_effect'}
            self.proceed_button.text = 'No Effects: Proceed'
        else:
            small_card = SmallCardPane(self.hub)
            def finish_action(name):
                self.set_buttons(step)
            small_card.encounter_type = self.encounter_type + categories
            small_card.setup([getattr(card, attribute) for card in cards], self, single_card, self.text_button.text, [card.kind + '/' + card.name + '.png' for card in cards], finish_action, single_card)

    def spawn_clue(self, step='finish', click=False, number=1):
        if not click:
            self.wait_step = step
            self.hub.waiting_panes.append(self)
            self.hub.networker.publish_payload({'message': 'spawn', 'value': 'clues', 'number': number}, self.investigator.name)
        else:
            def clue_click(loc):
                if not self.hub.location_manager.locations[loc]['clue']:
                    self.wait_step = step
                    self.hub.waiting_panes.append(self)
                    map_name = self.hub.map.name
                    self.hub.networker.publish_payload({'message': 'spawn', 'value': 'clues', 'number': number, 'location':map_name + ':' + loc}, self.investigator.name)
                    self.click_action = None
                    self.set_buttons(step)
            self.hub.click_pane = self
            self.click_action = clue_click

    def spawn_gate(self, step='finish', amt=1, condition=None):
        match condition:
            case 'spells':
                amt = len(self.investigator.possessions['spells'])
        for x in range(amt):
            if x == amt - 1:
                self.wait_step = step
                self.hub.waiting_panes.append(self)
            self.hub.networker.publish_payload({'message': 'spawn', 'value': 'gates', 'number': 1}, self.investigator.name)

    def spawn_monster(self, location=None, name=None, monster=None, step='finish'):
        if monster != None:
            location = self.hub.location_manager.get_map_name(monster.location) + ':' + monster.location
        self.hub.networker.publish_payload({'message': 'spawn', 'value': 'monsters', 'name': name, 'location': location}, self.investigator.name)
        self.set_buttons(step)

    def spend_clue(self, step='finish', clues=1, condition=None, is_check=False, not_spend=False):
        if condition != None:
            if condition == 'all':
                clues = len(self.investigator.clues)
            if condition == 'half':
                clues = math.ceil(self.hub.location_manager.player_count / 2)
            elif 'rumor_token' in condition:
                rumor = self.hub.location_manager.rumors[condition.split(':')[1]]['eldritch']
                clues = self.hub.location_manager.player_count - rumor
                clues = clues if clues > 0 else 0
            elif condition == 'the_storm':
                rumor_count = 0
                for map in self.hub.maps.values():
                    rumor_count += len(map.layouts['rumor'].children)
                clues = min(rumor_count, len(self.investigator.clues))
        if not not_spend:
            for triggers in [trigger for trigger in self.hub.triggers['spend_clue'] if not trigger['used']]:
                clues -= 1
                if not is_check:
                    triggers['used'] = True
                if clues == 0:
                    break
        if not is_check:
            for x in range(clues):
                clue = random.choice(self.investigator.clues)
                self.hub.networker.publish_payload({'message': 'card_discarded', 'kind': 'clues', 'value': clue}, self.investigator.name)
            self.set_buttons(step)
        return clues

    def solve_rumor(self, choice=False, step='finish', name=None):
        def choose_rumor(key):
            self.wait_step = step
            self.hub.waiting_panes.append(self)
            self.hub.networker.publish_payload({'message': 'solve_rumor', 'value': key}, self.investigator.name)
        if choice:
            choices = []
            for rumor in self.hub.location_manager.rumors.keys():
                choices.append(ActionButton(
                    width=100, height=300, texture='buttons/placeholder.png', text=human_readable(rumor), action=choose_rumor, action_args={'key': rumor}))
            self.choice_layout = create_choices(choices=choices, title='Select Rumor')
            self.layout.add(self.choice_layout)
        else:
            choose_rumor(name)

    def update_rumor(self, name, kind, amt, step='finish'):
        payload = {'message': 'update_rumor_solve', 'name': name}
        payload[kind] = amt
        self.hub.networker.publish_payload(payload, self.investigator.name)
        self.set_buttons(step)

    def take_damage(self, hp, san, action, args):
        self.clear_overlay()
        args = {} if args == None else args
        self.hp_damage = hp
        self.san_damage = san
        if hp == 0 and san == 0:
            action(**args)
        else:
            if hp < 0:
                self.hp_damage = min(-1, self.hp_damage + len(self.hub.triggers['combat_damage_reduction']))
            if san < 0:
                self.san_damage = min(-1, self.san_damage + len(self.hub.triggers['combat_san_reduction']))
            choices = []
            def resolve_damage():
                self.investigator.health = min(self.investigator.health + self.hp_damage, self.investigator.max_health)
                self.investigator.sanity = min(self.investigator.sanity + self.san_damage, self.investigator.max_sanity)
                payload = {'message': 'update_hpsan', 'hp': self.investigator.health, 'san': self.investigator.sanity}
                def choose_defeat(kind):
                    payload['kind'] = kind.lower() == 'health'
                    self.hub.networker.publish_payload(payload, self.investigator.name)
                    self.clear_overlay()
                    self.death_screen()
                if self.investigator.health <= 0 and self.investigator.sanity <= 0:
                    self.choice_layout = create_choices('Choose Defeat Type', choices=[ActionButton(width=100, height=50, texture='buttons/placeholder.png', action=choose_defeat, action_args={'kind': kind}, text=kind) for kind in ['Health', 'Sanity']])
                    self.layout.add(self.choice_layout)
                else:
                    self.hub.networker.publish_payload(payload, self.investigator.name)
                    if self.investigator.health <= 0 or self.investigator.sanity <= 0:
                        self.death_screen()
                    else:
                        triggers = []
                        if args.get('monster', False) and hasattr(args['monster'], 'health_damage') and self.hp_damage < 0:
                            triggers.append(args['monster'].health_damage)
                        if args.get('monster', False) and hasattr(args['monster'], 'san_damage') and self.san_damage < 0:
                            triggers.append(args['monster'].health_damage)
                        self.clear_overlay()
                        for trigger in triggers:
                            self.action_dict[trigger['action']](**trigger['aargs'])
                        action(**args)
            options = []
            for trigger in [trig for trig in self.hub.triggers['hp_san_loss'] if not trig.get('used', False)]:
                hp_check = hp < 0 and trigger.get('on_hp_loss', False)
                san_check = san < 0 and trigger.get('on_san_loss', False)
                small_card = SmallCardPane(self.hub)
                if (hp_check or san_check) and self.hub.trigger_check(trigger, self.encounter_type):
                    trigger['action']['title'] = human_readable(trigger['name'])
                    def finish_action(name):
                        inv = name.split(':')
                        used_trigger = next((trig for trig in self.hub.triggers['hp_san_loss'] if trig['name'] == inv[2] and trig['investigator'] == inv[1]), False)
                        if small_card.item_used:
                            self.choice_layout.children = [widget for widget in self.choice_layout.children if getattr(widget, 'action_args', {}) == None or getattr(widget, 'action_args', {}).get('name', '') != name]
                            self.layout.trigger_render()
                            if used_trigger and used_trigger.get('owner_only', False):
                                used_trigger['used'] = True
                            else:
                                self.hub.networker.publish_payload({'message': 'trigger_used', 'value': name, 'kind': 'hp_san_loss'}, 'server_update')
                        else:
                            small_card.encounters.append(used_trigger['action'])
                            used_trigger['used'] = False
                            #button = next((button for button in self.choice_layout.children if getattr(button, 'action_args', {}) == None or getattr(button, 'action_args', {}).get#('name', '') == name), False)
                            #if button:
                            #    self.choice_layout.children.remove(button)
                    def setup(encounters, parent, finish_action, name):
                        self.hub.info_pane = small_card
                        small_card.setup(encounters, parent, finish_action=finish_action, force_select=True)
                        small_card.encounter_name = name
                        inv = name.split(':')
                        used_trigger = next((trig for trig in self.hub.triggers['hp_san_loss'] if trig['name'] == inv[2] and trig['investigator'] == inv[1]), False)
                        used_trigger['used'] = True
                        #next((button for button in self.choice_layout.children if getattr(button, 'action_args', {}) == None or getattr(button, 'action_args', {}).get('name', '') == name)).disable()
                    button = ActionButton(scale=0.5, texture=trigger['texture'], action=setup, action_args={'encounters': [trigger['action']], 'parent': self, 'finish_action': finish_action, 'name': 'hp_san_loss:' + trigger['investigator'] + ':' + trigger['name']}, text=human_readable(trigger['investigator']))
                    if trigger.get('font_size', None) != None:
                        button.style = {'font_size': trigger['font_size']}
                    if trigger.get('used', False) and trigger.get('single_use', False):
                        button.disable()
                    choices.append(button)
            if self.hp_damage < 0 and args.get('monster', False) and args.get('monster').name == 'maniac' and len([ally for ally in self.investigator.possessions['assets'] if 'ally' in ally.tags]):
                def maniac():
                    self.clear_overlay()
                    self.hp_damage = 0
                    self.discard('assets', resolve_damage, 'ally')
                choices.append(ActionButton(scale=0.5, texture='monsters/maniac.png', action=maniac))
            next_button = ActionButton(
                y=50, width=100, height=50, texture='buttons/placeholder.png', text='Next', action=resolve_damage)
            self.choice_layout = create_choices(choices=choices, options=options + [next_button], title='Taking Damage', subtitle='Health: ' + str(-self.hp_damage) + '   Sanity: ' + str(-self.san_damage))
            self.layout.add(self.choice_layout)

    def trigger_encounter(self, kind, rumor=None):
        self.rumor_not_gate = rumor
        self.hub.networker.publish_payload({'message': 'get_encounter', 'value': kind}, self.investigator.name)

    def load_mythos(self, mythos):
        self.mythos = mythos
        self.encounter = MYTHOS[mythos]
        self.encounter_type = []
        self.phase_button.text = 'Mythos Phase'
        self.layout.clear()
        self.layout.add(self.text_button)
        self.layout.add(self.phase_button)
        text = human_readable(mythos) + '\n\n' + self.encounter['flavor'] + '\n\n' + self.encounter.get('text', '')
        if self.encounter.get('font_size', None) != None:
            self.text_button.style = {'font_size': int(self.encounter['font_size'])}
        self.text_button.text = text
        self.hub.info_manager.trigger_render()
        self.option_button.text = 'Waiting for other players'
        self.option_button.action = lambda: None
        self.option_button.action_args = None
        self.layout.add(self.option_button)

    def activate_mythos(self, name=None):
        if (self.encounter.get('lead_only', None) != None and self.investigator.name != self.hub.lead_investigator) or self.investigator.is_dead:
            self.hub.networker.publish_payload({'message': 'turn_finished', 'value': None}, self.investigator.name)
        elif len(self.monster_spawns):
            spawn_pane = SmallCardPane(self.hub)
            spawn_pane.setup(self.monster_spawns, self, False, textures=[trigger['texture'] for trigger in self.monster_spawns], finish_action=self.activate_mythos, force_select=True)
            self.monster_spawns = []
        else:
            self.encounter = MYTHOS[self.mythos]
            self.encounter_type.append('mythos')
            self.set_buttons('action')

    def load_reckoning_effects(self, monsters_only=False):
        self.reckonings = {
                'mythos': [],
                'monster': [],
                'item': [],
                'ancient_one': []
            }
        if self.hub.lead_investigator == self.investigator.name:
            for monster in [monster for monster in self.hub.location_manager.all_monsters if hasattr(monster, 'reckoning')]:
                if not monster.reckoning.get('on_location', False) or monster.location == self.investigator.location:
                    self.reckonings['monster'].append((monster.reckoning, 'monsters/' + monster.name + '.png'))
            if not monsters_only:
                if len(self.mythos_reckonings) > 0:
                    for reckon in self.mythos_reckonings:
                        self.reckonings['mythos'].append((reckon, 'ancient_ones/mythos_back.png'))
        if not monsters_only: 
            for kind in self.investigator.possessions.values():
                for card in [card for card in kind if hasattr(card, 'reckoning')]:
                    self.reckonings['item'].append((card.reckoning, card.kind + '/' + card.name + '.png'))

    def reckoning(self, kind='monster', first=False, step='finish'):
        kinds = ['monster', 'ancient_one', 'mythos', 'item', 'finish']
        scales = [0.5, 0.5, 0.4, 0.5]
        index = kinds.index(kind) + 1
        small_card = SmallCardPane(self.hub)
        if first:
            self.load_reckoning_effects()
        if index == 5:
            self.set_buttons(step)
            self.load_mythos(self.mythos)
            self.hub.show_encounter_pane()
        elif len(self.reckonings[kind]) > 0 and (not self.investigator.is_dead or kind != 'item'):
            def finish_action(name):
                self.reckoning(kinds[index], step=step)
            small_card.setup([reckon[0] for reckon in self.reckonings[kind]], self, False, 'Resolving ' + human_readable(kind) + ' Reckoning Effects', [reckon[1] for reckon in self.reckonings[kind]], finish_action, scale=scales[index-1])
            small_card.phase_button.text = 'Reckoning Phase'
        else:
            self.reckoning(kinds[index], step=step)

class SmallCardPane(EncounterPane):
    def __init__(self, hub):
        EncounterPane.__init__(self, hub)
        self.encounters = []
        self.small_card_pic = ActionButton(x=1015, y=400, width=250, height=385, texture='buttons/placeholder.png')
        small_card_dict = {
            'flip_card': self.flip_card,
            'trade': self.trade,
            'adjust_damage': self.adjust_damage,
            'mod_die': self.mod_die,
            'temp_bonus': self.temp_bonus,
            'monster_reckoning_move': self.monster_reckoning_move,
            'monster_reckoning_damage': self.monster_reckoning_damage,
            'kleptomania': self.kleptomania,
            'violent_outbursts': self.violent_outbursts,
            'spell_flip': self.spell_flip,
            'blessing_of_isis': self.blessing_of_isis
        }
        small_card_req_dict = {
            'trade': lambda args: self.hub.location_manager.player_count > 1,
            'choose_monster': lambda args: len(self.hub.location_manager.locations[self.investigator.location]) > 0 if args.get('on_location', True) else len(self.hub.location_manager.all_monsters) > 0
        }
        self.action_dict = self.action_dict | small_card_dict
        self.req_dict = self.req_dict | small_card_req_dict
        self.item_used = True
        self.encounter_name = ''
        self.scale = 0.5
        self.request_player = None
        self.gui_enabled = True
        self.player_encounters = []
        self.single_pick = True
        self.finish_action = None

    def setup(self, encounters, parent, single_pick=True, default_text=None, textures=[], finish_action=None, force_select=False, scale=0.5):
        self.scale = scale
        self.item_used = True
        self.finish_action = finish_action
        self.encounters = encounters
        self.set_return_gui(parent)
        self.clear_overlay()
        self.single_pick = single_pick
        self.default_text = default_text
        self.textures = textures if len(textures) > 0 else ['buttons/placeholder.png'] * len(self.encounters)
        if force_select and len(encounters) == 1:
            self.encounter_selected(encounters[0])
        else:
            self.pick_encounters()

    def set_return_gui(self, parent):
        self.parent = parent
        self.hub.info_manager.children = {0:[]}
        self.hub.info_manager.add(self.layout)

    def flip_card(self, kind, name, investigator=None):
        if investigator == None:
            investigator = self.investigator.name
        card = next((card for card in self.hub.location_manager.all_investigators[investigator].possessions[kind] if card.name == name))
        card.back_seen = True
        self.encounter = getattr(card, 'back')
        self.set_buttons('action')

    def spell_flip(self, name, take_action=False):
        card = next((card for card in self.investigator.possessions['spells'] if card.name == name))
        if take_action:
            self.encounter = card.action
            self.set_buttons('action')
        else:
            thresholds = list(card.back.keys())
            thresholds.sort()
            successes = len([roll for roll in self.rolls if roll >= self.investigator.success])
            index = 0
            for x in range(len(thresholds)):
                index = x
                if successes == thresholds[x]:
                    break
                elif successes < thresholds[x]:
                    index = x - 1
                    break
            self.encounter = card.back[thresholds[index]]
            self.set_buttons('action')

    def adjust_damage(self, hp_change=0, san_change=0, step='finish', return_value=None):
        if type(return_value) == int:
            if hp_change < 0:
                hp_change = return_value
            else:
                san_change = return_value
            return_value = None
        if return_value == None or (type(return_value) == bool and return_value):
            hp_change = hp_change if type(hp_change) == int else -self.parent.hp_damage
            san_change = san_change if type(san_change) == int else -self.parent.san_damage
            self.parent.hp_damage += hp_change
            self.parent.san_damage += san_change
        self.parent.choice_layout.children[2].text = 'Health: ' + str(self.parent.hp_damage) + '   Sanity: ' + str(self.parent.san_damage)
        to_remove = []
        for button in self.parent.choice_layout.children:
            if getattr(button, 'action_args', None) != None and len(button.action_args.get('name').split(':')) == 3:
                identifier = button.action_args['name'].split(':')
                trigger = next((trigger for trigger in self.hub.triggers[identifier[0]] if trigger['name'] == identifier[2] and trigger['investigator'] == identifier[1] and trigger['used']), False)
                if trigger:
                    to_remove.append(button)
        self.parent.choice_layout.children = [button for button in self.parent.choice_layout.children if button not in to_remove]
        self.set_buttons(step)

    def mod_die(self, trigger_name, step='finish'):
        self.encounter_name = trigger_name
        self.set_buttons(step)

    def temp_bonus(self, name, condition, stat=0, value=1, reroll=False, step='finish'):
        if stat == 'all':
            for x in range(5):
                self.investigator.skill_bonuses[x].append({'temp': True, 'value': value, 'name': name, 'condition': condition})
        else:
            if reroll:
                trigger = { 'name': name,
                            'mod_die': 'reroll',
                            'temp': True,
                            'action': {
                                'action': ['mod_die', 'set_buttons'],
                                'aargs': [
                                    {'trigger_name': condition + ':' + name, 'text': 'Use'},
                                    {'key': 'no_use', 'text': 'Back'}],
                                'title': human_readable(name),
                                'action_text': "You may reroll 1 die."}}
                self.hub.triggers[condition].append(trigger)
            else:
                self.investigator.skill_bonuses[stat].append({'temp': True, 'value': value, 'name': name, 'condition': condition})
        self.set_buttons(step)

    def trade(self, investigator=None, give_only=False, tag=None, swap=False, step='finish'):
        if investigator == None:
            self.choose_investigator('same_action', True)
            self.clear_buttons()
        else:
            pane = self.hub.info_panes['location'].possession_screen
            def finish_trade():
                if swap:
                    self.encounter[step[0] + 'args'][0]['swap'] = investigator
                pane.close_button.action = self.hub.info_panes['location'].on_show
                self.hub.info_manager.children = {0:[]}
                self.hub.info_manager.children[0].append(self.layout)
                self.hub.info_manager.children[0].append(self.hub.info_panes['possessions'].big_card)
                self.set_buttons(step)
            pane.investigator = self.hub.location_manager.all_investigators[investigator]
            pane.setup(True, give_only, tag)
            pane.action_point = 0
            pane.start_trade(tag)
            pane.close_button.action = finish_trade
            self.hub.info_manager.children[0].append(pane.layout)
            self.hub.info_manager.trigger_render()

    def monster_reckoning_move(self, monster, step='finish', distance=1, encounter=True, damage=0):
        paths = []
        closest = 100
        is_migo = monster.name == 'mi-go'
        if is_migo:
            locs = [loc for loc in self.hub.location_manager.locations.keys() if self.hub.location_manager.locations[loc]['clue']]
            if len(locs) == 0:
                self.set_buttons(step)
                return
        else:
            locs = self.hub.location_manager.all_investigators
        if monster.name == 'nightgaunt':
            same_space = [inv for inv in locs if locs[inv].location == monster.location]
            def send_move(investigator):
                self.send_encounter(investigator, {'action': ['allow_move'], 'aargs': [{'distance': 1, 'same_loc': False, 'must_move': True, 'nightgaunt': monster.monster_id, 'step': 'delayed', 'skip': True}], 'delayed': ['delayed'], 'dargs': [{'skip': True}], 'action_text': 'Move you and this Monster 1 space and become Delayed', 'title': 'Nightgaunt - Reckoning'}, step=step)
            if len(same_space) == 1:
                send_move(same_space[0])
                return
            elif len(same_space) > 1:
                choices = []
                for names in same_space:
                    choices.append(ActionButton(texture='investigators/' + names + '_portrait.png', action=send_move, action_args={'investigator': names}, scale=0.4))
                self.clear_overlay()
                self.choice_layout = create_choices('Select Investigator', choices=choices)
                return
        for loc in locs :
            location = loc if is_migo else locs[loc].location
            if monster.location == location:
                routes = [[location]]
            else:
                routes = self.hub.location_manager.find_path(monster.location, location, distance)
            if len(routes[0]) < closest:
                paths = []
                closest = len(routes[0])
            if len(routes[0]) == closest:
                paths = paths + routes
        def move_to_investigator(monster, destination):
            self.clear_overlay()
            self.hub.networker.publish_payload({'message': 'move_monster', 'value': monster.monster_id, 'location': destination}, self.investigator.name)
            same_loc = [inv for inv in self.hub.location_manager.all_investigators.keys() if self.hub.location_manager.all_investigators[inv].location == destination]
            if (damage > 0 or encounter) and len(same_loc) > 0:
                def selected(investigator):
                    self.hub.waiting_panes.append(self)
                    self.player_wait_step = 'waiting'
                    self.choice_layout = create_choices('Waiting for other player to finish')
                    self.layout.add(self.choice_layout)
                    self.player_wait_step = 'set_buttons'
                    self.player_wait_args = {'key': step}
                    self.clear_buttons()
                    self.hub.networker.publish_payload({'message': 'combat', 'value': monster.monster_id, 'sender': self.investigator.name}, investigator + '_player')
                if len(same_loc) == 1:
                    selected(same_loc[0])
                else:
                    inv_choices = []
                    for inv in same_loc:
                        inv_choices.append(ActionButton(texture='investigators/' + inv + '_portrait.png', action=selected, action_args={'investigator': inv}, scale=0.4))
                    self.clear_overlay()
                    self.choice_layout = create_choices('Select Investigator', choices=inv_choices)
                    self.layout.add(self.choice_layout)
            else:
                if is_migo:
                    self.despawn_clues(destination, step=step)
                else:
                    self.set_buttons(step)
        places = set()
        for route in paths:
            places.add(route[min(distance, len(route) - 1)])
        if len(places) > 1:
            choices = []
            for destination in places:
                choices.append(ActionButton(texture='buttons/placeholder.png', text=human_readable(destination), action=move_to_investigator, action_args={'monster': monster, 'destination': destination}))
            self.clear_overlay()
            self.clear_buttons()
            self.choice_layout = create_choices(choices=choices, title='Select Location')
            self.layout.add(self.choice_layout)
        else:
            move_to_investigator(monster, paths[0][min(distance, len(paths[0]) - 1)])

    def monster_reckoning_damage(self, monster, hp=0, san=0, adjacent=False, first=False, step='finish', cursed=False):
        if first:
            new_args = copy.deepcopy(self.encounter[self.current_key[0] + 'args'])
            del new_args[0]['first']
            del new_args[0]['skip']
            self.encounter[self.current_key[0] + 'args'] = new_args
            if cursed:
                self.player_encounters = [inv.name for inv in self.hub.location_manager.all_investigators.values() if next((cond for cond in inv.possessions['conditions'] if cond.name == 'cursed'), False)]
            else:
                locations = [monster.location] + (list(self.hub.location_manager.locations[monster.location]['routes'].keys()) if adjacent else [])
                self.player_encounters = [inv.name for inv in self.hub.location_manager.all_investigators.values() if inv.location in locations]
        if len(self.player_encounters) == 0:
            self.set_buttons(step)
        else:
            investigator = self.player_encounters[0]
            self.player_encounters = self.player_encounters[1:]
            self.send_encounter(investigator, {'action': ['hp_san'], 'aargs': [{'hp': hp, 'san': san, 'skip': True}], 'action_text': self.text_button.text, 'title': human_readable(monster.name) + ' - Reckoning'}, step=self.current_key)

    def kleptomania(self, current_items=None):
        if current_items == None:
            self.encounter['aargs'][0]['current_items'] = [item.name for item in self.investigator.possessions['assets']]
            self.encounter['aargs'][0]['skip'] = True
            del self.encounter['aargs'][0]['text']
            self.request_card('assets', 'action', tag='item')
        else:
            item = next((item for item in self.investigator.possessions['assets'] if item.name not in current_items))
            self.encounter['targs'][0]['needed'] = item.cost
            self.encounter['aargs'][0]['current_items'] = None
            del self.encounter['aargs'][0]['skip']
            self.encounter['aargs'][0]['text'] = 'Steal an item'
            self.encounter['dargs'][0]['text'] = 'Discard ' + human_readable(item.name)
            self.encounter['dargs'][0]['name'] = item.name
            self.encounter['test_text'] = 'You must hide from the authorities.\n\nItem Acquired: ' + human_readable(item.name) + '\n\nSuccesses needed (Cost): ' + str(item.cost)
            self.set_buttons('test')

    def violent_outbursts(self, current_players=None, step='finish'):
        if current_players == None:
            current_players = [inv.name for inv in self.hub.location_manager.all_investigators.values() if inv.location == self.investigator.location and inv.name != self.investigator.name]
        if len(current_players) == 0:
            self.phase_button.text = self.encounter.get('title', '')
            self.set_buttons(step)
        else:
            encounter = {'action': ['hp_san'], 'aargs': [{'hp': -2, 'skip': True, 'step': self.investigator.name}], 'action_text': 'Paranoia - Violent Outbursts\n\n\n' + human_readable(self.investigator.name)}
            self.hub.waiting_panes.append(self)
            receiver = current_players.pop(0)
            self.player_wait_step = 'violent_outbursts'
            self.player_wait_args = {'current_players': current_players, 'step': step}
            self.hub.networker.publish_payload({'message': 'player_encounter', 'value': encounter}, receiver + '_player')

    def blessing_of_isis(self):
        investigators = [inv for inv in self.hub.location_manager.all_investigators.values() if (not next((card for card in inv.possessions['conditions'] if card.name == 'blessed'), False)) and inv.location == self.investigator.location]
        for inv in investigators:
            self.hub.request_card('conditions', 'blessed', investigator=inv)
        self.set_buttons('finish')

    def player_encounter(self, encounter):
        self.encounter = encounter
        self.set_buttons('action')

    def encounter_selected(self, encounter):
        index = self.encounters.index(encounter)
        self.textures.pop(index)
        self.encounters.remove(encounter)
        self.encounter = encounter
        self.set_buttons('action')
        self.phase_button.text = self.encounter.get('title', '')
        self.encounter_name = self.encounter.get('title', '')

    def pick_encounters(self):
        choices = []
        self.text_button.text = self.default_text
        self.choice_layout.clear()
        for x in range(len(self.encounters)):
            choices.append(ActionButton(scale=self.scale, texture=self.textures[x], action=self.encounter_selected, action_args={'encounter': self.encounters[x]}))
        if len([encounter for encounter in self.encounters if encounter.get('is_required', False)]) == 0:
            choices.append(ActionButton(width=100, height=50, texture='buttons/placeholder.png', text='Skip Effects', action=self.finish, action_args={'skip': True}))
        self.choice_layout = create_choices('Choose Effect', choices=choices)
        self.layout.add(self.choice_layout)

    def jacqueline_check(self, item, owner):
        self.text_button.text = 'Once per round, when another Investigator gains a non-Common Condition, you may look at the back of that card and gain 1 Clue.\n\n' + human_readable(owner) + ' - ' + human_readable(item[:-1])
        self.phase_button.text = 'Jacqueline Fine - Passive'
        self.proceed_button.text = 'View Card'
        self.option_button.text = 'Decline'
        def respond(item, owner, checked):
            if checked:
                self.hub.networker.publish_payload({'message': 'get_clue', 'value': 1}, self.investigator.name)
            self.hub.networker.publish_payload({'message': 'jacqueline_checked', 'item': item, 'owner': owner, 'revealed': checked}, 'jacqueline_fine')
            self.hub.gui_set(True)
            self.finish()
        self.proceed_button.action = respond
        self.option_button.action = respond
        self.proceed_button.action_args = {'item': item, 'owner': owner, 'checked': True}
        self.option_button.action_args = {'item': item, 'owner': owner, 'checked': False}
        self.layout.clear()
        for button in [self.text_button, self.phase_button, self.option_button, self.proceed_button]:
            self.layout.add(button)

    def set_buttons(self, key, return_value=None):
        if key == 'no_use':
            self.encounters.append(self.encounter)
            self.item_used = False
            self.finish()
        else:
            if key == 'finish' and self.request_player != None:
                key = self.request_player
            super().set_buttons(key, return_value)

    def finish(self, skip=False):
        if not self.single_pick and len(self.encounters) > 0 and not skip:
            self.clear_buttons()
            self.phase_button.text = ''
            self.pick_encounters()
        else:
            self.encounter_type = []
            self.hub.info_manager.children = {0:[]}
            self.clear_overlay()
            self.hub.info_manager.add(self.parent.layout)
            self.hub.info_manager.trigger_render()
            self.hub.info_pane = self.parent
            if self.finish_action != None:
                self.finish_action(self.encounter_name)

class InvestigatorSkillPane(SmallCardPane):
    def __init__(self, hub):
        SmallCardPane.__init__(self, hub)
        investigator_dict = {
            'akachi_onyele': self.akachi_onyele,
            'charlie_kane': self.charlie_kane,
            'send_items': self.send_items,
            'jacqueline_fine': self.jacqueline_fine
        }
        self.action_dict = self.action_dict | investigator_dict
        self.server_value = None
        self.acquire_items = []
        self.action_array = []
        self.action_string = ''

    def akachi_onyele(self, is_first=False):
        if is_first:
            args = copy.deepcopy(self.encounter[self.current_key[0] + 'args'])
            del args[0]['is_first']
            self.encounter[self.current_key[0] + 'args'] = args
            self.hub.waiting_panes.append(self)
            self.wait_step = self.current_key
            self.hub.networker.publish_payload({'message': 'akachi_onyele', 'value': 'request'}, self.investigator.name)
        else:
            choices = []
            def select(gate):
                self.hub.networker.publish_payload({'message': 'akachi_onyele', 'value': self.hub.location_manager.get_map_name(gate) + ':' + gate}, self.investigator.name)
                self.set_buttons('finish')
            for gate in [gate.split(':')[1] for gate in self.server_value]:
                choices.append(ActionButton(texture='maps/' + human_readable(gate) + '_gate.png', action=select, action_args={'gate': gate}, scale=0.4, text=human_readable(gate), text_position=(0, -20)))
            self.choice_layout = create_choices('Select Gate to put on the bottom', choices=choices)

    def charlie_kane(self):
        self.hub.waiting_panes.append(self)
        self.player_wait_step = 'set_buttons'
        self.player_wait_args = {'key': 'finish'}
        self.proceed_button.text = 'Waiting for other player'
        self.hub.networker.publish_payload({'message': 'charlie_kane'}, self.chosen_investigator + '_player')

    def jacqueline_fine(self):
        investigators = list(self.hub.location_manager.all_investigators.values())
        inv_names = [investigator.name for investigator in investigators if investigator.name != self.hub.investigator.name and (len(self.hub.investigator.clues) > 0 or len(investigator.clues) > 0)]
        choices = []
        def trade_clues(name):
            self.clear_overlay()
            my_clues = len(self.investigator.clues)
            their_clues = len(self.hub.location_manager.all_investigators[name].clues)
            info_button = ActionButton(texture='buttons/placeholder.png', text='Trade Clues')
            self.action_string = '0'
            def send():
                transaction = int(self.action_string)
                if transaction > 0:
                    transaction = 0
                if not abs(transaction - 1) > my_clues:
                    transaction = transaction - 1
                    info_button.text = 'Send ' + str(abs(transaction)) + ' Clue' + ('s' if transaction < -1 else '')
                self.action_string = str(transaction)
            def take():
                transaction = int(self.action_string)
                if transaction < 0:
                    transaction = 0
                if not transaction + 1 > their_clues:
                    transaction = transaction + 1
                    info_button.text = 'Take ' + str(transaction) + ' Clue' + ('s' if transaction > 1 else '')
                self.action_string = str(transaction)
            jacqueline = ActionButton(texture='investigators/jacqueline_fine_portrait.png', text='Clues: ' + str(my_clues), text_position=(0,-70), scale=0.5)
            other = ActionButton(texture='investigators/' + name + '_portrait.png', text='Clues: ' + str(their_clues), text_position=(0,-70), scale=0.5)
            send_button = ActionButton(width=30, texture='buttons/placeholder.png', text='>>', action=send)
            take_button = ActionButton(width=30, texture='buttons/placeholder.png', text='<<', action=take)
            self.choice_layout = create_choices('Trade Clues - ' + human_readable(name), choices=[jacqueline, take_button, info_button, send_button, other])
            self.layout.add(self.choice_layout)
            def finish_trade(name):
                amt = abs(int(self.action_string))
                sender = 'jacqueline_fine' if int(self.action_string) < 0 else name
                taker = 'jacqueline_fine' if sender != 'jacqueline_fine' else name
                clue_list = [clue for clue in self.hub.location_manager.all_investigators[sender].clues]
                clues_to_send = []
                for x in range(amt):
                    clue = random.choice(clue_list)
                    clues_to_send.append(clue)
                    clue_list.remove(clue)
                self.hub.networker.publish_payload({'message': 'card_discarded', 'kind': 'clues', 'value': ';'.join(clues_to_send)}, sender)
                self.hub.networker.publish_payload({'message': 'get_clue', 'value': amt}, taker)
                self.finish()
            self.proceed_button.action = finish_trade
            self.proceed_button.action_args = {'name': name}
            self.proceed_button.text = 'Finish Trade'
        for name in inv_names:
            choices.append(ActionButton(texture='investigators/' + name + '_portrait.png', action=trade_clues, action_args={'name': name}, scale=0.4))
        self.clear_overlay()
        self.choice_layout = create_choices('Choose Investigator', 'Trade Clues', choices)
        self.layout.add(self.choice_layout)

    def send_items(self, reserve_pane):
        self.hub.overlay_showing = True
        self.text_button.text = 'You may allow other Investigators to gain any cards you purchase.'
        self.phase_button.text = 'Charlie Kane - Acquire Assets'
        self.charlie_send = True
        def resolve_action():
            reserve_pane.selected = self.acquire_items
            self.charlie_send = False
            self.finish()
        if len(self.acquire_items) == 0:
            resolve_action()
        else:
            def send(item, inv):
                is_service = 'service' in item['tags']
                self.acquire_items = [items for items in self.acquire_items if items != item]
                self.layout.remove(self.choice_layout)
                if not is_service:
                    self.hub.request_card('assets', item['name'], 'acquire', investigator=inv)
                    self.send_items(reserve_pane)
                else:
                    self.hub.networker.publish_payload({'message': 'card_discarded', 'value': item['name'], 'kind': 'assets'}, self.hub.investigator.name)
                    self.hub.waiting_panes.append(self)
                    self.player_wait_step = 'send_items'
                    self.player_wait_args = {'reserve_pane': reserve_pane}
                    self.text_button.text = 'Waiting for ' + human_readable(inv.name) + ' to resolve ' + human_readable(item['name'])
                    self.layout.children.remove(self.proceed_button)
                    self.hub.networker.publish_payload({'message': 'services', 'service': item['name'], 'sender': 'charlie_kane'}, inv.name + '_player')
            self.choice_layout.clear()
            choices = []
            for item in self.acquire_items:
                choices.append(ActionButton(texture='assets/' + item['name'].replace('.', '') + '.png', scale=0.5, action=send, action_args={'item': item}, name='charlie_send'))
            options = []
            for key in [inv for inv in list(self.hub.location_manager.all_investigators.keys()) if inv != self.investigator.name]:
                options.append(ActionButton(texture='investigators/' + key + '_portrait.png', scale=0.4, name=key))
            self.choice_layout = create_choices('Drag Items to send', choices=choices, options=options)
            for button in choices:
                button.initial_x = button.x
                button.initial_y = button.y
            self.layout.add(self.choice_layout)
            if self.proceed_button not in self.layout:
                self.layout.add(self.proceed_button)
            self.proceed_button.text = 'Finish'
            self.proceed_button.action = resolve_action

    def finish(self):
        self.action_array = []
        self.action_string = ''
        super().finish()