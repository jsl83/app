import arcade, arcade.gui

IMAGE_PATH_ROOT = ":resources:eldritch/images/maps"

class Map():
    def __init__(self, name, offset, zoom):
        self.layout = arcade.gui.UILayout(width=1280, height=800)
        map_texture = arcade.load_texture(":resources:eldritch/images/maps/" + name + ".png")
        self.map = arcade.gui.UITextureButton(texture=map_texture, x=offset[0], y=offset[1], scale=zoom)
        self.layout.add(self.map)

    def move(self, x, y):
        self.map.move(x, y)

    def get_location(self):
        return (self.map.x, self.map.y)
    
    def zoom(self, factor):
        self.map.scale(factor)