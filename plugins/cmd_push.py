"""YO cloud tools
"""
from utils.cloud import get_user_sessions, get_players_info

import os
import subprocess
import questionary
from utils.misc import switch_to_ssh

#--------------------------------------------------------------------------------------------------------
def args_push(parser):
    parser.add_argument(
            dest="name",
            help="Server name/ip to upload code",
            const=' ',
            nargs='?')

def cmd_push(args):
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


    cmd = ["dmesg -w"]
    switch_to_ssh(args.name, args=cmd, reconnect=False)
