import arcade, threading, sys, subprocess, signal, argparse, yaml, random, math
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
        self.reference = None
        self.lead_investigator = 0
        self.current_player = 0
        self.current_phase = 0
        self.phases = ['action', 'encounter', 'reckoning', 'mythos']
        self.yellow_card = False

        self.ancient_one = None
        self.mythos_deck = [{},{},{}]
        self.mysteries = {}
        self.solved_mysteries = []
        self.omen = 0
        self.expedition = None

        self.decks = {
            'conditions': [],
            'used_artifacts': [],
            'unique_assets': {},
            'spells': [],
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
            'generic': [12, list(range(12))],
            'the_amazon': [3, list(range(3))],
            'the_pyramids': [3, list(range(3))],
            'the_heart_of_africa': [3, list(range(3))],
            'antarctica': [3, list(range(3))],
            'tunguska': [3, list(range(3))],
            'the_himalayas': [3, list(range(3))],
            'gate': [24, list(range(24))]
        }
        self.expeditions = ['the_amazon', 'the_pyramids', 'the_heart_of_africa', 'antarctica', 'tunguska', 'the_himalayas']
        self.monster_id = 0
        self.monsters = []
        self.investigators = {}
        self.dead_investigators = {}
        self.rumors = []
        self.temporary_lead = None

        for map in LOCATIONS.keys():
            for location in LOCATIONS[map].keys():
                self.decks['clues'].append(map + ':' + location)
                if LOCATIONS[map][location] != None:
                    self.decks['gates']['deck'].append(map + ':' + location)

        for key in SPELLS.keys():
            for x in range(int(SPELLS[key]['variants'])):
                self.decks['spells'].append(key + str(x+1))

        for key in CONDITIONS.keys():
            for x in range(int(CONDITIONS[key]['variants'])):
                self.decks['conditions'].append(key + str(x+1))

        for key in ASSETS.keys():
            self.assets['deck'].append(key)

        for key in MONSTERS.keys():
            count = MONSTERS[key].get('count', 1)
            is_epic = MONSTERS[key].get('epic', False)
            if is_epic:
                self.decks['epic_monsters'].append(key)
            else:
                for x in range(count):
                    self.decks['monsters'].append(key)

        self.triggers = {}
        self.action_dict = {
            'strengthen_ao': self.strengthen_ao,
            'heal_monsters': self.heal_monsters,
            'spawn': self.spawn,
            'move_doom': self.move_doom,
            'discard_gates': self.discard_gates,
            'restock_reserve': self.restock_reserve,
            'on_reckoning': self.on_reckoning,
            'lose_game': self.lose_game,
            'solve_rumor': self.solve_rumor,
            'discard_cost': self.discard_cost,
            'mythos_reckoning': self.mythos_reckoning,
            'from_beyond': self.from_beyond,
            'set_payment': self.set_payment
        }
        self.omen_cycle = ['green', 'blue', 'red', 'blue']
        self.mythos = None
        self.reckoning_actions = []
        self.payment_needed = 0
        self.players_died = False

        '''
        #FOR TESTING
        self.set_subscriber_topic('akachi_onyele')
        self.selected_investigators = ['akachi_onyele']
        self.reference = REFERENCES[1]
        self.player_count = 1
        with open('ancient_ones/server_ancient_ones.yaml') as stream:
            self.ancient_one = yaml.safe_load(stream)['azathoth']
        self.ancient_one['name'] = 'azathoth'
        self.mythos_setup()
        for effects in self.ancient_one['effects']:
            if effects['kind'] == 'trigger':
                self.triggers[effects['condition']] = {
                    'action': effects['action'],
                    'args': effects['args']
                }
        self.is_first = True
        #END TESTING
        '''
        self.is_first = True

        self.get_locations = {
            'cultists': lambda: list(set(monster['location'] for monster in self.monsters if monster['name'] == 'cultist')),
            'gate_omen': lambda: [gate for gate in self.decks['gates']['board'] if LOCATIONS[gate.split(':')[0]][gate.split(':')[1]] == self.omen_cycle[self.omen]]
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
                    self.screen.select_ao(payload['value'])
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
                    self.investigators[payload['value']] = {
                        'assets':[], 'conditions': [], 'artifacts': [], 'unique_assets':[], 'spells':[], 'hp': 0, 'san': 0, 'clues': [], 'paid': -1, 'tickets': (0,0)}
                    self.set_subscriber_topic(payload['value'])
                    self.screen.add_investigator(payload['value'])
                    if self.players_died and len(self.selected_investigators) == self.player_count:
                        self.end_mythos()
                    else:          
                        if len(self.selected_investigators) == self.player_count:
                            self.publish_payload({'message': 'start_game', 'value': self.ancient_one['name']}, 'server_update')
                        else:
                            self.publish_payload({'message': 'investigator_selected', 'value': payload['value']}, 'server_update')
                case 'number_selected':
                    self.player_count = payload['value']
                    self.reference = REFERENCES[int((int(payload['value']) + 1) / 2)]
                    self.publish_payload({'message': 'ancient_ones', 'value': None}, 'server_update')
                case 'ready':
                    self.current_player += 1
                    if self.current_player == self.player_count:
                        self.initiate_gameboard()
                        self.publish_payload({'message': 'choose_lead', 'value': None}, 'server_update')
                    '''
                    #FOR TESTING
                    self.lead_investigator = 0
                    self.current_player = 0
                    self.current_phase = 0
                    self.ancient_one['mythos'] = [{},{},{}]
                    self.mythos_setup()
                    self.ancient_one['doom'] = 15
                    self.decks['gates']['board'] = []
                    self.is_first = True
                    self.assets = {
                        'deck': self.assets['deck'],
                        'discard': self.assets['discard'],
                        'reserve': []
                    }
                    self.investigators['akachi_onyele'] = {'tickets': (0,0), 'assets':[], 'conditions': [], 'artifacts': [], 'unique_assets':[], 'spells':[], 'hp': 0, 'san': 0, 'clues': ['world:arkham'], 'paid': -1}
                    self.initiate_gameboard()
                    self.publish_payload({'message': 'choose_lead', 'value': None}, 'server_update')
                    #END TESTING
                    '''
        elif topic in self.selected_investigators:
            if payload['message'] in ['spells', 'conditions']:
                ref = SPELLS if payload['message'] == 'spells' else CONDITIONS
                kind = payload['message']
                tag = payload.get('tag', '')
                name = payload.get('value', '')
                owned = payload.get('owned', '')
                items = [card for card in self.decks[kind] if (name == '' or name in card) and (tag == '' or tag in ref[card[:-1]]['tags']) and (owned == '' or card[:-1] not in owned)]
                item = random.choice(items)
                #self.decks[kind].remove(item)
                self.investigators[topic][kind].append(item)
                self.publish_payload({'message': payload['message'], 'value': item}, topic + '_server')
            else:
                match payload['message']:
                    case 'assets':
                        item = self.asset_request(payload['command'], payload['value'], payload['tag'])
                        if item != None:
                            self.investigators[topic]['assets'].append(item)
                            self.publish_payload({'message': 'asset', 'value': item}, topic + '_server')
                    case 'artifacts':
                        name = payload['value'] if payload['value'] != None else ''
                        tag = payload['tag'] if payload['tag'] != None else ''
                        item = self.get_artifact(name, tag)
                        if item != None:
                            self.investigators[topic]['artifacts'].append(item)
                            self.publish_payload({'message': 'artifacts', 'value': item}, topic + '_server')
                    case 'card_discarded':
                        if payload['kind'] == 'assets':
                            self.assets['discard'].append(payload['value'])
                            self.publish_payload({'message': 'discard', 'value': payload['value']}, 'server_update')
                        elif payload['kind'] == 'artifacts':
                            self.decks['used_artifacts'].append(payload['value'])
                        else:
                            self.decks[payload['kind']].append(payload['value'])
                        if payload['value'] in self.investigators[topic][payload['kind']]:
                            self.investigators[topic][payload['kind']].remove(payload['value'])
                        elif payload['kind'] == 'clues':
                            self.publish_payload({'message': 'token_removed', 'value': payload['value'], 'kind': 'clue'}, 'server_update')
                    case 'get_clue':
                        clue = random.choice(self.decks['clues'])
                        #self.decks['clues'].remove(clue)
                        self.investigators[topic]['clues'].append(clue)
                        self.publish_payload({'message': 'receive_clue', 'value': clue}, topic + '_server')
                    case 'spawn':
                        self.spawn(payload['value'], payload.get('name', None), payload.get('location', None), int(payload.get('number', 1)))
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
                                        name = random.choice(list(self.mythos_deck[x].keys()))
                                        #FOR TESTING
                                        if self.is_first:
                                            name = 'heat_wave_singes_the_globe'
                                            self.is_first = False
                                        else:
                                            name = 'mysterious_lights'
                                        #END TESTING
                                        if name == None:
                                            break
                                        self.mythos = self.mythos_deck[x][name]
                                        self.publish_payload({'message': 'mythos', 'value': name}, 'server_update')
                                        kind = self.mythos['color']
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
                                        #del self.mythos_deck[x][name]
                                        break
                        if self.current_phase == 2:
                            self.mythos_reckoning()
                        if self.current_phase == 3:
                            if self.yellow_card:
                                self.spawn('gates', number=self.reference[0])
                                self.yellow_card = False
                            if self.mythos.get('actions', None) != None:
                                for x in range(len(self.mythos['actions'])):
                                    if self.mythos.get('args', None) != None:
                                        self.action_dict[self.mythos['actions'][x]](**self.mythos['args'][x])
                                    else:
                                        self.action_dict[self.mythos['actions'][x]]()
                        if self.current_phase == 4:
                            self.end_mythos()
                        else:
                            topic = ''
                            if self.current_phase == 2 and self.mythos != None and self.mythos.get('lead_only', None) != None:
                                topic = 'server_update'
                            else:
                                topic = self.selected_investigators[self.current_player] + '_server'
                            self.publish_payload({'message': 'player_turn', 'value': self.phases[self.current_phase]}, topic)
                    case 'get_encounter':
                        kind = payload['value']
                        encounter = random.choice(self.encounters[kind][1])
                        self.encounters[kind][1].remove(encounter)
                        if len(self.encounters[kind][1]) == 0:
                            self.encounters[kind][1] = list(range(self.encounters[kind][0]))
                        if kind in self.expeditions:
                            self.spawn('expedition')
                        self.publish_payload({'message': 'encounter_choice', 'value': kind + ':' + str(encounter)}, topic + '_server')
                    case 'doom_change':
                        self.move_doom(int(payload['value']))
                    case 'remove_gate':
                        self.discard_gates(payload['value'])
                    case 'damage_monster':
                        self.server_damage_monster(int(payload['damage']), int(payload['value']))
                        self.publish_payload({'message': 'monster_damaged', 'value': payload['value'], 'damage': payload['damage']}, 'server_update')
                    case 'solve_rumor':
                        rumor = next((rumor for rumor in self.reckoning_actions if rumor['name'] == payload['value']), None)
                        if rumor != None:
                            self.solve_rumor(rumor)
                    case 'payment_made':
                        self.investigators[topic]['paid'] = int(payload['value'])
                    case 'payment_info':
                        payments = self.calc_group_payments(topic, payload['kind'])
                        self.publish_payload({'message': 'group_pay_update', 'max': payments[1], 'min': payments[0], 'kind': payload['kind']}, topic + '_server')
                    case 'end_mythos':
                        self.end_mythos()
                    case 'shuffle_mystery':
                        self.shuffle_mystery()
                    case 'move_monster':
                        self.publish_payload({'message': 'monster_moved', 'value': payload['value'], 'location': payload['location']}, 'server_update')
                        index = next((i for i, monster in enumerate(self.monsters) if monster['monster_id'] == int(payload['value'])), None)
                        chosen = self.monsters[index]
                        chosen['location'] = payload['location']
                    case 'mythos_reckoning':
                        self.mythos_reckoning(payload['value'], True)
                    case 'update_hpsan':
                        self.investigators[topic]['hp'] = payload['hp']
                        self.investigators[topic]['san'] = payload['san']
                        if self.investigators[topic]['hp'] <= 0 or self.investigators[topic]['san'] <= 0:
                            self.players_died = True
                            player = topic
                            current_lead = self.selected_investigators[self.lead_investigator]
                            if current_lead == player:
                                self.temporary_lead =  self.lead_investigator + 1 if len(self.selected_investigators) - 1 != self.lead_investigator else 0
                                self.publish_payload({'message': 'lead_selected', 'value': self.selected_investigators[self.lead_investigator], 'dead_trigger': True}, 'server_update')
                            self.dead_investigators[player] = {}
                            possessions_string = ''
                            for keys in [key for key in self.investigators[player].keys() if key in ['assets', 'unique_assets', 'spells', 'clues', 'tickets', 'artifacts']]:
                                self.dead_investigators[player][keys] = self.investigators[player][keys]
                                for item in self.investigators[player][keys]:
                                    if keys != 'tickets':
                                        possessions_string += keys + ':' + item
                                    else:
                                        possessions_string += 'rail:' + str(self.investigators[player]['tickets'][0])
                                        possessions_string += 'ship:' + str(self.investigators[player]['tickets'][1])
                            self.publish_payload({'message': 'investigator_death', 'possessions': possessions_string, 'value': topic, 'location': payload['location']}, 'server_update')
                            del self.investigators[player]
                            self.move_doom()
                    case 'update_tickets':
                        tickets = (payload['rail'], payload['ship'])
                        self.investigators[topic]['tickets'] = tickets

    def end_mythos(self):
        if not self.players_died:
            self.temporary_lead = None
            self.current_phase = 0
            self.payment_needed = 0
            self.players_died = False
            for investigator in self.investigators.keys():
                self.investigators[investigator]['paid'] = -1
            self.publish_payload({'message': 'choose_lead', 'value': None}, 'server_update')
        else:
            for player in [key for key in self.dead_investigators.keys() if key in self.selected_investigators]:
                self.selected_investigators.remove(player)
            self.publish_payload({'message': 'choose_new'}, 'server_update')

    def on_reckoning(self, args):
        self.reckoning_actions.append(args)

    def lose_game(self):
        pass

    def from_beyond(self):
        if len(self.reckoning_actions) == 0:
            self.move_doom()
        else:
            self.publish_payload({'message': 'mythos_switch'}, 'server_update')
            self.set_payment('investigators', divisor=2)

    def set_payment(self, kind, divisor=1):
        number = 0
        if kind == 'investigators':
            number = len(self.selected_investigators)
        elif kind == 'gates':
            number = len(self.decks['gates']['board'])
        self.payment_needed = math.ceil(number / divisor)

    def mythos_reckoning(self, number=1, doom=False):
        if doom and len(self.reckoning_actions) == 0:
            self.move_doom()
        else:
            for x in range(number):
                for actions in self.reckoning_actions:
                    action = actions.get('action', None)
                    if action != None:
                        if actions.get('args', None) != None:
                            self.action_dict[actions['action']](actions.get('args', None))
                        else:
                            self.action_dict[actions['action']]()
                    if not actions.get('recurring', True):
                        self.reckoning_actions.remove(actions)
                    else:
                        tokens = 1
                        if actions.get('rargs', None) != None:
                            tokens = self.rumor_tick(**actions['rargs'])
                        actions['recurring'] -= tokens
                        if actions['recurring'] <= 0:
                            if actions.get('unsolve', None) != None:
                                self.action_dict[actions['unsolve']](**actions['unsolve_args'])
                            self.solve_rumor(actions, False)
                        else:
                            self.publish_payload({'message': 'update_rumor', 'name': actions['name'], 'value': actions['recurring']}, 'server_update')

    def rumor_tick(self, count, divisor=1):
        tick = 0
        if count == 'gates':
            tick = len(self.decks['gates']['board'])
        elif count == 'lead_madness':
            lead = self.selected_investigators[self.lead_investigator]
            owned = [card[:-1] for card in self.investigators[lead]['conditions']]
            condition = random.choice([card for card in self.decks['conditions'] if ('madness' in CONDITIONS[card[:-1]]['tags']) and (card[:-1] not in owned)])
            #self.decks['conditions'].remove(condition)
            self.investigators[lead]['conditions'].append(condition)
            self.publish_payload({'message': 'conditions', 'value': condition}, lead + '_server')
            tick = len([card for card in owned if 'madness' in CONDITIONS[card]['tags']]) + 1
        return math.ceil(tick / divisor)

    def solve_rumor(self, rumor, solved=True):
        self.publish_payload({'message': 'rumor_solved', 'value': rumor['name'], 'solved': solved}, 'server_update')
        self.reckoning_actions.remove(rumor)

    def discard_gates(self, location=None, omen=False):
        locations = self.get_locations['gate_omen']() if omen else [location]
        for loc in locations:
            self.decks['gates']['board'].remove(loc)
            self.decks['gates']['discard'].append(loc)
            self.publish_payload({'message': 'token_removed', 'value': loc, 'kind': 'gate'}, 'server_update')

    def calc_group_payments(self, name, kind):
        has_paid = [investigator for investigator in self.selected_investigators if self.investigators[investigator]['paid'] >= 0]
        not_paid = [investigator for investigator in self.selected_investigators if investigator not in has_paid and investigator != name]
        paid = 0
        for key in has_paid:
            paid += self.investigators[key]['paid']
        max_pay = self.payment_needed - paid
        min_pay = 0
        remaining = 0
        for investigator in not_paid:
            if kind == 'clues':
                remaining += len(self.investigators[investigator]['clues'])
            else:
                remaining += self.investigators[investigator][kind]
        min_pay = max_pay - remaining
        min_pay = 0 if min_pay < 0 else min_pay
        return (min_pay, max_pay)

    def heal_monsters(self, amt):
        self.server_damage_monster(amt)
        self.publish_payload({'message': 'monster_damaged', 'value': -1, 'damage': amt}, 'server_update')

    def server_damage_monster(self, amt, monster_id=None):
        def do_damage(monster, dmg):
            damage = monster['damage'] + dmg
            monster['damage'] = damage if damage >= 0 else damage
            value = 0
            toughness = MONSTERS[monster['name']].get('toughness')
            if '+' in toughness:
                value = self.player_count + len(toughness)
            else:
                value = int(toughness)
            if damage >= value:
                self.monsters.remove(monster)
        if monster_id == None:
            for monster in self.monsters:
                do_damage(monster, amt)
        else:
            index = next((i for i, monster in enumerate(self.monsters) if monster['monster_id'] == monster_id), None)
            chosen = self.monsters[index]
            do_damage(chosen, amt)

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
                    #self.assets['deck'].remove(name)
                    return name
                elif tag != '':
                    name = random.choice([item for item in self.assets['deck'] if tag in ASSETS[item]['tags']])
                    #self.assets['deck'].remove(name)
                    return name

    def variant_request(self, cardtype, name, tag=None, owned=''):
        variant = random.choice(self.decks[cardtype][name])
        #self.decks[cardtype][name].remove(variant)
        return name + str(variant)
        
    def get_artifact(self, name, tag):
        if name != '' and name not in self.decks['used_artifacts']:
            self.decks['used_artifacts'].append(name)
            return name
        else:
            artifacts = [card for card in ARTIFACTS if (tag == '' or tag in ARTIFACTS[card]['tags']) and card not in self.decks['used_artifacts']]
            artifact = random.choice(artifacts)
            self.decks['used_artifacts'].append(artifact)
            return artifact
        
    def monster_surge(self):
        for gates in self.decks['gates']['board']:
            world = gates.split(':')[0]
            loc = gates.split(':')[1]
            if LOCATIONS[world][loc] == self.omen_cycle[self.omen]:
                self.spawn('monsters', location=gates, number=self.reference[2])

    def spawn(self, piece, name=None, location=None, number=1, locations=None):
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
                            #self.decks['gates']['deck'].remove(gate)
                            gate = 'world:arkham'
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
                if location != None:
                    #self.decks[piece].remove(location)
                    self.publish_payload({'message': 'spawn', 'value': 'clue', 'location': location.split(':')[1], 'map': location.split(':')[0]}, 'server_update')
                else:
                    for x in range(number):
                        token = random.choice(self.decks[piece])
                        #self.decks[piece].remove(token)
                        self.publish_payload({'message': 'spawn', 'value': 'clue', 'location': token.split(':')[1], 'map': token.split(':')[0]}, 'server_update')
            case 'monsters':
                def pull_monster(loc):
                    is_epic = False
                    monster = None
                    if name != None:
                        for deck in [self.decks['monsters'], self.decks['epic_monsters']]:
                            if name in deck:
                                monster = name
                                #deck.remove(name)
                                if deck == self.decks['epic_monsters']:
                                    is_epic = True
                    else:
                        monster = random.choice(self.decks['monsters'])
                        #self.decks['monsters'].remove(monster)
                    if monster != None:
                        server_monster = {'name': monster, 'location': loc, 'monster_id': self.monster_id, 'damage': 0, 'is_epic': is_epic}
                        self.monsters.append(server_monster)
                        self.publish_payload({'message': 'spawn',
                                            'value': 'monsters',
                                            'location': loc.split(':')[1],
                                            'map': loc.split(':')[0],
                                            'name': monster,
                                            'monster_id': self.monster_id
                                            },
                                            'server_update')
                        self.monster_id += 1
                if locations != None:
                    for loc in self.get_locations[locations]():
                        pull_monster(loc)
                else:
                    if location == 'expedition':
                        location = 'world:' + self.expedition
                    for x in range(number):
                        pull_monster(location)
            case 'expedition':
                locations = []
                for loc in self.expeditions:
                    for x in range(len(self.encounters[loc])):
                        locations.append(loc)
                self.expedition = random.choice(locations)
                self.publish_payload({'message': 'spawn', 'value': 'expedition', 'location': self.expedition, 'map': 'world'}, 'server_update')
            case 'rumor':
                self.publish_payload({'message': 'spawn', 'value': 'rumor', 'location': location.split(':')[1], 'name': name, 'map': location.split(':')[0]}, 'server_update')

    def initiate_gameboard(self):
        self.current_phase = 0
        self.current_player = 0
        kinds = ['gates', 'clues']
        self.spawn('expedition')
        for i in range(len(kinds)):
            self.spawn(kinds[i], number=self.reference[i])
        self.restock_reserve()
        for x in self.selected_investigators:
            self.publish_payload({'message': 'spawn', 'value': 'investigators', 'name': x, 'location': INVESTIGATORS[x]['location'], 'map': 'world'}, 'server_update')

    def discard_cost(self):
        to_remove = set()
        max_cost = 0
        for item in self.assets['reserve'] + self.assets['discard'] + self.assets['deck']:
            if ASSETS[item]['cost'] > max_cost:
                max_cost = ASSETS[item]['cost']
                to_remove = set()
            if ASSETS[item]['cost'] == max_cost:
                to_remove.add(item)
        self.publish_payload({'message': 'exile_from_discard', 'value': ':'.join([item for item in self.assets['discard'] if item in to_remove])}, 'server_update')
        self.assets['deck'] = [item for item in self.assets['deck'] if item not in to_remove]
        self.restock_reserve([item for item in self.assets['reserve'] if item in to_remove])
        self.assets['discard'] = [item for item in self.assets['discard'] if item not in to_remove]

    def restock_reserve(self, removed=[], discard=False, refill=True, cycle=False):
        if cycle:
            removed = [item for item in self.assets['reserve']]
        removed_items = ':'.join(removed)
        for item in removed:
            self.assets['reserve'].remove(item)
            if discard:
                self.assets['discard'].append(item)
                self.publish_payload({'message': 'discard', 'value': item}, 'server_update')
        items = ''
        if refill:
            for i in range(0, min(4 - len(self.assets['reserve']), len(self.assets['deck']))):
                item = random.choice(self.assets['deck'])
                #self.assets['deck'].remove(item)
                self.assets['reserve'].append(item)
                items += item + ':'
        self.publish_payload({'message': 'restock', 'value': items[0:-1], 'removed': removed_items}, 'server_update')

    def mythos_setup(self):
        with open('ancient_ones/server_mythos.yaml') as stream:
            cards = yaml.safe_load(stream)
        for x in range(3):
            for character in self.ancient_one['mythos'][x]:
                color = int(character)
                card = random.choice(list(cards[color].keys()))
                #FOR TESTING
                #if color == 0:
                #    card = 'legitimate_banking'
                if color == 1:
                    card = 'heat_wave_singes_the_globe'
                if color == 2:
                    card = 'mysterious_lights'
                #END TESTING
                self.mythos_deck[x][card] = cards[color][card]
                self.mythos_deck[x][card]['color'] = color

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
            self.move_doom(gates=True)
        self.publish_payload({'message': 'omen', 'value': self.omen}, 'server_update')

    def move_doom(self, amt=-1, gates=False, all_gates=False):
        if not gates:
            amt = -len(self.get_locations['gate_omen']())
        if all_gates:
            amt = -len(self.decks['gates']['board'])
        self.ancient_one['doom'] += amt
        self.publish_payload({'message': 'doom', 'value': self.ancient_one['doom']}, 'server_update')
    
    def strengthen_ao(self, amt=1):
        self.ancient_one.eldritch += amt

    def shuffle_mystery(self):
        if len(self.solved_mysteries) > 0:
            mystery = random.choice(self.solved_mysteries)
            self.solved_mysteries.remove(mystery)
            self.publish_payload({'message': 'mystery_count', 'value': str(len(self.solved_mysteries))}, 'server_update')
        else:
            self.move_doom()

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