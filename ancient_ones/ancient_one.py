import yaml

class AncientOne():
    def __init__(self, name):
        self.name = name
        with open('ancient_ones/ancient_ones.yaml') as stream:
            all_ancients = yaml.safe_load(stream)
            for key in all_ancients[name]:
                setattr(self, key, all_ancients[name][key])
        self.current_mystery = ''
        self.mystery_tracker = 0
        self.mystery_required = 0
        self.is_awakened = False

    def add_eldritch(self, amt=1):
        self.eldritch += amt
        self.eldritch = max(0, self.eldritch)