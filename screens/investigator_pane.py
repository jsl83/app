import arcade, arcade.gui
from screens.action_button import ActionButton
from encounters.encounter_pane import InvestigatorSkillPane

IMAGE_PATH_ROOT = ":resources:eldritch/images/"

class InvestigatorPane():
    def __init__(self, investigator, hub):
        self.investigator = investigator
        self.blank = arcade.load_texture(IMAGE_PATH_ROOT + 'blank.png')
        self.hub = hub

        self.layout = arcade.gui.UILayout(x=1000, y=400, width=280, height=400).with_background(texture=arcade.load_texture(
            IMAGE_PATH_ROOT + 'gui/investigator_pane_top.png'))
        self.details = arcade.gui.UILayout(x=1000, width=280, height=400).with_background(texture=arcade.load_texture(
            IMAGE_PATH_ROOT + 'gui/investigator_pane_stats.png'))
        self.skill_pane = arcade.gui.UILayout(x=1000, width=280, height=400).with_background(texture=arcade.load_texture(
            IMAGE_PATH_ROOT + 'gui/investigator_pane_skills.png'))
        self.layout.add(arcade.gui.UITextureButton(x=995, width=150, y=725, text=investigator.label, texture=self.blank, font="Typical Writer", style={'font_size': 20, 'font_color': arcade.color.BLACK}))
        self.layout.add(arcade.gui.UITextureButton(x=995, width=150, y=665, text=investigator.subtitle, texture=self.blank, font="Typical Writer", style={'font_size': 14, 'font_color': arcade.color.BLACK}))
        self.layout.add(arcade.gui.UITextureButton(x=1147, y=640, texture=arcade.load_texture(
            IMAGE_PATH_ROOT +'investigators\\' + investigator.name + '_portrait.png'), scale=0.45))
        self.health_button = ActionButton(x=1031, y=536, texture='icons/health_' + str(investigator.max_health) + '.png', action=self.rest)
        self.layout.add(self.health_button)
        self.toggle_attributes = ActionButton(1000, y=361, width=140, height=30, texture='blank.png', action=self.toggle_details, action_args={'flag': False})
        self.toggle_skills = ActionButton(1140, y=361, width=140, height=30, texture='blank.png', action=self.toggle_details, action_args={'flag': True})
        self.toggle_attributes.select(True)
        self.details.add(self.toggle_attributes)
        self.details.add(self.toggle_skills)
        self.skills = []
        for x in range(5):
            self.skills.append(arcade.gui.UITextureButton(x=1060, y=250 - 55 * x, width=200, texture=self.blank, align='center', style={'font_color': arcade.color.BLACK}))
            self.details.add(self.skills[x])
        self.rail_button = ActionButton(x=1036, width=115, height=36, y=450, action=self.ticket_action, action_args={'kind': 'rail'}, texture='blank.png',
                                        text='x ' + str(self.investigator.ship_tickets), text_position=(33,-2), style={'font_color': arcade.color.BLACK})
        self.ship_button = ActionButton(x=1036, width=115, height=36, y=403, action=self.ticket_action, action_args={'kind': 'ship'}, texture='blank.png',
                                        text='x ' + str(self.investigator.rail_tickets), text_position=(33,-2), style={'font_color': arcade.color.BLACK})
        self.clue_button = ActionButton(x=1172, y=450, width=70, height=36, texture='blank.png', text='x ' + str(len(self.investigator.clues)), text_position=(15,-2), style={'font_color': arcade.color.BLACK})
        self.focus_button = ActionButton(x=1172, y=403, width=70, height=36, action=self.focus_action, texture='blank.png', text='x ' + str(self.investigator.focus), text_position=(15,-2), style={'font_color': arcade.color.BLACK})
        self.skill_button = ActionButton(x=1040, y=192, width=200, height=135, style={'font_size': getattr(self.investigator, 'active_font', 13), 'font_color': arcade.color.BLACK},
            text=self.investigator.active, texture=self.blank, align='center', multiline=True, action=self.skill_action, bold=True)
        self.passive = ActionButton(x=1040, y=25, width=200, height=135, style={'font_size': getattr(self.investigator, 'passive_font', 13), 'font_color': arcade.color.BLACK},
            text=self.investigator.passive, align='center', multiline=True, texture=self.blank, bold=True)
        for button in [self.toggle_attributes, self.toggle_skills, self.skill_button, self.passive]:
            self.skill_pane.add(button)
        for button in [self.ship_button, self.rail_button, self.focus_button, self.clue_button]:
            self.layout.add(button)
        self.set_skills()
        self.layout.add(self.details)
        self.action_pane = InvestigatorSkillPane(self.hub)
        self.skill_reqs = {
            'diana_stanley': lambda *args: len([monster for monster in self.hub.location_manager.locations[self.investigator.location]['monsters'] if monster.name == 'cultist']) > 0,
            'jacqueline_fine': lambda *args: next((inv for inv in list(self.hub.location_manager.all_investigators.values()) if len(inv.clues) > 0), False),
            'lily_chen': lambda *args: self.investigator.health > 1 and self.investigator.sanity > 1 and not (self.investigator.health == self.investigator.max_health and self.investigator.sanity == self.investigator.max_sanity),
            'mark_harrigan': lambda *args: len(self.hub.location_manager.locations[self.investigator.location]['monsters']) > 0,
            'norman_withers': lambda *args: len(self.hub.location_manager.norman_check()) > 0 and self.hub.encounter_pane.spend_clue(clues=2, is_check=True),
            'silas_marsh': lambda *args: len([key for key in self.hub.location_manager.locations[self.investigator.location]['routes'].keys() if self.hub.location_manager.locations[self.investigator.location]['routes'][key] == 'ship']) > 0,
            'trish_scarborough': lambda *args: len(self.investigator.clues) == 0
        }
        self.skill_check()

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
        if (not ((kind == 'ship' and self.investigator.ship_tickets >= 2) or (kind == 'rail' and self.investigator.rail_tickets >= 2))) and not self.hub.actions_taken['ticket'] and self.hub.remaining_actions > 0 and kind in self.hub.location_manager.locations[self.investigator.location]['routes'].values():
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
            text = str(skill) + '     ' + str(token) + '    ' + str(mod) + '(' + str(self.investigator.calc_max_bonus(3, ['combat'])) + ')' + '      ' + str(skill + token + mod)
        else:
            text = str(skill) + '     ' + str(token) + '      ' + str(mod) + '       ' + str(skill + token + mod)
        self.skills[index].text = text

    def set_skills(self, index=5):
        if index > 4:
            for x in range(5):
                self.calc_skill(x)
        else:
            self.calc_skill(index)

    def toggle_details(self, flag):
        if flag:
            self.layout.children.remove(self.details)
            self.layout.add(self.skill_pane)
        else:
            self.layout.children.remove(self.skill_pane)
            self.layout.add(self.details)

    def on_show(self):
        self.skill_check()

    def skill_check(self):
        self.skill_button.disable()
        if (self.investigator.name not in self.skill_reqs.keys() or self.skill_reqs[self.investigator.name]()) and self.hub.remaining_actions > 0 and not self.hub.actions_taken['personal']:
            self.skill_button.enable()

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
                self.hub.small_card_pane.setup(triggers, self, single_pick=False, finish_action=show, textures=[trigger.get('texture', 'buttons/rectangle.png') for trigger in self.hub.triggers['rest_actions']])
            elif does_something:
                self.hub.action_taken('rest')

    def skill_action(self):
        self.hub.gui_set(False)
        self.hub.info_pane = self.action_pane
        def finish(name):
            self.hub.gui_set()
            self.hub.action_taken('personal', self.investigator.action.get('action_point', 1))
            self.skill_button.disable()
        self.action_pane.setup([self.investigator.action], self, force_select=True, finish_action=finish)