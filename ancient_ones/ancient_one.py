import yaml

with open('ancient_ones/ancient_ones.yaml') as stream:
    ANCIENTS = yaml.safe_load(stream)

class AncientOne():
    def __init__(self, name):
        self.name = name
        self.mysteries = ANCIENTS[name]['mysteries']
        text = ANCIENTS[name]['text'].split('\\n')
        self.text = ''
        self.doom = int(ANCIENTS[name]['doom'])
        for x in range(len(text)):
            self.text += text[x]
            if x != len(text):
                self.text += '\n\n'

    def awaken(self):
        pass