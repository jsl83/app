import arcade
import arcade.gui
import yaml
import math
from util import *
from screens.server_loading import ServerLoadingScreen

IMAGE_PATH_ROOT = ":resources:eldritch/images/"

class SelectionScreen(arcade.View):

    def __init__(self, path, networker, respawn=False):
        super().__init__()
        self.background = None
        self.selected = None
        self.front = True
        self.path = path
        self.holding = False
        self.click_time = 0
        self.y_position = 0
        self.initial_y = 0
        self.selection_options = []
        self.networker = networker
        self.respawn = respawn
        self.ancient_one = None

        self.load_options()

        self.manager = arcade.gui.UIManager()
        self.manager.enable()
        self.max_height = 800 if len(self.selection_options) * 3 < 18 else 650 + (math.ceil(len(self.selection_options) * 5 / 6) - 3) * 200
        self.selection_list = arcade.gui.UILayout(width=1280, height=self.max_height)
        self.detail_list = arcade.gui.UILayout(width=1280, height=800)

        self.setup()

    def load_options(self):
        try:
            with open(self.path + '/' + self.path + '.yaml') as stream:
                self.selection_options = yaml.safe_load(stream)
        except:
            self.selection_options = []

    def setup(self):
        row = 0
        column = 0
        count = 0
        for name in self.selection_options:
            texture = arcade.load_texture(IMAGE_PATH_ROOT + self.path + '\\' + name + '_portrait.png')
            scale = 125 / texture.width
            x = 150 + column * 171
            y = 515 - row * 200
            select_button = arcade.gui.UITextureButton(x, y, height=300, texture=texture, scale=scale, text=human_readable(name), text_position=(0,-70))
            select_button.name = name
            select_button.enabled = True
            self.selection_list.add(select_button)
            column += 1
            count += 1
            if column == 6:
                row += 1
                column = 0
        self.manager.add(self.selection_list, index=1)

        detail_buttons = ['Select', 'Flip', 'Back']
        for i in range(0, 3):
            button = arcade.gui.UITextureButton(1050, 300 + i * 100, texture=arcade.load_texture(IMAGE_PATH_ROOT + 'buttons\\placeholder.png'))
            button.text = detail_buttons[i]
            self.detail_list.add(button)

    def on_draw(self):
        self.clear()        
        self.manager.draw()
        self.click_time += 1

    def on_mouse_release(self, x, y, button, modifiers):
        self.holding = False
        if (self.click_time <= 5 or abs(self.y_position - self.initial_y) < 5):
            buttons = list(self.manager.get_widgets_at((x,y)))
            if len(buttons) > 0 and type(buttons[0]) is arcade.gui.UITextureButton:
                if self.selected:
                    text = buttons[0].text
                    if text == 'Select':
                        payload = {'message': self.path + '_selected', 'value': self.selected}
                        def send_login(encounter):
                            self.networker.publish_payload(payload, 'login')
                            if self.path == 'investigators':
                                self.networker.set_subscriber_topic(self.selected + '_server')
                                self.networker.set_subscriber_topic(self.selected + '_player')
                                self.networker.investigator = self.selected
                                if self.respawn:
                                    self.networker.game_screen.respawn_name = self.selected
                                self.networker.window.pop_handlers()
                                loading_screen = ServerLoadingScreen(self.networker)
                                for name in [button.name for button in self.selection_list.children if not button.enabled]:
                                    loading_screen.investigator_selected(name)
                                if self.ancient_one:
                                    loading_screen.select_ao(self.ancient_one)
                                    loading_screen.investigator_selected(self.selected)
                                self.networker.select_screen = loading_screen
                                self.networker.window.show_view(loading_screen)
                            else:
                                self.selection_list.clear()
                                self.ancient_one = self.selected
                                self.selected = None
                                self.path = 'investigators'
                                self.load_options()
                                self.setup()
                                self.networker.publish_payload({'message': 'get_investigators'}, 'login')
                        if self.respawn:
                            self.networker.window.pop_handlers()
                            self.networker.window.show_view(self.networker.game_screen)
                            payload['replace'] = self.networker.investigator
                        else:
                            self.manager.children = {0:[]}
                            self.manager.add(arcade.gui.UITextureButton(width=1280, y=700, text='Waiting for other players', texture=arcade.load_texture(IMAGE_PATH_ROOT + 'buttons/placeholder.png')))
                        if self.selected == 'lola_hayes' and self.respawn:
                            self.networker.game_screen.small_card_pane.set_return_gui(self.info_pane)
                            self.networker.game_screen.small_card_pane.improve_skill('01234')
                            self.networker.game_screen.small_card_pane.finish_action = send_login
                        else:
                            send_login('')
                    elif text == 'Back':
                        self.selected = None
                    elif text == 'Flip':
                        side = '_front.png' if not self.front else '_back.png'
                        self.detail_list.children[-1].texture = arcade.load_texture(IMAGE_PATH_ROOT + self.path + '\\' + self.selected + side)
                        self.front = not self.front
                    if not self.selected:
                        self.manager.children = {0:[]}
                        self.manager.add(self.selection_list)
                        self.detail_list.remove(self.detail_list.children[-1])
                elif buttons[0].enabled:
                    name = buttons[0].name
                    texture = arcade.load_texture(IMAGE_PATH_ROOT + self.path + '\\' + name + '_front.png')
                    scale = 700 / texture.height
                    x = (760 - texture.width * scale) / 2
                    detail_card = arcade.gui.UITextureButton(x + 150, 50, scale=scale, texture=texture)
                    self.detail_list.add(detail_card)
                    self.selected = name
                    self.manager.children = {0:[]}
                    self.manager.add(self.detail_list)

    def on_mouse_press(self, x, y, button, modifiers):
        self.holding = True
        self.click_time = 0
        self.initial_y = self.y_position

    def on_mouse_motion(self, x, y, dx, dy):
        if self.holding and self.max_height > 800:
            self.y_position += dy
            if self.y_position < 0:
                dy = dy - (self.y_position)
                self.y_position = 0
            if self.y_position > self.max_height - 725:
                dy = dy + (self.max_height - self.y_position - 725)
                self.y_position = self.max_height - 725
            for button in self.selection_list.children:
                button.move(0, dy)

    def investigator_selected(self, name):
        for i in self.selection_list.children:
            if i.name == name:
                i.enabled = False
                i.text = "SELECTED"
                i.text_position = (0,15)

    def select_ao(self, name):
        self.ancient_one = name