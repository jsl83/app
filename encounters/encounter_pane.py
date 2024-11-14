import arcade, arcade.gui
import yaml
import random
from screens.action_button import ActionButton
from util import *

ENCOUNTERS = {}
MYTHOS = {}

for color in ['generic', 'green', 'orange', 'purple']:
    with open('encounters/' + color + '.yaml') as stream:
        ENCOUNTERS[color] = yaml.safe_load(stream)
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
        self.phase_button = ActionButton(x=1020, width=240, y=725, height=50, texture='blank.png')
        self.text_button = ActionButton(x=1020, width=240, y=300, height=400, texture='blank.png')
        self.proceed_button = ActionButton(1020, 200, 240, 50, 'buttons/placeholder.png')
        self.option_button = ActionButton(1020, 125, 240, 50, 'buttons/placeholder.png')
        self.last_button = ActionButton(1020, 50, 240, 50, 'buttons/placeholder.png')
        self.action_dict = {
            'skill': self.skill_test,
            'gain_asset': self.gain_asset,
            'request_card': self.request_card,
            'monster_heal': self.monster_heal,
            'combat': self.encounter_phase,
            'delayed': self.delay,
            'hp_san': self.hp_san,
            'spawn_clue': self.spawn_clue,
            'gain_clue': self.gain_clue,
            'improve_skill': self.improve_skill,
            'allow_move': self.allow_move,
            'discard': self.discard,
            'spend_clue': self.spend_clue,
            'set_buttons': self.set_buttons
        }
        self.req_dict = {
            'request_card': lambda *args: not args[0].get('check', False) or next((item for item in self.investigator.possessions[args[0]['kind']] if item.name == args[0]['name']), None) == None,
            'spend_clue': lambda *args: len(self.investigator.clues) > 0,
            'discard': lambda *args: self.discard_check(args[0]['kind'], args[0].get('tag', 'any'), args[0].get('name', None)),
            'gain_asset': lambda *args: not args[0].get('reserve', False) or len([item for item in self.hub.info_panes['reserve'].reserve if args[0]['tag'] == 'any' or args[0]['tag'] in item['tags']]) > 0
        }
        self.encounter = None
        self.layout.add(self.text_button)
        self.layout.add(self.proceed_button)
        self.layout.add(self.phase_button)
        self.is_mythos = False
        self.move_action = None
        self.click_action = None
        self.allowed_locs = {}
        self.wait_step = None

    def discard_check(self, kind, tag='any', name=None):
        items = self.investigator.possessions[kind]
        items = [item for item in items if tag in item.tags] if tag != 'any' else [item for item in items if name == item.name] if name != None else items
        return len(items) > 0

    def encounter_phase(self, combat_only=False):
        location = self.investigator.location
        self.monsters = [monster for monster in self.hub.location_manager.locations[location]['monsters']] if self.first_fight else self.monsters
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
        elif not combat_only:
            self.phase_button.text = 'Encounter Phase'
            self.text_button.text = 'Choose Encounter'
            for encounter in self.encounters:
                payload = {'message': 'get_encounter', 'value': encounter if encounter != 'expedition' else self.investigator.location}
                choices.append(ActionButton(texture='encounters/' + encounter + '.png', action=self.hub.networker.publish_payload,
                                            action_args={'topic': self.investigator.name, 'payload': payload}, scale=0.3))
            self.hub.choice_layout = create_choices('Choose Encounter', choices=choices)
            self.hub.show_overlay()
        else:
            if self.proceed_button not in self.layout.children:
                self.layout.add(self.proceed_button)
            self.proceed_button.text = 'End Combat'
            self.proceed_button.action = self.finish
            self.proceed_button.action_args = {}

    def start_encounter(self, value):
        self.hub.clear_overlay()
        choice = value.split(':')
        loc = self.investigator.location if self.investigator.location.find('space') == -1 and choice[0] != 'generic' else self.hub.location_manager.locations[self.investigator.location]['kind']
        self.encounter = ENCOUNTERS[choice[0]][loc][int(choice[1])]
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
        monster.damage += successes
        if monster.damage >= monster.toughness:
            self.hub.location_manager.locations[self.investigator.location]['monsters'].remove(monster)
        self.monsters.remove(monster)
        self.hub.show_encounter_pane()
        self.encounter_phase()

    def mists(self):
        self.monsters = []
        self.first_fight = False
        self.hub.clear_overlay()
        self.layout.clear()
        self.layout.add(self.text_button)
        self.layout.add(self.phase_button)
        self.encounter_phase()

    def skill_test(self, stat, mod=0, step='pass', fail='fail'):
        for button in [self.proceed_button, self.option_button, self.last_button]:
            if button in self.layout.children:
                self.layout.children.remove(button)
        self.hub.info_manager.trigger_render()
        def confirm_test():
            if next((roll for roll in self.rolls if roll >= self.investigator.success), None) != None:
                self.set_buttons(step)
            else:
                self.set_buttons(fail)
        next_button = ActionButton(width=100, height=30, texture='buttons/placeholder.png', text='Next', action=confirm_test)
        self.rolls = self.hub.run_test(stat, mod, self.hub.encounter_pane, [next_button])
        #self.rolls = [1]

    def reroll(self, new, old):
        self.rolls.remove(old)
        self.rolls.append(new)

    def finish(self):
        self.layout.clear()
        for button in [self.phase_button, self.text_button, self.proceed_button, self.option_button, self.last_button]:
            button.text = ''
            button.enable()
        self.layout.add(self.text_button)
        self.layout.add(self.phase_button)
        self.encounter = None
        self.monsters = []
        self.encounters = []
        self.first_fight = True
        self.is_mythos = False
        self.rolls = []
        self.hub.clear_overlay()
        self.hub.gui_set(True)
        self.hub.switch_info_pane('investigator')
        self.hub.select_ui_button(0)
        self.hub.networker.publish_payload({'message': 'turn_finished', 'value': None}, self.investigator.name)

    def set_buttons(self, key):
        self.wait_step = None
        if key == 'finish':
            self.finish()
        else:
            self.layout.clear()
            self.layout.add(self.text_button)
            self.layout.add(self.phase_button)
            self.hub.clear_overlay()
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
                    self.layout.add(buttons[x])
            self.hub.info_manager.trigger_render()

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

    def discard(self, kind, step='finish', tag='any', amt='one', name=None):
        items = self.investigator.possessions[kind]
        items = [item for item in items if tag in item.tags] if tag != 'any' else [item for item in items if name == item.name] if name != None else items
        if len(items) == 0:
            self.set_buttons(step)
        else:
            options = []
            if amt == 'one':
                def next_step(card, step):
                    card.discard()
                    self.hub.networker.publish_payload({'message': 'card_discarded', 'value': card.get_server_name(), 'kind': kind}, self.investigator.name)
                    self.hub.info_panes['possessions'].setup()
                    self.set_buttons(step)
            choices = [ActionButton(texture=item.texture, width=120, height=185, action=next_step, action_args={'card': item, 'step': step}) for item in items]
            self.hub.choice_layout = create_choices(choices = choices, options = options, title='Discard ' + (name[0].upper() + name[1:] if name != None else kind) + ': ' + amt[0].upper() + amt[1:])
            self.hub.show_overlay()

    def spend_clue(self, step='finish', amt=1):
        for x in range(amt):
            clue = random.choice(self.investigator.clues)
            self.investigator.clues.remove(clue)
            self.hub.networker.publish_payload({'message': 'card_discarded', 'kind': 'clues', 'value': clue}, self.investigator.name)
        self.set_buttons(step)
        self.hub.info_panes['investigator'].clue_button.text = 'x ' + str(len(self.investigator.clues))

    def request_card(self, kind, step='finish', name='', tag=''):
        self.wait_step = step
        message_sent = self.hub.request_card(kind, name, tag=tag)
        if not message_sent:
            self.wait_step = None
            self.set_buttons(step)

    def monster_heal(self, amt):
        for location in self.hub.location_manager.locations:
            for monster in self.hub.location_manager.locations[location]['monsters']:
                monster.heal(amt)

    def delay(self, step='finish'):
        self.investigator.delayed = True
        self.set_buttons(step)

    def hp_san(self, step='finish', hp=0, san=0):
        if hp < 0 or san < 0:
            self.take_damage(hp, san, self.set_buttons, {'key': step})
        else:
            self.investigator.health += hp
            self.investigator.sanity += san
            self.set_buttons(step)

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

    def gain_clue(self, step='finish'):
        self.wait_step = step
        self.hub.networker.publish_payload({'message': 'get_clue'}, self.investigator.name)

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

    def take_damage(self, hp, san, action, args):
        if hp == 0 and san == 0:
            action(**args)
        else:
            choices = []
            self.investigator.hp_damage += hp
            self.investigator.san_damage += san
            if hp < 0:
                #choices.append(hp damage triggers)
                pass
            if san < 0:
                #choices.append(san damage triggers)
                pass
            next_button = ActionButton(
                width=100, height=30, texture='buttons/placeholder.png', text='Next', action=self.investigator.hp_san, action_args={'action': action, 'args': args})
            self.hub.choice_layout = create_choices(choices = choices, options=[next_button], title='Taking Damage' ,subtitle='Health: ' + str(hp) + '   Sanity: ' + str(san))
            self.hub.show_overlay()

    def load_mythos(self, mythos):
        mythos = 'a_dark_power'
        self.is_mythos = True
        self.phase_button.text = 'Mythos Phase'
        actions = MYTHOS[mythos]['actions']
        args = MYTHOS[mythos]['args']
        self.layout.clear()
        self.layout.add(self.text_button)
        self.layout.add(self.phase_button)
        text = MYTHOS[mythos]['flavor'] + '\n\n' + MYTHOS[mythos]['text']
        self.text_button.text = text
        self.hub.info_manager.trigger_render()
        for x in range(len(args)):
            self.action_dict[actions[x]](**args[x])
        for y in range(len(args), len(actions) - len(args)):
            self.action_dict[actions[y]]