import arcade, arcade.gui
from screens.action_button import ActionButton
from util import *

IMAGE_PATH_ROOT = ":resources:eldritch/images/"

class PossessionsPane():
    def __init__(self, investigator):
        self.investigator = investigator
        self.layout = arcade.gui.UILayout(x=1000)
        self.overlay_layout = arcade.gui.UILayout(x=1000, y=0, width=280, height=800)
        self.button_layout = arcade.gui.UILayout(x=1000, y=0, width=280, height=800)
        self.position = 0
        self.boundary = 0
        self.y_pos = 800

    def setup(self, item_dict=None):
        self.button_layout.children = []
        self.layout.children = []
        self.overlay_layout.children = []
        possessions = item_dict if item_dict != None else self.investigator.possessions
        y_pos = self.y_pos
        self.layout.add(arcade.gui.UITexturePane(self.button_layout, arcade.load_texture(IMAGE_PATH_ROOT + 'gui/info_pane.png')))
        self.layout.add(self.overlay_layout)
        for card_type in ['assets', 'unique_assets', 'artifacts', 'spells', 'conditions']:
            item_list = possessions[card_type]
            if len(item_list) > 0:
                y_pos -= 45
                self.overlay_layout.add(ActionButton(x=1000, y=y_pos, width=280, height=25, text=human_readable(card_type)))
                def create_button(x, y, name, kind):
                    if item_dict != None:
                        texture = kind + '/'
                        texture += name if kind not in ['unique_assets', 'spells', 'conditions'] else name[:-1]
                        texture += '.png'
                        args = {'name': name, 'kind': kind}
                    else:
                        texture = name.texture
                        args = None
                    self.button_layout.add(ActionButton(x, y, width=120, height=185, texture=texture, action_args=args))
                if len(item_list) > 1:
                    number = 0
                    for item in item_list:
                        if number == 0:
                            y_pos -= 190
                        create_button(1015 + number * 130, y_pos, item, card_type)
                        number += 1
                        if number == 2:
                            number = 0
                else:
                    y_pos -= 190
                    create_button(1080, y_pos, item_list[0], card_type)
        self.boundary = -y_pos + 20 if y_pos < 0 else 0

    def reset(self):
        for item in self.button_layout.children:
            item.reset_position()
        self.position = 0

    def move(self, y):
        if self.position + y < 0:
            y = self.position
        elif self.position + y > self.boundary:
            y = self.boundary - self.position
        self.position += y
        if y != 0:
            for item in self.button_layout.children + self.overlay_layout:
                item.move(0, y)

    def on_show(self):
        self.reset()

