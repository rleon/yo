"""YO cloud tools
"""
from utils.git import *
from utils.gerrit import *
from utils.cache import get_branch_cache
from profiles import get_config

#--------------------------------------------------------------------------------------------------------
def args_push(parser):
    parser.add_argument(
            "-s",
            "--squash",
            dest="squash",
            action="store_true",
            help="Squash all commits into one patch",
            default=False)
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
    parser.add_argument(
            "--upto",
            dest="upto",
            nargs=1,
            help="Push upto to this specific commit")
    parser.add_argument(
            "--topic",
            dest="topic",
            nargs=1,
            help="Push to this specific topic")
    parser.add_argument(
            "--base",
            dest="base",
            nargs=1,
            help="Base push on specific branch")

def cmd_push(args):
    """Push to gerrit"""

    args.root = git_root()
    if args.root is None:
        exit()

    remote = get_gerrit_remote()

    git_remote_update([remote])
    branch = git_current_branch()
    cache = get_branch_cache(branch)

    if not args.base:
        base = git_find_base(remote, branch)
    else:
        base = args.base[0]

    if not args.topic:
        args.topic=branch;
    else:
        args.topic=args.topic[0]

    if not args.upto:
        args.upto = git_current_sha()
    else:
        args.upto = args.upto[0]

    issue = cache['issue']
    changeid = cache['changeid']

    if args.squash:
        git_push_squash_gerrit(remote, args.upto, base, branch, args.topic,
                               issue, changeid, args.dry_run, args.verbose)
        return

    try:
        git_push_gerrit(remote, args.upto, base, args.topic, args.dry_run)
    except subprocess.CalledProcessError:
        # nothing to commit, working tree clean
        pass
