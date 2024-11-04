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
REFERENCES = { #gates, clues, surge
    1: [1, 1, 1],
    2: [1, 2, 2],
    3: [2, 3, 2],
    4: [2, 4, 3]
}
with open('small_cards/server_spells.yaml') as stream:
    SPELLS = yaml.safe_load(stream)
with open('locations/server_locations.yaml') as stream:
    LOCATIONS = yaml.safe_load(stream)
with open('small_cards/server_assets.yaml') as stream:
    ASSETS = yaml.safe_load(stream)
with open('small_cards/server_conditions.yaml') as stream:
    CONDITIONS = yaml.safe_load(stream)
with open('investigators/server_investigators.yaml') as stream:
    INVESTIGATORS = yaml.safe_load(stream)
with open('monsters/server_monsters.yaml') as stream:
    MONSTERS = yaml.safe_load(stream)
with open('small_cards/server_artifacts.yaml') as stream:
    ARTIFACTS = yaml.safe_load(stream)

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
        self.ready_count = 0
        self.reference = None
        self.lead_investigator = 0
        self.current_player = 0
        self.current_phase = 0
        self.phases = ['action', 'encounter', 'reckoning', 'mythos']
        self.yellow_card = False

        self.ancient_one = None
        self.mythos_deck = [{},{},{}]
        self.omen = 0

        self.decks = {
            'conditions': {},
            'used_artifacts': [],
            'unique_assets': {},
            'spells': {},
            'clues': [],
            'gates': {
                'deck': [],
                'discard': [],
                'board': []
            },
            'monsters': [],
            'epic_monsters': []
        }
        self.assets = {
            'deck': [],
            'discard': [],
            'reserve': []
        }
        self.encounters = {
            'green': [8, list(range(8))],
            'orange': [8, list(range(8))],
            'purple': [8, list(range(8))],
            #'generic': [12, list(range(12))],
            'generic': [1, list(range(1))],
            'the_amazon': [3, list(range(3))],
            'the_pyramids': [3, list(range(3))],
            'the_heart_of_africa': [3, list(range(3))],
            'antarctica': [3, list(range(3))],
            'tunguska': [3, list(range(3))],
            'the_himalayas': [3, list(range(3))]
        }
        self.expeditions = ['the_amazon', 'the_pyramids', 'the_heart_of_africa', 'antarctica', 'tunguska', 'the_himalayas']

        for map in LOCATIONS.keys():
            for location in LOCATIONS[map].keys():
                self.decks['clues'].append(map + ':' + location)
                if LOCATIONS[map][location] != None:
                    self.decks['gates']['deck'].append(map + ':' + location)

        for key in SPELLS.keys():
            self.decks['spells'][key] = list(range(1, int(SPELLS[key]['variants']) + 1))

        for key in CONDITIONS.keys():
            self.decks['conditions'][key] = list(range(1, int(CONDITIONS[key]['variants']) + 1))

        for key in ASSETS.keys():
            self.assets['deck'].append(key)

        for key in MONSTERS.keys():
            if MONSTERS[key] != None:
                self.decks['epic_monsters'].append(key)
            else:
                self.decks['monsters'].append(key)

        self.triggers = {}
        self.action_dict = {
            'strengthen_ao': self.strengthen_ao
        }

        # temporary variables set for testing - DELETE LATER
        self.set_subscriber_topic('akachi_onyele')
        self.selected_investigators = ['akachi_onyele']
        self.reference = REFERENCES[1]
        self.player_count = 1
        with open('ancient_ones/server_ancient_ones.yaml') as stream:
            self.ancient_one = yaml.safe_load(stream)['azathoth']
        self.ancient_one['name'] = 'azathoth'
        self.ancient_one['mythos'] = [['0'],['1'],['2']]
        self.mythos_setup()
        for effects in self.ancient_one['effects']:
            if effects['kind'] == 'trigger':
                self.triggers[effects['condition']] = {
                    'action': effects['action'],
                    'args': effects['args']
                }


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
                    with open('ancient_ones/server_ancient_ones.yaml') as stream:
                        ancient_one = yaml.safe_load(stream)[payload['value']]
                    self.ancient_one = ancient_one
                    self.ancient_one['name'] = payload['value']
                    self.screen.select_ao(self.ancient_one.name)
                    self.mythos_setup()
                    for effects in self.ancient_one['effects']:
                        if effects['kind'] == 'trigger':
                            self.triggers[effects['condition']] = {
                                'action': effects['action'],
                                'args': effects['args']
                            }
                    self.publish_payload({'message': 'investigators', 'value': payload['value']}, 'server_update')
                case 'investigators_selected':
                    self.selected_investigators.append(payload['value'])
                    self.set_subscriber_topic(payload['value'])
                    self.screen.add_investigator(payload['value'])
                    if len(self.selected_investigators) == self.player_count:
                        self.publish_payload({'message': 'start_game', 'value': self.ancient_one.name}, 'server_update')
                    else:
                        self.publish_payload({'message': 'investigator_selected', 'value': payload['value']}, 'server_update')
                case 'number_selected':
                    self.player_count = payload['value']
                    self.reference = REFERENCES[int((int(payload['value']) + 1) / 2)]
                    self.publish_payload({'message': 'ancient_ones', 'value': None}, 'server_update')
                case 'ready':
                    #self.ready_count += 1
                    #if self.ready_count == self.player_count:
                    #    self.initiate_gameboard()
                    #    self.ready_count = 0
                    #    self.publish_payload({'message': 'choose_lead', 'value': None}, 'server_update')
                    #FOR TESTING
                    self.lead_investigator = 0
                    self.current_player = 0
                    self.current_phase = 0
                    #END TESTING
                    self.initiate_gameboard()
                    self.publish_payload({'message': 'choose_lead', 'value': None}, 'server_update')
        elif topic in self.selected_investigators:
            if payload['message'] in ['spells', 'conditions']:
                item = self.variant_request(payload['message'], payload['value'], payload['command'])
                if item != None:
                    self.publish_payload({'message': payload['message'], 'value': item}, topic + '_server')
            else:
                match payload['message']:
                    case 'assets':
                        item = self.asset_request(payload['command'], payload['value'], payload['tag'])
                        if item != None:
                            self.publish_payload({'message': 'asset', 'value': item}, topic + '_server')
                    case 'artifacts':
                        name = payload['value'] if payload['value'] != None else ''
                        tag = payload['tag'] if payload['tag'] != None else ''
                        item = self.get_artifact(name, tag)
                        if item != None:
                            self.publish_payload({'message': 'artifact', 'value': item}, topic + '_server')
                    case 'spawn':
                        self.spawn(payload['value'], payload['name'], payload['location'], int(payload['number']))
                    case 'move_investigator':
                        self.publish_payload({'message': 'investigator_moved', 'value': payload['value'], 'destination': payload['destination']}, 'server_update')
                    case 'lead_selected':
                        self.lead_investigator = self.selected_investigators.index(payload['value'])
                        self.current_player = self.selected_investigators.index(payload['value'])
                        self.publish_payload({'message': 'lead_selected', 'value': payload['value']}, 'server_update')
                        self.publish_payload({'message': 'player_turn', 'value': 'action'}, payload['value'] + '_server')
                    case 'turn_finished':
                        self.current_player += 1
                        if self.current_player == len(self.selected_investigators):
                            self.current_player = 0
                        if self.current_player == self.lead_investigator:
                            self.current_phase += 1
                            if self.current_phase == 2:
                                for x in range(3):
                                    if len(self.mythos_deck[x]) > 0:
                                        mythos = random.choice(list(self.mythos_deck[x].keys()))
                                        self.publish_payload({'message': 'mythos', 'value': mythos}, 'server_update')
                                        kind = self.mythos_deck[x][mythos]
                                        if kind == 0:
                                            self.current_phase += 1
                                            self.set_omen()
                                            self.monster_surge()
                                            self.spawn('clues', number=self.reference[1])
                                        elif kind == 1:
                                            self.set_omen()
                                            self.yellow_card = True
                                        elif kind == 2:
                                            self.current_phase += 1
                                            self.spawn('clues', number=self.reference[1])
                                        del self.mythos_deck[x][mythos]
                                        break
                                #Trigger no mythos deck
                        if self.current_phase == 3 and self.yellow_card:
                            self.spawn('gates', number=self.reference[0])
                            self.yellow_card = False
                        if self.current_phase == 4:
                            self.current_phase = 0
                            self.publish_payload({'message': 'choose_lead', 'value': None}, 'server_update')
                        else:
                            self.publish_payload({'message': 'player_turn', 'value': self.phases[self.current_phase]},
                                                 self.selected_investigators[self.current_player] + '_server')
                    case 'get_encounter':
                        kind = payload['value']
                        #encounter = random.choice(self.encounters[kind][1])
                        #self.encounters[kind][1].remove(encounter)
                        encounter = 0
                        if len(self.encounters[kind][1]) == 0:
                            self.encounters[kind][1] = list(range(self.encounters[kind][0]))
                        if kind in self.expeditions:
                            self.spawn('expedition')
                        self.publish_payload({'message': 'encounter_choice', 'value': kind + ':' + str(encounter)}, topic + '_server')
                    case 'mythos_finished':
                        self.ready_count += 1
                        if self.ready_count == self.player_count:
                            self.current_phase = 0
                            self.publish_payload({'message': 'choose_lead', 'value': None}, 'server_update')
                            self.ready_count = 0

    def asset_request(self, command, name, tag=''):
        match command:
            case 'acquire':
                self.restock_reserve([name])
                return name
            case 'restock':
                self.restock_reserve([name], True)
            case 'discard':
                self.assets['discard'].append(name)
                self.publish_payload({'message': 'asset', 'discard': name}, 'server_update')
            case 'get':
                if name != '':
                    self.assets['deck'].remove(name)
                    return name
                elif tag != '':
                    name = random.choice([item for item in self.assets['deck'] if tag in ASSETS[item]['tags']])
                    self.assets['deck'].remove(name)
                    return name

    def variant_request(self, cardtype, name, command):
        if command == 'get':
            variant = random.choice(self.decks[cardtype][name])
            #self.decks[cardtype][name].remove(variant)
            return name + str(variant)
        elif command == 'discard':
            self.decks[cardtype][name[0:-1]].append(name[-1])
            return None
        
    def get_artifact(self, name, tag):
        if name != '' and name not in self.decks['used_artifacts']:
            self.decks['used_artifacts'].append(name)
            return name
        else:
            artifacts = [card for card in ARTIFACTS if tag == '' or tag in ARTIFACTS[card]['tags']]
            artifact = random.choice(artifacts)
            self.decks['used_artifacts'].append(artifact)
            return artifact
        
    def monster_surge(self):
        colors = ['green', 'blue', 'red', 'blue']
        for gates in self.decks['gates']['board']:
            world = gates.split(':')[0]
            loc = gates.split(':')[1]
            if LOCATIONS[world][loc] == colors[self.omen]:
                self.spawn('monsters', location=gates, number=self.reference[2])

    def spawn(self, piece, name=None, location=None, number=1):
        match piece:
            case 'gates':
                for x in range(0, number):
                    if location != None and location in self.decks['gates']['deck']:
                        #self.decks['gates']['deck'].remove(location)
                        self.decks['gates']['board'].append(location)
                        self.publish_payload({'message': 'spawn', 'value': 'gate', 'location': location.split(':')[1], 'map': location.split(':')[0]}, 'server_update')
                        self.spawn('monsters', location=location)
                    elif location == None:
                        if len(self.decks['gates']['deck']) > 0:
                            #gate = random.choice(self.decks['gates']['deck'])
                            gate = 'world:sydney'
                            #self.decks['gates']['deck'].remove(gate)
                            self.decks['gates']['board'].append(gate)
                            self.publish_payload({'message': 'spawn', 'value': 'gate', 'location': gate.split(':')[1], 'map': gate.split(':')[0]}, 'server_update')
                            self.spawn('monsters', location=gate)
                        elif len(self.decks['gates']['discard']) > 0:
                            self.decks['gates']['deck'].append(item for item in self.decks['gates']['discard'])
                            self.decks['gates']['discard'] = []
                            self.spawn('gates')
                        else:
                            #advance doom
                            pass
            case 'clues':
                for x in range(0, number):
                    token = random.choice(self.decks[piece])
                    token = 'world:space_1'
                    #self.decks[piece].remove(token)
                    self.publish_payload({'message': 'spawn', 'value': 'clue', 'location': token.split(':')[1], 'map': token.split(':')[0]}, 'server_update')
            case 'monsters':
                for x in range(0, number):
                    monster = random.choice(self.decks['monsters'])
                    #self.decks['monsters'].remove(monster)
                    self.publish_payload({'message': 'spawn',
                                        'value': 'monster',
                                        'location': location.split(':')[1],
                                        'map': location.split(':')[0],
                                        'name': monster
                                        },
                                        'server_update')
            case 'expedition':
                locations = [loc for loc in self.expeditions if len(self.encounters[loc][1]) > 0]
                location = random.choice(locations)
                self.publish_payload({'message': 'spawn', 'value': 'expedition', 'location': location, 'map': 'world'}, 'server_update')

    def initiate_gameboard(self):
        self.current_phase = 0
        self.current_player = 0
        kinds = ['gates', 'clues']
        self.spawn('expedition')
        for i in range(len(kinds)):
            self.spawn(kinds[i], self.reference[i])
        self.restock_reserve()
        for x in self.selected_investigators:
            self.publish_payload({'message': 'spawn', 'value': 'investigator', 'name': x, 'location': INVESTIGATORS[x]['location'], 'map': 'world'}, 'server_update')

    def restock_reserve(self, removed=[], discard=False):
        removed_items = ':'.join(removed)
        for item in removed:
            #self.assets['reserve'].remove(item)
            if discard:
                self.assets['discard'].append(item)
                self.publish_payload({'message': 'discard', 'value': item}, 'server_update')
        items = ''
        for i in range(0, 4 - len(self.assets['reserve'])):
            item = random.choice(self.assets['deck'])
            #self.assets['deck'].remove(item)
            #self.assets['reserve'].append(item)
            items += item + ':'
        self.publish_payload({'message': 'restock', 'value': items[0:-1], 'removed': removed_items}, 'server_update')

    def mythos_setup(self):
        with open('ancient_ones/server_mythos.yaml') as stream:
            cards = yaml.safe_load(stream)
        for x in range(3):
            for character in self.ancient_one['mythos'][x]:
                card = random.choice(list(cards[int(character)].keys()))
                self.mythos_deck[x][card] = int(character)
                del cards[int(character)][card]

    def set_omen(self, pos=None, trigger=True):
        if pos != None:
            self.omen = pos
        else:
            self.omen += 1
            if self.omen == 4:
                self.omen = 0
        if trigger:
            if hasattr(self.triggers, 'omen' + str(self.omen)):
                triggers = self.triggers['omen' + str(self.omen)]
                for effects in triggers:
                    triggers[effects]['action'](**triggers[effects]['args'])
            colors = ['green', 'blue', 'red', 'blue']
            adv_doom = 0
            for gates in self.decks['gates']['board']:
                world = gates.split(':')[0]
                loc = gates.split(':')[1]
                if LOCATIONS[world][loc] == colors[self.omen]:
                    adv_doom -= 1
            self.move_doom(adv_doom)
        self.publish_payload({'message': 'omen', 'value': self.omen}, 'server_update')

    def move_doom(self, amt=-1):
        self.ancient_one['doom'] += amt
        self.publish_payload({'message': 'doom', 'value': self.ancient_one['doom']}, 'server_update')
    
    def strengthen_ao(self, amt=1):
        self.ancient_one.eldritch += amt

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