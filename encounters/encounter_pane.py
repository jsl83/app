import arcade, arcade.gui, yaml, random, math
from screens.action_button import ActionButton
from util import *

ENCOUNTERS = {}
MYTHOS = {}
RUMORS = {}

for kind in ['generic', 'green', 'orange', 'purple', 'expeditions', 'gate', 'rumor']:
    with open('encounters/' + kind + '.yaml') as stream:
        ENCOUNTERS[kind] = yaml.safe_load(stream)
with open('encounters/mythos.yaml') as stream:
    MYTHOS = yaml.safe_load(stream)

class EncounterPane():
    def __init__(self, hub):
        self.layout = arcade.gui.UILayout(x=1000)
        self.hub = hub
        self.monsters = []
        self.encounters = []
        self.investigator = self.hub.investigator
        self.first_fight = True
        self.rolls = []
        self.rumor_not_gate = None
        self.phase_button = ActionButton(x=1020, width=240, y=725, height=50, texture='blank.png')
        self.text_button = ActionButton(x=1020, width=240, y=275, height=425, texture='blank.png')
        self.proceed_button = ActionButton(1020, 200, 240, 50, 'buttons/pressed_placeholder.png')
        self.option_button = ActionButton(1020, 125, 240, 50, 'buttons/placeholder.png')
        self.last_button = ActionButton(1020, 50, 240, 50, 'buttons/placeholder.png')
        self.action_dict = {
            'allow_move': self.allow_move,
            'ambush': self.ambush,
            'close_gate': self.close_gate,
            'combat': self.encounter_phase,
            'condition_check': self.condition_check,
            'damage_monsters': self.damage_monsters,
            'delayed': self.delay,
            'discard': self.discard,
            'end_mythos': self.end_mythos,
            'gain_asset': self.gain_asset,
            'gain_clue': self.gain_clue,
            'hp_san': self.hp_san,
            'improve_skill': self.improve_skill,
            'loss_per_condition': self.loss_per_condition,
            'monster_heal': self.monster_heal,
            'move_monster': self.move_monster,
            'mythos_reckoning': self.mythos_reckoning,
            'request_card': self.request_card,
            'server_check': lambda: self.set_buttons('pass') if self.mythos_switch else self.set_buttons('fail'),
            'set_buttons': self.set_buttons,
            'set_doom': self.set_doom,
            'shuffle_mystery': self.shuffle_mystery,
            'single_roll': self.single_roll,
            'skill': self.skill_test,
            'spawn_clue': self.spawn_clue,
            'spend_clue': self.spend_clue,
            'spawn_rumor': self.spawn_rumor,
            'solve_rumor': self.solve_rumor,
            'start_group_pay': self.start_group_pay,
            'trigger_encounter': self.trigger_encounter
        }
        self.req_dict = {
            'request_card': lambda *args: not args[0].get('check', False) or next((item for item in self.investigator.possessions[args[0]['kind']] if item.name == args[0]['name']), None) == None,
            'spend_clue': lambda *args: len(self.investigator.clues) >= args[0].get('amt', math.ceil((len(self.hub.location_manager.all_investigators) / (2 if args[0].get('condition') == 'half' else 1)))),
            'discard': lambda *args: self.discard_check(args[0]['kind'], args[0].get('tag', 'any'), args[0].get('name', None)),
            'solve_rumor': lambda *args: len(self.hub.location_manager.rumors) > 0,
            'gain_asset': lambda *args: not args[0].get('reserve', False) or len([item for item in self.hub.info_panes['reserve'].reserve if args[0]['tag'] == 'any' or args[0]['tag'] in item['tags']]) > 0
        }
        self.encounter = None
        self.layout.add(self.text_button)
        self.layout.add(self.proceed_button)
        self.layout.add(self.phase_button)
        self.move_action = None
        self.click_action = None
        self.allowed_locs = {}
        self.wait_step = None
        self.ambush_steps = None
        self.payment = 0
        self.set_button_set = set()
        self.mythos_switch = False
        self.reckonings = []
        self.priority_reckonings = []
        self.mythos = None

    def get_rumor(self, name):
        return MYTHOS[name]

    def discard_check(self, kind, tag='any', name=None):
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
            for monster in self.monsters:
                choices.append(ActionButton(texture='monsters/' + monster.name + '.png', action=self.combat_will, action_args={'monster': monster}, scale=0.5))
            options = [] if ('mists_of_releh' not in self.investigator.possessions['spells'] and not self.first_fight) or combat_only else [ActionButton(
                text='Mists of Releh', action=self.mists, width=100, height=50)]
            self.hub.choice_layout = create_choices('Choose Monster', choices=choices, options=options)
            self.hub.show_overlay()
        elif not combat_only and len(monsters) == 0:
            self.choose_encounter()
        else:
            if self.proceed_button not in self.layout.children:
                self.layout.add(self.proceed_button)
            self.proceed_button.text = 'End Combat'
            self.proceed_button.action = self.set_buttons
            self.proceed_button.action_args = {'key': step}

    def choose_encounter(self):
        choices = []
        self.phase_button.text = 'Encounter Phase'
        self.text_button.text = 'Choose Encounter'
        for encounter in self.encounters:
            button = ActionButton(texture='encounters/' + encounter + '.png', scale=0.3)
            button.action = self.hub.networker.publish_payload if encounter != 'rumor' else self.start_encounter
            payload = {'message': 'get_encounter', 'value': encounter if encounter != 'expedition' else self.investigator.location}
            button.action_args = {'topic': self.investigator.name, 'payload': payload} if encounter != 'rumor' else {'value': 'rumor:0'}            
            choices.append(button)
        self.hub.choice_layout = create_choices('Choose Encounter', choices=choices)
        self.hub.show_overlay()

    def start_encounter(self, value):
        self.hub.clear_overlay()
        choice = value.split(':')
        loc = 'gate' if choice[0] == 'gate' else self.investigator.location if (self.investigator.location.find('space') == -1 and choice[0] != 'generic') or choice[0] == 'rumor' else self.hub.location_manager.locations[self.investigator.location]['kind']
        choice[0] = 'expeditions' if choice[0] in ['the_amazon', 'the_pyramids', 'the_heart_of_africa', 'antarctica', 'tunguska', 'the_himalayas'] else choice[0]
        self.encounter = ENCOUNTERS[choice[0]][loc][int(choice[1])]
        if loc == 'gate':
            self.phase_button.text = self.encounter['world']
        if self.encounter['test'] != 'None':
            self.set_buttons('test')
        else:
            self.set_buttons('pass')

    def combat_will(self, monster):
        self.first_fight = False
        self.hub.info_manager.children = {0:[]}
        self.hub.info_panes['location'].show_monster(monster)
        self.hub.info_manager.add(self.hub.info_panes['location'].layout)
        self.hub.clear_overlay()
        def lose_san():
            self.hub.clear_overlay()
            successes = len([roll for roll in self.rolls if roll >= self.investigator.success])
            dmg = successes - monster.horror['san']
            dmg = dmg if dmg < 0 else 0
            self.take_damage(0, dmg, self.combat_strength, {'monster': monster})
        next_button = ActionButton(width=100, height=30, texture='buttons/placeholder.png', text='Next', action=lose_san)
        self.rolls = self.hub.run_test(monster.horror['index'], monster.horror['mod'], self.hub.encounter_pane,
                                       [next_button], 'Health: ' + str(self.investigator.health) + '   Sanity: ' + str(self.investigator.sanity))
        
    def combat_strength(self, monster):
        self.hub.clear_overlay()
        def lose_hp():
            self.hub.clear_overlay()
            successes = len([roll for roll in self.rolls if roll >= self.investigator.success])
            dmg = successes - monster.strength['str']
            dmg = dmg if dmg < 0 else 0
            self.take_damage(dmg, 0, self.resolve_combat, {'monster': monster})
        next_button = ActionButton(width=100, height=30, texture='buttons/placeholder.png', text='Next', action=lose_hp)
        self.rolls = self.hub.run_test(monster.strength['index'], monster.strength['mod'], self.hub.encounter_pane,
                                       [next_button], 'Health: ' + str(self.investigator.health) + '   Sanity: ' + str(self.investigator.sanity))
        
    def resolve_combat(self, monster):
        self.hub.clear_overlay()
        successes = len([roll for roll in self.rolls if roll >= self.investigator.success])
        if self.ambush_steps != None:
            if successes >= monster.toughness:
                pass
                #monster death triggers
            self.set_buttons(self.ambush_steps[0] if successes >= monster.toughness else self.ambush_steps[1])
            self.ambush_steps = None
            self.hub.show_encounter_pane()
        else:
            self.hub.show_encounter_pane()
            self.monsters.remove(monster)
            self.encounter_phase()
            self.hub.damage_monster(monster, successes)

    def mists(self):
        self.monsters = []
        self.first_fight = False
        self.hub.clear_overlay()
        self.layout.clear()
        self.layout.add(self.text_button)
        self.layout.add(self.phase_button)
        self.choose_encounter()

    def reroll(self, new, old):
        self.rolls.remove(old)
        self.rolls.append(new)

    def finish(self, skip=False):
        self.layout.clear()
        for button in [self.phase_button, self.text_button, self.proceed_button, self.option_button, self.last_button]:
            button.unset()
        self.layout.add(self.text_button)
        self.layout.add(self.phase_button)
        self.monsters = []
        self.encounters = []
        self.first_fight = True
        self.rolls = []
        self.hub.clear_overlay()
        self.hub.gui_set(True)
        self.hub.switch_info_pane('investigator')
        self.hub.select_ui_button(0)
        self.rumor_not_gate = None
        self.mythos_switch = False
        if not skip:
            self.hub.networker.publish_payload({'message': 'turn_finished', 'value': None}, self.investigator.name)

    def allow_move(self, distance, step='finish', same_loc=True, must_move=False):
        self.allowed_locs = self.hub.get_locations_within(distance, same_loc=same_loc)
        def action():
            self.move_action = None
            self.allowed_locs = set()
            self.set_buttons(step)
        self.move_action = action
        if not must_move:
            self.proceed_button.text = 'Stay still'
            self.proceed_button.action = self.set_buttons
            self.proceed_button.action_args = {'key': step}

    def ambush(self, name=None, step='finish', fail='finish'):
        self.ambush_steps = (step, fail)
        self.combat_will(self.hub.location_manager.create_ambush_monster(name))

    def close_gate(self, step='finish'):
        self.wait_step = step
        if self.rumor_not_gate != None:
            self.hub.networker.publish_payload({'message': 'solve_rumor', 'value': self.rumor_not_gate}, self.investigator.name)
        else:
            map_name = self.hub.location_manager.get_map_name(self.investigator.location)
            self.hub.networker.publish_payload({'message': 'remove_gate', 'value': map_name + ':' + self.investigator.location}, self.investigator.name)
    
    def condition_check(self, space_type=None, item_type=None, tag=None, step='finish', fail='finish'):
        pass_check = True
        if space_type != None and self.hub.location_manager.locations[self.investigator.location]['kind'] != space_type:
            pass_check = False
        if item_type != None and len([item for item in self.investigator.possessions[item_type] if tag == None or tag in item.tags]) == 0:
            pass_check = False
        self.set_buttons(step if pass_check else fail)

    def damage_monsters(self, damage, step='finish', single=True, epic=True, lose_hp=False):
        if len(self.hub.location_manager.get_all('monsters', True)) == 0:
            self.proceed_button.text = 'The world is peaceful'
            self.proceed_button.action = self.set_buttons
            self.proceed_button.action_args = {'key': 'finish'}
        else:
            if self.encounter.get(step + '_text', None) != None:
                self.text_button.text = self.encounter.get(step + '_text')
            self.layout.clear()
            self.proceed_button.disable()
            self.proceed_button.text = 'Select Monster'
            for button in [self.text_button, self.phase_button, self.proceed_button]:
                self.layout.add(button)
            if not single:
                def damage_all(loc, dmg):
                    for monster in self.hub.location_manager.locations[loc]['monsters']:
                        self.hub.damage_monster(monster, damage)
                    self.set_buttons(step)
                    self.click_action = None
                self.proceed_button.action = damage_all
                self.proceed_button.text = 'Select Location'
            def select(monster, dmg):
                self.hub.damage_monster(monster, damage)
                if lose_hp:
                    self.hub.clear_overlay()
                    self.hp_san(step, -monster.toughness)
                else:
                    self.set_buttons(step)
                self.click_action = None
            def damage_loc(loc):
                self.proceed_button.disable()
                choices = []
                options = []
                monsters = [monster for monster in self.hub.location_manager.locations[loc]['monsters'] if epic or not monster.epic]
                if len(monsters) > 0:
                    self.proceed_button.action_args = {'loc': loc, 'dmg': damage}
                    if not single:
                        self.proceed_button.enable()
                    for monster in monsters:
                        choices.append(ActionButton(
                            width=100, height=100, texture='monsters/' + monster.name + '.png', action=select if single else lambda: None, action_args={'monster': monster, 'dmg': damage} if single else None))
                        options.append(ActionButton(width=100, height=50, texture='buttons/placeholder.png', text=str(monster.toughness - monster.damage) + '/' + str(monster.toughness)))
                    self.hub.clear_overlay()
                    self.hub.choice_layout = create_choices(title='Select Monster(s)', subtitle='Damage: ' + str(damage), choices=choices, options=options)
                    self.hub.show_overlay()
            self.click_action = damage_loc
            self.option_button.text = 'Close Monster Selection'
            self.option_button.action = self.hub.clear_overlay
            self.layout.add(self.option_button)

    def delay(self, step='finish'):
        self.investigator.delayed = True
        self.set_buttons(step)

    def discard(self, kind, step='finish', tag='any', amt='one', name=None):
        items = self.investigator.possessions[kind]
        items = [item for item in items if tag in item.tags] if tag != 'any' else [item for item in items if name == item.name] if name != None else items
        if len(items) == 0:
            self.set_buttons(step)
        else:
            options = []
            selected = []
            def discard_card(card):
                card.discard()
                self.hub.networker.publish_payload({'message': 'card_discarded', 'value': card.get_server_name(), 'kind': kind}, self.investigator.name)
                self.hub.info_panes['possessions'].setup()
            if amt == 'one':
                def next_step(card, step):
                    discard_card(card)
                    self.set_buttons(step)
            else:
                def submit():
                    for item in selected:
                        discard_card(item)
                    self.set_buttons(step)
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
            self.hub.choice_layout = create_choices(choices = choices, options = options, title=title)
            self.hub.show_overlay()

    def end_mythos(self):
        self.hub.networker.publish_payload({'message': 'end_mythos'}, self.investigator.name)

    def gain_asset(self, tag='any', reserve=False, step='finish', name=''):
        if reserve:
            items = self.hub.info_panes['reserve'].reserve
            items = items if tag == 'any' else [item for item in items if tag in item['tags']]
            if len(items) > 0:
                def next_step(item, step):
                    self.wait_step = step
                    self.hub.request_card('assets', item, 'acquire')
                    self.hub.clear_overlay()
                choices = [ActionButton(texture=item['texture'], width=120, height=185, action=next_step, action_args={'item': item['name'], 'step': step}) for item in items]
                self.hub.choice_layout = create_choices(choices = choices, title='Choose Asset')
                self.hub.show_overlay()
        else:
            self.wait_step = step
            self.hub.request_card('assets', name, tag=tag)

    def gain_clue(self, step='finish', amt=1, rolls=False):
        if rolls:
            amt = len([roll for roll in self.rolls if roll >= self.investigator.success])
        for x in range(amt):
            if x == amt - 1:
                self.wait_step = step
            self.hub.networker.publish_payload({'message': 'get_clue', 'value': amt}, self.investigator.name)

    def group_pay(self, minimum, max, kind, step='finish'):
        calc_max = min(max, self.investigator.get_number(kind))
        if calc_max == 0:
            self.set_buttons(step)
        else:
            self.payment = minimum
            title = ''
            match kind:
                case 'clues':
                    title = 'Clues'
                case 'hp':
                    title = 'Health'
                case 'san':
                    title = 'Sanity'
            payment_button = ActionButton(height=100, width=100, text=str(self.payment), texture='buttons/placeholder.png')
            minus_button = ActionButton(height=50, width=50, text='-', texture='buttons/placeholder.png', action_args={'amt': -1})
            submit_button = ActionButton(height=50, width=100, text='Submit Payment', texture='buttons/placeholder.png')
            plus_button =  ActionButton(height=50, width=50, text='+', texture='buttons/placeholder.png', action_args={'amt': 1})
            options = [minus_button, submit_button, plus_button]
            def increment(amt):
                for button in options:
                    button.enable()
                self.payment += amt
                payment_button.text = str(self.payment)
                if self.payment < minimum or self.payment > calc_max:
                    submit_button.disable()
                if self.payment <= minimum:
                    minus_button.disable()
                if self.payment >= calc_max:
                    plus_button.disable()
            def pay():
                self.hub.networker.publish_payload({'message': 'payment_made', 'value': self.payment}, self.investigator.name)
                if kind == 'clues':
                    self.spend_clue(step, self.payment)
                elif kind == 'hp':
                    self.hp_san(step, self.payment)
                else:
                    self.hp_san(step, 0, self.payment)
            minus_button.action = increment
            plus_button.action = increment
            submit_button.action = pay
            subtitle = 'Minimum: ' + str(minimum) + '  ' + 'Maximum: ' + str(calc_max)
            self.hub.choice_layout = create_choices(choices=[payment_button], options=options, title='Spend ' + title, subtitle=subtitle)
            if self.hub.lead_investigator != self.investigator.name and self.proceed_button in self.layout.children:
                self.layout.remove(self.proceed_button)
                self.proceed_button.unset()
            minus_button.disable()
            if self.payment == calc_max:
                plus_button.disable()
            self.hub.show_overlay()

    def hp_san(self, step='finish', hp=0, san=0, stat=None, kind=None, tag=None):
        self.layout.clear()
        self.layout.add(self.text_button)
        self.layout.add(self.phase_button)
        if kind != None:
            damage = len([item for item in self.investigator.possessions[kind] if tag == None or tag in item.tags])
            if stat == 'health':
                hp = -damage
            else:
                san = -damage
        if hp < 0 or san < 0:
            self.take_damage(hp, san, self.set_buttons, {'key': step})
        else:
            self.investigator.health += hp
            self.investigator.sanity += san
            self.hub.networker.publish_payload({'message': 'update_hpsan', 'hp': self.investigator.health, 'san': self.investigator.sanity})
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
                button = ActionButton(width=80, height=80, texture='icons/' + skills[int(char)] + '.png', action=improve, action_args={'stat': int(char)})
                if self.investigator.skill_tokens[int(char)] < 2:
                    choices.append(button)
            options = []
            if option != None:
                options = [ActionButton(height=50, texture='buttons/placeholder.png', text='Skip', action=self.set_buttons, action_args={'key': option})]
            self.hub.choice_layout = create_choices(choices=choices, title='Improve a Skill', options=options)
            self.hub.show_overlay()

    def loss_per_condition(self, lose, per, step='finish'):
        amt = self.discard_check('conditions', per)
        if lose == 'clues':
            self.spend_clue(step, amt)
        else:
            self.hp_san(step, -amt if lose == 'health' else 0, -amt if lose == 'sanity' else 0)

    def monster_heal(self, amt, step='finish'):
        for location in self.hub.location_manager.locations:
            for monster in self.hub.location_manager.locations[location]['monsters']:
                monster.heal(amt)
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
                    self.click_action = lambda locat: move(monster, encounter, locat)
                    self.hub.clear_overlay()
                
            def select(loc):
                choices = []
                options = []
                monsters = self.hub.location_manager.locations[loc]['monsters']
                if len(monsters) > 0:
                    for monster in monsters:
                        choices.append(ActionButton(
                            width=100, height=100, texture='monsters/' + monster.name + '.png', action=move_any, action_args={'monster': monster, 'encounter': encounter}))
                        options.append(ActionButton(width=100, height=50, texture='buttons/placeholder.png', text=str(monster.toughness - monster.damage) + '/' + str(monster.toughness)))
                    self.hub.clear_overlay()
                    self.hub.choice_layout = create_choices(title='Move Monster(s)', choices=choices, options=options)
                    self.hub.show_overlay()
            self.click_action = select
            if optional:
                self.layout.add(self.option_button)
                self.option_button.text = 'Pass'
                self.option_button.action = self.set_buttons
                self.option_button.action_args = {'key': step}

    def mythos_reckoning(self, number=1, step='finish'):
        self.hub.networker.publish_payload({'message': 'mythos_reckoning', 'value': number}, self.investigator.name)
        self.set_buttons(step)

    def request_card(self, kind, step='finish', name='', tag=''):
        self.wait_step = step
        message_sent = self.hub.request_card(kind, name, tag=tag)
        if not message_sent:
            self.wait_step = None
            self.set_buttons(step)

    def set_buttons(self, key):
        self.wait_step = None
        if key == 'finish':
            self.finish()
        elif key == 'reckoning':
            self.reckoning()
        else:
            self.hub.clear_overlay()
            self.set_button_set = set()
            if key == 'no_effect':
                self.proceed_button.enable()
                self.proceed_button.text = 'Onward...'
                self.text_button.text = 'The long night continues...'
                self.layout.add(self.proceed_button)
                self.proceed_button.action = self.set_buttons
                self.proceed_button.action_args = {'key': 'finish'}
            else:
                buttons = [self.proceed_button, self.option_button, self.last_button]
                actions = self.encounter[key]
                self.text_button.text = self.encounter.get(key + '_text', self.text_button.text)
                for x in range(len(actions)):
                    args = self.encounter[key[0] + 'args'][x]
                    buttons[x].text = args.get('text', '')
                    buttons[x].enable()
                    if actions[x] in self.req_dict and not self.req_dict[actions[x]](args) and len(actions) > 0:
                        buttons[x].disable()
                    for arg in ['text', 'check']:
                        if arg in args:
                            del args[arg]
                    if actions[x] == 'skill' or args.get('skip', None) != None:
                        if 'skip' in args:
                            del args['skip']
                        buttons[x].action = lambda: None
                        buttons[x].action_args = None
                        self.action_dict[actions[x]](**args)
                    else:
                        buttons[x].action = self.action_dict[actions[x]]
                        buttons[x].action_args = args
                    self.set_button_set.add(buttons[x])
                self.layout.clear()
                self.layout.add(self.text_button)
                self.layout.add(self.phase_button)
                for button in self.set_button_set:
                    self.layout.add(button)
            self.hub.info_manager.trigger_render()

    def set_doom(self, increment=1, step='finish'):
        self.hub.networker.publish_payload({'message': 'doom_change', 'value': increment}, self.investigator.name)
        self.set_buttons(step)

    def shuffle_mystery(self, step='finish'):
        self.hub.networker.publish_payload({'message': 'shuffle_mystery'}, self.investigator.name)
        self.set_buttons(step)

    def single_roll(self, effects):
        def trigger_effects():
            for key in effects.keys():
                if str(self.rolls[0]) in str(key):
                    self.set_buttons(effects[key])
        self.rolls = self.hub.single_roll(self, [ActionButton(width=100, height=30, texture='buttons/placeholder.png', text='Next', action=trigger_effects)])

    def skill_test(self, stat, mod=0, step='pass', fail='fail', clue_mod=False):
        for button in [self.proceed_button, self.option_button, self.last_button]:
            if button in self.layout.children:
                self.layout.children.remove(button)
        self.hub.info_manager.trigger_render()
        mod = mod if not clue_mod else mod + len(self.investigator.clues)
        def confirm_test():
            if next((roll for roll in self.rolls if roll >= self.investigator.success), None) != None:
                self.set_buttons(step)
            else:
                self.set_buttons(fail)
        next_button = ActionButton(width=100, height=30, texture='buttons/placeholder.png', text='Next', action=confirm_test)
        self.rolls = self.hub.run_test(stat, mod, self.hub.encounter_pane, [next_button])

    def spawn_clue(self, step='finish', click=False, number=1):
        if not click:
            self.wait_step = step
            self.hub.networker.publish_payload({'message': 'spawn', 'value': 'clues', 'number': number}, self.investigator.name)
        else:
            def clue_click(loc):
                if not self.hub.location_manager.locations[loc]['clue']:
                    self.wait_step = step
                    map_name = self.hub.map.name
                    self.hub.networker.publish_payload({'message': 'spawn', 'value': 'clues', 'number': number, 'location':map_name + ':' + loc}, self.investigator.name)
                    self.click_action = None
                    self.set_buttons(step)
            self.click_action = clue_click

    def spend_clue(self, step='finish', clues=1, condition=None):
        if condition == 'half':
            clues = math.ceil((len(self.hub.location_manager.all_investigators) / 2))
        for x in range(min(clues, len(self.investigator.clues))):
            clue = random.choice(self.investigator.clues)
            self.investigator.clues.remove(clue)
            self.hub.networker.publish_payload({'message': 'card_discarded', 'kind': 'clues', 'value': clue}, self.investigator.name)
        self.set_buttons(step)
        self.hub.info_panes['investigator'].clue_button.text = 'x ' + str(len(self.investigator.clues))

    def spawn_rumor(self, name, manager_obj, step='finish'):
        self.hub.map.spawn('rumor', self.hub.location_manager, manager_obj['location'], name)
        self.hub.location_manager.rumors[name] = manager_obj
        self.set_buttons(step)

    def solve_rumor(self, choice=False, step='finish'):
        def choose_rumor(key):
            self.wait_step = step
            self.hub.networker.publish_payload({'message': 'solve_rumor', 'value': key}, self.investigator.name)
        if choice:
            choices = []
            for rumor in self.hub.location_manager.rumors.keys():
                choices.append(ActionButton(
                    width=100, height=300, texture='buttons/placeholder.png', text=human_readable(rumor), action=choose_rumor, action_args={'key': rumor}))
            self.hub.choice_layout = create_choices(choices=choices, title='Select Rumor')
            self.hub.show_overlay()
        else:
            rumor = next((rumor for rumor in self.hub.location_manager.rumors.keys() if self.hub.location_manager.rumors[rumor]['location'] == self.investigator.location), None)
            choose_rumor(rumor)

    def start_group_pay(self, kind):
        self.hub.networker.publish_payload({'message': 'payment_info', 'kind': kind}, self.investigator.name)

    def take_damage(self, hp, san, action, args):
        if hp == 0 and san == 0:
            action(**args)
        else:
            choices = []
            if hp < 0:
                #choices.append(hp damage triggers)
                pass
            if san < 0:
                #choices.append(san damage triggers)
                pass
            def resolve_damage(hp, san):
                self.investigator.health += hp
                self.investigator.sanity += san
                self.hub.networker.publish_payload({'message': 'update_hpsan', 'hp': self.investigator.health, 'san': self.investigator.sanity})
                action(**args)
            next_button = ActionButton(
                width=100, height=30, texture='buttons/placeholder.png', text='Next', action=resolve_damage, action_args={'hp': hp, 'san': san})
            self.hub.choice_layout = create_choices(choices = choices, options=[next_button], title='Taking Damage', subtitle='Health: ' + str(hp) + '   Sanity: ' + str(san))
            self.hub.show_overlay()

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
        self.option_button.text = 'Waiting for turn'
        self.option_button.action = lambda: None
        self.option_button.action_args = None
        self.layout.add(self.option_button)

    def activate_mythos(self):
        if self.encounter.get('lead_only', None) != None and self.investigator.name != self.hub.lead_investigator:
            self.set_buttons('finish')
        else:
            self.set_buttons('action')

    def reckoning(self):
        if len(self.priority_reckonings) > 0:
            action = self.priority_reckonings.pop(0)
            self.text_button.text = 'Reckoning\n\n' + action[2]
            action[0](**action[1])
        elif len(self.reckonings) > 0:
            pass
        else:
            self.finish()
            text = human_readable(self.mythos) + '\n\n' + self.encounter['flavor'] + '\n\n' + self.encounter.get('text', '')
            if self.encounter.get('font_size', None) != None:
                self.text_button.style = {'font_size': int(self.encounter['font_size'])}
            self.text_button.text = text