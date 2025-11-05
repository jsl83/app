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
        self.button_pane = arcade.gui.UILayout(1000, 330, 280, 470).with_background(arcade.load_texture(IMAGE_PATH_ROOT + 'gui/reserve_top.png'))
        self.shopping_pane = arcade.gui.UILayout(1000, 0, 280, 330).with_background(arcade.load_texture(IMAGE_PATH_ROOT + 'gui/shopping.png'))
        self.bottom_pane = arcade.gui.UILayout(1000, 0, 280, 330).with_background(arcade.load_texture(IMAGE_PATH_ROOT + 'gui/reserve_bottom.png'))
        self.discard_layout = arcade.gui.UILayout(x=1000, y=0, width=280, height=800)
        self.discard_pane = arcade.gui.UITexturePane(self.discard_layout, arcade.load_texture(IMAGE_PATH_ROOT + 'gui/reserve_pane.png'))
        self.enable_pane = arcade.gui.UILayout()
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
        y_pos = 749
        number = 0
        self.reserve_buttons = []
        for i in range(4):
            if number == 0:
                y_pos -= 201
            button = ActionButton(1014 + number * 140, y_pos, width=120, height=185, action=self.select_item, texture='assets/personal_assistant.png', scale=0.57)
            self.button_pane.add(button)
            number += 1
            if number == 2:
                number = 0
            self.reserve_buttons.append(button)
        self.layout.add(self.button_pane)
        self.layout.add(self.bottom_pane)
        self.acquire_button = ActionButton(x=1036, y=273, width=208, height=37, action=self.acquire_assets, text='Acquire Assets', font='Garamond Eldritch', style={'font_color': arcade.color.BLACK}, text_position=(0,-2))
        self.discard_button = ActionButton(x=1036, y=201, width=208, height=37, action=self.discard_action, text='View Discard', font='Garamond Eldritch', style={'font_color': arcade.color.BLACK}, text_position=(0,-2))
        self.credit_button = ActionButton(x=1000, y=163, width=115, height=55, font='Poster Bodoni', style={'font_color': arcade.color.BLACK, 'font_size': 18})
        self.debt_button = ActionButton(x=1090, y=0, width=100, height=138, action=self.bank_loan)
        self.cycle_button = ActionButton(x=1154, y=161, width=126, height=88, action=self.discard_action, text='Cycle', style={'font_color': arcade.color.BLACK, 'font_size': 18}, font='Garamond Eldritch', text_position=(5,15))
        self.cycle_button.disable()
        self.bottom_pane.add(self.acquire_button)
        self.bottom_pane.add(self.discard_button)
        self.shopping_pane.add(self.acquire_button)
        self.shopping_pane.add(self.cycle_button)
        self.shopping_pane.add(self.credit_button)
        self.shopping_pane.add(self.debt_button)
        self.discard_layout.add(ActionButton(x=1031, y=740, width=217, height=46, text='Close Discard', texture='buttons/button.png', action=self.close_discard, font='Garamond Eldritch', style={'font_color': arcade.color.BLACK}, text_position=(0,-2)))
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
            option.scale = 0.5
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
                self.disable_button(self.acquire_button)
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
                self.enable_button(self.acquire_button)
                self.enable_button(self.discard_button)
                self.disable_button(self.cycle_button)
                self.layout.children.remove(self.bottom_pane)
                self.layout.add(self.shopping_pane)
                self.layout.add(self.enable_pane)
                self.credit_button.text = str(self.successes)
            self.rolls, self.choice_layout = self.hub.run_test(1, self, options=[ActionButton(width=100, height=50, text='Finish', action=finish_test, texture='buttons/placeholder.png')])
            self.layout.add(self.choice_layout)
            self.disable_button(self.acquire_button)
            self.disable_button(self.discard_button)
            if next((item for item in self.hub.investigator.possessions['assets'] if item['name'] == 'debt'), False):
                self.enable_pane.append(ActionButton(x=self.debt_button.x, y=self.debt_button.y, width=self.debt_button.width, height=self.debt_button.height, texture='buttons/transparent.png'))
            for button in self.reserve_buttons:
                button.disable()

    def select_item(self, card):
        cost = card['cost']
        button = next((button for button in self.reserve_buttons if button.name == card['name']), None)
        if self.is_shopping:
            if card in self.selected:
                self.selected.remove(card)
                self.enable_pane.children = [overlay for overlay in self.enable_pane.children if getattr(overlay, 'name', 'Default') != card['name']]
                self.successes += cost
                if not self.acquire_button.enabled and self.successes >= 0:
                    self.enable_button(self.acquire_button)
            else:
                overlay = ActionButton(texture='buttons/transparent.png', x=button.x, y=button.y, width=button.width, height=button.height)
                overlay.name = card['name']
                self.enable_pane.add(overlay)
                self.enable_button(self.acquire_button)
                self.selected.append(card)
                self.successes -= cost
                if self.acquire_button.enabled and self.successes < 0:
                    self.disable_button(self.acquire_button)
            self.credit_button.text = str(self.successes)
            if len(self.selected) == 1:
                self.enable_button(self.cycle_button)
            elif self.cycle_button.enabled:
                self.disable_button(self.cycle_button)
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
        self.credit_button.text = str(self.successes)
        if self.successes > 0 and len(self.selected) > 0:
            self.acquire_button.enable()
        self.enable_pane.add(ActionButton(x=self.debt_button.x, y=self.debt_button.y, width=self.debt_button.width, height=self.debt_button.height, texture='gui/overlay.png'))
        self.layout.trigger_render()
        self.hub.info_manager.trigger_render()

    def reset(self):
        self.hub.gui_set(True)
        self.is_shopping = False
        self.successes = 0
        self.rolls = []
        self.selected = []
        self.enable_pane.clear()
        self.disable_button(self.acquire_button)
        for button in [self.discard_button, self.debt_button, self.cycle_button]:
            button.enable()
        self.layout.clear()
        for pane in [self.button_pane, self.bottom_pane]:
            self.layout.add(pane)
        self.layout.trigger_render()
        self.hub.clear_overlay()
        self.reset_discard()

    def close_discard(self):
        self.layout.children.clear()
        self.enable_pane.clear()
        self.layout.add(self.button_pane)
        self.layout.add(self.bottom_pane)
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
            button = ActionButton(1015 + column * 130, 540 - row * 190, width=120, height=185, name=name, texture='assets/' + name.replace('.','') + '.png')
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

    def enable_button(self, button):
        button.enable()
        button.set_style(color=arcade.color.BLACK, size=getattr(button, 'style', {}).get('font_size', 15))
        self.hub.info_manager.trigger_render()
        
    def disable_button(self, button):
        button.disable()
        button.set_style(color=arcade.color.ASH_GREY, size=getattr(button, 'style', {}).get('font_size', 15))
        self.hub.info_manager.trigger_render()