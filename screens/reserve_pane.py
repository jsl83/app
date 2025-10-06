import arcade, arcade.gui
from screens.action_button import ActionButton
from encounters.encounter_pane import InvestigatorSkillPane
from small_cards.small_card import *
from util import *

IMAGE_PATH_ROOT = ":resources:eldritch/images/"

class ReservePane():
    def __init__(self, hub):
        self.layout = arcade.gui.UILayout(x=1000)
        self.choice_layout = arcade.gui.UILayout()
        self.button_layout = arcade.gui.UILayout(x=1000, y=0, width=280, height=800)
        self.button_pane = arcade.gui.UITexturePane(self.button_layout, arcade.load_texture(IMAGE_PATH_ROOT + 'gui/info_pane.png'))
        self.discard_layout = arcade.gui.UILayout(x=1000, y=0, width=280, height=800)
        self.discard_pane = arcade.gui.UITexturePane(self.discard_layout, arcade.load_texture(IMAGE_PATH_ROOT + 'gui/info_pane.png'))
        self.reserve = []
        self.discard = []
        self.selected = []
        self.hub = hub
        self.successes = 0
        self.rolls = []
        self.is_shopping = False
        self.discard_view = False
        self.position = 0
        self.boundary = 0
        y_pos = 760
        number = 0
        self.reserve_buttons = []
        for i in range(4):
            if number == 0:
                y_pos -= 190
            button = ActionButton(1015 + number * 130, y_pos, width=120, height=185, texture='buttons/placeholder.png', action=self.select_item)
            self.button_layout.add(button)
            number += 1
            if number == 2:
                number = 0
            self.reserve_buttons.append(button)
        self.layout.add(self.button_pane)
        self.button_layout.add(ActionButton(x=1000, y=760, width=280, height=25, text='RESERVE'))
        self.acquire_button = ActionButton(x=1000, y=325, width=280, height=25, text='Acquire Assets', texture='buttons/placeholder.png', action=self.acquire_assets)
        self.discard_button = ActionButton(x=1000, y=275, width=280, height=25, text='View Discard', texture='buttons/placeholder.png', action=self.discard_action)
        self.debt_button = ActionButton(x=1000, y=225, width=280, height=25, text='Bank Loan', texture='buttons/placeholder.png', action=self.bank_loan)
        self.button_layout.add(self.acquire_button)
        self.button_layout.add(self.discard_button)
        self.discard_layout.add(ActionButton(x=1000, y=760, width=280, height=25, text='DISCARD'))
        self.discard_layout.add(ActionButton(x=1260, y=780, width=20, height=20, text='X', texture='buttons/placeholder.png', action=self.close_discard))
        self.empty_texture = arcade.load_texture(":resources:eldritch/images/buttons/placeholder.png")
        self.encounter_type = ['acquire_assets']

    def restock(self, removed, added):
        for item in removed:
            removal = next((r for r in self.reserve if r['name'] == item), None)
            reserve_button = next((button for button in self.reserve_buttons if (button.name == item)), None)
            reserve_button.name = None
            reserve_button.action_args = None
            reserve_button.texture = self.empty_texture
            reserve_button.disable()
            self.reserve.remove(removal)
        for item in added:
            option = next((button for button in self.reserve_buttons if (button.name == None or button.name == '')), None)
            card = get_asset(item)
            option.name = item
            option.texture = card['texture']
            option.action_args = {'card': card}
            option.enable()
            self.reserve.append(card)
        if len(self.reserve) == 0:
            self.acquire_button.disable()

    def retrieve_card(self, name):
        return get_asset(name)

    def acquire_assets(self):
        if self.is_shopping:
            def resolve_shop(name=None):
                services = [item for item in self.selected if 'service' in item['tags']]
                for item in self.selected:
                    self.hub.request_card('assets', item['name'], 'acquire')
                    self.reserve = [item for item in self.reserve if item['name'] != item]
                self.reset()
                if len(services) > 0:
                    self.hub.gui_set(False)
                    for service in services:
                        service['title'] = human_readable(service['name'])
                        self.hub.networker.publish_payload({'message': 'card_discarded', 'value': service['name'], 'kind': 'assets'}, self.hub.investigator.name)
                    def finish(name):
                        self.hub.action_taken('shop')
                        self.hub.gui_set(True)
                    self.hub.small_card_pane.setup(services, parent=self, single_pick=False, finish_action=finish, force_select=True, textures=[service['texture'] for service in services])
                else:
                    self.hub.action_taken('shop')
                self.acquire_button.disable()
            if self.hub.investigator.name == 'charlie_kane' and self.hub.location_manager.player_count > 1:
                send_pane = InvestigatorSkillPane(self.hub)
                send_pane.acquire_items = self.selected
                send_pane.finish_action = resolve_shop
                send_pane.set_return_gui(self)
                send_pane.send_items(self)
                self.hub.info_pane = send_pane
            else:
                resolve_shop()
        elif not self.hub.actions_taken['shop'] and self.hub.remaining_actions > 0:
            self.is_shopping = True
            self.hub.gui_set(False)
            def finish_test():
                for button in self.reserve_buttons:
                    button.enable()
                self.choice_layout.clear()
                self.layout.children.remove(self.choice_layout)
                for x in self.rolls:
                    if x >= self.hub.investigator.success:
                        self.successes += 1
                self.acquire_button.text = 'Acquire (Remaining cost ' + str(self.successes) + ')'
                self.acquire_button.enable()
                self.discard_button.text = 'Cycle 1 Card'
                self.layout.add(self.debt_button)
            self.rolls, self.choice_layout = self.hub.run_test(1, self, options=[ActionButton(width=100, height=50, text='Finish', action=finish_test, texture='buttons/placeholder.png')])
            self.layout.add(self.choice_layout)
            self.acquire_button.disable()
            self.discard_button.disable()
            for button in self.reserve_buttons:
                button.disable()

    def select_item(self, card):
        cost = card['cost']
        if self.is_shopping:
            if card in self.selected:
                self.selected.remove(card)
                self.successes += cost
                if not self.acquire_button.enabled and self.successes >= 0:
                    self.acquire_button.enable()
            else:
                self.acquire_button.enable()
                self.selected.append(card)
                self.successes -= cost
                if self.acquire_button.enabled and self.successes < 0:
                    self.acquire_button.disable()
                if len(self.selected) > 1:
                    self.discard_button.disable()
            self.acquire_button.text = 'Acquire (Remaining cost: ' + str(self.successes) + ')'
            if len(self.selected) == 1:
                self.discard_button.enable()
            else:
                self.discard_button.disable()
            self.layout.trigger_render()

    def discard_action(self):
        if self.is_shopping:
            self.hub.request_card('assets', self.selected[0]['name'], 'restock')
            self.reset()
            self.hub.action_taken('shop')
        else:
            self.layout.children.clear()
            self.layout.add(self.discard_pane)
            self.discard_view = True

    def bank_loan(self):
        self.hub.request_card('conditions', 'debt')
        self.successes += 2
        self.acquire_button.text = 'Acquire (Remaining cost ' + str(self.successes) + ')'
        if self.successes > 0 and len(self.selected) > 0:
            self.acquire_button.enable()

    def reset(self):
        self.hub.gui_set(True)
        self.is_shopping = False
        self.successes = 0
        self.rolls = []
        self.selected = []
        self.acquire_button.text = 'Acquire Assets'
        self.acquire_button.disable()
        self.discard_button.text = 'View Discard'
        self.discard_button.enable()
        self.layout.children = [elem for elem in self.layout.children if elem not in [self.debt_button, self.choice_layout]]
        self.layout.trigger_render()
        self.hub.clear_overlay()
        self.reset_discard()

    def close_discard(self):
        self.layout.children.clear()
        self.layout.add(self.button_pane)
        self.discard_view = False
        self.reset_discard()

    def discard_item(self, name, remove=False):
        if name in self.discard:
            self.discard.remove(name)
            item = next((item for item in self.discard_layout.children if item.name == name.replace('.', '')), None)
            self.discard_layout.children.remove(item)
            if int((len(self.discard) / 2) - 0.5) <= 2:
                self.boundary = 0
            for x in range(2, len(self.discard_layout.children)):
                discard = self.discard_layout.children[x]
                row = int(x / 2 - 1)
                column = x % 2
                discard.move(1015 + column * 130 - discard.x, 570 - row * 190 - discard.y)
                discard.initial_x = discard.x
                discard.initial_y = discard.y
            if len(self.discard) == 0:
                self.close_discard()
                self.discard_action()
        elif not remove:
            self.discard.append(name)
            column = (len(self.discard) + 1) % 2
            row = int((len(self.discard) / 2) - 0.5)
            if row > 2:
                self.boundary = 20 + (row - 3) * 190
            button = ActionButton(1015 + column * 130, 570 - row * 190, width=120, height=185, name=name, texture='assets/' + name.replace('.','') + '.png')
            button.name = name
            self.discard_layout.add(button)
    
    def move(self, y):
        if self.position + y < 0:
            y = self.position
        elif self.position + y > self.boundary:
            y = self.boundary - self.position
        self.position += y
        if y != 0:
            for item in self.discard_layout.children:
                item.move(0, y)

    def reset_discard(self):
        self.position = 0
        for item in self.discard_layout.children:
            item.reset_position()

    def on_show(self):
        self.close_discard()