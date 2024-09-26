import arcade
import threading
import sys
import subprocess
import signal
import argparse
import yaml
from python_banyan.banyan_base import BanyanBase
from screens.server_loading import ServerLoadingScreen

# Screen title and size
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 800
SCREEN_TITLE = "ELDRITCH HORROR"

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
        self.selected_investigators = []

        self.ancient_one = None
        self.gates = []
        self.monsters = []
        self.reserve = []
        self.condition_deck = []
        self.asset_deck = []
        self.artifact_deck = []
        self.spell_deck = []
        self.unique_asset_deck = []
        self.clues = []

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
                    self.screen.add_investigator(payload['value'])
                    if len(self.selected_investigators) == self.player_count:
                        for name in self.selected_investigators:
                            self.publish_payload({'message': 'start_game', 'value': None}, name)
                    else:
                        self.publish_payload({'message': 'investigator_selected', 'value': payload['value']}, 'server_update')
                case 'number_selected':
                    self.player_count = payload['value']
                    self.publish_payload({'message': 'ancient_ones', 'value': None}, 'server_update')

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