import arcade, arcade.gui
import yaml
from screens.action_button import ActionButton
from util import *

ENCOUNTERS = {}
MYTHOS = {}

with open('encounters/generic.yaml') as stream:
    ENCOUNTERS['generic'] = yaml.safe_load(stream)
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
        self.phase_button = ActionButton(x=1000, width=280, y=725, height=50, texture='blank.png')
        self.text_button = ActionButton(x=1000, width=280, y=300, height=400, texture='blank.png')
        self.proceed_button = ActionButton(1000, 200, 280, 50, 'buttons/placeholder.png')
        self.option_button = ActionButton(1000, 100, 280, 50, 'buttons/placeholder.png')
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
            'allow_move': self.allow_move
        }
        self.encounter = None
        self.layout.add(self.text_button)
        self.layout.add(self.proceed_button)
        self.layout.add(self.phase_button)
        self.is_mythos = False
        self.move_action = None
        self.allowed_locs = {}

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
        elif len(self.hub.location_manager.locations[location]['monsters']) == 0 and not combat_only:
            self.phase_button.text = 'Encounter Phase'
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
        self.encounter = ENCOUNTERS[choice[0]][int(choice[1])][loc]
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
        pass

    def skill_test(self, stat, mod, step, fail):
        for button in [self.proceed_button, self.option_button]:
            if button in self.layout.children:
                self.layout.children.remove(button)
        self.hub.info_manager.trigger_render()
        next_button = ActionButton(width=100, height=30, texture='buttons/placeholder.png', text='Next', action=self.confirm_test, action_args={'step': step, 'fail': fail})
        self.rolls = self.hub.run_test(stat, mod, self.hub.encounter_pane, [next_button])

    def confirm_test(self, step, fail):
        self.hub.clear_overlay()
        if next((roll for roll in self.rolls if roll >= self.investigator.success), None) != None:
            self.set_buttons(step)
        else:
            self.set_buttons(fail)

    def reroll(self, new, old):
        self.rolls.remove(old)
        self.rolls.append(new)

    def combine_actions(self, action_string, args):
        actions = action_string.split(';')
        step = args[0]['step']
        del args[0]['step']
        for x in range(len(actions)):
            arg = args[x]
            self.action_dict[actions[x]](**arg)
        self.set_buttons(step)

    def finish(self):
        self.layout.clear()
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
        if key == 'finish':
            self.finish()
        else:
            self.layout.clear()
            self.layout.add(self.text_button)
            self.layout.add(self.phase_button)
            buttons = [self.proceed_button, self.option_button]
            actions = self.encounter[key]
            self.text_button.text = self.encounter[key + '_text']
            for x in range(len(actions)):
                args = self.encounter[key[0] + 'args'][x]
                buttons[x].text = args['text']
                del args['text']
                if actions[x] in ['allow_move']:
                    self.action_dict[actions[x]](**args)
                    buttons[x].action = lambda: None
                    buttons[x].action_args = None
                else:
                    buttons[x].action = self.action_dict[actions[x]]
                    buttons[x].action_args = args
                self.layout.add(buttons[x])
            self.hub.info_manager.trigger_render()

    def gain_asset(self, tag='any', random=False, reserve=False, step='finish', name=''):
        if reserve:
            items = self.hub.info_panes['reserve'].reserve
            items = items if tag == 'any' else [item for item in items if tag in item['tags']]
            if len(items) > 0:
                def next_step(self, item, step):
                    self.hub.request_card('assets', item, 'acquire')
                    self.set_buttons(step)
                    self.hub.clear_overlay()
                choices = [ActionButton(texture=item.texture, action=next_step, action_args={'self': self, 'item': item['name'], 'step': step}) for item in items]
                self.hub.choice_layout = create_choices(choices = choices, title='Choose Asset')
                self.hub.show_overlay()
        else:
            self.hub.request_card('assets', name, tag=tag)
            self.set_buttons(step)

    def request_card(self, kind, step, name=''):
        self.hub.request_card(kind, name)
        self.set_buttons(step)

    def monster_heal(self, amt):
        for location in self.hub.location_manager.locations:
            for monster in self.hub.location_manager.locations[location]['monsters']:
                monster.heal(amt)

    def delay(self, step):
        self.investigator.delayed = True
        self.set_buttons(step)

    def hp_san(self, hp, san, step):
        self.take_damage(hp, san, self.set_buttons, {'key': step})
        self.layout.children.remove(self.proceed_button)

    def spawn_clue(self, step, random=True):
        self.hub.networker.publish_payload({'message': 'spawn', 'value': 'clues', 'number': 1}, self.investigator.name)
        self.set_buttons(step)

    def gain_clue(self, step):
        self.hub.networker.publish_payload({'message': 'get_clue'}, self.investigator.name)
        self.set_buttons(step)

    def improve_skill(self, skill, step, amt=1):
        self.investigator.improve_skill(skill, amt)
        self.hub.info_panes['investigator'].calc_skill(skill)
        self.set_buttons(step)

    def allow_move(self, distance, step):
        self.allowed_locs = self.hub.get_locations_within(distance)
        def action():
            self.move_action = None
            self.allowed_locs = set()
            self.set_buttons(step)
        self.move_action = action

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
            self.hub.choice_layout = create_choices(choices = choices, options=[next_button], title='Health: ' + str(hp) + '   Sanity: ' + str(san))
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