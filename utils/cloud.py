"""YO cloud tools
"""
from utils.cache import get_cloud_cache
import requests
import questionary

def get_players_info(r, s=False):
    headers = get_base_headers()
    host = []
    for setups in r.json():
        if setups['status'] != 'active':
            continue

        name = setups['setup_info']['name']

        if s is True:
            host += [questionary.Separator("--- %s ---" %(setups['session_description']))]
            host += [name]
        else:
            host += [questionary.Separator("--- %s %s ---" %(name, setups['session_description']))]
        host += [setups['setup_info']['players'][0]['ip']]
        if len(setups['setup_info']['players']) == 2:
            host += [setups['setup_info']['players'][1]['ip']]

    return host

def get_sessions_info(r):
    headers = get_base_headers()
    host = []
    for setups in r.json():
        if setups['status'] != 'active':
            continue

        host += [questionary.Separator("--- %s ---" %(setups['session_description']))]
        host += [setups['setup_info']['name']]

    return host

def get_players_data(r, n):
    name = None
    for setups in r.json():
        if setups['status'] != 'active':
            continue

        if name is not None and n is None:
            exit("You have more than one setup. Please specify VM to restart")

        name = setups['setup_info']['name']
        # n can be provided in one of the following formats:
        # 1. Setup name, e.g. 10.141.67.105-106_cx4
        # 2. Specific IP
        ip1=name.split('-')[0]
        try:
            ip2='.'.join(ip1.split('.')[:-1]) + '.' + name.split('-')[1].split('_')[0]
        except IndexError:
            # We have single node machine
            ip2=ip1
        if n is not None and name != n and ip1 != n and ip2 != n:
            name = None
            continue

        _id = setups['_id']
        host = setups['setup_info']['players'][0]['host_ip']
        players=[]
        if name == n:
            players = ['player1', 'player2']
        if ip1 == n:
            players = ['player1']
        if ip2 == n:
            players = ['player2']
        if n is not None:
            break

    if name is None:
        exit("There are no setups with this info")

    return _id, players, host

def get_base_headers():
    cache = get_cloud_cache()

    headers = {'Cache-Control' : 'no-cache'}
    headers.update({'User-Agent' : 'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/111.0'})
    headers.update({'Referer' : 'http://linux-cloud.mellanox.com/user_sessions'})
    headers.update({'Cookie': cache['cookie']})

    return headers

def get_user_sessions():
    """Get user sessions"""

    headers = get_base_headers()

    payload = {'user': '', 'limit': '0'}
    return requests.get('http://linux-cloud.mellanox.com/api/get_user_sessions', 
                        params=payload, headers=headers)
