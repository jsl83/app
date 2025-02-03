import arcade, arcade.gui, yaml, random, math
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
            'adjust_triggers': self.adjust_triggers,
            'allow_gate_close': self.allow_gate_close,
            'allow_move': self.allow_move,
            'ambush': self.ambush,
            'choose_investigator': self.choose_investigator,
            'close_gate': self.close_gate,
            'combat': self.encounter_phase,
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
            'hp_san': self.hp_san,
            'impair_encounter': self.impair_encounter,
            'improve_skill': self.improve_skill,
            'loss_per_condition': self.loss_per_condition,
            'monster_heal': self.monster_heal,
            'monster_reckoning': self.monster_reckoning,
            'monster_reckoning_move': self.monster_reckoning_move,
            'move_investigator': self.move_investigator,
            'move_monster': self.move_monster,
            'mythos_reckoning': self.mythos_reckoning,
            'recover': self.recover_investigator,
            'request_card': self.request_card,
            'resting_enabled': self.resting_enabled,
            'select_location': self.select_location,
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
            'spend_clue': self.spend_clue,
            'solve_rumor': self.solve_rumor,
            'trigger_check': self.trigger_check,
            'trigger_encounter': self.trigger_encounter,
            'update_rumor': self.update_rumor
        }
        self.req_dict = {
            'damage_monsters': lambda *args: len(self.hub.location_manager.get_all('monsters', True)) > 0 and (args[0].get('location', None) == None or len(self.hub.location_manager.locations[args[0]['location'] if args[0]['location'] != 'self' else self.investigator.location]['monsters']) > 0),
            'request_card': lambda *args: not args[0].get('check', False) or next((item for item in self.investigator.possessions[args[0]['kind']] if item.name == args[0]['name']), None) == None,
            'spend_clue': lambda args: len(self.investigator.clues) >= self.spend_clue(is_check=True, **args),
            'discard': lambda *args: self.discard_check(args[0]['kind'], args[0].get('tag', 'any'), args[0].get('name', None)),
            'solve_rumor': lambda *args: len(self.hub.location_manager.rumors) > 0,
            'gain_asset': lambda *args: not args[0].get('reserve', False) or len([item for item in self.hub.info_panes['reserve'].reserve if args[0]['tag'] == 'any' or args[0]['tag'] in item['tags']]) > 0,
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
        self.mythos_reckonings = []
        self.monster_reckonings = []
        self.monster_reckoning_loaded = False
        self.monster_death_triggers = []
        self.no_loc_click = None
        self.last_value = None
        self.player_index = 0
        self.encounter_type = []
        self.hp_damage = 0
        self.san_damage = 0
        self.current_key = ''

    def clear_overlay(self):
        if self.choice_layout in self.layout.children:
            self.choice_layout.clear()
            self.layout.children.remove(self.choice_layout)

    def clear_buttons(self, buttons=[]):
        self.layout.clear()
        self.layout.add(self.text_button)
        self.layout.add(self.phase_button)
        self.layout.add(self.choice_layout)
        for button in buttons:
            self.layout.add(button)

    def get_rumor(self, name):
        return MYTHOS[name]['manager_object']

    def discard_check(self, kind, tag='any', name=None):
        if kind == 'all':
            items = self.investigator.possessions['assets'] + self.investigator.possessions['artifacts'] + self.investigator.possessions['unique_assets']
        else:
            items = self.investigator.possessions[kind]
        items = [item for item in items if tag in item.tags] if tag != 'any' else [item for item in items if name == item.name] if name != None else items
        return len(items) > 0

    def encounter_phase(self, combat_only=False, step='finish'):
        location = self.investigator.location
        monsters = self.hub.location_manager.locations[location]['monsters']
        self.monsters = [monster for monster in monsters] if self.first_fight else self.monsters
        self.encounters = self.hub.location_manager.get_encounters(location)
        self.phase_button.text = 'Combat Phase'
        choices = []
        if len(self.monsters) > 0:
            small_card = SmallCardPane(self.hub)
            def finish_action(name):
                used_trigger = next((utrig for utrig in self.hub.triggers['precombat'] if human_readable(utrig['name']) == name))
                if small_card.item_used:
                    button = next((button for button in self.choice_layout.children if getattr(button, 'name', '') == name))
                    button.disable()
                    used_trigger['used'] = True
                else:
                    small_card.encounters.append(used_trigger['action'])
            for monster in self.monsters:
                choices.append(ActionButton(texture='monsters/' + monster.name + '.png', action=self.combat_will, action_args={'monster': monster}, scale=0.5))
            options = []
            for trigger in [trig for trig in self.hub.triggers['precombat'] if (not trig['used'] or not trig.get('single_use', False))]:
                trigger['action']['title'] = human_readable(trigger['name'])
                options.append(ActionButton(width=100, height=50, texture='buttons/placeholder.png', text=human_readable(trigger['name']), action=small_card.setup, action_args={'encounters':[trigger['action']], 'parent': self, 'finish_action': finish_action}, name=human_readable(trigger['name'])))
            self.choice_layout = create_choices('Choose Monster', choices=choices, options=options)
            self.layout.add(self.choice_layout)
        elif not combat_only and len(self.monsters) == 0:
            self.choose_encounter()
        else:
            self.set_buttons(step)

    def choose_encounter(self):
        choices = []
        self.phase_button.text = 'Encounter Phase'
        for encounter in self.encounters:
            request = False
            args = {}
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
        self.choice_layout = create_choices('Choose Encounter', choices=choices)
        self.layout.add(self.choice_layout)
        self.layout.add(self.phase_button)

    def start_encounter(self, value, loc=None):
        print(value, loc)
        #self.clear_overlay()
        choice = value.split(':')
        if loc == None:
            location = self.investigator.location
            loc = 'gate' if choice[0] == 'gate' else location if (location.find('space') == -1 and choice[0] != 'generic') else self.hub.location_manager.locations[location]['kind']
        #self.encounter = ENCOUNTERS[choice[0]][loc][int(choice[1])]
        self.encounter = ENCOUNTERS['gate']['gate'][0]
        self.encounter_type.append(choice[0])
        if loc == 'gate':
            self.phase_button.text = self.encounter['world']
        elif choice[0] == 'investigators':
            self.recover_name = loc
        if self.encounter['test'] != 'None':
            self.set_buttons('test')
        else:
            self.set_buttons('pass')
        print('here')

    def combat_will(self, monster, player_request=None):
        self.layout.clear()
        self.encounter_type.append('combat')
        self.first_fight = False
        self.hub.info_manager.children = {0:[]}
        self.hub.info_panes['location'].show_monster(monster)
        self.hub.info_panes['location'].description_layout.children.remove(self.hub.info_panes['location'].monster_close)
        self.layout.add(self.hub.info_panes['location'].layout)
        self.hub.info_manager.add(self.layout)
        self.clear_overlay()
        if monster.horror['mod'] == '-':
            self.combat_strength(monster, player_request)
        else:
            def lose_san():
                self.clear_overlay()
                self.encounter_type.remove('combat_will')
                successes = len([roll for roll in self.rolls if roll >= self.investigator.success])
                dmg = successes - monster.horror['san']
                dmg = dmg if dmg < 0 else 0
                self.take_damage(0, dmg, self.combat_strength, {'monster': monster, 'player_request': player_request})
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

    def resolve_combat(self, monster, player_request=None):
        self.hub.info_panes['location'].description_layout.add(self.hub.info_panes['location'].monster_close)
        self.encounter_type.remove('combat')
        successes = len([roll for roll in self.rolls if roll >= self.investigator.success])
        is_ambush = self.ambush_steps != None
        self.monster_death_triggers = self.hub.damage_monster(monster, successes, is_ambush)
        def finish_combat():
            self.layout.remove(self.hub.info_panes['location'].layout)
            if player_request == None:
                self.hub.show_encounter_pane()
                self.monsters.remove(monster)
                self.encounter_phase()
            else:
                self.hub.show_encounter_pane()
                self.hub.networker.publish_payload({'message': 'action_done'}, player_request + '_player')
        if len(self.monster_death_triggers) > 0:
            def show_triggers():
                if len(self.monster_death_triggers) > 0:
                    self.choice_layout = create_choices(choices=self.monster_death_triggers, title=human_readable(monster.name) + ' killed')
                    self.layout.add(self.choice_layout)
                    show_triggers()
                else:
                    finish_combat()
            triggers = []
            for trigger in self.monster_death_triggers:
                button_action = trigger.action
                button_args = trigger.action_args
                def action():
                    if button_args != None:
                        button_action(**button_args)
                    else:
                        button_action()
                    self.clear_overlay()
                trigger.action = action
                trigger.action_args = None
            self.monster_death_triggers = triggers
            show_triggers()
        elif is_ambush:
            self.set_buttons(self.ambush_steps[0] if successes >= monster.toughness else self.ambush_steps[1])
            self.ambush_steps = None
            self.hub.show_encounter_pane()
        else:
            finish_combat()

    def resolve_monster_reckoning(self, step, none_step, is_wait=False):
        if is_wait:
            self.clear_overlay()
            self.choice_layout = create_choices('Waiting for other player to finish')
            self.layout.add(self.choice_layout)
            self.player_wait_step = 'monster_reckoning'
            self.player_wait_args = {'step': step, 'none_step': none_step}
            self.hub.waiting_pane = self
        else:
            self.monster_reckoning(step, none_step)

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
        self.mythos_reckonings = []
        self.monster_reckonings = []
        self.no_loc_click = None
        if not skip:
            self.hub.my_turn = False
            self.hub.networker.publish_payload({'message': 'turn_finished', 'value': None}, self.investigator.name)

    def adjust_triggers(self, kind, args, step='finish'):
        self.hub.triggers[kind].append(args)
        self.set_buttons(step)

    def allow_gate_close(self, allow=True, step='finish'):
        self.gate_close = allow
        self.set_buttons(step)

    def allow_move(self, distance, step='finish', same_loc=True, must_move=False):
        allowed_locs = self.hub.get_locations_within(distance, self.investigator.location, same_loc=same_loc)
        def move(unit, location):
            self.hub.move_unit(unit, location)
            self.set_buttons(step)
        self.proceed_button.action = move
        self.proceed_button.action_args = {'unit': self.investigator.name, 'location': ''}
        self.option_button.text = 'Stay still'
        self.option_button.action = self.set_buttons
        self.option_button.action_args = {'key': step}
        self.hub.click_pane = self
        def no_click():
            self.proceed_button.text = 'Select location'
            self.proceed_button.disable()
            self.clear_buttons([self.proceed_button] + ([] if must_move else [self.option_button]))
        def loc_select(loc):
            if loc in allowed_locs:
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

    def choose_investigator(self, action, no_self=False, on_location=False, step='finish'):
        choices = []
        subtitle = ''
        if action == 'delay':
            def button_action(name):
                self.hub.networker.publish_payload({'message': 'become_delayed'}, name + '_server')
                self.set_buttons(step)
            subtitle = 'to become Delayed'
        elif action == 'same_action':
            def button_action(name):
                self.clear_overlay()
                self.encounter[self.current_key[0] + 'args'][0]['investigator'] = name
                self.encounter[self.current_key[0] + 'args'][0]['skip'] = True
                self.set_buttons(self.current_key)
        for names in [inv.name for inv in list(self.hub.location_manager.all_investigators.values()) if (not no_self or inv != self.investigator.name) and (not on_location or inv.location == self.investigator.location)]:
            choices.append(ActionButton(texture='investigators/' + names + '_portrait.png', action=button_action, action_args={'name': names}, scale=0.4))
        self.clear_overlay()
        self.choice_layout = create_choices('Choose Investigator', subtitle, choices)
        self.layout.add(self.choice_layout)

    def close_gate(self, step='finish', skip_triggers=False):
        if self.gate_close:
            self.wait_step = step
            self.hub.waiting_pane = self
            if not skip_triggers and len(self.hub.triggers['gate_close']) > 0:
                key = next((key for key in self.encounter if 'close_gate' in self.encounter[key]))
                index = self.encounter[key].index('close_gate')
                self.encounter[key[0] + 'args'][index]['skip'] = True
                self.encounter[key[0] + 'args'][index]['skip_triggers'] = True
                self.hub.small_card_pane.encounter_type = self.encounter_type
                self.hub.small_card_pane.setup(self.hub.triggers['gate_close'], self, key, False)
            else:
                if self.rumor_not_gate != None:
                    self.hub.networker.publish_payload({'message': 'solve_rumor', 'value': self.rumor_not_gate}, self.investigator.name)
                else:
                    map_name = self.hub.location_manager.get_map_name(self.investigator.location)
                    self.hub.networker.publish_payload({'message': 'remove_gate', 'value': map_name + ':' + self.investigator.location}, self.investigator.name)
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

    def damage_monsters(self, damage, step='finish', single=True, epic=True, lose_hp=False, location=None):
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
                self.hub.damage_monster(monster, damage)
                if lose_hp:
                    self.clear_overlay()
                    self.hp_san(step, -monster.toughness)
                else:
                    self.set_buttons(step)
                self.click_action = None
            def damage_loc(loc):
                self.proceed_button.disable()
                choices = []
                options = []
                monsters = [monster for monster in self.hub.location_manager.locations[loc]['monsters'] if epic or not monster.epic]
                def no_click():
                    self.clear_overlay()
                    self.proceed_button.disable()
                    self.proceed_button.text = 'Select Location'
                    self.clear_buttons([self.proceed_button])
                if len(monsters) > 0:
                    self.proceed_button.action_args = {'loc': loc}
                    for monster in monsters:
                        choices.append(ActionButton(
                            width=100, height=100, texture='monsters/' + monster.name + '.png', action=select if single else lambda *args: None, action_args={'monster': monster}))
                        options.append(ActionButton(width=100, height=50, texture='buttons/placeholder.png', text=str(monster.toughness - monster.damage) + '/' + str(monster.toughness)))
                    self.clear_overlay()
                    self.choice_layout = create_choices(title='Select ' + ('' if single else 'all ') + 'Monster(s)', subtitle=('Damage: ' + str(damage)) if damage != 99 else 'Discard Monster', choices=choices, options=options)
                    self.layout.add(self.choice_layout)
                    self.clear_buttons([self.proceed_button, self.option_button])
                    if not single:
                        self.proceed_button.enable()
                        self.proceed_button.text = 'Confirm: ' + human_readable(loc)
                        self.no_loc_click = no_click
                else:
                    no_click()
            if location != None:
                damage_loc(location)
            else:
                self.hub.click_pane = self
                self.click_action = damage_loc
                self.proceed_button.disable()
                self.option_button.text = 'Close Monster Selection'
                self.option_button.action = self.clear_overlay

    def delay(self, step='finish', bypass=False):
        def get_delayed():
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

    def discard(self, kind, step='finish', tag='any', amt='one', name=None, get_owner=False):
        investigator = self.investigator
        if get_owner:
            investigator = next((inv for inv in self.hub.location_manager.all_investigators.values() if name in [pos.name for pos in inv.possessions[kind]]))
        if name != None:
            card = next((item for item in investigator.possessions[kind] if item.name == name), None)
            if card != None:
                self.hub.networker.publish_payload({'message': 'card_discarded', 'value': card.get_server_name(), 'kind': kind}, investigator.name)
                self.hub.info_panes['possessions'].setup()
            self.set_buttons(step)
        else:
            items = []
            if kind == 'all':
                for possession_type in ['assets', 'unique_assets', 'artifacts']:
                    items += investigator.possessions[possession_type]
            else:
                items = investigator.possessions[kind]
            items = [item for item in items if tag in item.tags] if tag != 'any' else items
            if len(items) == 0:
                self.set_buttons(step)
            else:
                options = []
                selected = []
                def discard_card(card):
                    self.hub.networker.publish_payload({'message': 'card_discarded', 'value': card.get_server_name(), 'kind': card.kind}, investigator.name)
                    self.hub.info_panes['possessions'].setup()
                if amt == 'one':
                    def next_step(card, step):
                        discard_card(card)
                        self.wait_step = step
                        self.hub.waiting_pane = self
                else:
                    def submit():
                        if len(selected) == 0:
                            self.set_buttons(step)
                        else:
                            for x in range(len(selected)):
                                if x == len(selected) - 1:
                                    self.last_value = selected[x].get_server_name()
                                    self.wait_step = step
                                    self.hub.waiting_pane = self
                                discard_card(selected[x])
                    button = ActionButton(width=150, height=30, text='Discard: 0', texture='buttons/placeholder.png', action=submit)
                    def select(card, step):
                        if card in selected:
                            selected.remove(card)
                        else:
                            selected.append(card)
                        button.text = 'Discard: ' + str(len(selected))
                    options = [button]
                title = 'Discard ' + (human_readable(tag) + ' ' if tag != 'any' else '') + (human_readable(name) if name != None else kind) + ': ' + human_readable(amt)
                choices = [ActionButton(texture=item.texture, width=120, height=185, action=next_step if amt == 'one' else select, action_args={'card': item, 'step': step}) for item in items]
                self.choice_layout = create_choices(choices = choices, options = options, title=title)
                self.layout.add(self.choice_layout)

    def end_mythos(self):
        self.hub.networker.publish_payload({'message': 'end_mythos'}, self.investigator.name)

    def gain_asset(self, tag='any', reserve=False, step='finish', name=''):
        if reserve:
            items = self.hub.info_panes['reserve'].reserve
            pickable = []
            for tags in tag.split(','):
                pickable += items if tag == 'any' else [item for item in items if tags in item['tags']]
            if len(pickable) > 0:
                def next_step(item, step):
                    self.wait_step = step
                    self.hub.waiting_pane = self
                    self.hub.request_card('assets', item, 'acquire')
                    self.clear_overlay()
                choices = [ActionButton(texture=item['texture'], width=120, height=185, action=next_step, action_args={'item': item['name'], 'step': step}) for item in pickable]
                self.choice_layout = create_choices(choices = choices, title='Choose Asset')
                self.layout.add(self.choice_layout)
        else:
            self.wait_step = step
            self.hub.waiting_pane = self
            self.hub.request_card('assets', name, tag=tag)

    def gain_clue(self, step='finish', amt=1, rolls=False):
        if rolls:
            amt = len([roll for roll in self.rolls if roll >= self.investigator.success])
        if amt == 0:
            self.set_buttons(step)
        else:
            for x in range(amt):
                if x == amt - 1:
                    self.wait_step = step
                    self.hub.waiting_pane = self
                self.hub.networker.publish_payload({'message': 'get_clue', 'value': amt}, self.investigator.name)

    def group_pay(self, kind, name, step='finish', player_request=None, is_check=False):
        total_payment = self.group_payments[name]['group_total']
        payment_needed = self.group_payments[name]['needed']
        qty = self.investigator.get_number(kind)
        max_pay = min(payment_needed, qty)
        remaining_total = total_payment - qty
        min_pay = max(payment_needed - remaining_total, 0)
        self.group_payments[name]['my_payment'] = min_pay
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
        payment_button = ActionButton(height=100, width=100, text=min_pay, texture='buttons/placeholder.png')
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
                self.hub.waiting_pane = self
                self.player_wait_args = {'kind': kind, 'name': name, 'step': step}
                self.hub.networker.publish_payload({'message': 'group_pay_reckoning', 'kind': kind, 'name': name, 'player_request': self.investigator.name}, self.hub.all_investigators[self.player_index] + '_player')
                self.clear_buttons([self.proceed_button])
                self.proceed_button.disable()
                self.proceed_button.text = 'Waiting for other players'

    def hp_san(self, step='finish', hp=0, san=0, stat='health', kind=None, tag=None, no_damage_step=None):
        self.layout.clear()
        self.layout.add(self.text_button)
        self.layout.add(self.phase_button)
        if kind != None:
            if kind in ['assets', 'conditions', 'unique_assets', 'spells', 'artifacts']:
                damage = len([item for item in self.investigator.possessions[kind] if tag == None or tag in item.tags])
            elif kind == 'all':
                all_items = self.investigator.possessions['assets'] + self.investigator.possessions['unique_assets'] + self.investigator.possessions['artifacts']
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
            if hp < 0 or san < 0:
                self.take_damage(hp, san, self.set_buttons, {'key': step})
            else:
                self.investigator.health = min(self.investigator.health + hp, self.investigator.max_health)
                self.investigator.sanity = min(self.investigator.sanity + san, self.investigator.max_sanity)
                self.hub.networker.publish_payload({'message': 'update_hpsan', 'hp': self.investigator.health, 'san': self.investigator.sanity})
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

    def move_monster(self, step='finish', encounter=True, move_to='self', optional=False):
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
        if not self.monster_reckoning_loaded:
            monsters = [monster for monster in self.hub.location_manager.all_monsters if hasattr(monster, 'reckoning')]
            if len(monsters) == 0:
                self.set_buttons(none_step)
            else:
                choices = []
                for monster in monsters:
                    def choice(monster):
                        args = getattr(monster, 'reckoning_args', {})
                        args['monster'] = monster
                        args['step'] = step
                        args['none_step'] = none_step
                        self.action_dict[monster.reckoning](**args)
                        self.monster_reckonings = [button for button in self.monster_reckonings if button.action_args['monster'] != monster]
                    button = ActionButton(texture='monsters/' + monster.name + '.png', action=choice, action_args={'monster': monster}, scale=0.5)
                    choices.append(button)
                self.monster_reckonings = choices
                self.monster_reckoning_loaded = True
                self.monster_reckoning(step, none_step)
        else:
            if self.player_wait_step == None:
                if len(self.monster_reckonings) == 0:
                    self.monster_reckoning_loaded = False
                    self.set_buttons(step)
                else:
                    self.clear_overlay()
                    options = [ActionButton(texture='buttons/placeholder.png', text=button.action_args['monster'].option_text, action=button.action, action_args=button.action_args) for button in self.monster_reckonings]
                    self.choice_layout = create_choices('Monster Reckoning Effects', choices=self.monster_reckonings, options=options)
                    self.layout.add(self.choice_layout)

    def monster_reckoning_move(self, monster, step, none_step, distance=1, encounter=True, damage=0):
        is_wait = damage > 0
        paths = {}
        closest = 100
        investigators = self.hub.location_manager.all_investigators
        for investigator in investigators:
            route = list(self.hub.location_manager.find_path(monster.location, investigators[investigator]['location']))
            if len(route) < closest:
                paths = {}
                closest = len(route)
            if len(route) == closest:
                paths[investigator] = route
        if closest - 1 <= distance and encounter:
            is_wait = True
        if is_wait:
            self.hub.waiting_pane = self
            self.player_wait_step = 'waiting'
        else:
            self.player_wait_step = None
        def move_to_investigator(monster, distance, investigator):
            route = paths[investigator]
            distance = distance if distance < len(route) else len(route) - 1
            self.hub.networker.publish_payload({'message': 'move_monster', 'value': monster.monster_id, 'location': route[distance]}, self.investigator.name)
            self.resolve_monster_reckoning(step, none_step, is_wait)
            if route[distance] == investigators[investigator]['location'] and encounter:
                self.hub.networker.publish_payload({'message': 'combat', 'value': monster.monster_id, 'sender': self.investigator.name}, investigator + '_player')
        if len(paths) > 1:
            choices = []
            for name in paths:
                choices.append(ActionButton(texture='investigators/' + name + '_portrait.png', scale=0.3, action=move_to_investigator, action_args={
                    'monster': monster, 'distance': distance, 'investigator': name
                }))
            self.clear_overlay()
            self.choice_layout = create_choices(choices=choices, title='Select Investigator to move to')
            self.layout.add(self.choice_layout)
        else:
            investigator = list(paths.keys())[0]
            move_to_investigator(monster, distance, investigator)

    def recover_investigator(self, step='finish'):
        self.hub.networker.publish_payload({'message': 'recover_body', 'body': self.recover_name}, self.investigator.name)
        self.wait_step = step
        self.hub.waiting_pane = self

    def request_card(self, kind, step='finish', name='', tag='', trigger=False, investigator=None):
        if investigator in ['select', 'on_location']:
            self.choose_investigator('same_action', on_location=investigator == 'on_location')
        else:
            if investigator == None:
                requestor = self.investigator
            else:
                requestor = next((inv for inv in self.hub.location_manager.all_investigators.values() if inv.name == investigator))
            card = next((card for card in requestor.possessions[kind] if card.name == name), None)
            if (trigger or name in ['cursed', 'blessed']) and card != None:
                self.small_card([card])
            else:
                self.wait_step = step
                self.hub.waiting_pane = self
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

    def set_buttons(self, key):
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
            self.hub.networker.publish_payload({'message': 'action_done'}, key + '_player')
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
            elif key == 'dead':
                self.layout.clear()
                self.layout.add(self.text_button)
                self.text_button.text = 'You have fallen to the forces of darkness'
                if self.hub.my_turn:
                    self.hub.networker.publish_payload({'message': 'turn_finished'}, self.investigator.name)
            else:
                buttons = [self.proceed_button, self.option_button, self.last_button]
                actions = self.encounter[key]
                self.text_button.text = self.encounter.get(key + '_text', self.text_button.text)
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
                for x in range(len(self.encounter[key])):
                    self.layout.add(buttons[x])
                if len(self.choice_layout.children) > 0:
                    self.layout.add(self.choice_layout)
            #self.hub.info_manager.trigger_render()

    def set_doom(self, increment=1, step='finish'):
        print(increment)
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

    def single_roll(self, effects):
        def trigger_effects():
            self.layout.children.remove(self.choice_layout)
            for key in effects.keys():
                if str(self.rolls[0]) in str(key):
                    self.set_buttons(effects[key])
        roll = random.randint(1, 6) + self.investigator.encounter_impairment
        roll = 1 if roll < 1 else roll
        options = [ActionButton(width=100, height=30, texture='buttons/placeholder.png', text='Next', action=trigger_effects)]
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

    def skill_test(self, stat, mod=0, step='pass', fail='fail', clue_mod=False):
        self.clear_overlay()
        self.clear_buttons()
        mod = mod if not clue_mod else mod + len(self.investigator.clues)
        def confirm_test():
            if next((roll for roll in self.rolls if roll >= self.investigator.success), None) != None:
                self.set_buttons(step)
            else:
                self.set_buttons(fail)
        next_button = ActionButton(width=100, height=30, texture='buttons/placeholder.png', text='Next', action=confirm_test)
        self.rolls, self.choice_layout = self.hub.run_test(stat, self, mod, [next_button])
        self.layout.add(self.choice_layout)

    def skip_combat(self):
        self.monsters = []
        self.first_fight = False
        self.clear_overlay()
        self.clear_buttons()
        self.choose_encounter()

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
            def finish_action(name):
                self.set_buttons(step)
            self.hub.small_card_pane.encounter_type = self.encounter_type + categories
            self.hub.small_card_pane.setup([getattr(card, attribute) for card in cards], self, single_card, self.text_button.text, [card.kind + '/' + card.name + '.png' for card in cards], finish_action)

    def spawn_clue(self, step='finish', click=False, number=1):
        if not click:
            self.wait_step = step
            self.hub.waiting_pane = self
            self.hub.networker.publish_payload({'message': 'spawn', 'value': 'clues', 'number': number}, self.investigator.name)
        else:
            def clue_click(loc):
                if not self.hub.location_manager.locations[loc]['clue']:
                    self.wait_step = step
                    self.hub.waiting_pane = self
                    map_name = self.hub.map.name
                    self.hub.networker.publish_payload({'message': 'spawn', 'value': 'clues', 'number': number, 'location':map_name + ':' + loc}, self.investigator.name)
                    self.click_action = None
                    self.set_buttons(step)
            self.hub.click_pane = self
            self.click_action = clue_click

    def spend_clue(self, step='finish', clues=1, condition=None, is_check=False, not_spend=False):
        if condition != None:
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
            self.hub.waiting_pane = self
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
                self.investigator.health = self.investigator.health + self.hp_damage if self.investigator.health + self.hp_damage <= self.investigator.max_health else self.investigator.max_health
                self.investigator.sanity = self.investigator.sanity + self.san_damage if self.investigator.sanity + self.san_damage <= self.investigator.max_sanity else self.investigator.max_sanity
                payload = {'message': 'update_hpsan', 'hp': self.investigator.health, 'san': self.investigator.sanity}
                def own_death():
                    self.investigator.is_dead = True
                    self.set_buttons('dead')
                def choose_defeat(kind):
                    payload['kind'] = kind.lower() == 'health'
                    self.hub.networker.publish_payload(payload, self.investigator.name)
                    self.clear_overlay()
                if self.investigator.health <= 0 and self.investigator.sanity <= 0:
                    own_death()
                    self.choice_layout = create_choices('Choose Defeat Type', choices=[ActionButton(width=100, height=50, texture='buttons/placeholder.png', action=choose_defeat, action_args={'kind': kind}, text=kind) for kind in ['Health', 'Sanity']])
                    self.layout.add(self.choice_layout)
                else:
                    self.hub.networker.publish_payload(payload, self.investigator.name)
                    if self.investigator.health <= 0 or self.investigator.sanity <= 0:
                        own_death()
                    else:
                        self.clear_overlay()
                        action(**args)
            options = []
            for trigger in self.hub.triggers['hp_san_loss']:
                hp_check = hp < 0 and trigger.get('on_hp_loss', False)
                san_check = san < 0 and trigger.get('on_san_loss', False)
                small_card = SmallCardPane(self.hub)
                if (hp_check or san_check) and self.hub.trigger_check(trigger, self.encounter_type):
                    trigger['action']['title'] = human_readable(trigger['name'])
                    def finish_action(name):
                        used_trigger = next((trig for trig in self.hub.triggers['hp_san_loss'] if human_readable(trig['name']) == name))
                        if small_card.item_used:
                            action_button = next((button for button in self.choice_layout.children if getattr(button, 'text', '') == name))
                            action_button.disable()
                            used_trigger['used'] = True
                        else:
                            small_card.encounters.append(used_trigger['action'])
                    button = ActionButton(width=100, height=50, texture='buttons/placeholder.png', text=human_readable(trigger['name']), action=small_card.setup, action_args={'encounters': [trigger['action']], 'parent': self, 'finish_action': finish_action})
                    if trigger.get('font_size', None) != None:
                        button.style = {'font_size': trigger['font_size']}
                    if trigger.get('used', False) and trigger.get('single_use', False):
                        button.disable()
                    options.append(button)
            next_button = ActionButton(
                width=100, height=50, texture='buttons/placeholder.png', text='Next', action=resolve_damage)
            self.choice_layout = create_choices(choices = choices, options=options + [next_button], title='Taking Damage', subtitle='Health: ' + str(self.hp_damage) + '   Sanity: ' + str(self.san_damage))
            self.layout.add(self.choice_layout)

    def trigger_check(self, kind, match, pass_check, fail):
        if match in getattr(self, kind, []):
            self.set_buttons(pass_check)
        else:
            self.set_buttons(fail)

    def trigger_encounter(self, kind, rumor=None):
        self.rumor_not_gate = rumor
        self.hub.networker.publish_payload({'message': 'get_encounter', 'value': kind}, self.investigator.name)

    def load_mythos(self, mythos):
        self.mythos = mythos
        self.encounter = MYTHOS[mythos]
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

    def activate_mythos(self):
        if (self.encounter.get('lead_only', None) != None and self.investigator.name != self.hub.lead_investigator) or self.investigator.is_dead:
            self.hub.networker.publish_payload({'message': 'turn_finished', 'value': None}, self.investigator.name)
        else:
            self.encounter_type.append('mythos')
            self.set_buttons('action')

    def reckoning(self):
        self.encounter_type.append('reckoning')
        def choose_mythos(mythos_obj):
            self.encounter = mythos_obj[0]
            self.set_buttons('action')
            self.mythos_reckonings.remove(mythos_obj)
        if len(self.mythos_reckonings) > 0:
            self.clear_buttons()
            self.phase_button.text = 'Mythos Phase - Reckoning'
            self.text_button.text = ''
            choices = []
            for reckon in self.mythos_reckonings:
                reckon[0]['action_text'] = human_readable(reckon[1]) + '\n\n' + self.hub.location_manager.rumors[reckon[1]]['reckoning']
                choices.append(ActionButton(texture='ancient_ones/mythos_back.png', text=human_readable(reckon[1]), action=choose_mythos, action_args={'mythos_obj': reckon}, scale=0.4))
            self.clear_overlay()
            self.choice_layout = create_choices('Select Mythos Reckoning', choices=choices)
            self.layout.add(self.choice_layout)
        elif len(self.reckonings) > 0:
            pass
        else:
            self.finish()
            self.load_mythos(self.mythos)
            self.hub.show_encounter_pane()

class SmallCardPane(EncounterPane):
    def __init__(self, hub):
        EncounterPane.__init__(self, hub)
        self.cards = []
        self.small_card_pic = ActionButton(x=1015, y=400, width=250, height=385, texture='buttons/placeholder.png')
        small_card_dict = {
            'flip_card': self.flip_card,
            'trade': self.trade,
            'adjust_damage': self.adjust_damage,
            'mod_die': self.mod_die,
            'temp_bonus': self.temp_bonus
        }
        small_card_req_dict = {
            'trade': lambda args: self.hub.location_manager.player_count > 1
        }
        self.action_dict = self.action_dict | small_card_dict
        self.req_dict = self.req_dict | small_card_req_dict
        self.item_used = True
        self.encounter_name = ''

    def setup(self, encounters, parent, single_pick=True, default_text=None, textures=[], finish_action=None):
        self.item_used = True
        self.finish_action = finish_action
        self.encounters = encounters
        self.parent = parent
        self.clear_overlay()
        self.hub.info_manager.children = {0:[]}
        self.hub.info_manager.add(self.layout)
        self.single_pick = single_pick
        self.default_text = default_text
        self.textures = textures if len(textures) > 0 else ['buttons/placeholder.png'] * len(self.encounters)
        if len(encounters) == 1:
            self.encounter_selected(encounters[0])
        else:
            self.pick_encounters()

    def flip_card(self, kind, name, investigator=None):
        if investigator == None:
            investigator = self.investigator.name
        self.encounter = getattr(next((card for card in self.hub.location_manager.all_investigators[investigator]['possessions'][kind] if card.name == name)), 'back')
        self.set_buttons('action')

    def adjust_damage(self, hp_change=0, san_change=0, step='finish'):
        hp_change = hp_change if type(hp_change) == int else -self.parent.hp_damage
        san_change = san_change if type(san_change) == int else -self.parent.san_damage
        self.parent.hp_damage += hp_change
        self.parent.san_damage += san_change
        self.parent.choice_layout.children[2].text = 'Health: ' + str(self.hp_damage) + '   Sanity: ' + str(self.san_damage)
        self.set_buttons(step)

    def mod_die(self, trigger_name, step='finish'):
        self.encounter_name = trigger_name
        self.set_buttons(step)

    def temp_bonus(self, stat, value, name, condition, step='finish'):
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

    def encounter_selected(self, encounter):
        self.encounter = encounter
        self.set_buttons('action')
        self.phase_button.text = self.encounter.get('title', '')
        self.encounter_name = self.encounter.get('title', '')
        self.encounters.remove(encounter)

    def pick_encounters(self):
        choices = []
        self.text_button.text = self.default_text
        for x in range(len(self.encounters)):
            choices.append(ActionButton(scale=0.5, texture=self.textures[x], action=self.encounter_selected, action_args={'encounter': self.encounters[x]}))
        self.choice_layout = create_choices('Choose Card Effect', choices=choices)
        self.layout.add(self.choice_layout)

    def set_buttons(self, key):
        if key == 'no_use':
            self.item_used = False
            self.finish()
        else:
            super().set_buttons(key)

    def finish(self):
        self.encounter_type = []
        if not self.single_pick and len(self.cards) > 0:
            self.pick_encounter()
        else:
            self.hub.info_manager.children = {0:[]}
            self.clear_overlay()
            self.hub.info_manager.add(self.parent.layout)
            self.hub.info_manager.trigger_render()
            if self.finish_action != None:
                self.finish_action(self.encounter_name)