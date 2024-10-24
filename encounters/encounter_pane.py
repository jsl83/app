import arcade, arcade.gui
import yaml
from screens.action_button import ActionButton
from util import *

ENCOUNTERS = {}

with open('encounters/generic.yaml') as stream:
    ENCOUNTERS['generic'] = yaml.safe_load(stream)

class EncounterPane():
    def __init__(self, hub):
        self.layout = arcade.gui.UILayout(x=1000)
        self.hub = hub
        self.monsters = []
        self.encounters = []
        self.investigator = self.hub.investigator
        self.first_fight = True
        self.rolls = []
        self.text_button = ActionButton(x=1000, width=280, y=550, height=200, texture='blank.png')
        self.proceed_button = ActionButton(1000, 200, 280, 50, 'buttons/placeholder.png')
        self.option_button = ActionButton(1000, 100, 280, 50, 'buttons/placeholder.png')
        self.action_dict = {
            'skill': self.skill_test,
            'gain_asset': self.gain_asset,
            'request_card': self.request_card
        }
        self.encounter = None
        self.layout.add(self.text_button)
        self.layout.add(self.proceed_button)

    def encounter_phase(self, location):
        self.monsters = self.hub.location_manager.locations[location]['monsters']
        self.encounters = self.hub.location_manager.get_encounters(location)
        choices = []
        if len(self.monsters) > 0:
            for monster in self.monsters:
                choices.append(ActionButton(texture='monsters/' + monster.name + '.png', action=self.fight, action_args={'monster': monster}, scale=0.5))
            options = [] if 'mists_of_releh' not in self.investigator.possessions['spells'] and not self.first_fight else [ActionButton(text='Mists of Releh', action=self.mists)]
            self.hub.choice_layout = create_choices('Combat Encounter', choices=choices, options=options)
            self.hub.show_overlay()
        else:
            for encounter in self.encounters:
                payload = {'message': 'get_encounter', 'value': encounter if encounter != 'expedition' else self.investigator.location}
                choices.append(ActionButton(texture='encounters/' + encounter + '.png', action=self.hub.networker.publish_payload,
                                            action_args={'topic': self.investigator.name, 'payload': payload}, scale=0.3))
            self.hub.choice_layout = create_choices('Choose Encounter', choices=choices)
            self.hub.show_overlay()
                
    def start_encounter(self, value):
        self.hub.clear_overlay()
        choice = value.split(':')
        loc = self.investigator.location if self.investigator.location.find('space') == -1 and choice[0] != 'generic' else self.hub.location_manager.locations[self.investigator.location]['kind']
        self.encounter = ENCOUNTERS[choice[0]][int(choice[1])][loc]
        if self.encounter['test'] != 'None':
            self.set_buttons('test')
        else:
            self.set_buttons('pass')

    def fight(self, monster):
        self.first_fight = False
        self.hub.clear_overlay()

    def mists(self):
        pass

    def skill_test(self, stat, mod, pane):
        self.rolls = self.hub.run_test(stat, mod, pane)
        self.proceed_button.text = 'Next'
        self.proceed_button.action = self.confirm_test
        self.proceed_button.action_args = None

    def confirm_test(self):
        self.hub.clear_overlay()
        if next((roll for roll in self.rolls if roll >= self.investigator.success), None) != None:
            self.set_buttons('pass')
        else:
            self.set_buttons('fail')

    def reroll(self, new, old):
        self.rolls.remove(old)
        self.rolls.append(new)

    def combine_actions(self, action_string, args):
        actions = action_string.split(';')
        for x in range(len(actions)):
            arg = args[x]
            arg['pane'] = self
            self.action_dict[actions[x]](**arg)
    
    def set_buttons(self, key):
        self.layout.clear()
        self.layout.add(self.text_button)
        buttons = [self.proceed_button, self.option_button]
        actions = self.encounter[key]
        self.text_button.text = self.encounter[key + '_text']
        for x in range(len(actions)):
            if actions[x].find(';') == -1:
                args = self.encounter[key[0] + 'args'][x]
                args['pane'] = self
                buttons[x].action = self.action_dict[actions[x]]
                buttons[x].text = args['text']
                del args['text']
                buttons[x].action_args = args
            else:
                buttons[x].action = self.combine_actions
                args = self.encounter[key[0] + 'args']
                if x == 0:
                    buttons[x].text = args[0]['text']
                del args[0]['text']
                buttons[x].action_args = {'action_string': actions[x], 'args': args}
            self.layout.add(buttons[x])
        self.hub.info_manager.trigger_render()

    def gain_asset(self):
        pass

    def request_card(self):
        pass