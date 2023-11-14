"""YO cloud tools
"""
from utils.cloud import get_user_sessions, get_base_headers, get_players_info

import os
import subprocess
import questionary
from utils.git import *
from utils.misc import exec_on_remote, get_project

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

def cmd_deploy(args):
    """Deploy flow"""
    args.root = git_root()
    if args.root is None:
        exit()

    args.project = get_project(args)
    if args.project != "kernel":
        exit("Upload is supported for kernel tree only.")

    if args.name is None:
        r = get_user_sessions()
        players = get_players_info(r)
        if players is None:
            exit("There are no active setups to deploy")

        choice = questionary.select("Which server to deploy?", players).ask()
        if choice is None:
            exit()

        args.name = choice.split(' ')[0]

    br = "%s" % (git_current_branch())
    branches = [[br, br]]
    remote = "ssh://%s/w/kernel" % (args.name)
    git_push_branches(branches, True, args.dry_run, remote)

    if args.no_install or args.dry_run:
        exit()

    cmd = ['cd /w/kernel && \
            git checkout %s && \
            make -s -j 100 && \
            sudo make modules_install install && \
            sudo grubby --set-default $(ls -t -1 /boot/vmlinuz-* | head -1) && \
            sudo reboot' % (br)]
    exec_on_remote(args.name, cmd)
