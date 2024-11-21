import arcade.gui
IMAGE_PATH_ROOT = ":resources:eldritch/images/"

def human_readable(text: str):
    name = ''
    for token in text.split('_'):
        name += token.capitalize() + ' '
    return name[0:-1]

def create_choices(title='', subtitle='', choices=[], size=(1000,658), pos=(0,142), options=[],
                   flip: bool = False, offset=(0,200), background=IMAGE_PATH_ROOT + 'gui/overlay.png'):

    choice_gui = arcade.gui.UILayout(width=size[0], height=size[1], x=pos[0], y=pos[1]).with_background(arcade.load_texture(background))
    index = 1
    if title != '':
        choice_gui.add(arcade.gui.UITextureButton(y=size[1]-100, width=size[0], height=50, align='center', text=title))
        index += 1
    if subtitle != '':
        choice_gui.add(arcade.gui.UITextureButton(y=size[1]-150, width=size[0], height=50, align='center', text=subtitle))
        index += 1

    start_y = size[1] - offset[1] - (50 if subtitle != '' else 0)

    for menu in [choices, options]:
        choice_height = 0
        choice_width = 0
        for button in menu:
            choice_width += button.width + 20
            if button.height > choice_height:
                choice_height = button.height
            choice_gui.add(button)

        start_x = (size[0] - (choice_width - 20)) / 2
        start_y -= (choice_height / 2)

        for button in menu:
            button.move(start_x, start_y + ((choice_height - button.height) / 2))
            start_x += button.width + 20

        start_y -= 40

    return choice_gui

def get_distance(p1, p2):
    return (((p2[0] - p1[0]) ** 2) + ((p2[1] - p1[1]) ** 2)) ** 0.5