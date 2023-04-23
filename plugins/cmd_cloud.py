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
        if hours == 0:
            continue

        data = {'name' : name, 'id' : _id, 'timeout': hours}
        ext = requests.post('http://linux-cloud.mellanox.com/extend_lock', data=data, headers=headers)
        result.append((name, get_local_strtime(ext.json()['old_expiration_time']),
                       get_local_strtime(ext.json()['new_expiration_time'])))

    t.add_rows(result, False)
    print(t.draw())

def restart_vms(r, headers, n):
    name = None
    for setups in r.json():
        if setups['status'] != 'active':
            continue

        if name is not None and n is None:
            exit("You have more than one setup. Please specify name to VM restart")

        name = setups['setup_info']['name']
        if n is not None and name != n:
            name = None
            continue

        _id = setups['_id']
        host = setups['setup_info']['players'][0]['host_ip']
        numb_players = len(setups['setup_info']['players'])
        players = []
        count = 0
        for i in setups['setup_info']['players']:
            count += 1
            players += ['player%d' % (count)]
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
            "--restart-vms",
            dest="restart_vms",
            help="Restart VMs",
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

    if args.restart_vms:
        name = None;
        if args.restart_vms != ' ':
            name = args.restart_vms
        restart_vms(r, headers, name)
        return

    list_user_setups(r)
