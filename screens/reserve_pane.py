import arcade, arcade.gui
from screens.action_button import ActionButton
from util import *

IMAGE_PATH_ROOT = ":resources:eldritch/images/"

class ReservePane():
    def __init__(self, hub):
        self.layout = arcade.gui.UILayout(x=1000)
        self.button_layout = arcade.gui.UILayout(x=1000, y=0, width=280, height=800)
        self.reserve = []
        self.discard = []
        self.selected = []
        self.hub = hub
        self.successes = 0
        self.is_shopping = False
        y_pos = 760
        number = 0
        for i in range(4):
            if number == 0:
                y_pos -= 190
            self.button_layout.add(ActionButton(1015 + number * 130, y_pos, width=120, height=185, texture=arcade.load_texture(
                IMAGE_PATH_ROOT + 'buttons/placeholder.png'), action=self.select_item))
            number += 1
            if number == 2:
                number = 0
        self.layout.add(arcade.gui.UITexturePane(self.button_layout, arcade.load_texture(IMAGE_PATH_ROOT + 'gui/info_pane.png')))
        self.layout.add(ActionButton(x=1000, y=760, width=280, height=25, text='RESERVE'))
        self.acquire_button = ActionButton(x=1000, y=325, width=280, height=25, text='Acquire Assets', texture=arcade.load_texture(
            IMAGE_PATH_ROOT + 'buttons/placeholder.png'), action=self.acquire_assets)
        self.discard_button = ActionButton(x=1000, y=275, width=280, height=25, text='View Discard Pile', texture=arcade.load_texture(
            IMAGE_PATH_ROOT + 'buttons/placeholder.png'), action=self.discard_action)
        self.debt_button = ActionButton(x=1000, y=225, width=280, height=25, text='Bank Loan', texture=arcade.load_texture(
            IMAGE_PATH_ROOT + 'buttons/placeholder.png'), action=self.bank_loan)
        self.layout.add(self.acquire_button)
        self.layout.add(self.discard_button)

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
            for item in (self.selected):
                self.hub.request_card('assets', item, 'acquire:')
            self.reset()
        else:
            self.is_shopping = True
            self.hub.gui_set(False)
            for x in self.hub.run_test(1):
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
            pass

    def bank_loan(self):
        self.hub.request_card('conditions', 'debt')
        self.successes += 2
        self.acquire_button.text = 'Acquire (Remaining cost: ' + str(self.successes) + ')'

    def reset(self):
        self.hub.gui_set(True)
        self.is_shopping = False
        self.successes = 0
        self.selected = []
        self.acquire_button.text = 'Acquire Assets'
        self.acquire_button.disable()
        self.discard_button.text = 'View Discard'
        self.layout.children.remove(self.debt_button)
        self.layout.trigger_render()
        self.hub.clear_overlay()