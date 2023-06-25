"""YO cloud tools
"""
import os

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
        exit("Please specify server name")

    cmd = ['ssh', '-t', ] + [args.name] + ['dmesg -w']
    os.execvp(cmd[0], cmd)
