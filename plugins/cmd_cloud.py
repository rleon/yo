"""YO cloud tools
"""
from utils.misc import *
from utils.cloud import *

import os
import stat
import math
import requests
import tempfile
import questionary
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

def extend_setups(r):
    headers = get_base_headers()

    t = Texttable(max_width=0)
    t.set_header_align(["l", "l", "l", "l"])
    t.header(('Name', 'Description', 'Before', 'After'))
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
        result.append((name, setups['session_description'],
                       get_local_strtime(ext.json()['old_expiration_time']),
                       get_local_strtime(ext.json()['new_expiration_time'])))

    t.add_rows(result, False)
    print(t.draw())

def restart_vm(r, n):
    headers = get_base_headers()

    _id, players, host = get_players_data(r, n)
    data = {"players_info": {host: players}}
    ext = requests.post('http://linux-cloud.mellanox.com/api/session/reload_setup/%s' %(_id),
                        json=data, headers=headers)

def list_user_setups(r):
    t = Texttable(max_width=0)
    t.set_header_align(["l", "l", "l", "l"])
    t.header(('Name', 'Description', 'Order', 'Expire'))
    data = []
    for setups in r.json():
        if setups['status'] != 'active':
            continue

        data.append((setups['setup_info']['name'],
                     setups['session_description'],
                     get_local_strtime(setups['order_time'], True),
                     get_local_strtime(setups['expiration_time'], True)))

    t.add_rows(data, False)
    print(t.draw())

def edit_session_description(r, description, n):
    headers = get_base_headers()

    _id, players, host = get_players_data(r, n)
    ext = requests.put('http://linux-cloud.mellanox.com/api/%s/description/%s'
                       %(str(_id), str(description[0])), headers=headers)

def auto_extend(install):
    if not install:
        os.system("sudo rm -rf /etc/cron.daily/yo-cloud-extend")
        return

    with tempfile.NamedTemporaryFile('w') as f:
        f.write("#!/usr/bin/sh\n")
        f.write("sudo -u %s %s/yo cloud --extend\n" % (os.getlogin(), yo_root()))
        f.flush()
        os.chmod(f.name, os.stat(f.name).st_mode | stat.S_IEXEC)
        os.system("sudo cp -f %s /etc/cron.daily/yo-cloud-extend" % (f.name))

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
            "-d",
            "--edit-description",
            dest="description",
            help="Edit session description",
            nargs=1)
    parser.add_argument(
            "-r",
            "--restart-vm",
            dest="restart_vm",
            metavar="VM",
            help="Restart VM",
            const=' ',
            nargs='?')
    parser.add_argument(
            "--auto-extend",
            dest="auto_extend",
            metavar="on|off",
            choices=['on', 'off'],
            help="Set periodic job to automatically extend setups",
            nargs=1)

def cmd_cloud(args):
    """Manage sessions"""

    r = get_user_sessions()

    if args.auto_extend:
        auto_extend(args.auto_extend == ['on'])
        return

    if args.description:
        sessions = get_sessions_info(r)
        choice = questionary.select("Which session to edit?", sessions).ask()
        edit_session_description(r, args.description, choice)
        return;

    if args.extend:
        extend_setups(r)
        return

    if args.restart_vm:
        choice = None;
        if args.restart_vm != ' ':
            choice = args.restart_vm
        else:
            players = get_players_info(r, True)
            choice = questionary.select("Which server/setup to restart?", players).ask()

        if choice is None:
            exit()

        restart_vm(r, choice)
        return

    list_user_setups(r)
