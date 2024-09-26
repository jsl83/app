class Location():
    def __init__(self, data):

        self.name = data['name']
        self.x = data['x']
        self.y = data['y']
        self.kind = data['kind']
        self.size = data['size']
        self.color = None if self.size != 'large' else data['color']
        self.routes = data['routes']
        self.subtitle = data['subtitle'] if self.size != 'square' else ''

    def get_route_names(self):
        return list(map(lambda route: list(route.keys())[0], self.routes))