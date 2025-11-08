import arcade.gui
IMAGE_PATH_ROOT = ":resources:eldritch/images/"

def human_readable(text: str):
    name = ''
    for token in text.split('_'):
        name += token.capitalize() + ' '
    return name[0:-1]

def create_choices(title='', subtitle='', choices=[], size=(700,385), pos=(150,278), options=[],
                   flip: bool = False, offset=(0,200), background=IMAGE_PATH_ROOT + 'gui/base_overlay.png'):

    choice_gui = arcade.gui.UILayout(width=size[0], height=size[1], x=pos[0], y=pos[1]).with_background(arcade.load_texture(background))
    index = 1
    if title != '':
        title_button = arcade.gui.UITextureButton(x=pos[0], y=size[1]-115 + pos[1], width=size[0], height=50, align='center', text=title, font='UglyQua', style={'font_size': 18})
        title_button.identifier = 'overlay_title'
        choice_gui.add(title_button)
        index += 1
    if subtitle != '':
        subtitle_button = arcade.gui.UITextureButton(x=pos[0], y=size[1]-165 + pos[1], width=size[0], height=50, align='center', text=subtitle, font='UglyQua')
        subtitle_button.identifier = 'overlay_subtitle'
        choice_gui.add(subtitle_button)
        index += 1

    start_y = size[1] - offset[1] - (50 if subtitle != '' else 0) + pos[1]

    for menu in [choices, options]:
        choice_height = 0
        choice_width = 0
        for button in menu:
            choice_width += button.width + 20
            if button.height > choice_height:
                choice_height = button.height
            choice_gui.add(button)

        start_x = pos[0] + ((size[0] - (choice_width - 20)) / 2)
        start_y -= (choice_height / 2)

        for button in menu:
            button.move(start_x, start_y + ((choice_height - button.height) / 2))
            start_x += button.width + 20

        start_y -= (40 + choice_height / 2)

    return choice_gui

def get_distance(p1, p2):
    return (((p2[0] - p1[0]) ** 2) + ((p2[1] - p1[1]) ** 2)) ** 0.5