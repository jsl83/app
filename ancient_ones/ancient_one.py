import yaml

with open('ancient_ones/ancient_ones.yaml') as stream:
    ANCIENTS = yaml.safe_load(stream)

class AncientOne():
    def __init__(self, name):
        self.name = name
        for key in ANCIENTS[name]:
            setattr(self, key, ANCIENTS[name][key])

    def awaken(self):
        pass