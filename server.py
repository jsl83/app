import arcade
import threading
import sys
import subprocess
import signal
import argparse
import yaml
import random
from python_banyan.banyan_base import BanyanBase
from screens.server_loading import ServerLoadingScreen

# Screen title and size
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 800
SCREEN_TITLE = "ELDRITCH HORROR"
REFERENCES = {
    1: [1, 1, 1],
    2: [1, 2, 2],
    3: [2, 3, 2],
    4: [2, 4, 3]
}
with open('small_cards/server_spells.yaml') as stream:
    SPELLS = yaml.safe_load(stream)
with open('locations/server_locations.yaml') as stream:
    LOCATIONS = yaml.safe_load(stream)

class Networker(threading.Thread, BanyanBase):
    def __init__(self, back_plane_ip_address=None, process_name=None, player=0, screen=None):
        threading.Thread.__init__(self)
        self.the_lock = threading.Lock()
        self.daemon = True
        self.run_the_thread = threading.Event()
        self.run_the_thread = True
        self.start_backplane()
        BanyanBase.__init__(self, back_plane_ip_address=back_plane_ip_address,
            process_name=process_name, loop_time=.0001)
        self.set_subscriber_topic('login')
        self.start()

        self.screen = screen

        self.player_count = 0
        self.ready_count = 0
        self.reference = None

        self.ancient_one = None

        self.decks = {
            'conditions': {},
            'artifacts': {},
            'unique_assets': {},
            'spells': {},
            'clues': [],
            'gates': {
                'deck': [],
                'discard': [],
                'board': []
            },
            'monsters': {}
        }
        self.assets = {
            'deck': [],
            'discard': [],
            'reserve': []
        }

        for map in LOCATIONS.keys():
            for location in LOCATIONS[map].keys():
                self.decks['clues'].append(map + ':' + location)
                if LOCATIONS[map][location] != None:
                    self.decks['gates']['deck'].append(map + ':' + location)

        for cardtype in ['spells']:
            for key in SPELLS.keys():
                self.decks[cardtype][key] = list(range(1, int(SPELLS[key]) + 1))

        # temporary variables set for testing - DELETE LATER
        self.set_subscriber_topic('akachi_onyele')
        self.selected_investigators = ['akachi_onyele']
        self.reference = REFERENCES[1]
        self.player_count = 1

    def start_backplane(self):
        if sys.platform.startswith('win32'):
            return subprocess.Popen(['backplane'],
                                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP |
                                    subprocess.CREATE_NO_WINDOW)
        else:
            return subprocess.Popen(['backplane'],
                                    stdin=subprocess.PIPE, stderr=subprocess.PIPE,
                                    stdout=subprocess.PIPE)

    def run(self):
        self.receive_loop()

    def incoming_message_processing(self, topic, payload):
        if topic == 'login':
            match payload['message']:
                case 'get_login_state':
                    self.publish_payload({'message': 'number_select' if self.player_count == 0 else
                        'ancient_ones' if not self.ancient_one else 'investigators', 'value': self.screen.investigators}, 'server_update')
                case "ancient_ones_selected":
                    self.ancient_one = payload['value']
                    self.screen.select_ao(self.ancient_one)
                    self.publish_payload({'message': 'investigators', 'value': payload['value']}, 'server_update')
                case 'investigators_selected':
                    self.selected_investigators.append(payload['value'])
                    self.set_subscriber_topic(payload['value'])
                    self.screen.add_investigator(payload['value'])
                    if len(self.selected_investigators) == self.player_count:
                        self.publish_payload({'message': 'start_game', 'value': None}, 'server_update')
                    else:
                        self.publish_payload({'message': 'investigator_selected', 'value': payload['value']}, 'server_update')
                case 'number_selected':
                    self.player_count = payload['value']
                    self.reference = REFERENCES[int(int(payload['value']) / 2)]
                    self.publish_payload({'message': 'ancient_ones', 'value': None}, 'server_update')
                case 'ready':
                    self.ready_count += 1
                    if self.ready_count == self.player_count:
                        self.initiate_gameboard()
        elif topic in self.selected_investigators:
            match payload['message']:
                case 'spells':
                    spell = self.item_request('spells', payload['value'])
                    if spell != None:
                        self.publish_payload({'message': 'spells', 'value': spell}, topic + '_server')

    def item_request(self, cardtype, command):
        command_type = command.split(':')[0]
        name = command.split(':')[1]
        if command_type == 'get':
            variant = random.choice(self.decks[cardtype][name])
            self.decks[cardtype][name].remove(variant)
            return name + ':' + str(variant)
        elif command_type == 'discard':
            self.decks[cardtype][name[0:-1]].append(name[-1])
            return None

    def spawn(self, piece, name=None, location=None):
        if piece == 'gates':
            if len(self.decks['gates']['deck']) > 0:
                gate = random.choice(self.decks['gates']['deck'])
                gate = 'world:arkham'
                self.decks['gates']['deck'].remove(gate)
                self.decks['gates']['board'].append(gate)
                self.publish_payload({'message': 'spawn', 'value': 'gate', 'location': gate.split(':')[1], 'map': gate.split(':')[0]}, 'server_update')
            elif len(self.decks['gates']['discard']) > 0:
                self.decks['gates']['deck'].append(item for item in self.decks['gates']['discard'])
                self.decks['gates']['discard'] = []
                self.spawn('gates')
            else:
                #advance doom
                pass
        elif piece == 'clues':
            token = random.choice(self.decks[piece])
            token = 'world:arkham'
            self.decks[piece].remove(token)
            self.publish_payload({'message': 'spawn', 'value': 'clue', 'location': token.split(':')[1], 'map': token.split(':')[0]}, 'server_update')

    def initiate_gameboard(self):
        for i in range(0, self.reference[0]):
            self.spawn('clues')
        for i in range(0, self.reference[1]):
            self.spawn('gates')

def set_up_network(screen):
    parser = argparse.ArgumentParser()
    # allow user to bypass the IP address auto-discovery.
    # This is necessary if the component resides on a computer
    # other than the computing running the backplane.
    parser.add_argument("-b", dest="back_plane_ip_address", default="None",
                        help="None or Common Backplane IP address")
    parser.add_argument("-n", dest="process_name", default="Arcade p2p",
                        help="Banyan Process Name Header Entry")
    parser.add_argument("-p", dest="player", default="0",
                        help="Select player 0 or 1")

    args = parser.parse_args()

    if args.back_plane_ip_address == 'None':
        args.back_plane_ip_address = None
    kw_options = {'back_plane_ip_address': args.back_plane_ip_address,
                'process_name': args.process_name + ' player' + str(args.player),
                'player': int(args.player),
                'screen': screen
                }
    # instantiate MyGame and pass in the options
    return Networker(**kw_options)

# signal handler function called when Control-C occurs
# noinspection PyUnusedLocal,PyUnusedLocal
def signal_handler(sig, frame):
    print('Exiting Through Signal Handler')
    raise KeyboardInterrupt

# listen for SIGINT
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    loading_screen = ServerLoadingScreen()
    window.show_view(loading_screen)
    set_up_network(loading_screen)

    arcade.run()

if __name__ == '__main__':
    main()