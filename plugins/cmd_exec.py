"""YO cloud tools
"""
from utils.cloud import get_user_sessions, get_players_info
from utils.misc import exec_on_remote

import os
import questionary

#--------------------------------------------------------------------------------------------------------
def args_exec(parser):
    parser.add_argument(
            dest="name",
            help="Server name/ip to view console",
            const=' ',
            nargs='?')
    parser.add_argument(
            "--cmd",
            dest="cmd",
            nargs=1,
            help="Command to execute")

def cmd_exec(args):
    """Execute command"""
    if args.name is None:
        r = get_user_sessions()
        players = get_players_info(r)
        if players is None:
            exit("There are no active setups to connect")

        choice = questionary.select("Which server to connect?", players).ask()
        if choice is None:
            exit()

        args.name = choice.split(' ')[0]

    exec_on_remote(args.name, args.cmd)
