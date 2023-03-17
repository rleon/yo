"""YO cloud tools
"""
from utils.git import *
from utils.gerrit import *
from utils.cache import get_branch_cache
from profiles import get_config

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
            "-s",
            "--status",
            dest="status",
            action="store_true",
            help="Get regression status",
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

    config = get_config("verify")
    remote = get_gerrit_remote()

    git_remote_update([remote])
    branches = config["branches"]

    upto = []
    base = []
    topic = []
    issue = []
    changeid = []
    for branch in branches:
        upto += [branch]
        base += [git_find_base(remote, branch)]
        topic += [config["topic"]]

        cache = get_branch_cache(branch)
        issue += [cache['issue']]
        changeid += [cache['changeid']]

    git_push_squash_gerrit(remote, upto, base, branches, topic, issue,
                           changeid, args.dry_run, args.verbose)
