import arcade
import arcade.csscolor
import arcade.gui
from util import *
from investigators.investigator import Investigator
from locations.location_manager import LocationManager

IMAGE_PATH_ROOT = ":resources:eldritch/images/"

class HubScreen(arcade.View):
    
    def __init__(self, networker, investigator):
        super().__init__()
        self.background = None
        self.networker = networker

        self.investigator = Investigator(investigator)
        self.map_view_loc = (0,0)
        self.initial_loc = (0,0)
        self.initial_click = (0,0)
        self.zoom = 1
        self.click_time = 0
        self.holding = False
        self.slow_move = (0, 0)
        self.slow_move_count = 0
        
        self.map_manager = arcade.gui.UIManager()
        self.ui_manager = arcade.gui.UIManager()
        self.map_layout = arcade.gui.UILayout(width=1280, height=800)
        self.info_layout = arcade.gui.UILayout(width=1280, height=800)
        map_texture = arcade.load_texture(IMAGE_PATH_ROOT + 'maps/world_map_square.png')
        self.map = arcade.gui.UITextureButton(texture=map_texture, y=-200, scale=0.5)
        self.map_layout.add(self.map)
        self.info_layout.add(arcade.gui.UITextureButton(x=1000, width=280, height=800, texture=arcade.load_texture(
            IMAGE_PATH_ROOT + 'buttons/placeholder.png')))
        self.info_layout.add(arcade.gui.UITextureButton(x=0, width=1280, height=142, texture=arcade.load_texture(
            IMAGE_PATH_ROOT + 'buttons/placeholder.png')))
        self.map_manager.add(self.map_layout)
        self.ui_manager.add(self.info_layout)
        self.map_manager.enable()
        self.ui_manager.enable()

        self.location_manager = LocationManager()

    def on_draw(self):
        self.clear()
        self.map_manager.draw()
        self.ui_manager.draw()
        self.click_time += 1
        if self.slow_move[0] != 0 or self.slow_move[1] != 0:
            self.map_layout.children[0].move(self.slow_move[0], self.slow_move[1])
            self.check_map_boundaries()
            self.slow_move_count += 1
            if self.slow_move_count == 10:
                self.slow_move = (0,0)
                self.slow_move_count = 0
    
    def on_mouse_release(self, x, y, button, modifiers):
        self.holding = False
        if x < 1080 and y > 200:
            location = self.location_manager.get_closest_location((x,y), self.zoom, (self.map.x, self.map.y))
            if location != None and self.zoom == 2:
                self.slow_move = ((500 - x) / 10, (471 - y) / 10)

    def on_mouse_press(self, x, y, button, modifiers):
        map = list(self.map_manager.get_widgets_at((x,y)))
        ui_buttons = list(self.ui_manager.get_widgets_at((x,y)))
        if x < 1080 and y > 200:
            if self.click_time < 25 and get_distance((x,y), self.initial_click) < 50:
                if self.zoom == 1:
                    self.map.scale(2)
                    self.zoom = 2
                    self.map_layout.children[0].move(500 - (x * 2), 471 - (y * 2))
                else:
                    self.map.scale(0.5)
                    self.zoom = 1
                self.check_map_boundaries()
            self.holding = True
            self.click_time = 0
            self.initial_loc = self.map_view_loc
            self.initial_click = (x, y)

    def on_mouse_motion(self, x, y, dx, dy):
        if self.holding:
            self.map_layout.children[0].move(dx, dy)
            self.check_map_boundaries()

    def check_map_boundaries(self):
        x, y = self.map.x, self.map.y
        dx, dy = 0, 0
        if x > 0:
            dx = -x
        elif  x < (-1000 if self.zoom == 2 else 0):
            dx = -x - (1000 if self.zoom == 2 else 0)
        if y > -542:
            dy = -y + (-542 if self.zoom == 2 else -200)
        elif y < 800 - (1000 * self.zoom):
            dy = -y + (-1200 if self.zoom == 2 else -200)
        self.map_layout.children[0].move(dx, dy)