class TradePane(PossessionsPane):
    def __init__(self, investigator, hub):
        PossessionsPane.__init__(self, investigator)
        self.hub = hub
        self.y_pos = 600
        self.close_button = ActionButton(width=20, height=20, x=1250, y=770, texture='buttons/placeholder.png', text='X')
        self.portrait = ActionButton(width=80, height=112, x=1020, y=660, texture='buttons/placeholder.png')
        self.trade_button = ActionButton(width=100, height=25, x=1125, y=692, texture='buttons/placeholder.png', text='Trade', action=self.start_trade)
        self.text_button = ActionButton(width=150, height=45, x=1100, y=727, texture='buttons/placeholder.png')
        self.give = {'rail': [], 'ship': [], 'clues': [], 'assets': [], 'unique_assets': [], 'artifacts': [], 'spells': [], 'conditions': []}
        self.take = {'rail': [], 'ship': [], 'clues': [], 'assets': [], 'unique_assets': [], 'artifacts': [], 'spells': [], 'conditions': []}
        self.is_taking = True
        self.trade_with = ''
    
    def setup(self, item_dict, name, trade=False):
        self.trade_with = name if name != self.investigator.name else self.trade_with
        self.y_pos = 675
        self.trade_button.disable()
        if trade:
            self.trade_button.enable()
        tickets = []
        ticket_number = item_dict.get('rail', 0) + item_dict.get('ship', 0)
        if ticket_number > 0:
            self.y_pos -= 50
        clues = item_dict.get('clues', [])
        if len(clues) > 0:
            self.y_pos -= 50
        super().setup(item_dict)
        if ticket_number > 0:
            x_pos = 1070 + (140 - (26 * (ticket_number - 1)) - ticket_number * 57) / 2
            y_pos = 612
            self.y_pos -= 50
            for kind in ['rail', 'ship']:
                for x in range(item_dict.get(kind, 0)):
                    tickets.append(kind)
            for x in range(ticket_number):
                self.button_layout.add(ActionButton(scale=0.75, texture='icons/' + tickets[x] + '.png', x=x_pos, y=y_pos, action_args={'kind': kind, 'name': str(x)}))
                x_pos += 26
        if len(clues) > 0:
            x_pos = 1070 + (140 - (10 * (len(clues) - 1)) - len(clues) * 36) / 2
            y_pos = 607 if ticket_number == 0 else 557
            for clue in clues:
                self.button_layout.add(ActionButton(texture='icons/clue.png', x=x_pos, y=y_pos, action_args={'kind': 'clues', 'name': clue}))
        for buttons in self.button_layout.children:
            buttons.action = self.select
            buttons.action_args['button'] = buttons
            buttons.disable()
        for buttons in [self.close_button, self.portrait, self.trade_button, self.text_button]:
            self.layout.add(buttons)
        self.text_button.text = human_readable(name) + "'s Possessions"
        self.text_button.style = {'font_size': 14}
        self.portrait.texture = arcade.load_texture(IMAGE_PATH_ROOT + 'investigators/' + name + '_portrait.png')

    def start_trade(self):
        self.hub.gui_set(False)
        if not self.is_taking:
            self.trade_button.action = self.finish_trade
            item_dict = {}
            for key in ['assets', 'unique_assets', 'artifacts', 'spells', 'conditions']:
                item_dict[key] = [item.get_server_name() for item in self.investigator.possessions[key]]
            item_dict['rail'] = self.investigator.rail_tickets
            item_dict['ship'] = self.investigator.ship_tickets
            self.setup(item_dict, self.investigator.name, True)
        else:
            self.layout.remove(self.close_button)
        self.trade_button.text = 'Next' if self.is_taking else 'Finish'
        self.text_button.text = 'Select items to ' + ('take' if self.is_taking else 'give')
        self.is_taking = not self.is_taking
        for buttons in self.button_layout.children:
            buttons.enable()

    def finish_trade(self):
        self.trade_button.action = self.start_trade
        self.trade_button.text = 'Trade'
        self.is_taking = True
        self.hub.gui_set(True)
        self.close_button.action()
        payload = {'message': 'trade'}
        payload[self.investigator.name] = self.give
        payload[self.trade_with] = self.take
        self.hub.networker.publish_payload(payload, self.investigator.name)
        self.hub.networker.publish_payload(payload, self.trade_with + '_server')
        self.swap_items(self.give, self.take)
        self.give = {'rail': [], 'ship': [], 'clues': [], 'assets': [], 'unique_assets': [], 'artifacts': [], 'spells': [], 'conditions': []}
        self.take = {'rail': [], 'ship': [], 'clues': [], 'assets': [], 'unique_assets': [], 'artifacts': [], 'spells': [], 'conditions': []}
        self.hub.action_taken('trade')

    def swap_items(self, take, give):
        self.investigator.rail_tickets - len(give['rail']) + len(take['rail'])
        self.investigator.ship_tickets - len(give['ship']) + len(give['ship'])
        print(self.investigator.name)
        for kind in ['assets', 'unique_assets', 'artifacts', 'spells', 'conditions']:
            print(self.investigator.possessions[kind])
            print(give[kind])
            for item in give[kind]:
                card = next((card for card in self.investigator.possessions[kind] if card.get_server_name() == item))
                self.investigator.possessions[kind].remove(card)
            for item in take[kind]:
                self.hub.item_received(kind, item)

    def select(self, name, kind, button):
        reference = self.take if self.is_taking else self.give
        if name in reference[kind]:
            reference[kind].remove(name)
            button = next((button for button in self.overlay_layout.children if button.name == name))
            self.overlay_layout.children.remove(button)
        else:
            reference[kind].append(name)
            texture = 'gui/selected.png' if kind not in ['rail', 'ship'] else 'gui/ticket_select.png'
            height = button.height if kind not in ['rail', 'ship'] else button.height + 6
            width = button.width if kind not in ['rail', 'ship'] else button.width + 3
            button = ActionButton(x=button.x, y=button.y, width=width, height=height, texture=texture, name=name)
            if kind in ['rail','ship']:
                button.move(-3, -3)
            self.overlay_layout.add(button)
        self.hub.info_manager.trigger_render()