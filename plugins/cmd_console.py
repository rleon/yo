"""YO cloud tools
"""
from utils.cloud import get_user_sessions, get_base_headers, get_players_info

import os
import questionary

#--------------------------------------------------------------------------------------------------------
def args_console(parser):
    parser.add_argument(
            dest="name",
            help="Server name/ip to view console",
            const=' ',
            nargs='?')

def cmd_console(args):
    """View console"""
    if args.name is None:
        r = get_user_sessions()
        players = get_players_info(r)
        if players is None:
            exit("There are no active setups to connect")

        choice = questionary.select("Which server to connect?", players).ask()
        if choice is None:
            exit()

        args.name = choice.split(' ')[0]

    cmd = ['ssh', '-t', ] + [args.name] + ['dmesg -w']
    os.execvp(cmd[0], cmd)
