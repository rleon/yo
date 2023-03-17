"""YO cloud tools
"""
import os
import tempfile
from utils.git import *
from utils.gerrit import get_gerrit_remote, git_push_gerrit
from utils.cache import get_branch_cache
from utils.misc import in_directory
from profiles import get_config

def buiild_commit(remote, branch, changeid, verbose, dry_run):
    base_branch = git_find_base(remote, branch)
    base = "%s/%s" % (remote, base_branch)

    git_reset_branch(base, verbose)
    log = git_simple_output(['log', '-n', '100', '--abbrev=12',
                            '--format=commit %h (\"%s\")', 'HEAD..', branch])
    try:
        git_merge_squash(branch, verbose)
    except subprocess.CalledProcessError:
        return

    with tempfile.NamedTemporaryFile('w') as F:
        F.write('%s testing\n\n%s\n\nIssue: 1308201\nChange-Id: %s\n' % (branch, log, changeid))
        F.flush()

        try:
            git_commit_from_file(F.name, verbose)
        except subprocess.CalledProcessError:
            # nothing to commit, working tree clean
            pass

        try:
            git_push_gerrit(remote, "HEAD", base_branch, "leon_testing", dry_run)
        except subprocess.CalledProcessError:
            # nothing to commit, working tree clean
            pass

def buiild_commits(remote, branches, dry_run=False, verbose=False):
    with tempfile.TemporaryDirectory() as d:
        git_detach_workspace(d, verbose)

        with in_directory(d):
            for branch in branches:
                cache = get_branch_cache(branch)
                changeid = cache['changeid']
                buiild_commit(remote, branch, changeid, verbose, dry_run)

    git_worktree_prune()

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

    buiild_commits(remote, branches, args.dry_run, args.verbose)
