import arcade, threading, signal, argparse, requests
import threading
import signal
import argparse
from python_banyan.banyan_base import BanyanBase
from screens.hub_screen import HubScreen
from screens.select_screen import SelectionScreen
from screens.home_screen import HomeScreen
from server import Server

# Screen title and size
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 800
SCREEN_TITLE = "ELDRITCH HORROR"

class Networker(threading.Thread, BanyanBase):
    def __init__(self, back_plane_ip_address=None, process_name=None, player=0, window=None):
        threading.Thread.__init__(self)
        self.window = window
        self.the_lock = threading.Lock()
        self.daemon = True
        self.run_the_thread = threading.Event()
        self.run_the_thread = True
        self.select_screen = None
        self.game_screen = None
        self.investigator = None
        self.ancient_one = None
        BanyanBase.__init__(self, back_plane_ip_address=back_plane_ip_address,
            process_name=process_name, loop_time=.0001)
        self.start()
        self.window.pop_handlers()
        self.select_screen = SelectionScreen('ancient_ones' if int(player) == 0 else 'investigators', self)
        self.window.show_view(self.select_screen)
        self.set_subscriber_topic('server_update')
        if (int(player) != 0):
            self.publish_payload({'message': 'get_investigators'}, 'login')

    # Process banyan subscribed messages
    def run(self):
        """
        This thread continually attempts to receive
        incoming Banyan messages. If a message is received,
        incoming_message_processing is called to handle
        the message.

        """
        # start the banyan loop - incoming messages will be processed
        # by incoming_message_processing in this thread.
        self.receive_loop()

    def incoming_message_processing(self, topic, payload):
        if self.external_message_processor:
            self.external_message_processor(topic, payload)
        else:
            message = payload['message']
            if message == 'chosen_investigators':
                if payload.get('ancient_one', False):
                    self.select_screen.select_ao(payload['ancient_one'])
                for investigator in payload['value']:
                    self.select_screen.investigator_selected(investigator)
            elif message == 'start_game':
                self.game_screen = HubScreen(self, self.investigator, payload['value'], payload['investigators'])
                self.window.pop_handlers()
                self.window.show_view(self.game_screen)

    def show_select(self, names):
        self.select_screen = SelectionScreen('investigators', self, True)
        for name in names:
            self.select_screen.investigator_selected(name)
        self.window.pop_handlers()
        self.window.show_view(self.select_screen)

    def restart(self):
        pass

def set_up_network(ip_address="None", player="1"):
    parser = argparse.ArgumentParser()
    # allow user to bypass the IP address auto-discovery.
    # This is necessary if the component resides on a computer
    # other than the computing running the backplane.
    parser.add_argument("-b", dest="back_plane_ip_address", default=ip_address,
                        help="None or Common Backplane IP address")
    parser.add_argument("-n", dest="process_name", default="Arcade p2p",
                        help="Banyan Process Name Header Entry")
    parser.add_argument("-p", dest="player", default=player,
                        help="Select player 0 or 1")

    args = parser.parse_args()

    if args.back_plane_ip_address == 'None':
        args.back_plane_ip_address = None
    kw_options = {'back_plane_ip_address': args.back_plane_ip_address,
                'process_name': args.process_name + ' player' + str(args.player),
                'player': int(args.player)}

    return kw_options

# signal handler function called when Control-C occurs
# noinspection PyUnusedLocal,PyUnusedLocal
def signal_handler(sig, frame):
    print('Exiting Through Signal Handler')
    raise KeyboardInterrupt

# listen for SIGINT
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def start_server(window):
    ip = requests.get('https://checkip.amazonaws.com').text.strip()
    args = set_up_network(ip_address=ip, player="0")
    Server(**args)
    Networker(**args, window=window)

def join_game(ip_address, window):
    args = set_up_network(ip_address)
    Networker(**args, window=window)

def main():
    arcade.load_font(':resources:fonts/ttf/Garamond Eldritch.ttf')
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    window.show_view(HomeScreen(start_server, join_game, window))
    arcade.run()

if __name__ == '__main__':
    main()