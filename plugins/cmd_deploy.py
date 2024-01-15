"""YO cloud tools
"""
from utils.cloud import *

import os
import ipaddress
import subprocess
from utils.git import *
from utils.misc import *

def is_ipv4(string):
    try:
        ipaddress.IPv4Network(string)
        return True
    except ipaddress.AddressValueError:
        return False

def rebuild_kernel(name, br, headers, clean):
    with open("%s/scripts/yo-kbuild" % (yo_root()), "r") as f:
        exec_on_remote(name, args=["_BRANCH=%s" % (br), "_WITH_H=%s" % (headers),
                                   "_CLEAN=%s" % (clean), "bash"], script=f)


def init_setup(name, br):
    o = subprocess.check_output(['%s/scripts/yo-mirror' % (yo_root()), 'hpchead.lab.mtl.com', 'kernel'])
    print(o.strip().decode("utf-8"))
    with open('%s/scripts/yo-cloud-init' % (yo_root()), "r") as f:
        lines = []
        with open(os.path.expanduser('~/.ssh/known_hosts'), "r") as sr:
            lines = sr.readlines()
        with open(os.path.expanduser('~/.ssh/known_hosts'), "w") as sw:
            for line in lines:
                if line.startswith(name):
                    continue
                sw.write(line)

        exec_on_remote(name, args=["bash"], script=f)
    rebuild_kernel(name, br, True, False)

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
    parser.add_argument(
            "--with-headers",
            dest="with_headers",
            action="store_true",
            help="Install kernel headers too",
            default=False)
    parser.add_argument(
            "--with-clean",
            dest="clean",
            action="store_true",
            help="Call to make clean",
            default=False)

def cmd_deploy(args):
    """Deploy flow"""
    args.root = git_root()
    if args.root is None:
        exit()

    args.project = get_project(args)
    if args.project != "kernel":
        exit("Upload is supported for kernel tree only.")

    if args.name is None and not is_ipv4(args.init):
        args.name = ActiveSessions.get_players("to deploy")

    br = "%s" % (git_current_branch())
    if is_ipv4(args.init):
        # Special case, where user provided --init without any branch
        # followed by VM address
        init_setup(args.init, br)
        exit()
    elif args.init is not None:
        if args.init == ' ':
            args.init = br
        init_setup(args.name, args.init)
        exit()

    branches = [[br, br]]
    remote = "ssh://%s/w/kernel" % (args.name)
    git_push_branches(branches, True, args.dry_run, remote)

    if args.no_install or args.dry_run:
        exit()

    rebuild_kernel(args.name, br, args.with_headers, args.clean)
