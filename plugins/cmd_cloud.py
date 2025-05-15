"""YO cloud tools
"""

import os
import stat
import math
import tempfile
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

def extend_setups():
    t = Texttable(max_width=0)
    t.set_header_align(["l", "l", "l", "l"])
    t.header(('Name', 'Description', 'Before', 'After'))
    result = []
    for setups in ActiveSessions:
        hours = calculate_extend_delta(setups.expiration_time)
        if hours <= 0:
            continue

        data = {'extend_justification': 'Nuh touch mi tralala'}
        setups.put_no_api('extend_justification', data)

        data = {'name' : setups.name, 'id' : setups.id, 'timeout': hours}
        ext = ActiveSessions.post('extend_lock', data)
        result.append((setups.name, setups.description,
                       get_local_strtime(ext.json()['old_expiration_time']),
                       get_local_strtime(ext.json()['new_expiration_time'])))

    t.add_rows(result, False)
    print(t.draw())

def restart_vm(player=None):
    if player is None:
        player = ActiveSessions.get_players("to restart")

    setup = ActiveSessions.get_setup(player=player)
    data = {"players_info": {setup.host: setup.get_player_name(player)}}
    setup.post("reload_setup", data)

def list_user_setups():
    t = Texttable(max_width=0)
    t.set_header_align(["l", "l", "l", "l"])
    t.header(('Name', 'Description', 'Order', 'Expire'))
    data = []
    for setups in ActiveSessions:
        data.append((setups.name, setups.description,
                     get_local_strtime(setups.order_time, True),
                     get_local_strtime(setups.expiration_time, True)))

    t.add_rows(data, False)
    print(t.draw())

def edit_session_description(description):
    session = ActiveSessions.get_session("to edit")
    ActiveSessions.get_setup(name=session).put('description', description)

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

    from utils.cloud import ActiveSessions

    if args.auto_extend:
        auto_extend(args.auto_extend == ['on'])
        return

    if args.description:
        edit_session_description(str(args.description[0]))
        return;

    if args.extend:
        extend_setups()
        return

    if args.restart_vm:
        choice = None;
        if args.restart_vm != ' ':
            choice = args.restart_vm

        restart_vm(choice)
        return

    list_user_setups()
