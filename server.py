import arcade, threading, sys, subprocess, signal, argparse, yaml, random, math, copy
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
with open('ancient_ones/server_mythos.yaml') as stream:
    MYTHOS = yaml.safe_load(stream)

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
            'mythos_reckoning': self.mythos_reckoning,
            'from_beyond': self.from_beyond,
            'set_payment': self.set_payment,
            'clear_bodies': self.clear_bodies,
            'move_omen': self.set_omen,
            'discard_cost': self.discard_cost,
            'secrets_of_the_past': self.secrets_of_the_past,
            'spreading_sickness': self.spreading_sickness,
            'web_between_worlds': self.web_between_worlds
        }
        self.omen_cycle = ['green', 'blue', 'red', 'blue']
        self.mythos = None
        self.reckoning_actions = []
        self.end_of_mythos_actions = []
        self.players_died = -1
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
            'gate_omen': lambda: [gate for gate in self.decks['gates']['board'] if LOCATIONS[gate.split(':')[0]][gate.split(':')[1]] == self.omen_cycle[self.omen]],
            'monsters_on_loc': lambda loc: len([monster for monster in self.monsters if monster['location'] == loc])
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
                    if self.players_died < 0:
                        self.selected_investigators.append(payload['value'])
                    self.investigators[payload['value']] = {
                        'assets':[],
                        'conditions': [],
                        'artifacts': [],
                        'unique_assets':[],
                        'spells':[],
                        'hp': INVESTIGATORS[payload['value']]['hp'],
                        'san': 12 - INVESTIGATORS[payload['value']]['hp'],
                        'clues': [],
                        'tickets': [0,0]
                    }
                    self.set_subscriber_topic(payload['value'])
                    self.screen.add_investigator(payload['value'])
                    self.publish_payload({'message': 'investigator_selected', 'value': payload['value']}, 'server_update')
                    if self.players_died > 0:
                        self.publish_payload({
                            'message': 'spawn',
                            'value': 'investigators',
                            'name': payload['value'],
                            'replace': payload['replace'],
                            'map': 'world'}, 'server_update')
                        self.selected_investigators = [name.replace(payload['replace'], payload['value']) for name in self.selected_investigators]
                        for possession in INVESTIGATORS[payload['value']]['possessions']:
                            kind = possession.split(':')[0]
                            item_name = possession.split(':')[1]
                            if kind == 'assets':
                                self.asset_request('get', item_name, payload['value'])
                            elif kind in ['conditions', 'spells']:
                                self.spell_conditions_request(kind, payload['value'], name=item_name)
                            elif kind == 'artifacts':
                                self.artifact_request(payload['value'], item_name)
                        self.players_died -= 1
                        if self.players_died == 0:
                            self.end_mythos()
                    elif len(self.selected_investigators) == self.player_count:
                        self.publish_payload({'message': 'start_game', 'value': self.ancient_one['name'], 'investigators': self.selected_investigators}, 'server_update')
                        self.players_died = 0
                case 'number_selected':
                    self.player_count = payload['value']
                    self.reference = REFERENCES[int((int(payload['value']) + 1) / 2)]
                    self.publish_payload({'message': 'ancient_ones', 'value': None}, 'server_update')
                case 'ready':
                    self.current_player += 1
                    if self.current_player == self.player_count:
                        self.current_phase = 0
                        self.current_player = 0
                        kinds = ['gates', 'clues']
                        self.spawn('expedition')
                        for i in range(len(kinds)):
                            self.spawn(kinds[i], number=self.reference[i])
                        for name in self.selected_investigators:
                            for possession in INVESTIGATORS[name]['possessions']:
                                kind = possession.split(':')[0]
                                item_name = possession.split(':')[1]
                                if kind == 'assets':
                                    self.asset_request('get', item_name, name)
                                elif kind in ['conditions', 'spells']:
                                    self.spell_conditions_request(kind, name, name=item_name)
                                elif kind == 'artifacts':
                                    self.artifact_request(name, item_name)
                        self.restock_reserve()
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
                    self.investigators['akachi_onyele'] = {'tickets': (0,0), 'assets':[], 'conditions': [], 'artifacts': [], 'unique_assets':[], 'spells':[], 'hp': 0, 'san': 0, 'clues': ['world:arkham']}
                    self.initiate_gameboard()
                    self.publish_payload({'message': 'choose_lead', 'value': None}, 'server_update')
                    #END TESTING
                    '''
        elif topic in self.selected_investigators:
            if payload['message'] in ['spells', 'conditions']:
                self.spell_conditions_request(payload['message'], topic, payload.get('tag', ''), payload.get('value', ''))
            else:
                match payload['message']:
                    case 'assets':
                        item = self.asset_request(payload['command'], payload['value'], topic, payload['tag'])                            
                    case 'artifacts':
                        item = self.artifact_request(topic, payload.get('value', ''), payload.get('tag', ''))                            
                    case 'card_discarded':
                        if payload['kind'] == 'assets':
                            self.assets['discard'].append(payload['value'])
                            self.publish_payload({'message': 'discard', 'value': payload['value']}, 'server_update')
                        elif payload['kind'] == 'artifacts':
                            self.decks['used_artifacts'].append(payload['value'])
                        else:
                            self.decks[payload['kind']].append(payload['value'])
                        true_name = payload['value'] if payload['kind'] not in ['conditions', 'spells'] else payload['value'][:-1]
                        if true_name in self.investigators.get(topic, {payload['kind']: []})[payload['kind']]:
                            self.investigators[topic][payload['kind']].remove(true_name)
                            self.publish_payload({'message': 'possession_lost', 'value': payload['value'], 'kind': payload['kind'], 'owner': topic}, 'server_update')
                        elif payload['kind'] == 'clues' and payload.get('from_map', False):
                            self.publish_payload({'message': 'token_removed', 'value': payload['value'], 'kind': 'clue'}, 'server_update')
                    case 'get_clue':
                        clue = random.choice(self.decks['clues'])
                        #self.decks['clues'].remove(clue)
                        self.investigators[topic]['clues'].append(clue)
                        self.publish_payload({'message': 'receive_clue', 'value': clue, 'owner': topic}, 'server_update')
                    case 'spawn':
                        self.spawn(payload['value'], payload.get('name', None), payload.get('location', None), int(payload.get('number', 1)))
                    case 'move_investigator':
                        self.publish_payload({'message': 'unit_moved', 'value': payload['value'], 'destination': payload['destination'], 'kind': 'investigators'}, 'server_update')
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
                                            name = 'all_for_nothing'
                                            self.is_first = False
                                        else:
                                            name = 'a_dark_power'
                                            #name = 'the_storm'
                                        #END TESTING
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
                                        del self.mythos_deck[x][name]
                                        break
                            if self.yellow_card:
                                self.mythos_reckoning()
                        if self.current_phase == 3:
                            if self.mythos.get('actions', None) != None:
                                for x in range(len(self.mythos['actions'])):
                                    if self.mythos.get('args', None) != None:
                                        self.action_dict[self.mythos['actions'][x]](**self.mythos['args'][x])
                                    else:
                                        self.action_dict[self.mythos['actions'][x]]()
                            if self.yellow_card:
                                self.spawn('gates', number=self.reference[0])
                                self.yellow_card = False
                        if self.current_phase == 4:
                            self.end_mythos()
                        else:
                            topic = ''
                            #if self.current_phase == 2 and self.mythos != None and self.mythos.get('lead_only', None) != None:
                            #    topic = 'server_update'
                            #else:
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
                            kind = 'expeditions'
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
                    case 'end_mythos':
                        self.end_mythos()
                    case 'shuffle_mystery':
                        self.shuffle_mystery()
                    case 'move_monster':
                        self.publish_payload({'message': 'unit_moved', 'value': int(payload['value']), 'destination': payload['location'], 'kind': 'monsters'}, 'server_update')
                        index = next((i for i, monster in enumerate(self.monsters) if monster['monster_id'] == int(payload['value'])), None)
                        chosen = self.monsters[index]
                        chosen['location'] = payload['location']
                    case 'mythos_reckoning':
                        self.mythos_reckoning(payload['value'], True)
                    case 'update_hpsan':
                        investigator = self.investigators[topic]
                        investigator['hp'] = payload['hp']
                        investigator['san'] = payload['san']
                        if investigator['hp'] <= 0 or investigator['san'] <= 0:
                            self.players_died += 1
                            current_lead = self.selected_investigators[self.lead_investigator]
                            if current_lead == topic:
                                for x in range(len(self.selected_investigators) - 1):
                                    index = self.lead_investigator + x + 1 % len(self.selected_investigators)
                                    if self.selected_investigators[x] not in self.dead_investigators:
                                        self.publish_payload({'message': 'lead_selected', 'value': self.selected_investigators[x], 'dead_trigger': True}, 'server_update')
                                        break
                            health_death = False
                            if investigator['hp'] > -900:
                                health_death = self.investigators[topic]['hp'] <= 0
                                self.dead_investigators[topic] = copy.deepcopy(investigator)
                                self.dead_investigators[topic]['recovered'] = False
                            del self.investigators[topic]
                            self.move_doom()
                            self.publish_payload({'message': 'investigator_died', 'value': topic, 'kind': payload.get('kind', health_death), 'devoured': investigator['hp'] < -900}, 'server_update')
                        else:
                            self.player_update(topic)
                    case 'update_tickets':
                        self.investigators[topic]['tickets'] = [payload['rail'], payload['ship']]
                        self.player_update(topic)
                    case 'trade':
                        del payload['message']
                        give = list(payload.keys())[0]
                        take = list(payload.keys())[1]
                        tickets_ref = ['rail', 'ship']
                        for x in range(2):
                            self.investigators[give]['tickets'][x] += len(payload[give][tickets_ref[x]])
                            self.investigators[take]['tickets'][x] -= len(payload[give][tickets_ref[x]])
                            self.investigators[give]['tickets'][x] -= len(payload[take][tickets_ref[x]])
                            self.investigators[take]['tickets'][x] += len(payload[take][tickets_ref[x]])
                        for key in ['assets', 'unique_assets', 'spells', 'clues', 'artifacts']:
                            for item in payload[give][key]:
                                self.investigators[give][key].remove(item)
                                self.investigators[take][key].append(item)
                            for item in payload[take][key]:
                                self.investigators[give][key].append(item)
                                self.investigators[take][key].remove(item)
                    case 'recover_body':
                        take = self.investigators[topic]
                        give = payload['body']
                        for x in range(2):
                            take['tickets'][x] += self.dead_investigators[give]['tickets'][x]
                        for key in ['assets', 'unique_assets', 'spells', 'clues', 'artifacts']:
                            for item in self.dead_investigators[give][key]:
                                take[key].append(item)
                        self.dead_investigators[give]['recovered'] = True
                        self.publish_payload({'message': 'body_recovered', 'value': give, 'owner': topic}, 'server_update')
                    case 'set_omen':
                        self.set_omen(payload.get('pos', None), payload.get('trigger', True))
                    case 'update_rumor_solve':
                        rumor = next((rumor for rumor in self.reckoning_actions if rumor['name'] == payload['name']), None)
                        if rumor.get('solve_amt', None) != None:
                            rumor['solve_amt'] += payload['solve_amt']
                            if rumor['solve_amt'] >= math.ceil(self.player_count / rumor['solve_threshold']):
                                self.solve_rumor(rumor)
                            else:
                                self.publish_payload({'message': 'update_rumor', 'name': rumor['name'], 'value': rumor['recurring'], 'solve': rumor['solve_amt']}, 'server_update')
                        else:
                            rumor['recurring'] += payload['value']
                            if rumor['recurring'] <= 0:
                                self.solve_rumor(rumor, False)
                            else:
                                self.publish_payload({'message': 'update_rumor', 'name': rumor['name'], 'value': rumor['recurring']}, 'server_update')
                    case 'spawn_rumor':
                        rumor = random.choice(list(MYTHOS[2].keys()))
                        for num in range(len(MYTHOS[2][rumor]['actions'])):
                            self.action_dict[MYTHOS[2][rumor]['actions'][num]](**MYTHOS[2][rumor]['args'][num])
                        self.publish_payload({'message': 'mythos', 'value': rumor}, 'server_update')
                        topic = self.selected_investigators[self.current_player] + '_server'
                        self.publish_payload({'message': 'player_turn', 'value': self.phases[self.current_phase]}, topic)

    def clear_bodies(self):
        for names in [name for name in self.dead_investigators if not self.dead_investigators[name]['recovered']]:
            self.dead_investigators[names]['recovered'] = True
            self.publish_payload({'message': 'body_recovered', 'value': names}, 'server_update')

    def player_update(self, name):
        investigator = self.investigators[name]
        self.publish_payload({
            'message': 'player_update',
            'owner': name,
            'health': investigator['hp'],
            'sanity': investigator['san'],
            'rail_tickets': investigator['tickets'][0],
            'ship_tickets': investigator['tickets'][1]
        }, 'server_update')

    def end_mythos(self):
        for actions in self.end_of_mythos_actions:
            action = actions.get('action', None)
            if action != None:
                if actions.get('args', None) != None:
                    self.action_dict[action](**actions['args'])
                else:
                    self.action_dict[action]()
        if self.players_died == 0:
            self.current_phase = 0
            self.publish_payload({'message': 'choose_lead', 'value': None}, 'server_update')
        else:
            self.publish_payload({'message': 'choose_new', 'names': self.selected_investigators + list(self.dead_investigators.keys())}, 'server_update')

    def on_reckoning(self, args, recur_value=None):
        if recur_value == 'expeditions':
            args['recurring'] = len(self.expeditions)
        if args.get('end_of_mythos', None) != None:
            del args['end_of_mythos']
            self.end_of_mythos_actions.append(args)
        else:
            self.reckoning_actions.append(args)

    def lose_game(self):
        pass

    def from_beyond(self):
        if len(self.reckoning_actions) == 0:
            self.move_doom()
        else:
            self.publish_payload({'message': 'mythos_switch'}, 'server_update')
            self.set_payment('investigators', 'clues', 'from_beyond', divisor=2)

    def set_payment(self, kind, payment, name, divisor=1):
        number = 0
        if kind == 'investigators':
            number = len(self.selected_investigators)
        elif kind == 'gates':
            number = len(self.decks['gates']['board'])
        needed = math.ceil(number / divisor)
        total = 0
        for inv in self.investigators:
            if payment == 'clues':
                total += len(self.investigators[inv]['clues'])
            elif payment in ['hp', 'san']:
                total += self.investigators[inv][payment]
        self.publish_payload({'message': 'group_pay_update', 'total': total, 'needed': needed, 'name': name}, 'server_update')
        return needed

    def mythos_reckoning(self, number=1, doom=False):
        if doom and len(self.reckoning_actions) == 0:
            self.move_doom()
        else:
            for x in range(number):
                for actions in self.reckoning_actions:
                    action = actions.get('action', None)
                    if action != None:
                        if actions.get('args', None) != None:
                            self.action_dict[action](**actions['args'])
                        else:
                            self.action_dict[action]()
                    if actions.get('recurring', None) == None:
                        self.reckoning_actions.remove(actions)
                    else:
                        tokens = 1
                        if actions.get('rargs', None) != None:
                            tokens = self.rumor_tick(**actions['rargs'])
                        elif actions.get('check', None) != None:
                            number = self.get_locations[actions['check']](**actions['chargs'])
                            if actions.get('check_type', None) == 'treshold':
                                tokens = actions['recurring'] if number >= actions['recurring'] else 0
                            elif actions.get('check_type', None) == 'equal':
                                tokens = number
                        actions['recurring'] -= tokens
                        if actions['recurring'] <= 0:
                            if actions.get('unsolve', None) != None:
                                if actions.get('unsolve_args', None) != None:
                                    self.action_dict[actions['unsolve']](**actions['unsolve_args'])
                                else:
                                    self.action_dict[actions['unsolve']]()
                            self.solve_rumor(actions, False)
                        elif tokens != 0:
                            self.publish_payload({'message': 'update_rumor', 'name': actions['name'], 'value': actions['recurring']}, 'server_update')

    def rumor_tick(self, count='', divisor=1, tick=1):
        if count == 'gates':
            tick = len(self.decks['gates']['board'])
        elif count == 'growing_madness':
            lead = self.selected_investigators[self.lead_investigator]
            self.spell_conditions_request('conditions', lead, 'madness')
            tick = len([card for card in self.investigators[lead]['conditions'] if 'madness' in CONDITIONS[card]['tags']])
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

    def heal_monsters(self, amt):
        self.server_damage_monster(amt)
        self.publish_payload({'message': 'monster_damaged', 'value': -1, 'damage': amt}, 'server_update')

    def server_damage_monster(self, amt, monster_id=None):
        def do_damage(monster, dmg):
            damage = monster['damage'] + dmg
            monster['damage'] = damage if damage >= 0 else damage
            value = 0
            toughness = MONSTERS[monster['name']].get('toughness')
            if type(toughness) == str and '+' in toughness:
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

    def spell_conditions_request(self, kind, investigator, tag='', name=''):
        item = None
        ref = SPELLS if kind == 'spells' else CONDITIONS
        has_card = name != '' and next((card for card in self.investigators[investigator][kind] if name in card), None) != None
        items = [card for card in self.decks[kind] if (name == '' or name in card) and (tag == '' or tag in ref[card[:-1]]['tags']) and not has_card and card[:-1] not in self.investigators[investigator][kind]]
        if len(items) > 0:
            item = random.choice(items)
            #self.decks[kind].remove(item)
            self.investigators[investigator][kind].append(item[:-1])
            self.publish_payload({'message': 'card_received', 'kind': kind, 'value': item, 'owner': investigator}, 'server_update')

    def asset_request(self, command, name, investigator, tag=''):
        match command:
            case 'acquire':
                self.restock_reserve([name])
                self.investigators[investigator]['assets'].append(name)
                self.publish_payload({'message': 'card_received', 'kind': 'assets', 'value': name, 'owner': investigator}, 'server_update')
                return name
            case 'restock':
                self.restock_reserve([name], True)
            case 'discard':
                self.assets['discard'].append(name)
                self.publish_payload({'message': 'asset', 'discard': name}, 'server_update')
            case 'get':
                if name != '':
                    if name in self.assets['deck']:
                        pass
                    #self.assets['deck'].remove(name)
                    else:
                        name = None
                else:
                    name = random.choice([item for item in self.assets['deck'] if tag in ASSETS[item]['tags'] or tag == 'any'])
                    #self.assets['deck'].remove(name)
                if name != None:
                    self.investigators[investigator]['assets'].append(name)
                    self.publish_payload({'message': 'card_received', 'kind': 'assets', 'value': name, 'owner': investigator}, 'server_update')
        
    def artifact_request(self, investigator, name='', tag=''):
        if name != '' and name not in self.decks['used_artifacts']:
            self.decks['used_artifacts'].append(name)
        else:
            artifacts = [card for card in ARTIFACTS if (tag == '' or tag in ARTIFACTS[card]['tags']) and card not in self.decks['used_artifacts']]
            if len(artifacts) > 0:
                name = random.choice(artifacts)
                self.decks['used_artifacts'].append(name)
        if name != '':
            self.publish_payload({'message': 'card_received', 'kind': 'artifacts', 'value': name, 'owner': investigator}, 'server_update')
            self.investigators[investigator]['artifacts'].append(name)

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
                            gate = random.choice(self.decks['gates']['deck'])
                            self.decks['gates']['deck'].remove(gate)
                            gate = 'world:buenos_aires'
                            self.decks['gates']['board'].append(gate)
                            self.publish_payload({'message': 'spawn', 'value': 'gate', 'location': gate.split(':')[1], 'map': gate.split(':')[0]}, 'server_update')
                            self.spawn('monsters', location=gate, name='avian_thrall')
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

    def secrets_of_the_past(self, is_secrets=True):
        self.expeditions.remove(self.expedition)
        del self.encounters[self.expedition]
        if len(self.expeditions) == 0:
            if is_secrets:
                pass #LOSE GAME
        else:
            self.spawn('expedition')

    def spreading_sickness(self):
        amt = [rumor for rumor in self.reckoning_actions if rumor['name'] == 'spreading_sickness'][0]['recurring'] + 1
        encounter = {'action': ['hp_san'], 'aargs': [{'hp':-amt, 'step': 'reckoning', 'skip': True}], 'action_text': 'Spreading Sickness - Reckoning\n\nPlace a Health Token on this card, then each Investigator loses Health equal to the number of tokens on this card.'}
        self.publish_payload({'message': 'player_mythos_reckoning', 'value': encounter}, 'server_update')

    def web_between_worlds(self):
        payment = self.set_payment('investigators', 'clues', 'web_between_worlds', 2)
        encounter = {'action': ['group_pay_reckoning', 'update_rumor'], 'aargs': [{'kind': 'clues', 'name': 'web_between_worlds', 'first': True, 'text': 'Spend ' + str(payment) + ' Clues'}, {'name': 'web_between_worlds', 'kind': 'value', 'amt': -1, 'step': 'reckoning', 'text': 'Add 1 Eldritch Token'}], 'action_text': 'Web Between Worlds - Reckoning\n\nDiscard 1 Eldritch token from this card unless Investigators as a group spend Clues equal to half Investigators.'}
        self.publish_payload({'message': 'player_mythos_reckoning', 'value': encounter}, self.selected_investigators[self.lead_investigator] + '_server')

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
        for x in range(3):
            for character in self.ancient_one['mythos'][x]:
                color = int(character)
                card = random.choice(list(MYTHOS[color].keys()))
                if card != 'a_dark_power' and card != 'all_for_nothing':
                #FOR TESTING
                #if color == 0:
                #    card = 'patrolling_the_border'
                #if color == 1:
                #    card = 'rally_the_people'
                #if color == 2:
                #    card = 'return_of_the_ancient_ones'
                #END TESTING
                    self.mythos_deck[x][card] = MYTHOS[color][card]
                    self.mythos_deck[x][card]['color'] = color
                    del MYTHOS[color][card]
        #FOR TESTING
        self.mythos_deck[0]['a_dark_power'] = MYTHOS[1]['a_dark_power']
        self.mythos_deck[0]['a_dark_power']['color'] = 1
        self.mythos_deck[0]['all_for_nothing'] = MYTHOS[1]['all_for_nothing']
        self.mythos_deck[0]['all_for_nothing']['color'] = 1
        #END TESTING

    def set_omen(self, pos=None, trigger=True, increment=1):
        if pos != None:
            self.omen = pos
        else:
            self.omen += increment
            if self.omen == 4:
                self.omen = 0
            elif self.omen == -1:
                self.omen = 3
        if trigger:
            if hasattr(self.triggers, 'omen' + str(self.omen)):
                triggers = self.triggers['omen' + str(self.omen)]
                for effects in triggers:
                    triggers[effects]['action'](**triggers[effects]['args'])
            self.move_doom(gates=True)
        self.publish_payload({'message': 'omen', 'value': self.omen}, 'server_update')

    def move_doom(self, amt=-1, gates=False, all_gates=False):
        if gates:
            amt = -len(self.get_locations['gate_omen']())
        if all_gates:
            amt = -len(self.decks['gates']['board'])
        if amt != 0:
            self.ancient_one['doom'] += amt
            self.ancient_one['doom'] = self.ancient_one['doom'] if self.ancient_one['doom'] >= 0 else 0
            if self.ancient_one['doom'] == 0:
                #AWAKEN LOGIC
                pass
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