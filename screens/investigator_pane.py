import arcade, arcade.gui
from screens.action_button import ActionButton

IMAGE_PATH_ROOT = ":resources:eldritch/images/"

class InvestigatorPane():
    def __init__(self, investigator):
        self.investigator = investigator
        self.blank = arcade.load_texture(IMAGE_PATH_ROOT + 'blank.png')

        self.layout = arcade.gui.UILayout(x=1000, width=280, height=800).with_background(texture=arcade.load_texture(
            IMAGE_PATH_ROOT + 'buttons/placeholder.png'))
        self.layout.add(arcade.gui.UITextureButton(x=1005, width=150, y=735, text=investigator.label, texture=self.blank, font="Typical Writer", style={'font_size': 20}))
        self.layout.add(arcade.gui.UITextureButton(x=1005, width=150, y=675, text=investigator.subtitle, texture=self.blank, font="Typical Writer", style={'font_size': 14}))
        self.layout.add(arcade.gui.UITextureButton(x=1155, y=625, texture=arcade.load_texture(
            IMAGE_PATH_ROOT +'investigators\\' + investigator.name + '_portrait.png'), scale=0.5))
        self.layout.add(arcade.gui.UITextureButton(x=1031, y=550, texture=arcade.load_texture(
            IMAGE_PATH_ROOT +'icons\\health_' + str(investigator.max_health-1) + '.png')))
        self.layout.add(arcade.gui.UITextureButton(x=1000, y=25, texture=arcade.load_texture(
            IMAGE_PATH_ROOT +'icons\\skill_frame.png')))
        self.ship_button = ActionButton(x=1040, width=115, y=490, action=self.ship_ticket_action, texture=arcade.load_texture(
            IMAGE_PATH_ROOT +'icons\\ship_ticket.png'), text='x ' + str(self.investigator.ship_tickets), text_position=(35,-2))
        self.rail_button = ActionButton(x=1040, width=115, y=435, action=self.rail_ticket_action, texture=arcade.load_texture(
            IMAGE_PATH_ROOT +'icons\\train_ticket.png'), text='x ' + str(self.investigator.rail_tickets), text_position=(35,-2))
        self.clue_button = ActionButton(x=1175, y=490, texture=arcade.load_texture(
            IMAGE_PATH_ROOT +'icons\\clue.png'), text='x ' + str(self.investigator.clues), text_position=(15,-2))
        self.focus_button = ActionButton(x=1175, y=435, action=self.focus_action, texture=arcade.load_texture(
            IMAGE_PATH_ROOT +'icons\\focus.png'), text='x ' + str(self.investigator.focus), text_position=(15,-2))
        
        for button in [self.ship_button, self.rail_button, self.focus_button, self.clue_button]:
            self.layout.add(button)

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