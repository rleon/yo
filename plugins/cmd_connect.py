"""YO cloud tools
"""
from utils.misc import switch_to_ssh
from utils.cloud import *

#--------------------------------------------------------------------------------------------------------
def args_connect(parser):
    parser.add_argument(
            dest="name",
            help="Server name/ip to run repro",
            const=' ',
            nargs='?')
    parser.add_argument(
            "--no-reconnect",
            dest="no_reconnect",
            action="store_true",
            help="Disable automatic reconnect",
            default=False)

def cmd_connect(args):
    """Connect to server"""
    if args.name is None:
        args.name = ActiveSessions.get_players("to connect")

    switch_to_ssh(args.name, reconnect=not args.no_reconnect)
