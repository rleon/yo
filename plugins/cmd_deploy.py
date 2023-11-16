"""YO cloud tools
"""
from utils.cloud import *

import os
import ipaddress
import subprocess
import questionary
from utils.git import *
from utils.misc import *

def is_ipv4(string):
    try:
        ipaddress.IPv4Network(string)
        return True
    except ValueError:
        return False

def rebuild_kernel(name, br):
    subprocess.call(['rsync', '-amz', '--no-o', '--no-g',
                     '--no-p', '--info=progress2', '--inplace',
                     '--force', '--delete-excluded',
                     '%s/scripts' % (yo_root()), '%s:/w' % (name)])
    exec_on_remote(name, ["/w/scripts/yo-kbuild", br])


def init_setup(name, br):
    subprocess.call(['%s/scripts/yo-mirror' % (yo_root()), name, 'kernel'])
    subprocess.call(['scp', '%s/scripts/yo-cloud-init' % (yo_root()), '%s:/tmp/' % (name)])
    exec_on_remote(name, ["/tmp/yo-cloud-init"])
    rebuild_kernel(name, br)

#--------------------------------------------------------------------------------------------------------
def args_deploy(parser):
    parser.add_argument(
            dest="name",
            help="Server name/ip to upload code",
            const=' ',
            nargs='?')
    parser.add_argument(
            "-n",
            "--dry-run",
            dest="dry_run",
            action="store_true",
            help="dry run",
            default=False)
    parser.add_argument(
            "--no-install",
            dest="no_install",
            action="store_true",
            help="Don't rebuild and install",
            default=False)
    parser.add_argument(
            "--init",
            dest="init",
            help="initialize test VM to specific branch, default current",
            metavar="branch",
            const=' ',
            nargs='?')

def cmd_deploy(args):
    """Deploy flow"""
    args.root = git_root()
    if args.root is None:
        exit()

    args.project = get_project(args)
    if args.project != "kernel":
        exit("Upload is supported for kernel tree only.")

    if args.name is None and not is_ipv4(args.init):
        r = get_user_sessions()
        players = get_players_info(r)
        if players is None:
            exit("There are no active setups to deploy")

        choice = questionary.select("Which server to deploy?", players).ask()
        if choice is None:
            exit()

        args.name = choice.split(' ')[0]

    br = "%s" % (git_current_branch())
    if is_ipv4(args.init) or args.init == ' ':
        # Special case, where user provided --init without any branch
        # followed by VM address
        init_setup(args.name, br)
        exit()
    elif args.init is not None:
        init_setup(args.name, args.init)
        exit()

    branches = [[br, br]]
    remote = "ssh://%s/w/kernel" % (args.name)
    git_push_branches(branches, True, args.dry_run, remote)

    if args.no_install or args.dry_run:
        exit()

    rebuild_kernel(args.name, br)
