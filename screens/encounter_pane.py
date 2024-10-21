import arcade, arcade.gui
from screens.action_button import ActionButton
from util import *

IMAGE_PATH_ROOT = ":resources:eldritch/images/"

class EncounterPane():
    def __init__(self, hub):
        self.layout = arcade.gui.UILayout(x=1000)
        self.hub = hub
        self.monsters = []
        self.encounters = []
        self.investigator = self.hub.investigator

    def encounter_phase(self, location):
        self.monsters = self.hub.location_manager.locations[location]['monsters']
        self.encounters = self.hub.location_manager.get_encounters(location)
        choices = []
        if len(self.monsters) > 0:
            for monster in self.monsters:
                choices.append(ActionButton(texture='monsters/' + monster.name + '.png', action=self.fight, action_args={'monster': monster}, scale=0.5))
            options = [] if 'mists_of_releh' not in self.investigator.possessions['spells'] else [ActionButton(text='Mists of Releh', action=self.mists)]
            self.hub.choice_layout = create_choices('Combat Encounter', choices=choices, options=options)
            self.hub.show_overlay()
        else:
            for encounter in self.encounters:
                payload = {'message': 'get_encounter', 'value': encounter if encounter != 'expedition' else self.investigator.location}
                choices.append(ActionButton(texture='encounters/' + encounter + '.png', action=self.hub.networker.publish_payload,
                                            action_args={'topic': self.investigator.name, 'payload': payload}, scale=0.3))
            self.hub.choice_layout = create_choices('Choose Encounter', choices=choices)
            self.hub.show_overlay()
                
    def encounter(self, value):
        print(value)

    def fight(self, monster):
        pass

    def mists(self):
        pass