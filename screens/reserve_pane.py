import arcade, arcade.gui
from screens.action_button import ActionButton
from util import *

IMAGE_PATH_ROOT = ":resources:eldritch/images/"

class ReservePane():
    def __init__(self, hub):
        self.layout = arcade.gui.UILayout(x=1000)
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
        for i in range(4):
            if number == 0:
                y_pos -= 190
            self.button_layout.add(ActionButton(1015 + number * 130, y_pos, width=120, height=185, texture='buttons/placeholder.png', action=self.select_item))
            number += 1
            if number == 2:
                number = 0
        self.layout.add(self.button_pane)
        self.button_layout.add(ActionButton(x=1000, y=760, width=280, height=25, text='RESERVE'))
        self.acquire_button = ActionButton(x=1000, y=325, width=280, height=25, text='Acquire Assets', texture='buttons/placeholder.png', action=self.acquire_assets)
        self.discard_button = ActionButton(x=1000, y=275, width=280, height=25, text='View Discard', texture='buttons/placeholder.png', action=self.discard_action)
        self.debt_button = ActionButton(x=1000, y=225, width=280, height=25, text='Bank Loan', texture='buttons/placeholder.png', action=self.bank_loan)
        self.button_layout.add(self.acquire_button)
        self.button_layout.add(self.discard_button)
        self.discard_layout.add(ActionButton(x=1000, y=760, width=280, height=25, text='DISCARD'))
        self.discard_layout.add(ActionButton(x=1260, y=780, width=20, height=20, text='X', texture='buttons/placeholder.png', action=self.close_discard))

    def restock(self, removed, added):
        if removed != '':
            for item in removed:
                item = item.replace('.', '')
                option = next((button for button in self.button_layout.children if button.name == item), None)
                option.name = added[0].replace('.', '')
                option.texture = arcade.load_texture(IMAGE_PATH_ROOT + 'assets/' + option.name + '.png')
                option.action_args = {'name': option.name, 'cost': int(self.hub.get_item_info(added[0])['cost'])}
                added.remove(added[0])
            for item in added:
                option = next((button for button in self.button_layout.children if button.name == None or button.name == ''), None)
                cost = int(self.hub.get_item_info(item)['cost'])
                item = item.replace('.', '')
                option.name = item
                option.texture = arcade.load_texture(IMAGE_PATH_ROOT + 'assets/' + item + '.png')
                option.action_args = {'name': option.name, 'cost': cost}

    def acquire_assets(self):
        if self.is_shopping:
            self.hub.action_taken('shop')
            for item in (self.selected):
                self.hub.request_card('assets', item, 'acquire:')
            self.reset()
        else:
            self.is_shopping = True
            self.hub.gui_set(False)
            self.rolls = self.hub.run_test(1, pane=self)
            for x in self.rolls:
                if x >= self.hub.investigator.success:
                    self.successes += 1
            self.acquire_button.text = 'Acquire (Remaining cost ' + str(self.successes) + ')'
            self.acquire_button.disable()
            self.discard_button.text = 'Cycle Card'
            self.discard_button.disable()
            self.layout.add(self.debt_button)

    def select_item(self, name, cost):
        self.acquire_button.enable()
        if name in self.selected:
            self.selected.remove(name)
            self.successes += cost
            if not self.acquire_button.enabled and self.successes >= 0:
                self.acquire_button.enable()
        else:
            self.selected.append(name)
            self.successes -= cost
            if self.acquire_button.enabled and self.successes < 0:
                self.acquire_button.disable()
            if len(self.selected) > 1:
                self.discard_button.disable()
        self.acquire_button.text = 'Acquire (Remaining cost: ' + str(self.successes) + ')'
        if len(self.selected) == 1:
            self.discard_button.enable()

    def discard_action(self):
        if self.is_shopping:
            self.hub.request_card('assets', self.selected[0], 'restock:')
            self.reset()
        else:
            self.layout.children.clear()
            self.layout.add(self.discard_pane)
            self.discard_view = True

    def bank_loan(self):
        self.hub.request_card('conditions', 'debt')
        self.add_success(2)

    def reset(self):
        self.hub.gui_set(True)
        self.is_shopping = False
        self.successes = 0
        self.rolls = []
        self.selected = []
        self.acquire_button.text = 'Acquire Assets'
        self.acquire_button.disable()
        self.discard_button.text = 'View Discard'
        if self.debt_button in self.layout.children:
            self.layout.children.remove(self.debt_button)
        self.layout.trigger_render()
        self.hub.clear_overlay()
        self.reset_discard()

    def close_discard(self):
        self.layout.children.clear()
        self.layout.add(self.button_pane)
        self.discard_view = False
        self.reset_discard()

    def discard_item(self, name):
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
                discard.initial_x = 1015 + column * 130 - discard.x
                discard.initial_y = 570 - row * 190 - discard.y
            if len(self.discard) == 0:
                self.close_discard()
                self.discard_action()
        else:
            self.discard.append(name)
            column = (len(self.discard) + 1) % 2
            row = int((len(self.discard) / 2) - 0.5)
            if row > 2:
                self.boundary = 20 + (row - 3) * 190
            self.discard_layout.add(ActionButton(1015 + column * 130, 570 - row * 190, width=120, height=185, name=name, texture='assets/' + name.replace('.','') + '.png'))
    
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

    def reroll(self, new, old):
        self.rolls.remove(old)
        self.rolls.append(new)
        if new >= self.hub.investigator.success:
            self.successes += 1
        self.acquire_button.text = 'Acquire (Remaining cost: ' + str(self.successes) + ')'