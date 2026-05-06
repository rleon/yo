"""YO local kernel build with ccache
"""
import os
import subprocess
from utils.git import *
from utils.misc import *

CCACHE_DIR = os.path.expanduser("~/ccache")

def args_build(parser):
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Run 'make clean' instead of building",
        default=False)
    parser.add_argument(
        "-v",
        "--verbose",
        dest="verbose",
        action="store_true",
        help="Be more verbose (drop make's -s flag)",
        default=False)

def cmd_build(args):
    """Build the kernel locally with ccache"""
    args.root = git_root()
    if args.root is None:
        exit()

    args.project = get_project(args)
    if args.project != "kernel":
        exit("Build is supported for kernel tree only.")

    if args.clean:
        subprocess.check_call(["make", "clean"], cwd=args.root)
        return

    if not os.path.exists(os.path.join(args.root, ".config")):
        exit("No .config in %s. Configure the kernel first (e.g. 'make defconfig')." % args.root)

    os.makedirs(CCACHE_DIR, exist_ok=True)

    env = os.environ.copy()
    env["CCACHE_DIR"] = CCACHE_DIR

    num_jobs = len(os.sched_getaffinity(0)) * 2
    cmd = ["make", "CC=ccache gcc", "-j%d" % num_jobs]
    if not args.verbose:
        cmd += ["-s"]

    subprocess.check_call(cmd, cwd=args.root, env=env)
