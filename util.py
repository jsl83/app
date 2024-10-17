import arcade.gui
from screens.action_button import ActionButton
IMAGE_PATH_ROOT = ":resources:eldritch/images/"

def human_readable(text: str):
    name = ''
    for token in text.split('_'):
        name += token.capitalize() + ' '
    return name[0:-1]

def create_choices(title='', subtitle='', choices=[], size=(1000,658), pos=(0,142), show_animation: bool = False,
                   flip: bool = False, offset=(0,200), background=IMAGE_PATH_ROOT + 'gui/overlay.png'):

    choice_gui = arcade.gui.UILayout(width=size[0], height=size[1], x=pos[0], y=pos[1]).with_background(arcade.load_texture(background))
    index = 1
    if title:
        choice_gui.add(arcade.gui.UITextureButton(y=size[1]-100, width=size[0], height=50, align='center', text=title))
        choice_gui.children[1].title = title
        index += 1
    if subtitle:
        choice_gui.add(arcade.gui.UITextureButton(y=size[1]-150, width=size[0], height=50, align='center', text=subtitle))
        choice_gui.children[index].subtitle = subtitle
        index += 1
    choice_width = 0
    choice_height = 0
    for choice in choices:
        choice_width += choice.width + 20
        if choice.height > choice_height:
            choice_height = choice.height
        choice_gui.add(choice)

    start_x = (size[0] - (choice_width - 20)) / 2
    start_y = size[1] - offset[1] - (choice_height / 2)

    for element in choice_gui.children[index:len(choice_gui.children)]:
        element.move(start_x, start_y + ((choice_height - element.height) / 2))
        start_x += element.width + 20

    return choice_gui

def get_distance(p1, p2):
    return (((p2[0] - p1[0]) ** 2) + ((p2[1] - p1[1]) ** 2)) ** 0.5