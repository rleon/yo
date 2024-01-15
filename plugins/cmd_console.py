"""YO cloud tools
"""
from utils.misc import switch_to_ssh
from utils.cloud import *

#--------------------------------------------------------------------------------------------------------
def args_console(parser):
    parser.add_argument(
            dest="name",
            help="Server name/ip to view console",
            const=' ',
            nargs='?')
    parser.add_argument(
            "--no-reconnect",
            dest="no_reconnect",
            action="store_true",
            help="Disable automatic reconnect",
            default=False)

def cmd_console(args):
    """View console"""
    if args.name is None:
        args.name = ActiveSessions.get_players("to get console")

    cmd = ["dmesg -w"]
    switch_to_ssh(args.name, args=cmd,
                  reconnect=not args.no_reconnect, clear=True)
