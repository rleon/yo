"""YO cloud tools
"""
import os
from utils.git import *
from utils.misc import *
from utils.ci import *

#--------------------------------------------------------------------------------------------------------
def args_verify(parser):
    parser.add_argument(
            "-n",
            "--dry-run",
            dest="dry_run",
            action="store_true",
            help="dry run",
            default=False)
    parser.add_argument(
            "-v",
            "--verbose",
            dest="verbose",
            action="store_true",
            help="Be more verbose",
            default=False)

def cmd_verify(args):
    """Verify branches"""

    args.root = git_root()
    if args.root is None:
        exit()

    args.project = get_project(args)
    if args.project != "kernel":
        exit("Verify is supported for kernel tree only.")

    args.num_jobs = len(os.sched_getaffinity(0)) * 2
    args.rev = "HEAD"

    git_call(["--no-pager", "log", "--oneline", "-n1", args.rev])
    run_nbu_ci(args.rev)
