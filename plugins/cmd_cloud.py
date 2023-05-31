"""YO cloud tools
"""
from utils.cache import get_cloud_cache

import math
import requests
from texttable import Texttable
from datetime import datetime
try:
    import zoneinfo
except ImportError:
    from backports import zoneinfo

def get_local_strtime(time, tzinfo=False):
    if not tzinfo:
        strtime = datetime.strptime(time, "%a, %d %b %Y %H:%M:%S %Z").astimezone()
    else:
        strtime = datetime.strptime(time, "%Y-%m-%d %H:%M:%S").astimezone()
    strtime = strtime + strtime.utcoffset()
    strtime = strtime.replace(tzinfo=None)
    return strtime.strftime("%Y-%m-%d %H:%M:%S")

def calculate_extend_delta(current_expire):
    expire = datetime.strptime(current_expire, "%Y-%m-%d %H:%M:%S").replace(tzinfo=zoneinfo.ZoneInfo('GMT'))
    now = datetime.now(zoneinfo.ZoneInfo('GMT'))
    difference = expire - now
    h = difference.days * 24 + math.ceil(difference.seconds/3600)
    return 96 - h

def extend_setups(r, headers):
    t = Texttable(max_width=0)
    t.set_header_align(["l", "l", "l"])
    t.header(('Name', 'Before', 'After'))
    result = []
    for setups in r.json():
        if setups['status'] != 'active':
            continue

        name = setups['setup_info']['name']
        _id = setups['_id']
        hours = calculate_extend_delta(setups['expiration_time'])
        if hours <= 0:
            continue

        data = {'name' : name, 'id' : _id, 'timeout': hours}
        ext = requests.post('http://linux-cloud.mellanox.com/extend_lock', data=data, headers=headers)
        result.append((name, get_local_strtime(ext.json()['old_expiration_time']),
                       get_local_strtime(ext.json()['new_expiration_time'])))

    t.add_rows(result, False)
    print(t.draw())

def restart_vm(r, headers, n):
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
        print("There are no setups to restart")
        return

    data = {"players_info": {host: players}}
    ext = requests.post('http://linux-cloud.mellanox.com/api/session/reload_setup/%s' %(_id),
                        json=data, headers=headers)

def list_user_setups(r):
    t = Texttable(max_width=0)
    t.set_header_align(["l", "l", "l"])
    t.header(('Name', 'Order', 'Expire'))
    data = []
    for setups in r.json():
        if setups['status'] != 'active':
            continue

        data.append((setups['setup_info']['name'],
                     get_local_strtime(setups['order_time'], True),
                     get_local_strtime(setups['expiration_time'], True)))

    t.add_rows(data, False)
    print(t.draw())

#--------------------------------------------------------------------------------------------------------
def args_cloud(parser):
    parser.add_argument(
            "-e",
            "--extend",
            dest="extend",
            action="store_true",
            help="Extend setup",
            default=False)
    parser.add_argument(
            "-r",
            "--restart-vm",
            dest="restart_vm",
            help="Restart VM",
            const=' ',
            nargs='?')

def cmd_cloud(args):
    """Manage sessions"""

    cache = get_cloud_cache()

    headers = {'Cache-Control' : 'no-cache'}
    headers.update({'User-Agent' : 'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/111.0'})
    headers.update({'Referer' : 'http://linux-cloud.mellanox.com/user_sessions'})
    headers.update({'Cookie': cache['cookie']})
    payload = {'user': '', 'limit': '0'}
    r = requests.get('http://linux-cloud.mellanox.com/api/get_user_sessions', params=payload, headers=headers)

    if args.extend:
        extend_setups(r, headers)
        return

    if args.restart_vm:
        name = None;
        if args.restart_vm != ' ':
            name = args.restart_vm
        restart_vm(r, headers, name)
        return

    list_user_setups(r)
