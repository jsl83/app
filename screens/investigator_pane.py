import arcade, arcade.gui
from screens.action_button import ActionButton

IMAGE_PATH_ROOT = ":resources:eldritch/images/"

class InvestigatorPane():
    def __init__(self, investigator):
        self.investigator = investigator
        self.blank = arcade.load_texture(IMAGE_PATH_ROOT + 'blank.png')

        self.layout = arcade.gui.UILayout(x=1000, width=280, height=800).with_background(texture=arcade.load_texture(
            IMAGE_PATH_ROOT + 'buttons/placeholder.png'))
        self.details = arcade.gui.UILayout(x=1000, width=280, height=350)
        self.layout.add(arcade.gui.UITextureButton(x=1005, width=150, y=735, text=investigator.label, texture=self.blank, font="Typical Writer", style={'font_size': 20}))
        self.layout.add(arcade.gui.UITextureButton(x=1005, width=150, y=675, text=investigator.subtitle, texture=self.blank, font="Typical Writer", style={'font_size': 14}))
        self.layout.add(arcade.gui.UITextureButton(x=1155, y=625, texture=arcade.load_texture(
            IMAGE_PATH_ROOT +'investigators\\' + investigator.name + '_portrait.png'), scale=0.5))
        self.layout.add(arcade.gui.UITextureButton(x=1031, y=530, texture=arcade.load_texture(
            IMAGE_PATH_ROOT +'icons\\health_' + str(investigator.max_health-1) + '.png')))
        self.toggle_attributes = ActionButton(1000, y=340, width=140, height=30, texture=arcade.load_texture(
                IMAGE_PATH_ROOT + 'buttons/placeholder.png'), text='Attributes', action=self.toggle_details, action_args={'flag': False},
                texture_pressed=arcade.load_texture(IMAGE_PATH_ROOT + '/buttons/pressed_placeholder.png'))
        self.toggle_skills = ActionButton(1140, y=340, width=140, height=30, texture=arcade.load_texture(
                IMAGE_PATH_ROOT + 'buttons/placeholder.png'), text='Skills', action=self.toggle_details, action_args={'flag': True},
                texture_pressed=arcade.load_texture(IMAGE_PATH_ROOT + '/buttons/pressed_placeholder.png'))
        self.toggle_attributes.select(True)
        self.layout.add(self.toggle_attributes)
        self.layout.add(self.toggle_skills)
        self.skills = []
        for x in range(5):
            self.skills.append(arcade.gui.UITextureButton(x=1060, y=225 - 55 * x, width=200, texture=self.blank, align='center'))
            self.details.add(self.skills[x])
        self.ship_button = ActionButton(x=1040, width=115, y=452, action=self.ship_ticket_action, texture=arcade.load_texture(
            IMAGE_PATH_ROOT +'icons\\ship_ticket.png'), text='x ' + str(self.investigator.ship_tickets), text_position=(35,-2))
        self.rail_button = ActionButton(x=1040, width=115, y=397, action=self.rail_ticket_action, texture=arcade.load_texture(
            IMAGE_PATH_ROOT +'icons\\train_ticket.png'), text='x ' + str(self.investigator.rail_tickets), text_position=(35,-2))
        self.clue_button = ActionButton(x=1175, y=452, texture=arcade.load_texture(
            IMAGE_PATH_ROOT +'icons\\clue.png'), text='x ' + str(self.investigator.clues), text_position=(15,-2))
        self.focus_button = ActionButton(x=1175, y=397, action=self.focus_action, texture=arcade.load_texture(
            IMAGE_PATH_ROOT +'icons\\focus.png'), text='x ' + str(self.investigator.focus), text_position=(15,-2))
        self.skill_button = ActionButton(x=1040, y=180, width=200, height=135, style={'font_size': 14},
            text=self.investigator.active, texture=self.blank, align='center', multiline=True)
        self.passive = arcade.gui.UITextureButton(x=1040, y=25, width=200, height=135, style={'font_size': 14},
            text=self.investigator.passive, texture=self.blank, align='center', multiline=True)

        for button in [self.ship_button, self.rail_button, self.focus_button, self.clue_button]:
            self.layout.add(button)
        self.set_skills()
        self.layout.add(self.details)

    def focus_action(self):
        self.investigator.get_token('focus')
        self.focus_button.clear()
        self.focus_button.text = 'x ' + str(self.investigator.focus)
        if self.investigator.focus == 2:
            self.focus_button.enabled = False

    def rail_ticket_action(self):
        self.investigator.get_token('rail')
        self.set_ticket_counts()
        if self.investigator.rail_tickets == 2:
            self.rail_button.enabled = False

    def ship_ticket_action(self):
        self.investigator.get_token('ship')
        self.set_ticket_counts()
        if self.investigator.ship_tickets == 2:
            self.ship_button.enabled = False

    def set_ticket_counts(self):
        for button in [self.rail_button, self.ship_button]:
            button.clear()
            button.enabled = True
        self.rail_button.text = 'x ' + str(self.investigator.rail_tickets)
        self.ship_button.text = 'x ' + str(self.investigator.ship_tickets)

    def calc_skill(self, index):
        skill = self.investigator.skills[index]
        token = self.investigator.skill_tokens[index]
        mod = self.investigator.skill_mods[index]
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