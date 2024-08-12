"""YO cloud tools
"""
from utils.cache import get_cloud_cache
import requests
import questionary

class CloudSetup:
    def __init__(self, raw, headers):
        self.raw = raw
        self.headers = headers

    @property
    def id(self):
        return self.raw['_id']

    @property
    def name(self):
        return self.raw['setup_info']['name']

    @property
    def description(self):
        return self.raw['session_description']

    @property
    def expiration_time(self):
        return self.raw['expiration_time']

    @property
    def order_time(self):
        return self.raw['order_time']

    @property
    def host(self):
        return self.raw['setup_info']['players'][0]['host_ip']

    def get_players(self):
        players = [self.raw['setup_info']['players'][0]['ip']] 
        if len(self.raw['setup_info']['players']) == 2:
            players += [self.raw['setup_info']['players'][1]['ip']]
        return players

    def get_player_name(self, player):
        if player == self.raw['setup_info']['players'][0]['ip']:
            return ['player1']
        return ['player2']

    def put(self, command, data):
        return requests.put('http://linux-cloud.mellanox.com/api/%s/%s/%s'
                       %(self.id, command, data), headers=self.headers)

    def put_no_api(self, command, data):
        return requests.put('http://linux-cloud.mellanox.com/session/%s/%s'
                            %(command, self.id), json=data, headers=self.headers)

    def post(self, command, data):
        return requests.post('http://linux-cloud.mellanox.com/api/session/%s/%s'
                             %(command, self.id), json=data, headers=self.headers)

class CloudSessions:
    def __init__(self, status='active'):
        cache = get_cloud_cache()

        self.headers = {'Cache-Control' : 'no-cache'}
        self.headers.update({'User-Agent' : 'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/111.0'})
        self.headers.update({'Referer' : 'http://linux-cloud.mellanox.com/user_sessions'})
        self.headers.update({'Cookie': cache['cookie']})

        payload = {'user': '', 'limit': '0'}
        r = requests.get('http://linux-cloud.mellanox.com/api/get_user_sessions',
                         params=payload, headers=self.headers)

        self.data = []
        for session in r.json():
            if session['status'] != status:
                continue

            self.data += [CloudSetup(session, self.headers)]

    def __getitem__(self, index):
        return self.data[index]

    def post(self, command, data):
        return requests.post('http://linux-cloud.mellanox.com/%s' %(command),
                             data=data, headers=self.headers)

    def get_session(self, msg):
        sessions = []
        for setups in self.data:
            sessions += [questionary.Separator("--- %s ---" %(setups.description))]
            sessions += [setups.name]

        res = questionary.select("Which session %s?" %(msg), sessions).ask()
        if res is None:
            exit()
        return res

    def get_players(self, msg):
        host = []
        for setups in self.data:
            host += [questionary.Separator("--- %s %s ---" %(setups.name, setups.description))]
            host += setups.get_players()
            
        res = questionary.select("Which server %s?" %(msg), host).ask()
        if res is None:
            exit()
        return res

    def get_setup(self, name=None, player=None):
        for setup in self.data:
            if name == setup.name:
                return setup

            if player is None:
                continue

            if player in setup.get_players():
                return setup

        exit("Something very bad happen")

ActiveSessions=CloudSessions()
