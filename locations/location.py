class Location():
    def __init__(self, data):

        self.name = data['name']
        self.coordinates = (data['x'], data['y'])
        self.kind = data['kind']
        self.size = data['size']