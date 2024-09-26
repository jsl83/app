import arcade.gui

def human_readable(text: str):
    name = ''
    for token in text.split('_'):
        name += token.capitalize() + ' '
    return name[0:-1]

def create_choices(title=None, subtitle=None, choices=[], show_animation: bool = False, flip: bool = False):

    choice_gui = arcade.gui.UILayout(width=1280, height=800)
    index = 0
    if title:
        choice_gui.add(arcade.gui.UITextureButton(y=700, width=1280, height=50, align='center', **title))
        index += 1
    if subtitle:
        choice_gui.add(arcade.gui.UITextureButton(y=650, width=1280, height=50, align='center', **subtitle))
        index += 1
    choice_width = 0
    choice_height = 0
    for choice in choices:
        texture = arcade.load_texture(choice['path'])
        button = arcade.gui.UITextureButton(texture=texture, **choice)
        button.value = choice['value']
        choice_width += button.width + 20
        if button.height > choice_height:
            choice_height = button.height
        choice_gui.add(button)

    start_x = (1280 - (choice_width - 20)) / 2
    start_y = 400 - (choice_height / 2)

    for element in choice_gui.children[index:len(choice_gui.children)]:
        element.move(start_x, start_y + ((choice_height - element.height) / 2))
        start_x += element.width + 20

    return choice_gui

def get_distance(p1, p2):
    return (((p2[0] - p1[0]) ** 2) + ((p2[1] - p1[1]) ** 2)) ** 0.5