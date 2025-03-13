import arcade, arcade.gui
from screens.action_button import ActionButton
from encounters.encounter_pane import InvestigatorSkillPane

IMAGE_PATH_ROOT = ":resources:eldritch/images/"

class InvestigatorPane():
    def __init__(self, investigator, hub):
        self.investigator = investigator
        self.blank = arcade.load_texture(IMAGE_PATH_ROOT + 'blank.png')
        self.hub = hub

        self.layout = arcade.gui.UILayout(x=1000, width=280, height=800).with_background(texture=arcade.load_texture(
            IMAGE_PATH_ROOT + 'buttons/placeholder.png'))
        self.details = arcade.gui.UILayout(x=1000, width=280, height=350)
        self.layout.add(arcade.gui.UITextureButton(x=1005, width=150, y=735, text=investigator.label, texture=self.blank, font="Typical Writer", style={'font_size': 20}))
        self.layout.add(arcade.gui.UITextureButton(x=1005, width=150, y=675, text=investigator.subtitle, texture=self.blank, font="Typical Writer", style={'font_size': 14}))
        self.layout.add(arcade.gui.UITextureButton(x=1155, y=625, texture=arcade.load_texture(
            IMAGE_PATH_ROOT +'investigators\\' + investigator.name + '_portrait.png'), scale=0.5))
        self.health_button = ActionButton(x=1031, y=530, texture='icons/health_' + str(investigator.max_health) + '.png', action=self.rest)
        self.layout.add(self.health_button)
        self.toggle_attributes = ActionButton(1000, y=340, width=140, height=30, texture='buttons/placeholder.png', text='Attributes',
                                              action=self.toggle_details, action_args={'flag': False}, texture_pressed='/buttons/pressed_placeholder.png')
        self.toggle_skills = ActionButton(1140, y=340, width=140, height=30, texture='buttons/placeholder.png', text='Skills',
                                          action=self.toggle_details, action_args={'flag': True}, texture_pressed='/buttons/pressed_placeholder.png')
        self.toggle_attributes.select(True)
        self.layout.add(self.toggle_attributes)
        self.layout.add(self.toggle_skills)
        self.skills = []
        for x in range(5):
            self.skills.append(arcade.gui.UITextureButton(x=1060, y=225 - 55 * x, width=200, texture=self.blank, align='center'))
            self.details.add(self.skills[x])
        self.ship_button = ActionButton(x=1040, width=115, y=452, action=self.ticket_action, action_args={'kind': 'ship'}, texture='icons/ship.png',
                                        text='x ' + str(self.investigator.ship_tickets), text_position=(35,-2))
        self.rail_button = ActionButton(x=1040, width=115, y=397, action=self.ticket_action, action_args={'kind': 'rail'}, texture='icons/rail.png',
                                        text='x ' + str(self.investigator.rail_tickets), text_position=(35,-2))
        self.clue_button = ActionButton(x=1175, y=452, texture='icons/clue.png', text='x ' + str(len(self.investigator.clues)), text_position=(15,-2))
        self.focus_button = ActionButton(x=1175, y=397, action=self.focus_action, texture='icons/focus.png', text='x ' + str(self.investigator.focus), text_position=(15,-2))
        self.skill_button = ActionButton(x=1040, y=180, width=200, height=135, style={'font_size': 14},
            text=self.investigator.active, texture='blank.png', align='center', multiline=True, action=self.skill_action)
        self.passive = arcade.gui.UITextureButton(x=1040, y=25, width=200, height=135, style={'font_size': 14},
            text=self.investigator.passive, texture=self.blank, align='center', multiline=True)

        for button in [self.ship_button, self.rail_button, self.focus_button, self.clue_button]:
            self.layout.add(button)
        self.set_skills()
        self.layout.add(self.details)
        self.action_pane = InvestigatorSkillPane(self.hub)

    def focus_action(self):
        if self.investigator.focus < 2 and not self.hub.actions_taken['focus'] and self.hub.remaining_actions > 0:
            self.investigator.focus += 1
            self.focus_button.clear()
            self.focus_button.text = 'x ' + str(self.investigator.focus)
            self.hub.action_taken('focus')
            self.hub.undo_action = {'action': self.undo_focus, 'args': {}}

    def undo_focus(self):
        self.hub.actions_taken['focus'] = False
        self.hub.remaining_actions += 1
        self.hub.undo_action = None
        self.investigator.focus -= 1
        self.focus_button.clear()
        self.focus_button.text = 'x ' + str(self.investigator.focus)

    def ticket_action(self, kind):
        if (not ((kind == 'ship' and self.investigator.ship_tickets >= 2) or (kind == 'rail' and self.investigator.rail_tickets >= 2))) and not self.hub.actions_taken['ticket'] and self.hub.remaining_actions > 0:
            tickets = self.investigator.get_ticket(kind)
            self.set_ticket_counts()
            self.hub.action_taken('ticket')
            self.hub.networker.publish_payload({'message': 'update_tickets', 'ship': self.investigator.ship_tickets, 'rail': self.investigator.rail_tickets}, self.investigator.name)
            self.hub.undo_action = {'action': self.undo_ticket, 'args': {'tickets': tickets}}

    def undo_ticket(self, tickets):
        self.hub.actions_taken['ticket'] = False
        self.hub.remaining_actions += 1
        self.hub.undo_action = None
        self.investigator.rail_tickets += tickets[0]
        self.investigator.ship_tickets += tickets[1]
        self.hub.networker.publish_payload({'message': 'update_tickets', 'ship': self.investigator.ship_tickets, 'rail': self.investigator.rail_tickets}, self.investigator.name)
        self.set_ticket_counts()

    def set_ticket_counts(self):
        for button in [self.rail_button, self.ship_button]:
            button.clear()
            button.enabled = True
        self.rail_button.text = 'x ' + str(self.investigator.rail_tickets)
        self.ship_button.text = 'x ' + str(self.investigator.ship_tickets)

    def calc_skill(self, index):
        skill = self.investigator.skills[index]
        token = self.investigator.skill_tokens[index]
        mod = self.investigator.max_bonus[index]
        if index == 3:
            text = str(skill) + '      ' + str(token) + '     ' + str(mod) + '(' + str(self.investigator.calc_max_bonus(3, ['combat'])) + ')' + '    ' + str(skill + token + mod)
        else:
            text = str(skill) + '      ' + str(token) + '      ' + str(mod) + '      ' + str(skill + token + mod)
        self.skills[index].text = text

    def set_skills(self, index=5):
        if index > 4:
            for x in range(5):
                self.calc_skill(x)
        else:
            self.calc_skill(index)

    def toggle_details(self, flag):
        self.details.clear()
        if flag:
            self.details.add(self.passive)
            self.details.add(self.skill_button)
            self.toggle_skills.select(True)
            self.toggle_attributes.select(False)
        else:
            self.toggle_skills.select(False)
            self.toggle_attributes.select(True)
            for x in self.skills:
                self.details.add(x)

    def on_show(self):
        pass

    def rest(self):
        if not self.hub.actions_taken['rest']:
            does_something = False
            if not ((self.investigator.health == self.investigator.max_health and self.investigator.sanity == self.investigator.max_sanity and len(self.investigator.rest_triggers) == 0) or len(self.investigator.recover_restrictions) != 0):
                if len(self.investigator.sanity_recover_restrictions) == 0:
                    self.investigator.sanity += (1 + len([trigger for trigger in self.hub.triggers['rest_san_bonus'] if self.hub.trigger_check(trigger, [])]))
                if len(self.investigator.health_recover_restrictions) == 0:
                    self.investigator.health += (1 + len([trigger for trigger in self.hub.triggers['rest_hp_bonus'] if self.hub.trigger_check(trigger, [])]))
                self.hub.networker.publish_payload({'message': 'update_hpsan', 'hp': self.investigator.health, 'san': self.investigator.sanity}, self.investigator.name)
                does_something = True
            triggers = []
            for trigger in self.hub.triggers['rest_actions']:
                pass_condition = True
                if trigger['name'] == 'witch_doctor' and len(self.investigator.health_recover_restrictions) > 0 and not next((cond for cond in self.investigator.possessions['conditions'] if cond.name == 'cursed'), False):
                    pass_condition = False
                if not self.hub.trigger_check(trigger, 'rest'):
                    pass_condition = False
                if pass_condition:
                    triggers.append(trigger)
            if len(triggers) > 0:
                self.hub.info_pane = None
                def show(name):
                    self.hub.gui_set(True)
                    self.hub.switch_info_pane('investigator')
                    self.hub.info_manager.trigger_render()
                    self.hub.action_taken('rest')
                self.hub.gui_set(False)
                self.hub.small_card_pane.encounter_type = ['rest']
                self.hub.small_card_pane.setup(triggers, self, single_pick=False, finish_action=show, textures=['buttons/placeholder.png']*len(self.hub.triggers['rest_actions']))
            elif does_something:
                self.hub.action_taken('rest')

    def skill_action(self):
        self.hub.gui_set(False)
        self.hub.info_pane = self.action_pane
        def finish(name):
            self.hub.gui_set()
            self.hub.action_taken('personal', self.investigator.action.get('action_point', 1))
        self.action_pane.setup([self.investigator.action], self, force_select=True, finish_action=finish)