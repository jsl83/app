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
        self.selected = None
        self.path = path
        self.click_time = 0
        self.selection_options = []
        self.networker = networker
        self.respawn = respawn
        self.ancient_one = None
        self.textures = {}
        self.manager = arcade.gui.UIManager()
        self.manager.enable()
        self.empty_texture = arcade.load_texture(IMAGE_PATH_ROOT + 'investigators/empty_circle.png')
        self.blank_texture = arcade.load_texture(IMAGE_PATH_ROOT + 'blank.png')
        self.selection_icons = arcade.gui.UILayout()
        self.detail_card = None
        self.select_bg = None
        self.detail_bg = None
        self.back_card = None
        self.selector = None
        self.load_options()
        self.setup()

    def load_options(self):
        try:
            with open(self.path + '/' + self.path + '.yaml') as stream:
                self.selection_options = list(yaml.safe_load(stream).keys())
        except:
            self.selection_options = []

    def select(self, name, x, y):
        self.selected = name
        self.detail_card.texture = self.textures[name]['front']
        self.back_card.texture = self.textures[name]['back']
        self.manager.remove(self.detail_bg)
        self.manager.add(self.detail_bg)
        self.selector.move(x-45-self.selector.x, y-38-self.selector.y)
        self.confirm_button.text = ('Challenge ' + human_readable(name)) if self.path == 'ancient_ones' else 'Embark'

    def setup(self):
        is_ao = self.path == 'ancient_ones'
        for option in self.selection_options:
            self.textures[option] = {'front': arcade.load_texture(IMAGE_PATH_ROOT + self.path + '/' + option + '_front.png'),
                                        'back': self.blank_texture if self.path == 'ancient_ones' else arcade.load_texture(IMAGE_PATH_ROOT + self.path + '/' + option + '_back.png'),
                                        'portrait': arcade.load_texture(IMAGE_PATH_ROOT + self.path + '/' + option + '_portrait.png')}
        if is_ao:
            self.select_bg = arcade.gui.UITextureButton(width=640, height=800, texture=arcade.load_texture(IMAGE_PATH_ROOT + 'gui' + '/' + self.path + '_select.png'))
            self.detail_bg = arcade.gui.UITextureButton(width=640, height=800, x=640, texture=arcade.load_texture(IMAGE_PATH_ROOT + 'gui' + '/' + self.path + '_details.png'))
            self.detail_card = arcade.gui.UITextureButton(width=640, height=800, x=640, texture=self.blank_texture)
            self.back_card = arcade.gui.UITextureButton(width=640, height=800, x=640, texture=self.blank_texture)
            self.selector = arcade.gui.UITextureButton(texture=arcade.load_texture(IMAGE_PATH_ROOT + 'gui/ao_selection.png'), scale=0.9)
            self.confirm_button = arcade.gui.UITextureButton(texture=self.blank_texture, width=640, height=90, font='UglyQua', style={'font_size': 24})
            self.confirm_button.name = 'confirm'
            positions = [(88,596), (270,593), (452,595), (90,392), (270,395), (457,393), (90,195), (270,191), (450,195)]
            for x in range(8):
                icon = arcade.gui.UITextureButton(positions[x][0], positions[x][1], 100, 100, self.empty_texture)
                self.selection_icons.add(icon)
            self.switch_page(0, 8)
        else:
            self.select_bg = arcade.gui.UITextureButton(texture=arcade.load_texture(IMAGE_PATH_ROOT + 'gui' + '/' + self.path + '_details.png'))
            self.detail_bg = arcade.gui.UITextureButton(y=300, texture=arcade.load_texture(IMAGE_PATH_ROOT + 'gui' + '/' + self.path + '_select.png'))
            #self.detail_bg = arcade.gui.UITextureButton(y=300, texture=self.blank_texture)
            self.detail_card = arcade.gui.UITextureButton(x=150, y=305, width=619, height=496, texture=arcade.load_texture(IMAGE_PATH_ROOT + 'blank.png'))
            self.back_card = arcade.gui.UITextureButton(x=731, y=264, width=681, height=540, texture=arcade.load_texture(IMAGE_PATH_ROOT + 'blank.png'))
            self.selector = arcade.gui.UITextureButton(texture=self.blank_texture)
            self.confirm_button = arcade.gui.UITextureButton(texture=arcade.load_texture(IMAGE_PATH_ROOT + 'blank.png'), x=1053, y=0, width=190, height=100, font='UglyQua', style={'font_size': 18, 'font_color': arcade.color.RED})
            self.confirm_button.name = 'confirm'
            positions = [(69,13), (296,19), (521,13), (747,26)]
            for x in range(4):
                icon = arcade.gui.UITextureButton(positions[x][0], positions[x][1], 158, 221, self.empty_texture)
                self.selection_icons.add(icon)
            self.switch_page(0, 4)
            page_positions = [(1021, 188), (1100, 197), (1188, 208)]
            for x in range(3):
                page_button = arcade.gui.UITextureButton(page_positions[x][0], page_positions[x][1], 75, 50, self.blank_texture)
                page_button.name = str(x)
                self.selection_icons.add(page_button)
            self.page_selector = arcade.gui.UITextureButton(1021, 155, texture=arcade.load_texture(IMAGE_PATH_ROOT + 'gui/page.png'))
        self.select(self.selection_options[0], self.selection_icons.children[0].x, self.selection_icons.children[0].y)
        self.manager.add(self.detail_card)
        self.manager.add(self.back_card)
        self.manager.add(self.detail_bg)
        self.manager.add(self.select_bg)
        self.manager.add(self.selection_icons)
        self.manager.add(self.selector)
        self.manager.add(self.confirm_button)
        if not is_ao:
            self.manager.add(self.page_selector)

    def switch_page(self, page, number):
        for x in range(number):
            if (page*number) + x < len(self.selection_options):
                name = self.selection_options[(page*number) + x]
                self.selection_icons.children[x].texture = self.textures[name]['portrait']
                self.selection_icons.children[x].name = name
            else:
                self.selection_icons.children[x].texture = self.empty_texture
                self.selection_icons.children[x].name = ''

    def on_draw(self):
        self.clear()        
        self.manager.draw()
        self.click_time += 1

    def on_mouse_release(self, x, y, button, modifiers):
        if (self.click_time <= 5):
            buttons = [button for button in list(self.manager.get_widgets_at((x,y))) if button in self.selection_icons.children + [self.confirm_button] and getattr(button, 'enabled', True)]
            if len(buttons) > 0:
                action = getattr(buttons[0], 'name')
                if action == 'random':
                    pass
                elif action == 'confirm':
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
                            for name in [button.name for button in self.selection_icons.children if not getattr(button, 'enabled', True)]:
                                loading_screen.investigator_selected(name)
                            if self.ancient_one:
                                loading_screen.select_ao(self.ancient_one)
                                loading_screen.investigator_selected(self.selected)
                            self.networker.select_screen = loading_screen
                            self.networker.window.show_view(loading_screen)
                        else:
                            self.selection_icons.clear()
                            self.manager.clear()
                            self.ancient_one = self.selected
                            self.selected = None
                            self.path = 'investigators'
                            self.load_options()
                            self.setup()
                            self.networker.publish_payload({'message': 'get_investigators'}, 'login')
                            self.manager.trigger_render()
                    if self.respawn:
                        self.networker.window.pop_handlers()
                        self.networker.window.show_view(self.networker.game_screen)
                        payload['replace'] = self.networker.investigator
                    if self.selected == 'lola_hayes' and self.respawn:
                        self.networker.game_screen.small_card_pane.set_return_gui(self.info_pane)
                        self.networker.game_screen.small_card_pane.improve_skill('01234')
                        self.networker.game_screen.small_card_pane.finish_action = send_login
                    else:
                        send_login('')
                elif action in ['0','1','2']:
                    self.switch_page(int(action), 4)
                    self.page_selector.move(buttons[0].x - self.page_selector.x, buttons[0].y - self.page_selector.y - 33)
                elif action != '':
                    self.select(action, buttons[0].x, buttons[0].y)

    def on_mouse_press(self, x, y, button, modifiers):
        self.click_time = 0

    def investigator_selected(self, name):
        for i in self.selection_icons.children:
            if i.name == name:
                i.enabled = False
                i.text = "SELECTED"

    def select_ao(self, name):
        self.ancient_one = name