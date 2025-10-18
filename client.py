import arcade
import threading
import signal
import argparse
from python_banyan.banyan_base import BanyanBase
from screens.hub_screen import HubScreen
from screens.select_screen import SelectionScreen

# Screen title and size
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 800
SCREEN_TITLE = "ELDRITCH HORROR"

class Networker(threading.Thread, BanyanBase):
    def __init__(self, back_plane_ip_address=None, process_name=None, player=0):
        threading.Thread.__init__(self)
        self.window = None
        self.the_lock = threading.Lock()
        self.daemon = True
        self.run_the_thread = threading.Event()
        self.run_the_thread = True
        self.select_screen = None
        self.game_screen = None
        self.investigator = None
        BanyanBase.__init__(self, back_plane_ip_address=back_plane_ip_address,
            process_name=process_name, loop_time=.0001)
        #self.set_subscriber_topic('akachi_onyele_server')
        self.start()

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
            #'''
            message = payload['message']
            match topic:
                case 'server_update':
                    match message:
                        case 'ancient_ones' | 'investigators' | 'number_select':
                            self.select_screen = SelectionScreen(message, self)
                            if (message == 'investigators'):
                                for name in payload['value']:
                                    self.select_screen.remove_option(name)
                            self.window.pop_handlers()
                            self.window.show_view(self.select_screen)
                        case 'investigator_selected':
                            self.select_screen.remove_option(payload['value'])
                        case 'start_game':
                            self.game_screen = HubScreen(self, self.investigator, payload['value'], payload['investigators'])
                            self.window.pop_handlers()
                            self.window.show_view(self.game_screen)
            #'''
            #self.window.show_view(HubScreen(self, 'akachi_onyele', 'azathoth'))

    def show_select(self, names):
        self.select_screen = SelectionScreen('investigators', self, True)
        for name in names:
            self.select_screen.remove_option(name)
        self.window.show_view(self.select_screen)

    def restart(self):
        pass

def set_up_network():
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
                'player': int(args.player)}

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
    networker = set_up_network()
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    networker.window = window
    networker.set_subscriber_topic('server_update')
    networker.publish_payload({'message': 'get_login_state', 'value': None}, 'login')
    arcade.run()

if __name__ == '__main__':
    main()